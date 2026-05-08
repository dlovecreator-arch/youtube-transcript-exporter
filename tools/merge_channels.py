#!/usr/bin/env python3
"""Safely merge duplicate channel folders in out/ and markdown/.

Problem it solves
- yt-dlp sometimes creates different uploader folder names for the same channel
  (e.g. "EmilioOrtiz" vs "Emilio Ortiz"). This fragments your dataset and
  breaks completeness checks.

Safety design
- Dry-run by default: prints an exact plan.
- Apply mode only moves items; it does not delete data.
- Source folder is renamed to a _legacy_* name after merge so rollback is easy.

Usage
  python3 tools/merge_channels.py                       # dry run
  python3 tools/merge_channels.py --apply --yes         # execute

Optional:
  python3 tools/merge_channels.py --group emilioortiz   # run only one group
"""

from __future__ import annotations

import argparse
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "out"
MD_DIR = REPO_ROOT / "markdown"

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{11}$")


def norm_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def count_video_folders(chan_dir: Path) -> int:
    if not chan_dir.exists():
        return 0
    n = 0
    for p in chan_dir.iterdir():
        if p.is_dir() and VIDEO_ID_RE.match(p.name):
            n += 1
    return n


def list_md_files(chan_dir: Path) -> set[str]:
    if not chan_dir.exists():
        return set()
    return {p.name for p in chan_dir.glob("*.md") if p.is_file()}


@dataclass
class Move:
    src: Path
    dst: Path


def plan_merge_out(group: list[Path]) -> tuple[Path, list[Move], list[Path]]:
    """Choose canonical target (largest), move other folders' VIDEO_ID dirs into it."""
    group = [p for p in group if p.exists()]
    target = max(group, key=count_video_folders)
    moves: list[Move] = []
    legacy_sources: list[Path] = []

    for src in group:
        if src == target:
            continue
        for child in src.iterdir():
            if not child.is_dir():
                continue
            # Move only actual video-id folders and _channel_meta.
            if child.name == "_channel_meta" or VIDEO_ID_RE.match(child.name):
                dst = target / child.name
                if not dst.exists():
                    moves.append(Move(src=child, dst=dst))
                    continue

                # Collision: merge missing files/subfolders from src->dst.
                # We never overwrite existing files.
                for p in child.glob("**/*"):
                    rel = p.relative_to(child)
                    dst_p = dst / rel
                    if p.is_dir():
                        if not dst_p.exists():
                            moves.append(Move(src=p, dst=dst_p))
                        continue
                    if p.is_file() and not dst_p.exists():
                        moves.append(Move(src=p, dst=dst_p))
        legacy_sources.append(src)

    return target, moves, legacy_sources


def plan_merge_markdown(group: list[Path]) -> tuple[Path, list[Move], list[Path]]:
    """Merge markdown channel folders by moving missing *.md files into target."""
    group = [p for p in group if p.exists()]
    target = max(group, key=lambda p: len(list_md_files(p)))
    moves: list[Move] = []
    legacy_sources: list[Path] = []

    target_files = list_md_files(target)
    for src in group:
        if src == target:
            continue
        for f in src.glob("*.md"):
            if not f.is_file():
                continue
            if f.name in target_files:
                continue
            moves.append(Move(src=f, dst=target / f.name))
        legacy_sources.append(src)

    return target, moves, legacy_sources


def rename_to_legacy(src: Path) -> Path:
    legacy = src.parent / ("_legacy_" + src.name)
    if legacy.exists():
        # ensure unique
        i = 2
        while (src.parent / ("_legacy_" + src.name + f"_{i}")).exists():
            i += 1
        legacy = src.parent / ("_legacy_" + src.name + f"_{i}")
    src.rename(legacy)
    return legacy


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--group", help="normalized key to merge only one group")
    args = ap.parse_args()

    # Detect duplicate out/ channel folders
    out_groups: dict[str, list[Path]] = {}
    for p in OUT_DIR.iterdir():
        if p.is_dir() and not p.name.startswith("_"):
            out_groups.setdefault(norm_key(p.name), []).append(p)

    dup_out = {k: v for k, v in out_groups.items() if len(v) > 1}

    # Detect duplicate markdown/ channel folders
    md_groups: dict[str, list[Path]] = {}
    for p in MD_DIR.iterdir():
        if p.is_dir() and not p.name.startswith("_") and not p.name.startswith("."):
            md_groups.setdefault(norm_key(p.name.replace("⧸", "/")), []).append(p)
    dup_md = {k: v for k, v in md_groups.items() if len(v) > 1}

    if args.group:
        dup_out = {k: v for k, v in dup_out.items() if k == args.group}
        dup_md = {k: v for k, v in dup_md.items() if k == args.group}

    if not dup_out and not dup_md:
        print("No duplicate channel groups detected.")
        return

    for key, group in dup_out.items():
        target, moves, legacy_sources = plan_merge_out(group)
        print(f"\n[OUT] Merge group '{key}':")
        for p in group:
            print(f"  - {p.name} (video_folders={count_video_folders(p)})")
        print(f"  Target: {target.name}")
        print(f"  Planned moves: {len(moves)}")
        for m in moves[:20]:
            print(f"    MOVE {m.src} -> {m.dst}")
        if len(moves) > 20:
            print(f"    ... and {len(moves) - 20} more")

    for key, group in dup_md.items():
        target, moves, legacy_sources = plan_merge_markdown(group)
        print(f"\n[MARKDOWN] Merge group '{key}':")
        for p in group:
            print(f"  - {p.name} (md_files={len(list_md_files(p))})")
        print(f"  Target: {target.name}")
        print(f"  Planned moves: {len(moves)}")
        for m in moves[:20]:
            print(f"    MOVE {m.src} -> {m.dst}")
        if len(moves) > 20:
            print(f"    ... and {len(moves) - 20} more")

    if not args.apply:
        print("\nDry-run complete. Re-run with --apply --yes to execute.")
        return

    if not args.yes:
        resp = input("Type 'yes' to apply all moves: ")
        if resp.strip().lower() != "yes":
            print("Aborting")
            return

    # Execute merges
    for key, group in dup_out.items():
        target, moves, legacy_sources = plan_merge_out(group)
        for m in moves:
            m.dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(m.src), str(m.dst))
        for src in legacy_sources:
            # If now empty or only has leftovers that collided, keep as legacy.
            rename_to_legacy(src)

    for key, group in dup_md.items():
        target, moves, legacy_sources = plan_merge_markdown(group)
        for m in moves:
            m.dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(m.src), str(m.dst))
        for src in legacy_sources:
            rename_to_legacy(src)

    print("\nDone. Source folders preserved under _legacy_* names.")


if __name__ == "__main__":
    main()
