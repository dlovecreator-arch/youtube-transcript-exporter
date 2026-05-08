#!/bin/bash
################################################################################
# MARKDOWN INTEGRITY VALIDATOR & SAFEGUARD
# Ensures markdown generation is complete before operations
# This prevents the markdown loss that happened earlier
################################################################################

set -euo pipefail

log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

verify_markdown_integrity() {
  log "Verifying markdown integrity..."
  
  python3 << 'PYEOF'
import json
import os
from pathlib import Path
from collections import defaultdict

with open("db/canonical.json") as f:
    db = json.load(f)

videos = db.get("videos", [])
channels_in_db = defaultdict(int)
for v in videos:
    ch = v.get("channel", "Unknown")
    channels_in_db[ch] += 1

# Count markdown
md_count = len(list(Path("markdown").glob("**/*.md")))
video_count = len(videos)

print(f"\nMarkdown Status:")
print(f"  Videos in DB: {video_count}")
print(f"  Markdown files: {md_count}")
print(f"  Coverage: {md_count/video_count*100:.1f}%")
print()

# Check each channel
channels_missing = []
for ch in channels_in_db.keys():
    safe_ch = ch.replace(" ", "_").replace("/", "⧸")
    md_dir = Path("markdown") / safe_ch
    if not md_dir.exists():
        channels_missing.append(ch)

if channels_missing:
    print(f"ERROR: {len(channels_missing)} channels missing markdown:")
    for ch in channels_missing:
        print(f"  ✗ {ch}")
    print()
    print("SOLUTION: Run this before any operations:")
    print("  python3 markdown_generator.py")
    exit(1)

if md_count < video_count * 0.9:
    print(f"WARNING: Only {md_count/video_count*100:.1f}% markdown coverage")
    print(f"Missing: {video_count - md_count} files")
    exit(1)

print("✓ Markdown integrity verified")
print("✓ System ready for operations")

PYEOF
}

# Run verification
verify_markdown_integrity
