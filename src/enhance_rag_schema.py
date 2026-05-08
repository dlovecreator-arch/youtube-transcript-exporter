#!/usr/bin/env python3
"""
Enhanced metadata extraction with RAG-optimized schema.

Upgrades canonical.json to include:
- source_id: youtube_channelslug_videoid
- captured_date: ISO timestamp
- transcript_source: youtube_caption | whisper | manual
- confidence: 0.85 (YouTube auto-captions accuracy baseline)
- tradition: [] (can be manually enriched later)

Features:
  - Comprehensive error handling
  - Input validation
  - Recovery on partial failure
"""

import json
import re
import logging
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_BASE = REPO_ROOT / "out"
DB_FILE = REPO_ROOT / "db" / "canonical.json"

def sanitize_slug(name: str) -> str:
    """Convert channel name to URL-safe slug."""
    try:
        return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
    except Exception as e:
        logger.warning(f"Error sanitizing slug for '{name}': {e}")
        return "unknown"

def extract_guest(title: str, description: str = "") -> str | None:
    """Extract guest name from title/description."""
    try:
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
    except Exception as e:
        logger.debug(f"Error extracting guest from '{title}': {e}")
        return None

def extract_topics(tags: list, description: str, title: str) -> list:
    """Extract topic tags."""
    try:
        topics = set()
        if tags and isinstance(tags, list):
            for tag in tags[:8]:
                tag_lower = str(tag).lower()
                if tag_lower not in ['interview', 'podcast', 'youtube', '2024', '2025', 'new']:
                    topics.add(tag_lower)
        
        if title and isinstance(title, str):
            for word in title.split():
                if word.isupper() and len(word) > 2:
                    topics.add(word.lower())
        
        return sorted(list(topics))
    except Exception as e:
        logger.debug(f"Error extracting topics: {e}")
        return []

def enhance_canonical_db():
    """
    Load existing canonical.json, add RAG-optimized fields, save back.
    """
    try:
        logger.info("Loading existing canonical.json...")
        
        if not DB_FILE.exists():
            logger.error(f"canonical.json not found at {DB_FILE}")
            logger.info("Initialize with: mkdir -p db && python3 << 'EOF'")
            logger.info("import json")
            logger.info("db = {'videos': [], 'metadata': {'total_videos': 0, 'total_channels': 0, 'last_sync': None, 'version': '1.0'}}")
            logger.info("with open('db/canonical.json', 'w') as f: json.dump(db, f, indent=2)")
            logger.info("EOF")
            sys.exit(1)
        
        try:
            db = json.loads(DB_FILE.read_text())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"File may be corrupted. Backup is recommended.")
            sys.exit(1)
        
        videos = db.get("videos", [])
        
        if not videos:
            logger.warning("No videos found in database")
            return
        
        captured_now = datetime.utcnow().isoformat() + "Z"
        
        logger.info(f"Enhancing {len(videos)} videos with RAG schema...")
        
        enhanced_count = 0
        skipped_count = 0
        
        for i, video in enumerate(videos):
            try:
                if i % 500 == 0:
                    logger.info(f"  Progress: {i}/{len(videos)}")
                
                channel = video.get("channel", "")
                video_id = video.get("id", "")
                
                if not channel or not video_id:
                    skipped_count += 1
                    logger.debug(f"Skipping video with missing channel or id")
                    continue
                
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
                
                enhanced_count += 1
            
            except Exception as e:
                skipped_count += 1
                logger.warning(f"Error enhancing video {i}: {e}")
                continue
        
        # Write back with error handling
        try:
            logger.info("Saving enhanced canonical.json...")
            DB_FILE.write_text(json.dumps(db, indent=2))
        except Exception as e:
            logger.error(f"Failed to write database: {e}")
            logger.error("Database may not have been updated")
            sys.exit(1)
        
        logger.info(f"✓ Enhanced {enhanced_count} videos, skipped {skipped_count}")
        logger.info(f"  - Added source_id (youtube_channelslug_videoid)")
        logger.info(f"  - Added captured_date ({captured_now})")
        logger.info(f"  - Added transcript_source (youtube_caption)")
        logger.info(f"  - Added confidence (0.85)")
        logger.info(f"  - Added tradition ([])")
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    enhance_canonical_db()
