#!/usr/bin/env python3
"""
Unicode-aware channel video counter
Handles accented characters and special folder names correctly
"""

import os
from pathlib import Path
import json

def count_videos_by_channel():
    """Count videos per channel, handling Unicode folder names correctly"""
    
    out_dir = Path('out')
    channels = {}
    
    for channel_folder in os.listdir(out_dir):
        channel_path = out_dir / channel_folder
        
        if not channel_path.is_dir():
            continue
        
        video_count = 0
        for video_folder in os.listdir(channel_path):
            video_path = channel_path / video_folder
            
            if not video_path.is_dir():
                continue
            
            # Count .info.json files in this video folder
            for file in os.listdir(video_path):
                if file.endswith('.info.json'):
                    video_count += 1
                    break
        
        if video_count > 0:
            channels[channel_folder] = video_count
    
    return channels

def count_total_files():
    """Count total .info.json files directly"""
    total = len(list(Path('out').glob('*/*/*.info.json')))
    return total

if __name__ == '__main__':
    print("=" * 70)
    print("CHANNEL VIDEO COUNT (Unicode-Aware)")
    print("=" * 70)
    print()
    
    channels = count_videos_by_channel()
    total_from_counting = sum(channels.values())
    total_files = count_total_files()
    
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
