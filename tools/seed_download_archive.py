#!/usr/bin/env python3
"""Seed db/downloaded.txt with all video IDs already present in out/.

Run this once after upgrading to ytx 1.0 so that `ytx update` and
`ytx add <url>` don't re-download anything you already have.

Idempotent: never duplicates entries.
"""
from __future__ import annotations

import json
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

    found: set[str] = set()
    n = 0
    for info in OUT.glob("*/*/*.info.json"):
        n += 1
        try:
            data = json.loads(info.read_text(errors="ignore"))
        except Exception:
            continue
        vid = data.get("id")
        if vid and isinstance(vid, str) and len(vid) == 11 and not vid.startswith("UC"):
            found.add(vid)

    new = found - existing
    if new:
        with ARCHIVE.open("a") as fh:
            for vid in sorted(new):
                fh.write(f"youtube {vid}\n")

    total = len(existing | found)
    print(f"scanned: {n} info.json files")
    print(f"added:   {len(new)} new ids to download archive")
    print(f"total:   {total} ids in {ARCHIVE.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
