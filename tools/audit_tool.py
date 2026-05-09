#!/usr/bin/env python3
"""
COMPREHENSIVE SYSTEM AUDIT TOOL
Detects ALL common issues: duplicates, legacy folders, inconsistencies, etc.
Run this before asking for major changes to catch problems early.
"""

import os
import json
import hashlib
from pathlib import Path
from collections import defaultdict
import re

class SystemAudit:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.info = []
        
    def run_full_audit(self):
        """Run all audit checks"""
        print("=" * 80)
        print("COMPREHENSIVE SYSTEM AUDIT")
        print("=" * 80)
        print()
        
        self.check_legacy_folders()
        self.check_duplicate_folders()
        self.check_database_integrity()
        self.check_whitespace_issues()
        self.check_orphaned_files()
        self.check_empty_directories()
        self.check_naming_consistency()
        
        self.print_summary()
    
    def check_legacy_folders(self):
        """Check for _legacy_ prefixed folders in ALL locations"""
        print("1. Checking for legacy folders...")
        legacy_folders = []
        
        # Check markdown/
        for d in Path("markdown").rglob("*"):
            if d.is_dir() and "_legacy" in d.name.lower():
                legacy_folders.append(("markdown", d.relative_to("markdown")))
        
        # Check out/
        for d in Path("out").rglob("*"):
            if d.is_dir() and "_legacy" in d.name.lower():
                legacy_folders.append(("out", d.relative_to("out")))
        
        if legacy_folders:
            for location, path in legacy_folders:
                self.issues.append(f"Legacy folder found: {location}/{path}")
                print(f"   ✗ {location}/{path}")
        else:
            print("   ✓ No legacy folders found")
        print()
    
    def check_duplicate_folders(self):
        """Check for duplicate folders with different naming"""
        print("2. Checking for duplicate folders...")
        duplicates = []
        
        for base_path in ["markdown", "out"]:
            if not Path(base_path).exists():
                continue
            
            folders = {}
            for d in Path(base_path).iterdir():
                if not d.is_dir():
                    continue
                
                # Normalize: remove trailing underscore, lowercase
                normalized = d.name.rstrip('_').lower()
                if normalized not in folders:
                    folders[normalized] = []
                folders[normalized].append(d.name)
            
            for normalized, names in folders.items():
                if len(names) > 1:
                    duplicates.append((base_path, normalized, names))
        
        if duplicates:
            for base_path, normalized, names in duplicates:
                msg = f"Duplicate folders in {base_path}/: {', '.join(names)}"
                self.issues.append(msg)
                print(f"   ✗ {msg}")
        else:
            print("   ✓ No duplicate folders found")
        print()
    
    def check_database_integrity(self):
        """Check database for issues"""
        print("3. Checking database integrity...")
        
        try:
            db = json.load(open("db/canonical.json"))
            videos = db.get("videos", [])
            
            # Check for IDs with whitespace
            whitespace_ids = sum(1 for v in videos if v.get('id') and v.get('id') != v.get('id').strip())
            if whitespace_ids:
                self.issues.append(f"Database: {whitespace_ids} video IDs with whitespace")
                print(f"   ✗ {whitespace_ids} IDs with whitespace")
            
            # Check for channel names with whitespace
            whitespace_channels = sum(1 for v in videos if v.get('channel') and v.get('channel') != v.get('channel').strip())
            if whitespace_channels:
                self.issues.append(f"Database: {whitespace_channels} channel names with whitespace")
                print(f"   ✗ {whitespace_channels} channel names with whitespace")
            
            # Check for duplicate IDs
            ids = [v.get('id') for v in videos if v.get('id')]
            dup_ids = len(ids) - len(set(ids))
            if dup_ids:
                self.issues.append(f"Database: {dup_ids} duplicate video IDs")
                print(f"   ✗ {dup_ids} duplicate video IDs")
            
            if whitespace_ids == 0 and whitespace_channels == 0 and dup_ids == 0:
                print("   ✓ Database integrity verified")
        except Exception as e:
            self.issues.append(f"Database error: {e}")
            print(f"   ✗ Error reading database: {e}")
        print()
    
    def check_whitespace_issues(self):
        """Check all folders for whitespace issues"""
        print("4. Checking for whitespace issues...")
        issues_found = 0
        
        for base_path in ["markdown", "out"]:
            if not Path(base_path).exists():
                continue
            
            for d in Path(base_path).iterdir():
                if not d.is_dir():
                    continue
                
                if d.name != d.name.strip():
                    self.warnings.append(f"{base_path}/{d.name} has leading/trailing whitespace")
                    issues_found += 1
        
        if issues_found:
            print(f"   ! {issues_found} folders with whitespace issues")
        else:
            print("   ✓ No whitespace issues in folder names")
        print()
    
    def check_orphaned_files(self):
        """Check for orphaned files"""
        print("5. Checking for orphaned files...")
        
        try:
            db = json.load(open("db/canonical.json"))
            db_ids = set(v.get('id') for v in db['videos'] if v.get('id'))
            
            # Check VTT files
            vtt_count = 0
            orphaned_vtt = 0
            for f in Path("out").rglob("*.vtt"):
                vtt_count += 1
                matches = re.findall(r'\[?([A-Za-z0-9_-]{11})\]?', f.name)
                if matches and matches[-1] not in db_ids:
                    orphaned_vtt += 1
            
            if orphaned_vtt:
                self.warnings.append(f"Found {orphaned_vtt} orphaned VTT files")
                print(f"   ! {orphaned_vtt}/{vtt_count} VTT files are orphaned")
            else:
                print(f"   ✓ All VTT files have DB references")
        except Exception as e:
            print(f"   ✗ Error checking orphaned files: {e}")
        print()
    
    def check_empty_directories(self):
        """Check for empty directories"""
        print("6. Checking for empty directories...")
        empty_count = 0
        
        for base_path in ["markdown", "out"]:
            if not Path(base_path).exists():
                continue
            
            for d in Path(base_path).iterdir():
                if d.is_dir() and not any(d.iterdir()):
                    self.warnings.append(f"Empty directory: {base_path}/{d.name}")
                    empty_count += 1
        
        if empty_count:
            print(f"   ! {empty_count} empty directories found")
        else:
            print("   ✓ No empty directories")
        print()
    
    def check_naming_consistency(self):
        """Check for naming convention consistency"""
        print("7. Checking naming consistency...")
        
        # Check markdown file naming
        bracket_files = 0
        underscore_files = 0
        
        for f in Path("markdown").rglob("*.md"):
            if "_[" in f.name and f.name.endswith("].md"):
                bracket_files += 1
            elif "_" in f.name:
                underscore_files += 1
        
        print(f"   Markdown files with title_[ID].md: {bracket_files}")
        print(f"   Markdown files with title_ID.md: {underscore_files}")
        
        if bracket_files > 0 and underscore_files > 0:
            self.warnings.append("Mixed naming conventions in markdown files")
            print(f"   ! Mixed naming conventions detected")
        else:
            print(f"   ✓ Consistent naming convention")
        print()
    
    def print_summary(self):
        """Print audit summary"""
        print("=" * 80)
        print("AUDIT SUMMARY")
        print("=" * 80)
        print()
        
        print(f"Critical Issues Found: {len(self.issues)}")
        if self.issues:
            for issue in self.issues:
                print(f"  ✗ {issue}")
        print()
        
        print(f"Warnings: {len(self.warnings)}")
        if self.warnings:
            for warning in self.warnings:
                print(f"  ! {warning}")
        print()
        
        if not self.issues:
            print("✅ SYSTEM AUDIT PASSED - No critical issues found!")
        else:
            print(f"⚠️  {len(self.issues)} critical issues require attention")
        print()

if __name__ == "__main__":
    audit = SystemAudit()
    audit.run_full_audit()
