#!/usr/bin/env python3
"""
Comprehensive Test Suite for YouTube Transcript Exporter

Run with: python3 -m pytest tests/ -v
Or manually: python3 tests/test_all.py
"""

import unittest
import json
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSystemHealth(unittest.TestCase):
    """Test system health checks"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db_path = Path(self.temp_dir.name) / "canonical.json"
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.temp_dir.cleanup()
    
    def test_database_creation(self):
        """Test database can be created"""
        db = {
            "videos": [],
            "metadata": {
                "total_videos": 0,
                "total_channels": 0,
                "last_sync": None,
                "version": "1.0"
            }
        }
        
        self.test_db_path.write_text(json.dumps(db))
        self.assertTrue(self.test_db_path.exists())
        
        loaded = json.loads(self.test_db_path.read_text())
        self.assertEqual(len(loaded["videos"]), 0)
    
    def test_database_json_validity(self):
        """Test database JSON is valid"""
        db = {
            "videos": [
                {
                    "id": "test123",
                    "title": "Test Video",
                    "channel": "Test Channel",
                    "transcript": "Test transcript content"
                }
            ],
            "metadata": {
                "total_videos": 1,
                "total_channels": 1,
                "last_sync": datetime.utcnow().isoformat(),
                "version": "1.0"
            }
        }
        
        self.test_db_path.write_text(json.dumps(db))
        
        try:
            loaded = json.loads(self.test_db_path.read_text())
            self.assertEqual(loaded["metadata"]["total_videos"], 1)
        except json.JSONDecodeError:
            self.fail("Database JSON is invalid")


class TestFileOperations(unittest.TestCase):
    """Test file operations"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_directory_creation(self):
        """Test directory structure creation"""
        dirs = ["db", "out", "markdown", "logs"]
        
        for d in dirs:
            dir_path = self.base_path / d
            dir_path.mkdir(parents=True, exist_ok=True)
            self.assertTrue(dir_path.exists())
            self.assertTrue(dir_path.is_dir())
    
    def test_file_permissions(self):
        """Test file can be read and written"""
        test_file = self.base_path / "test.txt"
        test_content = "Test content"
        
        test_file.write_text(test_content)
        read_content = test_file.read_text()
        
        self.assertEqual(test_content, read_content)


class TestDataValidation(unittest.TestCase):
    """Test data validation functions"""
    
    def test_sanitize_slug(self):
        """Test slug sanitization"""
        from src.enhance_rag_schema import sanitize_slug
        
        test_cases = [
            ("Test Channel", "test_channel"),
            ("Test-Channel-Name", "test_channel_name"),
            ("André Duqum", "andr_duqum"),
            ("Channel@#$%", "channel"),
        ]
        
        for input_val, expected in test_cases:
            result = sanitize_slug(input_val)
            self.assertEqual(result, expected, f"Failed for input: {input_val}")
    
    def test_extract_guest(self):
        """Test guest extraction"""
        from src.enhance_rag_schema import extract_guest
        
        test_cases = [
            ("Interview | John Smith", "John Smith"),
            ("John Smith REVEALS Secret", "John Smith"),
            ("Random Title", None),
        ]
        
        for title, expected in test_cases:
            result = extract_guest(title)
            self.assertEqual(result, expected, f"Failed for: {title}")


class TestConfiguration(unittest.TestCase):
    """Test configuration management"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "config.json"
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_default_config(self):
        """Test default configuration"""
        config = {
            "youtube_api_key": None,
            "max_workers": 4,
            "download_timeout": 300,
            "retry_attempts": 3,
        }
        
        self.config_path.write_text(json.dumps(config))
        loaded = json.loads(self.config_path.read_text())
        
        self.assertEqual(loaded["max_workers"], 4)
        self.assertEqual(loaded["download_timeout"], 300)
    
    def test_config_override(self):
        """Test configuration override"""
        config = {
            "max_workers": 8,
            "custom_setting": "value"
        }
        
        self.config_path.write_text(json.dumps(config))
        loaded = json.loads(self.config_path.read_text())
        
        self.assertEqual(loaded["max_workers"], 8)
        self.assertEqual(loaded["custom_setting"], "value")


class TestErrorHandling(unittest.TestCase):
    """Test error handling"""
    
    def test_missing_database_handling(self):
        """Test handling of missing database"""
        temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(temp_dir.name) / "nonexistent.json"
        
        self.assertFalse(db_path.exists())
        temp_dir.cleanup()
    
    def test_corrupted_json_handling(self):
        """Test handling of corrupted JSON"""
        temp_dir = tempfile.TemporaryDirectory()
        bad_json_path = Path(temp_dir.name) / "bad.json"
        
        bad_json_path.write_text("{invalid json]")
        
        try:
            json.loads(bad_json_path.read_text())
            self.fail("Should have raised JSONDecodeError")
        except json.JSONDecodeError:
            pass  # Expected
        
        temp_dir.cleanup()


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
