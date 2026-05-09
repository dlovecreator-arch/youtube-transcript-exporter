#!/usr/bin/env python3
"""Generate Markdown transcripts with optimized YAML frontmatter.

Improvements:
- Full AI-agent-ready schema (token_count, reading_time, etc)
- Slug field for Obsidian safe filtering
- Word count for transcript length tracking
- Confidence scores for guest extraction quality
- Both .md and .txt outputs (Obsidian compatibility)
- Proper string formatting for Notion API compatibility
"""
import json
import os
import re
import sys
import math
import argparse
import hashlib
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_FILE = REPO_ROOT / "db" / "canonical.json"
OUT_BASE = REPO_ROOT / "out"
MARKDOWN_BASE = REPO_ROOT / "markdown"
MARKDOWN_BASE.mkdir(exist_ok=True)

# Approximate token count (1 token ≈ 4 characters, conservative estimate)
def estimate_tokens(text: str) -> int:
    """Estimate token count for Claude/GPT consumption."""
    return max(1, len(text) // 4)

def estimate_reading_time(text: str) -> int:
    """Estimate reading time in minutes (avg 200 words/minute)."""
    word_count = len(text.split())
    return max(1, word_count // 200)

def extract_guest_with_confidence(title: str, description: str = "") -> tuple:
    """Extract guest name and return (name, confidence_score)."""
    confidence = 0.0
    
    # Pattern 1: "Title | Guest Name" (highest confidence)
    match = re.search(r'\|\s*([A-Z][A-Za-z\s\.]+)(?:\s*\[|$)', title)
    if match:
        guest = match.group(1).strip()
        if guest and len(guest) > 2 and guest not in ["Emilio Ortiz", "Viviane Chauvet", "The Alchemist"]:
            return (guest, 0.95)
    
    # Pattern 2: "Name REVEALS/SHOWS/etc" (high confidence)
    match = re.match(r'^([A-Z][A-Za-z\s]+?)\s+(REVEALS|SHOWS|TELLS|WARNS|DISCUSSES|EXPLAINS|SHARES|PREDICTS)', title)
    if match:
        guest = match.group(1).strip()
        if len(guest) > 2:
            return (guest, 0.85)
    
    # Pattern 3: Description first line (medium confidence)
    if description:
        first_line = description.split('\n')[0]
        match = re.match(r'^([A-Z][A-Za-z\s]+)\s+(?:is|discusses|talks)', first_line)
        if match:
            return (match.group(1).strip(), 0.65)
    
    return (None, 0.0)

def clean_vtt_text(vtt_path: Path) -> str:
    """Extract clean text from VTT caption file."""
    lines = vtt_path.read_text(errors="ignore").splitlines()
    blocks = []
    current_block = []
    
    for line in lines:
        line = line.strip()
        
        # Skip headers, timestamps, cue IDs
        if line in {"WEBVTT", "Kind: captions", "Language: en"} or line.startswith("NOTE") or line.startswith("STYLE"):
            continue
        if "-->" in line or re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3}$", line):
            continue
        if re.fullmatch(r"\d+", line):
            continue
        
        if not line:
            if current_block:
                blocks.append(" ".join(current_block))
                current_block = []
        else:
            # Clean HTML tags and markers
            line = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", "", line)
            line = re.sub(r"<[^>]+>", "", line)
            line = line.replace("[music]", "").replace("[Applause]", "").replace("[Music]", "")
            line = line.strip()
            if line:
                current_block.append(line)
    
    if current_block:
        blocks.append(" ".join(current_block))
    
    # Remove near-duplicates (YouTube progressive captions)
    cleaned = []
    for block in blocks:
        if cleaned and len(block) > 0:
            if similarity(block, cleaned[-1]) > 0.8:
                continue
            if block in cleaned[-1]:
                continue
        cleaned.append(block)
    
    final = "\n\n".join(cleaned)
    final = re.sub(r"\s+", " ", final)
    
    return final.strip()

def similarity(a: str, b: str) -> float:
    """Simple similarity check (0-1)."""
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a, b).ratio()

