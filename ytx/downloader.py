"""Resilient yt-dlp wrapper -- the masterpiece downloader.

Why this exists
---------------
yt-dlp is excellent, but YouTube actively fights bulk extraction. Naive
loops break in 10+ ways: rate limiting, expired PO tokens, age gates,
captions toggling on/off, channel /videos pagination hiding history,
network blips, hangs, partial downloads, and "this video is private".

This module is the lessons-learned-distilled, community-recommended set
of defaults that makes channel-scale extraction reliable.

Key features
------------
1. Idempotent re-runs via yt-dlp's --download-archive
2. Adaptive timeout based on channel size
3. /videos -> root URL auto-fallback (recovers full channel history)
4. Multi-client extractor (android,web,ios) for PO-token resilience
5. Cookies-from-browser opt-in (huge reliability win vs rate limits)
6. Subtitles + auto-subs + info.json only (no media bloat by default)
7. Fragment + file-access retries
8. Quarantines @handle/UCxxx folders that yt-dlp creates by mistake
9. Channel-meta separation -- never confuses channel listings with videos

References (best practice, public yt-dlp wiki + GitHub discussions):
- https://github.com/yt-dlp/yt-dlp/wiki/Extractors#youtube
- yt-dlp issue trackers on rate-limiting and PO tokens
- Community recipes for archiving channels
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from . import log
from .config import (
    DOWNLOAD_ARCHIVE,
    OUT_DIR,
    TIMEOUTS,
    USER_AGENTS,
    ensure_dirs,
)


@dataclass
class DownloadOptions:
    """User-tunable download options.

    Defaults are conservative for unattended channel-scale runs.
    """
    cookies_from_browser: Optional[str] = None  # e.g. "chrome", "safari", "firefox"
    cookies_file: Optional[Path] = None
    proxy: Optional[str] = None
    sleep_requests: float = 1.0
    sleep_interval: float = 2.5
    max_sleep_interval: float = 10.0
    retries: int = 10
    fragment_retries: int = 10
    file_access_retries: int = 5
    socket_timeout: int = 20
    sub_langs: str = "en.*,en"  # en plus en-US, en-GB, etc.
    extractor_clients: tuple[str, ...] = ("android", "web", "ios")
    write_thumbnail: bool = False
    write_description: bool = True  # cheap, valuable for guests/show notes
    keep_video: bool = False  # never download media by default
    max_attempts: int = 5
    inter_attempt_sleep: int = 120

    extra_args: list[str] = field(default_factory=list)


def _yt_dlp_bin() -> str:
    bin_ = shutil.which("yt-dlp")
    if not bin_:
        raise SystemExit("yt-dlp not found in PATH. Install with: pip install -U yt-dlp")
    return bin_


def _user_agent(idx: int) -> str:
    return USER_AGENTS[idx % len(USER_AGENTS)]


def _count_info_json(out_dir: Path) -> int:
    """Count completed downloads (one .info.json per video)."""
    return sum(1 for _ in out_dir.glob("*/*/*.info.json"))


def _estimate_timeout(known_count: int) -> int:
    """Pick a timeout bucket based on observed/estimated channel size."""
    if known_count >= 5000:
        return TIMEOUTS["xlarge"]
    if known_count >= 2000:
        return TIMEOUTS["large"]
    if known_count >= 500:
        return TIMEOUTS["medium"]
    return TIMEOUTS["small"]


def _build_argv(url: str, opts: DownloadOptions, attempt: int) -> list[str]:
    """Build the yt-dlp argument vector for one attempt."""
    argv: list[str] = [
        _yt_dlp_bin(),
        # subs+info only, no media
        "--skip-download",
        "--write-info-json",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs", opts.sub_langs,
        "--sub-format", "vtt/best",
        "--convert-subs", "vtt",
        # be a polite scraper
        "--sleep-requests", str(opts.sleep_requests),
        "--sleep-interval", str(opts.sleep_interval),
        "--max-sleep-interval", str(opts.max_sleep_interval),
        # robust retries
        "--retries", str(opts.retries),
        "--fragment-retries", str(opts.fragment_retries),
        "--file-access-retries", str(opts.file_access_retries),
        "--socket-timeout", str(opts.socket_timeout),
        # don't die on a single bad video
        "--ignore-errors",
        "--no-warnings",
        "--no-abort-on-error",
        # idempotency
        "--download-archive", str(DOWNLOAD_ARCHIVE),
        # better channel coverage: try multiple player clients
        "--extractor-args", f"youtube:player_client={','.join(opts.extractor_clients)}",
        # rotating UA
        "--user-agent", _user_agent(attempt),
        # canonical output layout (must match the rest of the pipeline)
        "--output", f"{OUT_DIR}/%(uploader)s/%(id)s/%(title)s [%(id)s].%(ext)s",
        # never write partial info.json
        "--no-overwrites",
    ]
    if opts.write_description:
        argv.append("--write-description")
    if opts.write_thumbnail:
        argv += ["--write-thumbnail", "--convert-thumbnails", "jpg"]
    if opts.cookies_from_browser:
        argv += ["--cookies-from-browser", opts.cookies_from_browser]
    if opts.cookies_file:
        argv += ["--cookies", str(opts.cookies_file)]
    if opts.proxy:
        argv += ["--proxy", opts.proxy]
    argv += opts.extra_args
    argv.append(url)
    return argv


def _quarantine_channel_meta() -> int:
    """Move accidental channel-listing folders (@handle, UCxxx) into _channel_meta/.

    yt-dlp occasionally writes channel-level metadata into a folder named for the
    handle or channel id. These are NOT videos -- they confuse downstream tools.
    """
    moved = 0
    for d in OUT_DIR.glob("*/@*"):
        if d.is_dir():
            target = d.parent / "_channel_meta" / d.name
            target.parent.mkdir(parents=True, exist_ok=True)
            d.rename(target)
            moved += 1
    for d in OUT_DIR.glob("*/UC*"):
        if d.is_dir() and len(d.name) >= 22:
            target = d.parent / "_channel_meta" / d.name
            target.parent.mkdir(parents=True, exist_ok=True)
            d.rename(target)
            moved += 1
    return moved


def download_channel(url: str, opts: Optional[DownloadOptions] = None) -> int:
    """Download a single channel/playlist/video URL with resilience.

    Returns the number of completed .info.json files in `out/` afterwards.
    """
    ensure_dirs()
    opts = opts or DownloadOptions()
    start_count = _count_info_json(OUT_DIR)
    log.info("download_start", url=url, start_count=start_count)

    current_url = url
    last_count = start_count
    attempt = 1
    while attempt <= opts.max_attempts:
        timeout = _estimate_timeout(last_count)
        log.info(
            "download_attempt",
            attempt=attempt,
            url=current_url,
            timeout_s=timeout,
        )

        argv = _build_argv(current_url, opts, attempt)
        try:
            subprocess.run(
                argv, timeout=timeout, check=False, stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired:
            log.warn("download_timeout", attempt=attempt, timeout_s=timeout)

        moved = _quarantine_channel_meta()
        if moved:
            log.info("quarantined_channel_meta", count=moved)

        count = _count_info_json(OUT_DIR)
        delta = count - last_count
        log.info("download_progress", count=count, delta=delta)
        last_count = count

        # Heuristic: if /videos tab returned suspiciously few, fall back to root
        if attempt == 1 and delta < 20 and "/videos" in current_url:
            new_url = current_url.replace("/videos", "")
            log.warn("url_fallback", from_url=current_url, to_url=new_url, reason="under-20-results")
            current_url = new_url
        elif delta == 0 and attempt > 1:
            # No new content this attempt -- likely done
            log.info("download_no_new_content", attempt=attempt)
            break

        attempt += 1
        if attempt <= opts.max_attempts:
            log.info("inter_attempt_sleep", seconds=opts.inter_attempt_sleep)
            time.sleep(opts.inter_attempt_sleep)

    final = _count_info_json(OUT_DIR)
    log.info("download_complete", url=url, total=final, gained=final - start_count)
    return final


def download_from_file(path: Path, opts: Optional[DownloadOptions] = None) -> dict[str, int]:
    """Download a list of channel URLs from a file (one per line, # comments ok)."""
    results: dict[str, int] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        results[line] = download_channel(line, opts)
    return results
