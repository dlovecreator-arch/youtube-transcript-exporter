#!/usr/bin/env python3
"""
Enhanced Markdown Generator with RAG-optimized frontmatter.

Extends canonical.json schema into markdown with comprehensive metadata:
- source_id, captured_date, transcript_source, confidence
- tradition field for manual enrichment
- Future-ready for chunk-level extraction
"""

import json
import re
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_FILE = REPO_ROOT / "db" / "canonical.json"
OUT_BASE = REPO_ROOT / "out"
MARKDOWN_BASE = REPO_ROOT / "markdown"

def sanitize_filename(name: str) -> str:
    """Make string safe for filename."""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name[:80]

def generate_markdown_with_rag(record: dict, transcript_text: str) -> str:
    """Generate markdown with RAG-optimized frontmatter."""
    
    # YAML frontmatter with comprehensive metadata
    frontmatter = f"""---
source_id: {record.get('source_id', 'unknown')}
id: {record.get('id', 'unknown')}
title: "{record.get('title', 'Untitled').replace('"', '\\"')}"
channel: {record.get('channel', 'Unknown')}
guest: {record.get('guest') or ''}
url: {record.get('url', '')}
published_date: {record.get('date', '')}
captured_date: {record.get('captured_date', '')}
duration_seconds: {record.get('duration', 0)}
views: {record.get('views', 0)}
likes: {record.get('likes', 0)}
transcript_source: {record.get('transcript_source', 'youtube_caption')}
confidence: {record.get('confidence', 0.85)}
tradition: {json.dumps(record.get('tradition', []))}
tags: {json.dumps(record.get('tags', []))}
category: {record.get('category', '')}
word_count: {len(transcript_text.split())}
---

# {record.get('title', 'Untitled')}

> **Source**: {record.get('source_id', 'unknown')}  
> **Channel**: {record.get('channel', 'Unknown')}  
> **Guest**: {record.get('guest') or 'N/A'}  
> **Date**: {record.get('date', 'Unknown')}  
> **Duration**: {record.get('duration', 0)}s  
> **Confidence**: {record.get('confidence', 0.85)} (YouTube auto-captions)

## Transcript

{transcript_text}
"""
    
    return frontmatter

def regenerate_markdown_with_rag():
    """Regenerate all markdown files with RAG schema."""
    
    if not DB_FILE.exists():
        print("ERROR: canonical.json not found")
        return
    
    db = json.loads(DB_FILE.read_text())
    videos = db.get("videos", [])
    
    print(f"Regenerating {len(videos)} markdown files with RAG schema...")
    
    success = 0
    for i, record in enumerate(videos, 1):
        if i % 100 == 0:
            print(f"  Progress: {i}/{len(videos)}")
        
        video_id = record['id']
        
        # Find transcript in out/
        transcript_text = None
        for source_dir in [record.get('sources', [video_id])]:
            for folder in OUT_BASE.glob(f"*/{source_dir}"):
                if not folder.is_dir():
                    continue
                vtt_files = [f for f in folder.glob("*.en.vtt") if f"[{video_id}]" in f.name]
                if not vtt_files:
                    vtt_files = list(folder.glob("*.en.vtt"))
                if vtt_files:
                    try:
                        # Simple VTT -> text extraction
                        vtt_content = vtt_files[0].read_text()
                        lines = vtt_content.split('\n')
                        blocks = []
                        for line in lines:
                            if '-->' not in line and line.strip() and not line.startswith('WEBVTT'):
                                blocks.append(line.strip())
                        transcript_text = ' '.join(blocks)
                        break
                    except:
                        pass
            if transcript_text:
                break
        
        if not transcript_text:
            continue
        
        # Generate markdown
        md_content = generate_markdown_with_rag(record, transcript_text)
        
        # Write to markdown/
        channel_dir = MARKDOWN_BASE / sanitize_filename(record['channel'])
        channel_dir.mkdir(parents=True, exist_ok=True)
        
        safe_title = sanitize_filename(record['title'])
        md_file = channel_dir / f"{safe_title}_{video_id}.md"
        md_file.write_text(md_content, encoding='utf-8')
        
        success += 1
    
    print(f"✓ Regenerated {success} markdown files with RAG schema")

if __name__ == "__main__":
    regenerate_markdown_with_rag()
