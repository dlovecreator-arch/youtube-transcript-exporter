#!/usr/bin/env python3
"""Data hygiene utilities for local working folder (NOT committed data).

Goals
- Keep out/<channel>/<video_id>/... layout clean and deterministic.
- Quarantine channel-level metadata folders like out/<channel>/UCxxxx into out/<channel>/_channel_meta/.
- Detect duplicate channel folders (e.g. "EmilioOrtiz" vs "Emilio Ortiz") and offer a safe merge plan.
- Detect temp/artifact files (e.g. *.tmp) and offer deletion.

This script is designed to be SAFE:
- Default mode is dry-run (prints planned actions).
- Use --apply to actually perform changes.

Usage:
  python3 tools/cleanup_data.py               # dry-run
  python3 tools/cleanup_data.py --apply       # execute actions
  python3 tools/cleanup_data.py --apply --yes # execute without prompts
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "out"
MARKDOWN_DIR = REPO_ROOT / "markdown"

VIDEO_ID_RE = re.compile(r"[A-Za-z0-9_\-]{11}$")
CHANNEL_META_RE = re.compile(r"^(UC[a-zA-Z0-9_\-]{10,})$")
TEMP_FILE_RE = re.compile(r".*\.(tmp|temp|part|swp)$", re.IGNORECASE)


def norm_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


@dataclass
class Action:
    kind: str
    src: Path
    dst: Path | None = None
    note: str | None = None


def iter_channel_dirs(base: Path) -> Iterable[Path]:
    if not base.exists():
        return []
    return [p for p in base.iterdir() if p.is_dir() and not p.name.startswith(".")]


def find_duplicate_channel_folders() -> list[list[Path]]:
    groups: dict[str, list[Path]] = {}
    for p in iter_channel_dirs(OUT_DIR):
        groups.setdefault(norm_key(p.name), []).append(p)
    return [v for v in groups.values() if len(v) > 1]


def plan_quarantine_channel_meta() -> list[Action]:
    actions: list[Action] = []
    for chan in iter_channel_dirs(OUT_DIR):
        for child in chan.iterdir():
            if not child.is_dir():
                continue
            if child.name == "_channel_meta":
                continue
            if VIDEO_ID_RE.fullmatch(child.name):
                continue
            if CHANNEL_META_RE.fullmatch(child.name):
                dst_dir = chan / "_channel_meta"
                actions.append(Action(kind="move", src=child, dst=dst_dir / child.name, note="quarantine channel meta"))
    return actions


def plan_delete_temp_files() -> list[Action]:
    actions: list[Action] = []
    if not OUT_DIR.exists():
        return actions
    for p in OUT_DIR.glob("**/*"):
        if p.is_file() and TEMP_FILE_RE.fullmatch(p.name):
            actions.append(Action(kind="delete", src=p, note="temp/artifact"))
    return actions


def plan_markdown_duplicate_channel_folders() -> list[list[Path]]:
    groups: dict[str, list[Path]] = {}
    for p in iter_channel_dirs(MARKDOWN_DIR):
        if p.name.startswith("_"):
            continue
        groups.setdefault(norm_key(p.name.replace("⧸", "/")), []).append(p)
    return [v for v in groups.values() if len(v) > 1]


def print_actions(actions: list[Action]) -> None:
    for a in actions:
        if a.kind == "move":
            print(f"MOVE  {a.src} -> {a.dst}  ({a.note or ''})")
        elif a.kind == "delete":
            print(f"DELETE {a.src}  ({a.note or ''})")


def apply_actions(actions: list[Action]) -> None:
    for a in actions:
        if a.kind == "move":
            assert a.dst is not None
            a.dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(a.src), str(a.dst))
        elif a.kind == "delete":
            a.src.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Execute changes")
    parser.add_argument("--yes", action="store_true", help="Do not prompt")
    args = parser.parse_args()

    print("=== Data Hygiene (dry-run by default) ===")
    print(f"out/: {OUT_DIR}")
    print(f"markdown/: {MARKDOWN_DIR}")

    # 1) out/ channel-meta quarantine
    quarantine = plan_quarantine_channel_meta()
    print(f"\n[1] Quarantine channel-meta folders (non-video-id folders matching UC*)")
    print(f"Planned actions: {len(quarantine)}")
    print_actions(quarantine[:20])
    if len(quarantine) > 20:
        print(f"... and {len(quarantine) - 20} more")

    # 2) temp files
    temp = plan_delete_temp_files()
    print(f"\n[2] Delete temp/artifact files")
    print(f"Planned actions: {len(temp)}")
    print_actions(temp[:20])

    # 3) duplicates
    dups = find_duplicate_channel_folders()
    print(f"\n[3] Duplicate out/ channel folders (needs human decision)")
    if not dups:
        print("None detected")
    else:
        for g in dups:
            print("Possible duplicate group:")
            for p in g:
                print("  -", p)
        print("Note: This script does NOT auto-merge channel folders. It will in a future version, with safeguards.")

    md_dups = plan_markdown_duplicate_channel_folders()
    print(f"\n[4] Duplicate markdown/ channel folders (needs human decision)")
    if not md_dups:
        print("None detected")
    else:
        for g in md_dups:
            print("Possible duplicate group:")
            for p in g:
                print("  -", p)

    actions = quarantine + temp

    if not args.apply:
        print("\nDRY RUN complete. Re-run with --apply to execute the move/delete actions above.")
        return

    if not args.yes:
        resp = input(f"\nApply {len(actions)} actions? Type 'yes' to continue: ")
        if resp.strip().lower() != "yes":
            print("Aborting.")
            return

    apply_actions(actions)
    print("\nDone.")


if __name__ == "__main__":
    main()
