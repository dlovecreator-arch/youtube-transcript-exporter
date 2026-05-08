#!/usr/bin/env python3
"""
COMPREHENSIVE SYSTEM HEALTH CHECK
Validates data integrity, coverage, and pipeline completeness.
MUST run after every major operation.
"""

import json
import os
from pathlib import Path
from collections import defaultdict

def check_system_health():
    """Run comprehensive health checks across all system layers."""
    
    print("\n" + "=" * 80)
    print("SYSTEM HEALTH CHECK - COMPREHENSIVE")
    print("=" * 80 + "\n")
    
    issues = []
    warnings = []
    
    # 1. CANONICAL DB CHECKS
    print("[1] CANONICAL DATABASE")
    try:
        with open('db/canonical.json') as f:
            data = json.load(f)
        
        videos = data.get('videos', [])
        channels_in_db = set(v.get('channel') for v in videos)
        
        print(f"  ✓ Total videos: {len(videos)}")
        print(f"  ✓ Unique channels: {len(channels_in_db)}")
        
        # Check for RAG fields
        rag_fields = ['source_id', 'captured_date', 'transcript_source', 'confidence']
        missing_rag = sum(1 for v in videos if not all(v.get(f) for f in rag_fields))
        if missing_rag > 0:
            issues.append(f"CRITICAL: {missing_rag} videos missing RAG schema fields")
        else:
            print(f"  ✓ RAG schema: 100% complete ({len(videos)} videos)")
        
    except Exception as e:
        issues.append(f"CRITICAL: Cannot read canonical.json: {e}")
        return issues, warnings
    
    # 2. RAW DOWNLOADS CHECKS
    print("\n[2] RAW DOWNLOADS (out/ directory)")
    raw_videos = {}
    for channel_folder in os.listdir('out'):
        channel_path = Path('out') / channel_folder
        if not channel_path.is_dir():
            continue
        
        count = 0
        for video_folder in os.listdir(channel_path):
            video_path = channel_path / video_folder
            if video_path.is_dir():
                if list(video_path.glob('*.info.json')):
                    count += 1
        
        if count > 0:
            raw_videos[channel_folder] = count
    
    total_raw = sum(raw_videos.values())
    print(f"  ✓ Raw video folders: {total_raw}")
    print(f"  ✓ Channel folders: {len(raw_videos)}")
    
    # 3. MARKDOWN COVERAGE CHECK (CRITICAL)
    print("\n[3] MARKDOWN VAULT COVERAGE")
    markdown_channels = set()
    for folder in Path('markdown').iterdir():
        if folder.is_dir() and folder.name not in ['.DS_Store']:
            markdown_channels.add(folder.name)
    
    markdown_count = len(list(Path('markdown').glob('**/*.md')))
    print(f"  ✓ Markdown files: {markdown_count}")
    print(f"  ✓ Markdown channel folders: {len(markdown_channels)}")
    
    # CRITICAL: Check coverage mismatch
    if len(markdown_channels) < len(channels_in_db):
        missing_channels = len(channels_in_db) - len(markdown_channels)
        issues.append(
            f"CRITICAL: {missing_channels} channels in DB but missing markdown folders! "
            f"({len(markdown_channels)}/{len(channels_in_db)})"
        )
        print(f"  ⚠️ MISSING: {missing_channels} channels lack markdown folders")
    
    # CRITICAL: Check video count alignment
    expected_markdown_min = len(videos) * 0.90  # Allow 10% buffer for processing
    if markdown_count < expected_markdown_min:
        shortfall = int(expected_markdown_min - markdown_count)
        issues.append(
            f"CRITICAL: Markdown incomplete. "
            f"Have {markdown_count}, need ~{int(expected_markdown_min)} "
            f"(missing ~{shortfall} files)"
        )
        print(f"  ⚠️ INCOMPLETE: {markdown_count} files < {int(expected_markdown_min)} expected")
    
    # 4. RAW vs CANONICAL ALIGNMENT
    print("\n[4] RAW vs CANONICAL ALIGNMENT")
    raw_total = sum(raw_videos.values())
    canonical_total = len(videos)
    diff = abs(raw_total - canonical_total)
    
    if diff > 10:  # Allow small differences for processing
        warnings.append(
            f"WARNING: Raw downloads ({raw_total}) differ from canonical ({canonical_total}) "
            f"by {diff}. This may indicate processing in progress."
        )
        print(f"  ⚠️ Raw: {raw_total}, Canonical: {canonical_total}, Diff: {diff}")
    else:
        print(f"  ✓ Raw: {raw_total}, Canonical: {canonical_total}, Aligned")
    
    # 5. CAPTION FILES CHECK
    print("\n[5] CAPTION FILES (.vtt)")
    caption_count = len(list(Path('out').glob('**/*.en.vtt')))
    caption_rate = (caption_count / raw_total * 100) if raw_total > 0 else 0
    
    if caption_rate < 90:
        warnings.append(
            f"WARNING: Low caption coverage: {caption_rate:.1f}% "
            f"({caption_count}/{raw_total})"
        )
        print(f"  ⚠️ Caption coverage: {caption_rate:.1f}% ({caption_count}/{raw_total})")
    else:
        print(f"  ✓ Caption coverage: {caption_rate:.1f}% ({caption_count}/{raw_total})")
    
    # 6. SUMMARY
    print("\n" + "=" * 80)
    if issues:
        print("🔴 CRITICAL ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not issues:
        print("✅ SYSTEM HEALTH: GOOD")
    else:
        print("\n⚠️  ACTION REQUIRED: Fix critical issues before proceeding")
    
    print("=" * 80 + "\n")
    
    return issues, warnings

if __name__ == '__main__':
    issues, warnings = check_system_health()
    exit(1 if issues else 0)
