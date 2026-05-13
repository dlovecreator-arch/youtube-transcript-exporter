"""Structured logging for ytx -- human-friendly stdout + JSONL log file."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import LOG_DIR


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Logger:
    """Lightweight logger.

    Writes one .jsonl record per event AND a friendly line to stdout.
    Designed to be cheap, append-only, and grep-friendly.
    """

    def __init__(self, name: str = "ytx"):
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.name = name
        self.path = LOG_DIR / f"{name}.jsonl"

    def _emit(self, level: str, msg: str, **fields: Any) -> None:
        rec = {"ts": _ts(), "level": level, "name": self.name, "msg": msg, **fields}
        try:
            with self.path.open("a") as fh:
                fh.write(json.dumps(rec) + "\n")
        except OSError:
            pass
        prefix = {"info": "\033[32m✓", "warn": "\033[33m!", "error": "\033[31m✗", "debug": "\033[90m·"}.get(level, " ")
        print(f"{prefix}\033[0m {msg}", file=sys.stderr if level == "error" else sys.stdout)

    def info(self, msg: str, **f: Any) -> None: self._emit("info", msg, **f)
    def warn(self, msg: str, **f: Any) -> None: self._emit("warn", msg, **f)
    def error(self, msg: str, **f: Any) -> None: self._emit("error", msg, **f)
    def debug(self, msg: str, **f: Any) -> None: self._emit("debug", msg, **f)


_default = Logger("ytx")


def info(msg: str, **f: Any) -> None: _default.info(msg, **f)
def warn(msg: str, **f: Any) -> None: _default.warn(msg, **f)
def error(msg: str, **f: Any) -> None: _default.error(msg, **f)
def debug(msg: str, **f: Any) -> None: _default.debug(msg, **f)
