"""Status dashboard for the local YouTube transcript dataset."""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from .config import DB_FILE, MARKDOWN_DIR, OUT_DIR, REPO_ROOT, TRASH_DIR


def _du(path: Path) -> str:
    if not path.exists():
        return "0B"
    try:
        out = subprocess_check_output(["du", "-sh", str(path)])
        return out.split()[0]
    except Exception:
        return "?"


def subprocess_check_output(cmd: list[str]) -> str:
    import subprocess
    return subprocess.check_output(cmd, text=True).strip()


def _count_fast(pattern: str, root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for _ in root.glob(pattern))


@dataclass
class Status:
    db_videos: int
    db_channels: int
    out_channels: int
    out_infos: int
    markdown_channels: int
    markdown_files: int
    caption_pct: float
    media_files: int
    part_files: int
    trash_size: str
    out_size: str
    markdown_size: str
    db_size: str
    disk_free_gb: float
    missing_markdown_channels: list[str]


def collect() -> Status:
    db_channels_set: set[str] = set()
    db_videos = 0
    if DB_FILE.exists():
        db = json.loads(DB_FILE.read_text())
        db_videos = len(db.get("videos", []))
        db_channels_set = set(db.get("channels", {}).keys())

    out_channels_set = {p.name for p in OUT_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")} if OUT_DIR.exists() else set()
    md_channels_set = {p.name for p in MARKDOWN_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")} if MARKDOWN_DIR.exists() else set()
    out_infos = _count_fast("*/*/*.info.json", OUT_DIR)
    vtts = _count_fast("*/*/*.en*.vtt", OUT_DIR)
    markdown_files = _count_fast("*/*.md", MARKDOWN_DIR)
    media_files = sum(1 for ext in ("*.mp4", "*.mkv", "*.webm") for _ in OUT_DIR.rglob(ext)) if OUT_DIR.exists() else 0
    part_files = _count_fast("**/*.part", OUT_DIR)
    total, used, free = shutil.disk_usage(REPO_ROOT)

    return Status(
        db_videos=db_videos,
        db_channels=len(db_channels_set),
        out_channels=len(out_channels_set),
        out_infos=out_infos,
        markdown_channels=len(md_channels_set),
        markdown_files=markdown_files,
        caption_pct=(vtts / out_infos * 100) if out_infos else 0.0,
        media_files=media_files,
        part_files=part_files,
        trash_size=_du(TRASH_DIR),
        out_size=_du(OUT_DIR),
        markdown_size=_du(MARKDOWN_DIR),
        db_size=_du(DB_FILE.parent),
        disk_free_gb=free / (1024**3),
        missing_markdown_channels=sorted(out_channels_set - md_channels_set),
    )


def render(s: Status) -> str:
    lines = [
        "# ytx status",
        "",
        "## Dataset",
        f"- DB: {s.db_videos:,} videos across {s.db_channels:,} channels",
        f"- Raw out/: {s.out_infos:,} info.json files across {s.out_channels:,} channel folders ({s.out_size})",
        f"- Markdown: {s.markdown_files:,} files across {s.markdown_channels:,} channel folders ({s.markdown_size})",
        f"- Caption coverage: {s.caption_pct:.1f}%",
        "",
        "## Disk",
        f"- db/: {s.db_size}",
        f"- .trash/: {s.trash_size}",
        f"- free: {s.disk_free_gb:.1f} GB",
        "",
        "## Health quick-look",
        f"- {'✅' if s.media_files == 0 else '❌'} stray media files in out/: {s.media_files}",
        f"- {'✅' if s.part_files == 0 else '❌'} .part files in out/: {s.part_files}",
        f"- {'✅' if not s.missing_markdown_channels else '⚠️'} channels missing markdown folders: {len(s.missing_markdown_channels)}",
    ]
    for ch in s.missing_markdown_channels[:10]:
        lines.append(f"  - {ch}")
    if len(s.missing_markdown_channels) > 10:
        lines.append(f"  - ... {len(s.missing_markdown_channels) - 10} more")
    lines += [
        "",
        "## Suggested next commands",
        "- python3 -m ytx audit        # full health report",
        "- python3 -m ytx doctor       # environment/dependency check",
        "- python3 -m ytx update       # refresh channels.txt when ready",
    ]
    return "\n".join(lines)
