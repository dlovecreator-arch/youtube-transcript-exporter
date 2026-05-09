#!/usr/bin/env python3
"""Validate markdown folder structure against out/ folder.

This script MUST be run after any markdown generation to ensure
no duplicates or naming misalignment exists.

Usage:
    python3 validate_markdown_alignment.py
    
Exit codes:
    0 = Perfect alignment
    1 = Misalignment detected
"""
import os
import sys
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).parent.parent
OUT_DIR = REPO_ROOT / 'out'
MD_DIR = REPO_ROOT / 'markdown'

def normalize_name(name):
    """Ultra-aggressive normalization to catch ALL duplicate variations.
    
    This catches duplicates like:
    - Kerry K vs Kerry_K
    - John Burgos vs John_Burgos
    - The Alchemist vs The_Alchemist
    - André Duqum vs Andre Duqum (accents)
    """
    return (name
            .lower()
            .replace(' ', '')
            .replace('_', '')
            .replace('-', '')
            .replace('.', '')
            .replace('⧸', 'w')
            .replace('é', 'e')
            .replace('à', 'a')
    )

def check_alignment():
    """Verify markdown folders match out/ folders exactly."""
    print("="*70)
    print("VALIDATING MARKDOWN/OUT ALIGNMENT")
    print("="*70 + "\n")
    
    # Get all channels
    out_channels = sorted([d for d in os.listdir(OUT_DIR) if (OUT_DIR / d).is_dir()])
    md_channels = sorted([d for d in os.listdir(MD_DIR) if (MD_DIR / d).is_dir()])
    
    print(f"OUT folder:  {len(out_channels)} channels")
    print(f"MD folder:   {len(md_channels)} channels\n")
    
    # Check exact matches
    out_set = set(out_channels)
    md_set = set(md_channels)
    
    missing_from_md = out_set - md_set
    extra_in_md = md_set - out_set
    
    issues = 0
    
    if missing_from_md:
        print(f"❌ MISSING from markdown ({len(missing_from_md)}):")
        for ch in sorted(missing_from_md):
            print(f"   - {ch}")
        issues += len(missing_from_md)
    
    if extra_in_md:
        print(f"❌ EXTRA in markdown ({len(extra_in_md)}):")
        for ch in sorted(extra_in_md):
            print(f"   - {ch}")
        issues += len(extra_in_md)
    
    # Check for duplicates (normalized)
    normalized_map = defaultdict(list)
    for ch in md_channels:
        norm = normalize_name(ch)
        normalized_map[norm].append(ch)
    
    duplicates = {norm: channels for norm, channels in normalized_map.items() if len(channels) > 1}
    
    if duplicates:
        print(f"\n❌ DUPLICATE CHANNELS DETECTED ({len(duplicates)}):")
        for norm_name, versions in sorted(duplicates.items()):
            print(f"   Normalized: {norm_name}")
            for v in versions:
                count = len([f for f in os.listdir(MD_DIR / v) if f.endswith('.md')])
                print(f"      - {v:<45} ({count} files)")
        issues += len(duplicates)
    
    # Summary
    print("\n" + "="*70)
    if issues == 0:
        print("✅ PERFECT ALIGNMENT - NO DUPLICATES")
        print("="*70)
        
        # Stats
        total_files = sum(1 for root, dirs, files in os.walk(MD_DIR) 
                         for f in files if f.endswith('.md'))
        print(f"\n📊 Statistics:")
        print(f"   - Channels: {len(out_channels)}")
        print(f"   - Markdown files: {total_files:,}")
        print(f"   - Avg per channel: {total_files // len(out_channels)}")
        
        return 0
    else:
        print(f"❌ FOUND {issues} ISSUES - FIX BEFORE COMMITTING")
        print("="*70)
        return 1

if __name__ == '__main__':
    sys.exit(check_alignment())