def slugify(text: str) -> str:
    """Create safe slug for Obsidian filename."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def generate_markdown(record: dict, transcript_text: str) -> str:
    """Generate Markdown with optimized YAML frontmatter."""
    
    # Parse date
    upload_date = record.get("date", "")
    if len(upload_date) == 8:
        date_obj = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
    else:
        date_obj = upload_date or "1970-01-01"
    
    # Guest extraction with confidence
    guest, confidence = extract_guest_with_confidence(
        record.get("title", ""),
        record.get("description", "")
    )
    
    # Calculate metrics
    word_count = len(transcript_text.split())
    token_count = estimate_tokens(transcript_text)
    reading_time = estimate_reading_time(transcript_text)
    slug = slugify(record["title"])
    
    # Format sources as comma-separated (Notion compatible)
    sources_str = ", ".join(record.get("sources", []))
    
    # Format tags as comma-separated
    tags_str = ", ".join(record.get("tags", []))
    
    # Build YAML frontmatter
    frontmatter = f"""---
id: {record['id']}
title: "{record['title'].replace('"', '\\"')}"
slug: {slug}
guest: "{guest if guest else ""}"
guest_confidence: {confidence:.2f}
channel: {record['channel']}
uploader: {record['uploader']}
date: {date_obj}
duration_sec: {record['duration']}
views: {record['views']}
likes: {record['likes']}
url: {record['url']}
category: {record.get("category") or "Uncategorized"}
tags: [{tags_str}]
description: "{(record.get("description", "").replace('"', '\\"')[:200])}"
word_count: {word_count}
token_count: {token_count}
reading_time_min: {reading_time}
language: en
transcript_complete: {len(transcript_text) > 100}
sources: {sources_str}
generated: {datetime.now().isoformat()}
---
"""
    
    # Build content
    title = record['title']
    guest_line = f" | {guest}" if guest else ""
    
    content = f"""# {title}{guest_line}

