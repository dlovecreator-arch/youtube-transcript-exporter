#!/usr/bin/env python3
"""Unified CLI for YouTube Transcript Exporter.

Design goals
- Keep existing scripts working (export.sh is the stable interface).
- Provide a single, friendly entrypoint for users:

    python -m ytexporter ...

- Keep dependencies minimal (stdlib only).

Examples
  python -m ytexporter health
  python -m ytexporter new-channel https://www.youtube.com/@LexFridman
  python -m ytexporter rebuild-metadata
  python -m ytexporter rebuild-markdown
  python -m ytexporter audit

Notes
- This CLI shells out to existing scripts, so behavior stays consistent.
- It is intentionally conservative: no auto-deletes.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPORT_SH = REPO_ROOT / "export.sh"
HEALTH_CHECK = REPO_ROOT / "system_health_check.py"
VALIDATE_PROD = REPO_ROOT / "validate_production.sh"


def run(cmd: list[str], *, cwd: Path = REPO_ROOT) -> int:
    proc = subprocess.run(cmd, cwd=str(cwd))
    return proc.returncode


def ensure_exists(path: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"Missing {label}: {path}")


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="ytexporter",
        description="YouTube Transcript Exporter (unified CLI)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("health", help="Run system health check")
    sub.add_parser("validate", help="Run production readiness validator")

    p_new = sub.add_parser("new-channel", help="Download + process a new channel URL")
    p_new.add_argument("url")

    sub.add_parser("rebuild-metadata", help="Rebuild db/canonical.json from out/*.info.json")
    sub.add_parser("rebuild-markdown", help="(Incremental) regenerate markdown vault")
    sub.add_parser("audit", help="Run quality audit")

    p_notion = sub.add_parser("export-notion", help="Export to Notion (optional)")
    p_notion.add_argument("--max", type=int, default=None)

    args = parser.parse_args(argv)

    if args.cmd == "health":
        ensure_exists(HEALTH_CHECK, "health check")
        return run([sys.executable, str(HEALTH_CHECK)])

    if args.cmd == "validate":
        ensure_exists(VALIDATE_PROD, "production validator")
        return run(["bash", str(VALIDATE_PROD)])

    ensure_exists(EXPORT_SH, "export.sh")

    if args.cmd == "new-channel":
        return run(["bash", str(EXPORT_SH), "--new-channel", args.url])

    if args.cmd == "rebuild-metadata":
        return run(["bash", str(EXPORT_SH), "--rebuild-metadata"])

    if args.cmd == "rebuild-markdown":
        return run(["bash", str(EXPORT_SH), "--rebuild-markdown"])

    if args.cmd == "audit":
        return run(["bash", str(EXPORT_SH), "--audit"])

    if args.cmd == "export-notion":
        cmd = ["bash", str(EXPORT_SH), "--export-notion"]
        if args.max is not None:
            cmd += ["--max", str(args.max)]
        return run(cmd)

    raise SystemExit("Unknown command")


if __name__ == "__main__":
    raise SystemExit(main())
