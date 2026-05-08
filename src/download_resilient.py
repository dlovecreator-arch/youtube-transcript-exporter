#!/usr/bin/env python3
"""
YouTube Channel Downloader with Intelligent Rate Limiting & Resilience

Core strategy:
- Increased inter-video sleep (2.5s instead of 1.5s)
- Rotating user agents to avoid fingerprinting
- Exponential backoff on batch failure
- Adaptive timeout: scales based on estimated video count
  * Small channels (<500): 600s (10 min)
  * Medium channels (500-2000): 3600s (60 min)
  * Large channels (2000+): 7200s (120 min)
- Resume-safe: can re-run indefinitely to accumulate all videos
"""

import subprocess
import sys
import time
import random
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "out"
LOG_FILE = REPO_ROOT / "archive" / "logs" / f"yt_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

def log(msg):
    """Log to both file and stdout."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def count_videos(out_dir):
    """Count .info.json files (completed downloads)."""
    return len(list(out_dir.glob("*/*.info.json")))

def estimate_timeout(video_count):
    """
    Calculate adaptive timeout based on estimated video count.
    
    At 2.5s per video:
    - 100 videos = 250s (4 min)
    - 500 videos = 1250s (21 min) -> use 600s (10 min) for small channels
    - 1000 videos = 2500s (42 min) -> use 3600s (60 min) for medium
    - 2000 videos = 5000s (83 min) -> use 7200s (120 min) for large
    
    Add 50% safety margin.
    """
    if video_count < 500:
        return 600  # 10 minutes
    elif video_count < 2000:
        return 3600  # 60 minutes
    else:
        return 7200  # 120 minutes

def download_with_backoff(url, max_attempts=5):
    """Download with exponential backoff and user agent rotation."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    log(f"Starting download: {url}")
    log("Strategy: exponential backoff + rotating user agents + adaptive timeout")
    
    attempt = 1
    backoff = 5
    last_count = 0
    
    while attempt <= max_attempts:
        user_agent = random.choice(USER_AGENTS)
        log(f"Attempt {attempt}/{max_attempts} (UA rotation: {USER_AGENTS.index(user_agent) + 1}/{len(USER_AGENTS)})")
        
        # Estimate timeout based on current download count (assume similar size)
        current_count = count_videos(OUT_DIR)
        estimated_total = max(500, current_count * 2)  # Conservative estimate
        timeout_seconds = estimate_timeout(estimated_total)
        timeout_minutes = timeout_seconds // 60
        log(f"Using timeout: {timeout_minutes} minutes ({timeout_seconds} seconds) for estimated {estimated_total} videos")
        
        try:
            # Core yt-dlp call with better rate limiting
            subprocess.run(
                [
                    "yt-dlp",
                    "--skip-download",
                    "--write-info-json",
                    "--write-auto-subs",
                    "--sub-langs", "en",
                    "--sub-format", "vtt",
                    "--no-playlist",
                    "--socket-timeout", "8",
                    "--retries", "1",
                    "--retry-sleep", "3",
                    "--max-sleep-interval", "6",
                    "--sleep-interval", "2.5",  # Key: increased from 1.5s
                    "--ignore-errors",
                    "--no-warnings",
                    "--user-agent", user_agent,
                    "--output", f"{OUT_DIR}/%(uploader)s/%(id)s/%(title)s [%(id)s].%(ext)s",
                    url
                ],
                timeout=timeout_seconds,  # Adaptive based on channel size
                check=False
            )
        except subprocess.TimeoutExpired:
            log(f"Attempt {attempt} timed out after {timeout_seconds}s ({timeout_minutes} min)")

        except Exception as e:
            log(f"ERROR in attempt {attempt}: {e}")
        
        current_count = count_videos(OUT_DIR)
        log(f"Progress: {current_count} videos (gained {current_count - last_count} this attempt)")
        last_count = current_count
        
        # If we made progress, continue with next attempt
        if current_count > 0 and attempt < max_attempts:
            log(f"Sleeping 120s before next attempt (inter-batch cool-down)...")
            time.sleep(120)
        
        # Exponential backoff
        if attempt < max_attempts:
            log(f"Backoff: sleeping {backoff}s before next attempt")
            time.sleep(backoff)
            backoff = min(backoff * 1.5, 120)
        
        attempt += 1
    
    final_count = count_videos(OUT_DIR)
    log(f"Download complete: {final_count} total videos downloaded")
    return final_count

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: download_resilient.py <YouTube URL> [max_attempts]")
        sys.exit(1)
    
    url = sys.argv[1]
    max_attempts = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    download_with_backoff(url, max_attempts)
    log("Downloader done")
