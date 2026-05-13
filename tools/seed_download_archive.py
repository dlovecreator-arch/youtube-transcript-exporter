#!/usr/bin/env python3
"""Seed db/downloaded.txt with all video IDs already present in out/.

Run this once after upgrading to ytx 1.0 so that `ytx update` and
`ytx add <url>` don't re-download anything you already have.

Idempotent: never duplicates entries.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = REPO_ROOT / "out"
ARCHIVE = REPO_ROOT / "db" / "downloaded.txt"


def main() -> None:
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    existing: set[str] = set()
    if ARCHIVE.exists():
        for line in ARCHIVE.read_text().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                existing.add(parts[1])

    # Use canonical folder names instead of parsing every .info.json. This is
    # much faster on large corpora and matches the enforced layout:
    # out/<channel>/<video_id>/.
    folders = [
        p for p in OUT.glob("*/*")
        if p.is_dir() and p.name != "_channel_meta" and len(p.name) == 11 and not p.name.startswith("UC")
    ]
    found = {p.name for p in folders}

    new = found - existing
    if new:
        with ARCHIVE.open("a") as fh:
            for vid in sorted(new):
                fh.write(f"youtube {vid}\n")

    total = len(existing | found)
    print(f"scanned: {len(folders)} video folders")
    print(f"added:   {len(new)} new ids to download archive")
    print(f"total:   {total} ids in {ARCHIVE.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
