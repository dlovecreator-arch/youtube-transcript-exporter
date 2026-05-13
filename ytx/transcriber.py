"""Whisper fallback transcriber for videos without captions.

Some channels (Shorts-heavy, music, foreign-language, or just unlucky) have
no YouTube auto-captions. This module detects those gaps and fills them by
downloading audio-only, transcribing with faster-whisper, and emitting
a .en.vtt file in the same format yt-dlp uses -- so the rest of the
pipeline is unchanged.

Design choices
--------------
- Uses ``faster-whisper`` (CTranslate2) which is ~4x faster than openai-whisper
  on CPU and far less RAM-hungry. Apple Silicon CoreML is enabled automatically.
- Default model: ``small`` (good accuracy + fast). Configurable via env or arg.
- Audio is downloaded as opus (smallest), transcribed, then deleted.
- VAD filter on by default to skip silence.
- Idempotent: if a .en.vtt already exists, skip.

To install:
    pip install faster-whisper

We import lazily so the rest of ytx works without Whisper installed.
"""
from __future__ import annotations

import datetime as _dt
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from . import log
from .config import OUT_DIR


@dataclass
class TranscribeOptions:
    model: str = "small"        # tiny|base|small|medium|large-v3
    language: Optional[str] = "en"
    compute_type: str = "auto"  # "int8" CPU, "int8_float16" GPU, "auto"
    beam_size: int = 5
    vad_filter: bool = True
    delete_audio_after: bool = True


def _has_whisper() -> bool:
    try:
        import faster_whisper  # noqa: F401
        return True
    except ImportError:
        return False


def find_caption_less(out_dir: Path = OUT_DIR) -> list[Path]:
    """Return video folders that have .info.json but no .en.vtt."""
    gaps: list[Path] = []
    for info in out_dir.glob("*/*/*.info.json"):
        folder = info.parent
        has_vtt = any(folder.glob("*.en*.vtt"))
        if not has_vtt:
            gaps.append(folder)
    return gaps


def _seconds_to_vtt_ts(seconds: float) -> str:
    td = _dt.timedelta(seconds=seconds)
    hh = int(td.total_seconds() // 3600)
    mm = int((td.total_seconds() % 3600) // 60)
    ss = td.total_seconds() % 60
    return f"{hh:02d}:{mm:02d}:{ss:06.3f}".replace(".", ",") if False else f"{hh:02d}:{mm:02d}:{ss:06.3f}"


def _segments_to_vtt(segments: Iterable, output: Path) -> int:
    lines = ["WEBVTT", ""]
    n = 0
    for seg in segments:
        start = _seconds_to_vtt_ts(seg.start)
        end = _seconds_to_vtt_ts(seg.end)
        text = (seg.text or "").strip().replace("\n", " ")
        if not text:
            continue
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")
        n += 1
    output.write_text("\n".join(lines))
    return n


def _download_audio(video_url: str, folder: Path) -> Optional[Path]:
    """Download audio-only via yt-dlp into folder. Returns the audio file path."""
    yt = shutil.which("yt-dlp")
    if not yt:
        log.error("yt-dlp not installed; cannot fetch audio for whisper")
        return None
    out_template = str(folder / "_whisper_audio.%(ext)s")
    cmd = [
        yt,
        "-f", "bestaudio[ext=m4a]/bestaudio",
        "--extract-audio",
        "--audio-format", "opus",
        "--audio-quality", "5",
        "-o", out_template,
        "--no-warnings",
        "--ignore-errors",
        video_url,
    ]
    try:
        subprocess.run(cmd, check=False, stdin=subprocess.DEVNULL, timeout=600)
    except subprocess.TimeoutExpired:
        log.warn("audio_download_timeout", url=video_url)
        return None
    audios = list(folder.glob("_whisper_audio.*"))
    return audios[0] if audios else None


def transcribe_folder(folder: Path, opts: TranscribeOptions) -> Optional[Path]:
    """Generate a .en.vtt for a single video folder via Whisper.

    Returns path to created .vtt, or None on failure.
    """
    if any(folder.glob("*.en*.vtt")):
        return None  # already has captions

    info_files = list(folder.glob("*.info.json"))
    if not info_files:
        log.warn("transcribe_no_info_json", folder=str(folder))
        return None

    import json
    info = json.loads(info_files[0].read_text())
    video_url = info.get("webpage_url") or info.get("original_url") or f"https://www.youtube.com/watch?v={info.get('id')}"
    title_stem = info_files[0].name.replace(".info.json", "")
    vtt_path = folder / f"{title_stem}.en.vtt"

    audio = _download_audio(video_url, folder)
    if not audio:
        log.warn("transcribe_audio_missing", folder=str(folder))
        return None

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        log.error("faster_whisper not installed; pip install faster-whisper")
        return None

    log.info("transcribe_start", folder=folder.name, model=opts.model)
    model = WhisperModel(opts.model, compute_type=opts.compute_type)
    segments, _info = model.transcribe(
        str(audio),
        language=opts.language,
        beam_size=opts.beam_size,
        vad_filter=opts.vad_filter,
    )
    n = _segments_to_vtt(segments, vtt_path)
    log.info("transcribe_done", folder=folder.name, segments=n, path=str(vtt_path))

    if opts.delete_audio_after:
        try:
            audio.unlink()
        except OSError:
            pass

    return vtt_path


def transcribe_all(opts: Optional[TranscribeOptions] = None, limit: Optional[int] = None) -> int:
    """Walk out/, find caption-less folders, transcribe each. Returns count generated."""
    if not _has_whisper():
        log.error("whisper_not_installed", hint="pip install faster-whisper")
        return 0
    opts = opts or TranscribeOptions()
    gaps = find_caption_less()
    log.info("transcribe_scan", caption_less=len(gaps))
    if limit:
        gaps = gaps[:limit]
    n = 0
    for folder in gaps:
        if transcribe_folder(folder, opts):
            n += 1
    log.info("transcribe_complete", generated=n)
    return n