**Channel**: {record['channel']}  
**Published**: {date_obj}  
**Guest**: {guest if guest else "N/A"}  
**Duration**: {record['duration']} seconds ({record['duration']//60} min)  
**Views**: {record['views']:,} | **Likes**: {record['likes']:,}  
**Link**: {record['url']}

---

## Transcript

{transcript_text}

---

*Automatically extracted from YouTube captions. Last updated {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC*
"""
    
    return frontmatter + "\n" + content

def process_all_transcripts():
    """Generate Markdown for all videos in canonical DB.

    IMPORTANT: This is incremental by default.
    Historically this script wiped the entire markdown/ vault on each run.
    That was destructive, slow, and caused the "all my markdown disappeared"
    incident when a run was interrupted.

    Use --clean if you explicitly want to delete and regenerate everything.
    """
    
    # Load canonical DB
    try:
        db = json.loads(DB_FILE.read_text())
    except FileNotFoundError:
        print(f"Error: {DB_FILE} not found. Run metadata_extractor.py first.")
        return
    
    videos = db.get("videos", [])
    print(f"Processing {len(videos)} videos...")

    # Non-destructive by default. We never wipe markdown/ during normal runs.
    MARKDOWN_BASE.mkdir(exist_ok=True)

    stats = {
        "success": 0,
        "no_transcript": 0,
        "error": 0,
    }

    for i, record in enumerate(videos, 1):
        video_id = record['id']

        # Find transcript file by video_id in any channel folder
        transcript_text = None
        candidate_folders = list(OUT_BASE.glob(f"*/{video_id}"))
        for folder in candidate_folders:
            if not folder.is_dir():
                continue
            # Look for canonical VTT file: "<title> [<id>].en.vtt"
            vtt_files = [f for f in folder.glob("*.en.vtt") if f"[{video_id}]" in f.name]
            if not vtt_files:
                vtt_files = list(folder.glob("*.en.vtt"))
            if vtt_files:
                try:
                    transcript_text = clean_vtt_text(vtt_files[0])
                    # Also write transcript.en.txt back to the source folder
                    # so each video folder has consistent contents.
                    (folder / "transcript.en.txt").write_text(transcript_text, encoding='utf-8')
                    break
                except Exception as e:
                    print(f"  ! Error reading {vtt_files[0]}: {e}")
                    stats["error"] += 1

        if not transcript_text:
            stats["no_transcript"] += 1
            continue

        # Generate Markdown
        md_content = generate_markdown(record, transcript_text)

        # Create channel folder structure
        channel_dir = MARKDOWN_BASE / safe_channel_dir(record.get('channel', 'Unknown'))
        channel_dir.mkdir(parents=True, exist_ok=True)

        # Stable, filesystem-safe filename. Never use raw title.
        md_file = channel_dir / safe_markdown_filename(record.get('title', ''), video_id)

        # Write only if changed (saves time + avoids churn)
        try:
            new_hash = sha256_text(md_content)
            if md_file.exists():
                old_hash = sha256_text(md_file.read_text(encoding='utf-8', errors='ignore'))
                if old_hash == new_hash:
                    # No change.
                    pass
                else:
                    md_file.write_text(md_content, encoding='utf-8')
            else:
                md_file.write_text(md_content, encoding='utf-8')
        except Exception as e:
            print(f"  ! Error writing {md_file}: {e}")
            stats["error"] += 1
            continue

        if (i % 100) == 0:
            print(f"  ✓ {i}/{len(videos)} ({stats['success']} success)")

        stats["success"] += 1
    
    print(f"\n✓ Markdown generation complete:")
    print(f"  - Success: {stats['success']}")
    print(f"  - No transcript: {stats['no_transcript']}")
    print(f"  - Errors: {stats['error']}")
    print(f"  - Output: {MARKDOWN_BASE}")
    print(f"  - Files: {stats['success']} .md files")

def sanitize_filename(name: str) -> str:
    """Make string safe for filename."""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name[:80]

def safe_channel_dir(channel: str) -> str:
    """Channel folder name MUST match out/ folder exactly (with spaces).

    Per NAMING_CONVENTION.md: markdown/Channel Name/ must equal out/Channel Name/.
    Only strip filesystem-illegal characters; preserve spaces.
    """
    s = (channel or "Unknown").strip()
    # Strip only truly illegal filesystem characters (no slash mangling, keep spaces)
    s = re.sub(r'[<>:"/\\?*]', '', s)
    # Collapse multiple spaces
    s = re.sub(r"\s+", " ", s).strip()
    return s[:120] or "Unknown"


def safe_markdown_filename(title: str, video_id: str) -> str:
    """Stable markdown filename. Avoids slashes/emojis and long paths."""
    base = slugify(title)[:80] or "untitled"
    return f"{base}_[{video_id}].md"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Generate markdown transcripts (incremental by default).")
    parser.add_argument("--clean", action="store_true", help="Delete markdown channel folders before regenerating (dangerous)")
    args = parser.parse_args()

    # Single-instance lock: prevent multiple concurrent runs that race
    # and recreate folders the user just deleted.
    import fcntl
    lock_path = REPO_ROOT / ".markdown_generator.lock"
    lock_file = open(lock_path, "w")
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("❌ Another markdown_generator.py is already running. Exiting.")
        print(f"   (Lock file: {lock_path})")
        sys.exit(2)
    lock_file.write(str(os.getpid()))
    lock_file.flush()

    if args.clean:
        import shutil
        for child in MARKDOWN_BASE.iterdir():
            if child.is_dir():
                shutil.rmtree(child)

    process_all_transcripts()


if __name__ == "__main__":
    main()
