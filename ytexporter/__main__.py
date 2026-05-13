#!/usr/bin/env python3
"""Backward-compatible shim for the old `python -m ytexporter` entrypoint.

The canonical CLI is now `python -m ytx`. This module translates the old command
names where possible and delegates to ytx so there is only one implementation.
"""
from __future__ import annotations

import sys

from ytx.__main__ import main as ytx_main

ALIASES = {
    "health": "doctor",
    "new-channel": "add",
    "rebuild-metadata": "metadata",
    "rebuild-markdown": "markdown",
    "validate": "audit",
}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        args = ["--help"]
    if args and args[0] in ALIASES:
        args[0] = ALIASES[args[0]]
    if args and args[0] == "export-notion":
        print("Notion export is no longer active. Use: python -m ytx export jsonl", file=sys.stderr)
        return 2
    return ytx_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
