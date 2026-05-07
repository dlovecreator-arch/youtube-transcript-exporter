#!/usr/bin/env python3
"""Format Obsidian vault structure with proper hierarchy and index files."""
import json
from pathlib import Path

MARKDOWN_BASE = Path(__file__).resolve().parent.parent / "markdown"
DB_FILE = Path(__file__).resolve().parent.parent / "db" / "canonical.json"

def create_channel_index(channel_dir: Path, channel_name: str):
    """Create index.md for a channel directory."""
    
    # Get all videos in this channel
    md_files = sorted(channel_dir.glob("*_*.md"))
    
    # Parse metadata from files
    videos = []
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            # Extract title from frontmatter
            match = re.search(r'title: "([^"]+)"', content)
            title = match.group(1) if match else md_file.stem
            
            # Extract date
            match = re.search(r'date: (\d{4}-\d{2}-\d{2})', content)
            date = match.group(1) if match else "Unknown"
            
            # Extract guest
            match = re.search(r'guest: "([^"]*)"', content)
            guest = match.group(1) if match and match.group(1) else "No guest identified"
            
            # Extract video ID
            video_id = md_file.stem.split('_')[-1] if '_' in md_file.stem else "unknown"
            
            videos.append({
                'title': title,
                'date': date,
                'guest': guest,
                'file': md_file.name,
                'id': video_id
            })
        except:
            continue
    
    # Sort by date descending
    videos.sort(key=lambda x: x['date'], reverse=True)
    
    # Generate index
    lines = [
        f"# {channel_name}",
        "",
        f"**Total Videos**: {len(videos)}",
        "",
        "## Videos",
        ""
    ]
    
    for v in videos:
        lines.append(f"### [{v['title']}]({v['file']})")
        lines.append(f"- **Guest**: {v['guest']}")
        lines.append(f"- **Date**: {v['date']}")
        lines.append(f"- **Video ID**: `{v['id']}`")
        lines.append("")
    
    index_file = channel_dir / "_index.md"
    index_file.write_text("\n".join(lines), encoding='utf-8')
    print(f"✓ Created index for {channel_name} ({len(videos)} videos)")

def create_global_index():
    """Create main index.md for entire vault."""
    
    try:
        db = json.loads(DB_FILE.read_text())
    except:
        return
    
    videos = db.get("videos", [])
    
    lines = [
        "# YouTube Transcripts Vault",
        "",
        f"**Total Videos**: {len(videos)}",
        f"**Generated**: $(date)",
        "",
        "## Quick Links",
        ""
    ]
    
    # Get channel counts
    channels = {}
    for v in videos:
        ch = v.get("channel", "Unknown")
        channels[ch] = channels.get(ch, 0) + 1
    
    # Add channel links
    for ch in sorted(channels.keys()):
        safe_ch = ch.replace(" ", "_")
        lines.append(f"- **{ch}**: {channels[ch]} videos - [[{safe_ch}/_index|Browse]]")
    
    lines.extend([
        "",
        "## Search Tips",
        "- Use `#tag:prophecy` to find videos by topic",
        "- Use `@guest:\"Kerry K\"` to find videos by specific guest",
        "- Use `date: 2025` to find videos by year",
        "",
        "## Folders",
        ""
    ])
    
    for ch_dir in sorted(MARKDOWN_BASE.glob("*")):
        if ch_dir.is_dir() and not ch_dir.name.startswith("_"):
            lines.append(f"- [[{ch_dir.name}/_index|{ch_dir.name}]]")
    
    index_file = MARKDOWN_BASE / "_start_here.md"
    index_file.write_text("\n".join(lines), encoding='utf-8')
    print(f"✓ Created global index at _start_here.md")

def main():
    """Format entire Obsidian vault structure."""
    print("Formatting Obsidian vault...")
    
    # Create index for each channel
    for channel_dir in sorted(MARKDOWN_BASE.glob("*")):
        if channel_dir.is_dir() and not channel_dir.name.startswith("_"):
            channel_name = channel_dir.name.replace("_", " ")
            create_channel_index(channel_dir, channel_name)
    
    # Create global index
    create_global_index()
    print("\n✓ Obsidian vault structure complete!")

if __name__ == "__main__":
    import re
    main()
