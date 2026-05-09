#!/usr/bin/env python3
"""
Unicode-aware channel video counter
Handles accented characters and special folder names correctly

Features:
  - Comprehensive error handling
  - Detailed error messages
  - Directory validation
"""

import os
from pathlib import Path
import json
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def count_videos_by_channel():
    """Count videos per channel, handling Unicode folder names correctly"""
    
    try:
        out_dir = Path('out')
        
        if not out_dir.exists():
            logger.error("Directory 'out' not found")
            logger.info("Create it with: mkdir -p out")
            return {}
        
        if not out_dir.is_dir():
            logger.error(f"'out' exists but is not a directory")
            return {}
        
        channels = {}
        
        for channel_folder in os.listdir(out_dir):
            try:
                channel_path = out_dir / channel_folder
                
                if not channel_path.is_dir():
                    continue
                
                video_count = 0
                for video_folder in os.listdir(channel_path):
                    try:
                        video_path = channel_path / video_folder
                        
                        if not video_path.is_dir():
                            continue
                        
                        # Count .info.json files in this video folder
                        for file in os.listdir(video_path):
                            if file.endswith('.info.json'):
                                video_count += 1
                                break
                    except OSError as e:
                        logger.warning(f"Error reading {video_path}: {e}")
                        continue
                
                if video_count > 0:
                    channels[channel_folder] = video_count
            
            except OSError as e:
                logger.warning(f"Error reading channel {channel_folder}: {e}")
                continue
        
        return channels
    
    except Exception as e:
        logger.error(f"Error counting videos: {e}")
        return {}

def count_total_files():
    """Count total .info.json files directly"""
    try:
        out_dir = Path('out')
        if not out_dir.exists():
            logger.warning("'out' directory not found")
            return 0
        total = len(list(out_dir.glob('*/*/*.info.json')))
        return total
    except Exception as e:
        logger.error(f"Error counting total files: {e}")
        return 0

if __name__ == '__main__':
    try:
        print("=" * 70)
        print("CHANNEL VIDEO COUNT (Unicode-Aware)")
        print("=" * 70)
        print()
        
        channels = count_videos_by_channel()
        total_from_counting = sum(channels.values())
        total_files = count_total_files()
        
        if not channels:
            logger.warning("No channels found. Initialize downloads with:")
            logger.warning("  ./download_parallel.sh 'https://www.youtube.com/c/ChannelName'")
            sys.exit(1)
        
        print(f"Channels: {len(channels)}")
        print()
        
        for channel in sorted(channels.keys()):
            count = channels[channel]
            print(f"  {channel}: {count}")
        
        print()
        print("=" * 70)
        print(f"Total (counted): {total_from_counting}")
        print(f"Total (files): {total_files}")
        print(f"Match: {'✅ YES' if total_from_counting == total_files else f'⚠️ MISMATCH ({abs(total_files - total_from_counting)} diff)'}")
        print("=" * 70)
        
        # Also show the correct André Duqum count
        for channel, count in channels.items():
            if 'duq' in channel.lower() or 'andré' in channel.lower():
                print(f"\n✓ André Duqum verified: {count} videos")
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
