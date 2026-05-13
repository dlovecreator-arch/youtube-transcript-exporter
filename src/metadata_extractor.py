#!/usr/bin/env python3
"""Metadata extractor: Parse all .info.json files into canonical database.

Extracts:
- Guest names (from title/description heuristics)
- YouTube tags/categories
- View/like counts
- Deduplicates across channels
"""
import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_BASE = REPO_ROOT / "out"
DB_FILE = REPO_ROOT / "db" / "canonical.json"
DB_FILE.parent.mkdir(exist_ok=True)


def extract_guest(title: str, description: str = "") -> str | None:
    """Extract guest name from title/description using heuristics.
    
    Patterns:
    - "Title | Guest Name"
    - "Title with Guest Name [INTERVIEW]"
    - "Guest Name REVEALS..." (starts title)
    """
    # Pattern: Title | Guest
    match = re.search(r'\|\s*([A-Z][A-Za-z\s\.]+)(?:\s*\[|$)', title)
    if match:
        guest = match.group(1).strip()
        if guest and len(guest) > 2 and guest != "Emilio Ortiz" and guest != "Viviane Chauvet":
            return guest
    
    # Pattern: starts with Name REVEALS/SHOWS/TELLS/WARNS
    match = re.match(r'^([A-Z][A-Za-z\s]+?)\s+(REVEALS|SHOWS|TELLS|WARNS|DISCUSSES|EXPLAINS|SHARES|PREDICTS)', title)
    if match:
        guest = match.group(1).strip()
        if len(guest) > 2:
            return guest
    
    # Last resort: description first line
    if description:
        first_line = description.split('\n')[0]
        match = re.match(r'^([A-Z][A-Za-z\s]+)\s+(?:is|discusses|talks)', first_line)
        if match:
            return match.group(1).strip()
    
    return None


def extract_topics(tags: list, description: str, title: str) -> list:
    """Extract topic tags from YouTube tags + title keywords."""
    topics = set()
    
    if tags:
        # Filter out low-value tags
        for tag in tags[:8]:  # Top 8 tags only
            tag_lower = tag.lower()
            if tag_lower not in ['interview', 'podcast', 'youtube', '2024', '2025', 'new']:
                topics.add(tag_lower)
    
    # Extract from title: ALL_CAPS words are usually topics
    for word in title.split():
        if word.isupper() and len(word) > 2:
            topics.add(word.lower())
    
    return sorted(list(topics))


def build_canonical_db():
    """Scan all .info.json files and build canonical database."""
    
    db = {
        "version": "1.0",
        "generated": datetime.now().isoformat(),
        "videos": [],
        "channels": defaultdict(int),
        "duplicates": defaultdict(list),
    }
    
    video_by_id = {}  # Track duplicates
    
    for info_path in sorted(OUT_BASE.rglob("*.info.json")):
        try:
            data = json.loads(info_path.read_text(errors="ignore"))
        except:
            continue
        
        # Skip channel metadata
        video_id = data.get("id", "")
        if not video_id or video_id.startswith("UC"):
            continue
        
        # Build canonical record
        # Use the folder name as the canonical channel (humans curate these for clean naming).
        # Fall back to YT's `channel` field if the folder is unusual.
        # The folder layout is out/<channel>/<video_id>/<file>.info.json,
        # so info_path.parent.parent.name is the channel folder name.
        folder_channel = info_path.parent.parent.name if info_path.parent.parent != OUT_BASE else None
        yt_channel = (data.get("channel") or "").strip()
        yt_uploader = (data.get("uploader") or "").strip()
        canonical_channel = (folder_channel or yt_channel or yt_uploader or "Unknown").strip()

        record = {
            "id": video_id,
            "title": data.get("title", "Untitled"),
            "channel": canonical_channel,
            "channel_id": data.get("channel_id", ""),
            "uploader": yt_uploader or "Unknown",
            "date": data.get("upload_date", ""),
            "duration": data.get("duration", 0),
            "views": data.get("view_count", 0),
            "likes": data.get("like_count", 0),
            "url": f"https://youtu.be/{video_id}",
            "description": (data.get("description") or "")[:300],
            "category": data.get("categories", [None])[0] if data.get("categories") else None,
            "guest": extract_guest(data.get("title", ""), data.get("description", "")),
            "tags": extract_topics(data.get("tags", []), data.get("description", ""), data.get("title", "")),
            "sources": [str(info_path.parent.name)],
        }
        
        db["channels"][record["channel"]] += 1
        
        # Dedup: if we've seen this video_id before, link it
        if video_id in video_by_id:
            db["duplicates"][video_id].append(record["sources"][0])
            existing_idx = video_by_id[video_id]
            db["videos"][existing_idx]["sources"].extend(record["sources"])
        else:
            video_by_id[video_id] = len(db["videos"])
            db["videos"].append(record)
    
    # Convert defaultdicts to regular dicts for JSON
    db["channels"] = dict(db["channels"])
    db["duplicates"] = dict(db["duplicates"])
    
    # Write canonical database
    DB_FILE.write_text(json.dumps(db, indent=2))
    
    print(f"✓ Canonical DB created: {DB_FILE}")
    print(f"  - Total videos: {len(db['videos'])}")
    print(f"  - Channels: {len(db['channels'])}")
    print(f"  - Duplicates: {len(db['duplicates'])}")
    print(f"  - Videos with guests: {sum(1 for v in db['videos'] if v['guest'])}")
    
    return db


if __name__ == "__main__":
    db = build_canonical_db()
