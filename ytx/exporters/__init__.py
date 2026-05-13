"""JSONL exporter -- the RAG-friendly dump.

Emits one JSON record per video to a single .jsonl file. Each record
contains canonical metadata plus the full transcript text. Optionally
chunked by token-approximation for embeddings.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from .. import log
from ..config import DB_FILE, OUT_DIR


def _read_transcript(video_id: str, channel: str) -> Optional[str]:
    """Find the transcript.en.txt for a video, else read .en.vtt and strip."""
    # canonical layout: out/<channel>/<video_id>/transcript.en.txt
    folder = OUT_DIR / channel / video_id
    txt = folder / "transcript.en.txt"
    if txt.exists():
        return txt.read_text()
    # fallback: vtt
    vtts = list(folder.glob("*.en*.vtt"))
    if vtts:
        return _vtt_to_text(vtts[0].read_text())
    return None


def _vtt_to_text(vtt: str) -> str:
    """Cheap VTT -> plain text. Drops timing lines and headers."""
    lines = []
    for raw in vtt.splitlines():
        line = raw.strip()
        if not line or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        if "-->" in line:
            continue
        if line.isdigit():
            continue
        lines.append(line)
    # dedup adjacent identical lines (YouTube auto-captions are noisy)
    out = []
    prev = None
    for l in lines:
        if l != prev:
            out.append(l)
        prev = l
    return " ".join(out)


def export(output_path: Path, include_transcript: bool = True, channels: Optional[Iterable[str]] = None) -> int:
    """Write JSONL of all videos (optionally filtered by channel)."""
    db = json.loads(DB_FILE.read_text())
    videos = db.get("videos", [])
    if channels:
        wanted = set(channels)
        videos = [v for v in videos if v.get("channel") in wanted]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with output_path.open("w") as fh:
        for v in videos:
            rec = {
                "source_id": f"youtube_{(v.get('channel') or '').lower().replace(' ', '_')}_{v.get('id')}",
                "id": v.get("id"),
                "title": v.get("title"),
                "channel": v.get("channel"),
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
            if include_transcript:
                t = _read_transcript(v.get("id"), v.get("channel") or v.get("uploader") or "")
                rec["transcript"] = t
                rec["has_transcript"] = bool(t)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    log.info("jsonl_export_complete", path=str(output_path), records=n)
    return n
