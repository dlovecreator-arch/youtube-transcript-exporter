"""Audit + alignment checks -- the single 'is this healthy?' command."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from . import log
from .config import DB_FILE, MARKDOWN_DIR, OUT_DIR


@dataclass
class AuditReport:
    ok: bool = True
    videos_in_db: int = 0
    channels_in_db: int = 0
    out_video_folders: int = 0
    out_channels: int = 0
    markdown_files: int = 0
    markdown_channels: int = 0
    caption_coverage_pct: float = 0.0
    orphan_vtts: int = 0
    missing_markdown_channels: list[str] = field(default_factory=list)
    missing_db_channels: list[str] = field(default_factory=list)
    whitespace_folders: list[str] = field(default_factory=list)
    media_files: int = 0
    part_files: int = 0
    notes: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [
            "# YouTube Transcript Exporter -- Audit Report",
            "",
            "## Counts",
            f"- DB videos: {self.videos_in_db}",
            f"- DB channels: {self.channels_in_db}",
            f"- out/ video folders: {self.out_video_folders}",
            f"- out/ channel folders: {self.out_channels}",
            f"- markdown files: {self.markdown_files}",
            f"- markdown channel folders: {self.markdown_channels}",
            f"- caption coverage: {self.caption_coverage_pct:.1f}%",
            "",
            "## Health",
        ]
        flag = "✓" if not self.missing_markdown_channels else "✗"
        lines.append(f"- {flag} channels missing markdown: {len(self.missing_markdown_channels)}")
        if self.missing_markdown_channels:
            for c in self.missing_markdown_channels[:20]:
                lines.append(f"    - {c}")
        flag = "✓" if not self.missing_db_channels else "✗"
        lines.append(f"- {flag} channels missing from DB: {len(self.missing_db_channels)}")
        if self.missing_db_channels:
            for c in self.missing_db_channels[:20]:
                lines.append(f"    - {c}")
        flag = "✓" if not self.whitespace_folders else "✗"
        lines.append(f"- {flag} folders with whitespace issues: {len(self.whitespace_folders)}")
        for c in self.whitespace_folders[:5]:
            lines.append(f"    - {c}")
        flag = "✓" if self.media_files == 0 else "✗"
        lines.append(f"- {flag} stray media files in out/: {self.media_files}")
        flag = "✓" if self.part_files == 0 else "✗"
        lines.append(f"- {flag} .part orphan files: {self.part_files}")
        flag = "✓" if self.orphan_vtts == 0 else "!"
        lines.append(f"- {flag} orphan .vtt files (no info.json sibling): {self.orphan_vtts}")
        lines.append("")
        if self.notes:
            lines.append("## Notes")
            for n in self.notes:
                lines.append(f"- {n}")
        lines.append("")
        lines.append("---")
        lines.append(f"overall: {'PASS' if self.ok else 'NEEDS ATTENTION'}")
        return "\n".join(lines)


def run(full: bool = True, log_result: bool = True) -> AuditReport:
    rep = AuditReport()

    # DB
    if DB_FILE.exists():
        db = json.loads(DB_FILE.read_text())
        rep.videos_in_db = len(db.get("videos", []))
        rep.channels_in_db = len(db.get("channels", {}))
        db_channels = set(db.get("channels", {}).keys())
    else:
        db_channels = set()
        rep.notes.append("db/canonical.json does not exist")
        rep.ok = False

    # out/
    out_channels = {p.name for p in OUT_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")}
    rep.out_channels = len(out_channels)
    rep.out_video_folders = sum(1 for _ in OUT_DIR.glob("*/*/*.info.json"))

    # markdown/
    md_channels = {p.name for p in MARKDOWN_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")}
    rep.markdown_channels = len(md_channels)
    rep.markdown_files = sum(1 for _ in MARKDOWN_DIR.glob("*/*.md"))

    # captions
    info_total = rep.out_video_folders
    vtt_total = sum(1 for _ in OUT_DIR.glob("*/*/*.en*.vtt"))
    rep.caption_coverage_pct = (vtt_total / info_total * 100) if info_total else 0.0

    if full:
        # orphan vtts -- vtt without sibling info.json in same folder
        orphan_count = 0
        for vtt in OUT_DIR.glob("*/*/*.en*.vtt"):
            if not list(vtt.parent.glob("*.info.json")):
                orphan_count += 1
        rep.orphan_vtts = orphan_count
    else:
        rep.notes.append("quick mode: skipped orphan VTT scan")

    # alignment
    rep.missing_markdown_channels = sorted(out_channels - md_channels - {"_channel_meta"})
    rep.missing_db_channels = sorted(out_channels - db_channels - {"_channel_meta"})

    # whitespace
    for base in (OUT_DIR, MARKDOWN_DIR):
        for p in base.iterdir():
            if p.is_dir() and p.name != p.name.strip():
                rep.whitespace_folders.append(str(p))

    if full:
        # media bloat
        rep.media_files = sum(1 for _ in OUT_DIR.rglob("*.mp4")) + sum(1 for _ in OUT_DIR.rglob("*.mkv")) + sum(1 for _ in OUT_DIR.rglob("*.webm"))
        rep.part_files = sum(1 for _ in OUT_DIR.rglob("*.part"))
    else:
        rep.notes.append("quick mode: skipped recursive media/.part scan")

    rep.ok = (
        not rep.missing_markdown_channels
        and not rep.missing_db_channels
        and not rep.whitespace_folders
        and rep.media_files == 0
        and rep.part_files == 0
    )
    if log_result:
        log.info(
            "audit_complete",
            ok=rep.ok,
            db_videos=rep.videos_in_db,
            out_folders=rep.out_video_folders,
            md_files=rep.markdown_files,
            caption_pct=round(rep.caption_coverage_pct, 1),
        )
    return rep
