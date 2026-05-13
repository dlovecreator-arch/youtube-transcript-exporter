"""Repo paths and runtime config for ytx."""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "out"
DB_DIR = REPO_ROOT / "db"
DB_FILE = DB_DIR / "canonical.json"
MARKDOWN_DIR = REPO_ROOT / "markdown"
ARCHIVE_DIR = REPO_ROOT / "archive"
LOG_DIR = REPO_ROOT / "logs"
TRASH_DIR = REPO_ROOT / ".trash"
CHANNELS_FILE = REPO_ROOT / "channels.txt"

# yt-dlp archive: one global archive so re-runs are O(1) idempotent
DOWNLOAD_ARCHIVE = DB_DIR / "downloaded.txt"

# Adaptive timeouts (seconds) based on estimated channel size
TIMEOUTS = {
    "small": 600,      # < 500 videos
    "medium": 3600,    # 500-2000
    "large": 7200,     # 2000+
    "xlarge": 14400,   # 5000+
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
]


def ensure_dirs() -> None:
    for d in (OUT_DIR, DB_DIR, MARKDOWN_DIR, ARCHIVE_DIR, LOG_DIR, TRASH_DIR):
        d.mkdir(parents=True, exist_ok=True)


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, "").lower() in ("1", "true", "yes", "on") if name in os.environ else default
