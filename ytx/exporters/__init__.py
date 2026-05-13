"""Exporters for RAG and second-brain workflows.

Supports:
- video-level JSONL (`ytx export jsonl`)
- timestamped chunk JSONL (`ytx export chunks`)

The chunk exporter parses VTT timing and creates citation-ready records with
`url_at_timestamp`, so every embedding result can trace back to the exact
YouTube moment.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from .. import log
from ..config import DB_FILE, OUT_DIR


@dataclass
class Segment:
    start: float
    end: float
    text: str


def _source_id(channel: str, video_id: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", (channel or "unknown").lower()).strip("_")
    return f"youtube_{slug}_{video_id}"


def _video_folder(video_id: str, channel: str | None = None) -> Optional[Path]:
    """Find out/<channel>/<video_id>, falling back to a one-off global lookup."""
    if channel:
        folder = OUT_DIR / channel / video_id
        if folder.is_dir():
            return folder
    matches = [p for p in OUT_DIR.glob(f"*/{video_id}") if p.is_dir()]
    return matches[0] if matches else None


def _read_transcript(video_id: str, channel: str) -> Optional[str]:
    """Find transcript.en.txt for a video, else read .en.vtt and strip."""
    folder = _video_folder(video_id, channel)
    if not folder:
        return None
    txt = folder / "transcript.en.txt"
    if txt.exists():
        return txt.read_text(errors="ignore")
    vtts = list(folder.glob("*.en*.vtt"))
    if vtts:
        return _vtt_to_text(vtts[0].read_text(errors="ignore"))
    return None


def _clean_caption_text(text: str) -> str:
    text = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("[Music]", "").replace("[music]", "").replace("[Applause]", "")
    return re.sub(r"\s+", " ", text).strip()


def _vtt_to_text(vtt: str) -> str:
    """Cheap VTT -> plain text. Drops timing lines and headers."""
    lines = []
    for raw in vtt.splitlines():
        line = raw.strip()
        if not line or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE", "STYLE")):
            continue
        if "-->" in line:
            continue
        if line.isdigit():
            continue
        line = _clean_caption_text(line)
        if line:
            lines.append(line)
    out = []
    prev = None
    for line in lines:
        if line != prev:
            out.append(line)
        prev = line
    return " ".join(out)


def _parse_ts(ts: str) -> float:
    """Parse VTT timestamp to seconds."""
    ts = ts.strip().replace(",", ".")
    parts = ts.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return float(ts)


def parse_vtt_segments(vtt: str) -> list[Segment]:
    """Parse VTT into timestamped segments.

    Handles multi-line cues and strips YouTube's inline progressive timestamp
    markers.
    """
    segments: list[Segment] = []
    lines = vtt.splitlines()
    i = 0
    previous_full = ""
    while i < len(lines):
        line = lines[i].strip()
        if "-->" not in line:
            i += 1
            continue
        times = line.split("-->")
        start = _parse_ts(times[0].strip())
        end = _parse_ts(times[1].strip().split()[0])
        i += 1
        text_lines: list[str] = []
        while i < len(lines) and lines[i].strip():
            text_lines.append(lines[i].strip())
            i += 1
        full_text = _clean_caption_text(" ".join(text_lines))
        text = full_text
        # YouTube auto-captions often emit progressive cues where each cue
        # repeats the previous text and appends a few words. Keep only the new
        # suffix so chunks do not become 3x repetitive.
        if previous_full and full_text.startswith(previous_full):
            text = full_text[len(previous_full):].strip()
        elif previous_full and previous_full in full_text:
            text = full_text.split(previous_full, 1)[-1].strip()
        if full_text:
            previous_full = full_text
        if text:
            if not segments or segments[-1].text != text:
                segments.append(Segment(start=start, end=end, text=text))
        i += 1
    return segments


def _record_base(v: dict) -> dict:
    video_id = v.get("id")
    channel = v.get("channel") or v.get("uploader") or "Unknown"
    return {
        "source_id": _source_id(channel, video_id),
        "id": video_id,
        "title": v.get("title"),
        "channel": channel,
        "channel_id": v.get("channel_id"),
        "uploader": v.get("uploader"),
        "guest": v.get("guest"),
        "date": v.get("date"),
        "duration": v.get("duration"),
        "views": v.get("views"),
        "likes": v.get("likes"),
        "url": v.get("url"),
        "category": v.get("category"),
        "tags": v.get("tags", []),
        "description": v.get("description"),
    }


def export_jsonl(output_path: Path, include_transcript: bool = True, channels: Optional[Iterable[str]] = None) -> int:
    """Write video-level JSONL of all videos (optionally filtered by channel)."""
    db = json.loads(DB_FILE.read_text())
    videos = db.get("videos", [])
    if channels:
        wanted = set(channels)
        videos = [v for v in videos if v.get("channel") in wanted]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with output_path.open("w") as fh:
        for v in videos:
            rec = _record_base(v)
            if include_transcript:
                t = _read_transcript(v.get("id"), rec["channel"])
                rec["transcript"] = t
                rec["has_transcript"] = bool(t)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    log.info("jsonl_export_complete", path=str(output_path), records=n)
    return n


def _segments_for_video(video_id: str, channel: str) -> list[Segment]:
    folder = _video_folder(video_id, channel)
    if not folder:
        return []
    vtts = sorted(folder.glob("*.en*.vtt"))
    if not vtts:
        return []
    return parse_vtt_segments(vtts[0].read_text(errors="ignore"))


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def export_chunks(
    output_path: Path,
    channels: Optional[Iterable[str]] = None,
    chunk_tokens: int = 800,
    overlap_tokens: int = 120,
    max_videos: Optional[int] = None,
) -> int:
    """Export timestamped transcript chunks for embeddings/RAG."""
    db = json.loads(DB_FILE.read_text())
    videos = db.get("videos", [])
    if channels:
        wanted = set(channels)
        videos = [v for v in videos if v.get("channel") in wanted]
    if max_videos:
        videos = videos[:max_videos]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with output_path.open("w") as fh:
        for v in videos:
            base = _record_base(v)
            segments = _segments_for_video(base["id"], base["channel"])
            if not segments:
                continue

            chunk: list[Segment] = []
            chunk_text = ""
            chunk_idx = 0

            def flush(current: list[Segment]) -> None:
                nonlocal n, chunk_idx
                if not current:
                    return
                text = " ".join(s.text for s in current).strip()
                if not text:
                    return
                start = current[0].start
                end = current[-1].end
                rec = {
                    **base,
                    "chunk_id": f"{base['source_id']}_{chunk_idx:05d}",
                    "chunk_index": chunk_idx,
                    "start_seconds": round(start, 3),
                    "end_seconds": round(end, 3),
                    "url_at_timestamp": f"{base['url']}?t={int(start)}" if base.get("url") else None,
                    "text": text,
                    "token_count": _approx_tokens(text),
                    "transcript_source": "youtube_caption",
                }
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
                chunk_idx += 1

            for seg in segments:
                proposed = (chunk_text + " " + seg.text).strip()
                if chunk and _approx_tokens(proposed) > chunk_tokens:
                    flush(chunk)
                    # Retain a small text overlap by segment. Approximate but stable.
                    overlap: list[Segment] = []
                    overlap_text = ""
                    for prev in reversed(chunk):
                        test = (prev.text + " " + overlap_text).strip()
                        if _approx_tokens(test) > overlap_tokens:
                            break
                        overlap.insert(0, prev)
                        overlap_text = test
                    chunk = overlap[:]
                    chunk_text = " ".join(s.text for s in chunk)
                chunk.append(seg)
                chunk_text = (chunk_text + " " + seg.text).strip()
            flush(chunk)

    log.info("chunk_export_complete", path=str(output_path), chunks=n)
    return n


# Backwards-compatible name used by ytx.__main__ before chunk export existed.
export = export_jsonl
