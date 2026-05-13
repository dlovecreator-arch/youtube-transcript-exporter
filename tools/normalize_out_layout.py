#!/usr/bin/env python3
"""Normalize out/ layout: quarantine @handle and UCxxx folders, flatten nested channel-name subfolders.

Run after a download (the resilient downloader does this automatically, but if you ran
yt-dlp by hand or imported pre-existing data, run this once).

Idempotent: safe to re-run.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = REPO_ROOT / "out"


def is_video_id_folder(name: str) -> bool:
    """YouTube IDs are 11 chars and don't start with UC."""
    return len(name) == 11 and not name.startswith("UC")


def quarantine_meta(channel_dir: Path) -> int:
    """Move @handle and UCxxx subfolders into _channel_meta/."""
    moved = 0
    meta = channel_dir / "_channel_meta"
    for sub in list(channel_dir.iterdir()):
        if not sub.is_dir() or sub.name == "_channel_meta":
            continue
        if sub.name.startswith("@") or (sub.name.startswith("UC") and len(sub.name) == 24):
            meta.mkdir(exist_ok=True)
            target = meta / sub.name
            i = 0
            while target.exists():
                i += 1
                target = meta / f"{sub.name}_dup{i}"
            shutil.move(str(sub), str(target))
            moved += 1
            print(f"  quarantined: {channel_dir.name}/{sub.name}")
    return moved


def flatten_nested(channel_dir: Path) -> int:
    """If channel_dir contains a single non-video subfolder full of videos, flatten it up."""
    flattened = 0
    for sub in list(channel_dir.iterdir()):
        if not sub.is_dir() or sub.name == "_channel_meta":
            continue
        if is_video_id_folder(sub.name):
            continue
        # subfolder name is something like "GaryVee" or "Amar" -- look inside
        children = list(sub.iterdir())
        if not children:
            try: sub.rmdir()
            except OSError: pass
            continue
        # Are most of them video-id folders?
        video_like = sum(1 for c in children if c.is_dir() and is_video_id_folder(c.name))
        if video_like > len(children) * 0.7:
            print(f"  flattening: {channel_dir.name}/{sub.name} ({video_like} videos)")
            for child in list(sub.iterdir()):
                target = channel_dir / child.name
                if not target.exists():
                    shutil.move(str(child), str(target))
                elif child.is_dir():
                    # merge file-by-file
                    for f in child.iterdir():
                        t = target / f.name
                        if not t.exists():
                            shutil.move(str(f), str(t))
                        elif f.is_file():
                            f.unlink()
                        else:
                            shutil.rmtree(f)
                    try: child.rmdir()
                    except OSError: pass
                else:
                    child.unlink()
            try:
                sub.rmdir()
                flattened += 1
            except OSError as e:
                print(f"  could not remove {sub}: {e}")
    return flattened


def main() -> int:
    if not OUT.exists():
        print("out/ does not exist")
        return 1

    total_meta = 0
    total_flat = 0
    for channel_dir in sorted(OUT.iterdir()):
        if not channel_dir.is_dir() or channel_dir.name.startswith("."):
            continue
        total_meta += quarantine_meta(channel_dir)
        total_flat += flatten_nested(channel_dir)

    print()
    print(f"quarantined: {total_meta} @handle/UCxxx folders -> _channel_meta/")
    print(f"flattened:   {total_flat} nested channel-name subfolders")
    return 0


if __name__ == "__main__":
    sys.exit(main())
