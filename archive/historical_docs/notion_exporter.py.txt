#!/usr/bin/env python3
"""Notion API exporter: Push transcripts to Notion database.

Requires: NOTION_TOKEN environment variable

Creates database schema if needed, then bulk imports video records.
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# You'll need: pip install notion-client
try:
    from notion_client import Client
except ImportError:
    print("Error: pip install notion-client")
    sys.exit(1)

DB_FILE = Path(__file__).resolve().parent.parent / "db" / "canonical.json"


class NotionExporter:
    def __init__(self, token: str = None, database_id: str = None):
        """Initialize Notion client."""
        token = token or os.getenv("NOTION_TOKEN")
        if not token:
            raise ValueError("NOTION_TOKEN environment variable not set")
        
        self.client = Client(auth=token)
        self.database_id = database_id
    
    def create_database(self, parent_page_id: str, title: str = "YouTube Transcripts") -> str:
        """Create Notion database with transcript schema."""
        
        schema = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": {
                "Title": {"title": {}},
                "Video ID": {"rich_text": {}},
                "Guest": {"rich_text": {}},
                "Channel": {"select": {
                    "options": [
                        {"name": "Emilio Ortiz", "color": "purple"},
                        {"name": "Viviane Chauvet", "color": "blue"},
                    ]
                }},
                "Date": {"date": {}},
                "Duration (min)": {"number": {"format": "number"}},
                "Views": {"number": {"format": "number"}},
                "Likes": {"number": {"format": "number"}},
                "Topics": {"multi_select": {}},
                "Category": {"select": {}},
                "Link": {"url": {}},
                "Transcript": {"rich_text": {}},
                "Transcript Length": {"number": {"format": "number"}},
                "Last Updated": {"last_edited_time": {}},
            }
        }
        
        response = self.client.databases.create(**schema)
        db_id = response['id']
        print(f"✓ Created Notion database: {db_id}")
        
        # Save to config
        config_file = Path(__file__).resolve().parent.parent / "config.json"
        config = {"notion_database_id": db_id}
        config_file.write_text(json.dumps(config, indent=2))
        
        return db_id
    
    def bulk_import(self, max_records: int = None):
        """Import all videos from canonical DB into Notion."""
        
        if not self.database_id:
            print("Error: database_id not set. Use create_database() first or set NOTION_DATABASE_ID env var.")
            sys.exit(1)
        
        # Load canonical DB
        try:
            db = json.loads(DB_FILE.read_text())
        except FileNotFoundError:
            print(f"Error: {DB_FILE} not found. Run metadata_extractor.py first.")
            sys.exit(1)
        
        videos = db.get("videos", [])
        if max_records:
            videos = videos[:max_records]
        
        print(f"Importing {len(videos)} videos to Notion...")
        
        stats = {"success": 0, "error": 0}
        
        for i, record in enumerate(videos, 1):
            try:
                # Build page properties
                properties = {
                    "Title": {
                        "title": [{"type": "text", "text": {"content": record['title'][:200]}}]
                    },
                    "Video ID": {
                        "rich_text": [{"type": "text", "text": {"content": record['id']}}]
                    },
                    "Guest": {
                        "rich_text": [{"type": "text", "text": {"content": record.get("guest") or "N/A"}}]
                    },
                    "Channel": {
                        "select": {"name": record['channel'][:50]}
                    },
                    "Date": {
                        "date": {"start": self.format_date(record.get("date", ""))}
                    },
                    "Duration (min)": {
                        "number": int(record.get("duration", 0) / 60)
                    },
                    "Views": {
                        "number": record.get("views", 0)
                    },
                    "Likes": {
                        "number": record.get("likes", 0)
                    },
                    "Topics": {
                        "multi_select": [
                            {"name": tag[:50]} for tag in (record.get("tags", [])[:5])
                        ]
                    },
                    "Category": {
                        "select": {"name": (record.get("category") or "Other")[:50]}
                    },
                    "Link": {
                        "url": record['url']
                    },
                }
                
                # Add optional transcript snippet (first 2000 chars) if stored
                # Note: Full transcript would be too large for Notion
                # Instead, keep transcript in Markdown vault and link it
                
                # Create page
                self.client.pages.create(
                    parent={"database_id": self.database_id},
                    properties=properties
                )
                
                stats["success"] += 1
                
                if (i % 50) == 0:
                    print(f"  ✓ {i}/{len(videos)}")
                
            except Exception as e:
                print(f"  ! Error importing {record['id']}: {e}")
                stats["error"] += 1
        
        print(f"\n✓ Notion import complete:")
        print(f"  - Success: {stats['success']}")
        print(f"  - Errors: {stats['error']}")
        print(f"  - Database: {self.database_id}")
    
    @staticmethod
    def format_date(date_str: str) -> str:
        """Convert YYYYMMDD to YYYY-MM-DD."""
        if len(date_str) == 8:
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        return date_str or "2025-01-01"


def main():
    # Get Notion token from env
    token = os.getenv("NOTION_TOKEN")
    if not token:
        print("Usage: NOTION_TOKEN=xxx DATABASE_ID=xxx python3 notion_exporter.py")
        print("\nOr for first-time setup (requires parent page ID):")
        print("  NOTION_TOKEN=xxx NOTION_PARENT_PAGE=xxx python3 notion_exporter.py --create")
        sys.exit(1)
    
    exporter = NotionExporter(token=token)
    
    # Check if we need to create database
    if "--create" in sys.argv:
        parent_page_id = os.getenv("NOTION_PARENT_PAGE")
        if not parent_page_id:
            print("Error: NOTION_PARENT_PAGE required for --create")
            sys.exit(1)
        db_id = exporter.create_database(parent_page_id)
        exporter.database_id = db_id
    else:
        exporter.database_id = os.getenv("NOTION_DATABASE_ID")
        if not exporter.database_id:
            print("Error: NOTION_DATABASE_ID env var required")
            sys.exit(1)
    
    # Import videos
    exporter.bulk_import()


if __name__ == "__main__":
    main()
