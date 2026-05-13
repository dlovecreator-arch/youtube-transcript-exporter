"""Safe self-healing helpers for ytx."""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .config import DOWNLOAD_ARCHIVE, OUT_DIR, REPO_ROOT


@dataclass
class FixPlan:
    channel_meta_dirs: list[str] = field(default_factory=list)
    nested_channel_dirs: list[str] = field(default_factory=list)
    archive_missing_ids: int = 0

    @property
    def needs_work(self) -> bool:
        return bool(self.channel_meta_dirs or self.nested_channel_dirs or self.archive_missing_ids)


def _is_video_id(name: str) -> bool:
    return len(name) == 11 and not name.startswith("UC")


def build_plan() -> FixPlan:
    plan = FixPlan()
    if not OUT_DIR.exists():
        return plan

    for channel_dir in sorted(OUT_DIR.iterdir()):
        if not channel_dir.is_dir() or channel_dir.name.startswith("."):
            continue
        for sub in sorted(channel_dir.iterdir()):
            if not sub.is_dir() or sub.name == "_channel_meta":
                continue
            if sub.name.startswith("@") or (sub.name.startswith("UC") and len(sub.name) == 24):
                plan.channel_meta_dirs.append(str(sub.relative_to(REPO_ROOT)))
                continue
            if not _is_video_id(sub.name):
                children = list(sub.iterdir())
                if children:
                    video_like = sum(1 for c in children if c.is_dir() and _is_video_id(c.name))
                    if video_like > len(children) * 0.7:
                        plan.nested_channel_dirs.append(str(sub.relative_to(REPO_ROOT)))

    existing: set[str] = set()
    if DOWNLOAD_ARCHIVE.exists():
        for line in DOWNLOAD_ARCHIVE.read_text().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                existing.add(parts[1])

    # For speed, use folder names rather than parsing every .info.json.
    # Canonical layout is out/<channel>/<video_id>/.
    found: set[str] = {
        folder.name
        for folder in OUT_DIR.glob("*/*")
        if folder.is_dir() and folder.name != "_channel_meta" and _is_video_id(folder.name)
    }
    plan.archive_missing_ids = len(found - existing)
    return plan


def render_plan(plan: FixPlan) -> str:
    lines = ["# ytx fix plan", ""]
    if not plan.needs_work:
        lines.append("No safe fixes needed.")
        return "\n".join(lines)
    if plan.channel_meta_dirs:
        lines.append(f"- Quarantine {len(plan.channel_meta_dirs)} @handle/UCxxx metadata folder(s) into _channel_meta/:")
        for p in plan.channel_meta_dirs[:20]:
            lines.append(f"  - {p}")
        if len(plan.channel_meta_dirs) > 20:
            lines.append(f"  - ... {len(plan.channel_meta_dirs) - 20} more")
    if plan.nested_channel_dirs:
        lines.append(f"- Flatten {len(plan.nested_channel_dirs)} nested channel-name folder(s):")
        for p in plan.nested_channel_dirs[:20]:
            lines.append(f"  - {p}")
    if plan.archive_missing_ids:
        lines.append(f"- Add {plan.archive_missing_ids} existing video id(s) to {DOWNLOAD_ARCHIVE.relative_to(REPO_ROOT)}")
    lines += ["", "Apply with: python3 -m ytx fix --apply"]
    return "\n".join(lines)


def apply() -> int:
    """Apply safe repairs. Never deletes user data."""
    commands = [
        [sys.executable, str(REPO_ROOT / "tools" / "normalize_out_layout.py")],
        [sys.executable, str(REPO_ROOT / "tools" / "seed_download_archive.py")],
    ]
    for cmd in commands:
        rc = subprocess.call(cmd, cwd=REPO_ROOT)
        if rc != 0:
            return rc
    return 0
