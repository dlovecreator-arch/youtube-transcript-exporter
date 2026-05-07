#!/usr/bin/env python3
"""
Enhanced metadata extraction with RAG-optimized schema.

Upgrades canonical.json to include:
- source_id: youtube_channelslug_videoid
- captured_date: ISO timestamp
- transcript_source: youtube_caption | whisper | manual
- confidence: 0.85 (YouTube auto-captions accuracy baseline)
- tradition: [] (can be manually enriched later)
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_BASE = REPO_ROOT / "out"
DB_FILE = REPO_ROOT / "db" / "canonical.json"

def sanitize_slug(name: str) -> str:
    """Convert channel name to URL-safe slug."""
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')

def extract_guest(title: str, description: str = "") -> str | None:
    """Extract guest name from title/description."""
    # Pattern: "Title | Guest Name"
    match = re.search(r'\|\s*([A-Z][A-Za-z\s\.]+)(?:\s*\[|$)', title)
    if match:
        guest = match.group(1).strip()
        if guest and len(guest) > 2 and guest not in ["Emilio Ortiz", "Viviane Chauvet", "The Alchemist"]:
            return guest
    
    # Pattern: "Guest Name REVEALS/SHOWS/etc"
    match = re.match(r'^([A-Z][A-Za-z\s]+?)\s+(REVEALS|SHOWS|TELLS|WARNS|DISCUSSES|EXPLAINS|SHARES|PREDICTS)', title)
    if match:
        guest = match.group(1).strip()
        if len(guest) > 2:
            return guest
    
    return None

def extract_topics(tags: list, description: str, title: str) -> list:
    """Extract topic tags."""
    topics = set()
    if tags:
        for tag in tags[:8]:
            tag_lower = tag.lower()
            if tag_lower not in ['interview', 'podcast', 'youtube', '2024', '2025', 'new']:
                topics.add(tag_lower)
    
    for word in title.split():
        if word.isupper() and len(word) > 2:
            topics.add(word.lower())
    
    return sorted(list(topics))

def enhance_canonical_db():
    """
    Load existing canonical.json, add RAG-optimized fields, save back.
    """
    print("Loading existing canonical.json...")
    if not DB_FILE.exists():
        print("ERROR: canonical.json not found")
        return
    
    db = json.loads(DB_FILE.read_text())
    videos = db.get("videos", [])
    captured_now = datetime.utcnow().isoformat() + "Z"
    
    print(f"Enhancing {len(videos)} videos with RAG schema...")
    
    for i, video in enumerate(videos):
        if i % 500 == 0:
            print(f"  Progress: {i}/{len(videos)}")
        
        channel = video.get("channel", "")
        video_id = video.get("id", "")
        
        # Add source_id: youtube_channelslug_videoid
        if not video.get("source_id"):
            channel_slug = sanitize_slug(channel)
            video["source_id"] = f"youtube_{channel_slug}_{video_id}"
        
        # Add captured_date
        if not video.get("captured_date"):
            video["captured_date"] = captured_now
        
        # Add transcript_source (we're using YouTube auto-captions)
        if not video.get("transcript_source"):
            video["transcript_source"] = "youtube_caption"
        
        # Add confidence (YouTube auto-captions ~85% accurate)
        if not video.get("confidence"):
            video["confidence"] = 0.85
        
        # Add tradition (empty for now, can be manually enriched)
        if not video.get("tradition"):
            video["tradition"] = []
    
    # Write back
    print("Saving enhanced canonical.json...")
    DB_FILE.write_text(json.dumps(db, indent=2))
    
    print(f"✓ Enhanced {len(videos)} videos")
    print(f"  - Added source_id (youtube_channelslug_videoid)")
    print(f"  - Added captured_date ({captured_now})")
    print(f"  - Added transcript_source (youtube_caption)")
    print(f"  - Added confidence (0.85)")
    print(f"  - Added tradition ([])")

if __name__ == "__main__":
    enhance_canonical_db()
