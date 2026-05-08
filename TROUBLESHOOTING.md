# Troubleshooting Guide

## Quick Diagnosis

Start here: Run the health check and capture the output.

```bash
python3 system_health_check.py > health_report.txt 2>&1
```

Then search this document for your symptoms.

## Common Issues & Solutions

### Issue: "command not found: python3"

**Symptoms**:
```
bash: python3: command not found
```

**Causes**:
- Python not installed
- Python not in PATH
- Wrong python version

**Solutions**:

1. **Check if Python is installed**:
   ```bash
   which python
   python --version
   ```

2. **Install Python** (if not installed):
   ```bash
   # macOS
   brew install python3

   # Ubuntu/Debian
   sudo apt-get install python3

   # Fedora
   sudo dnf install python3

   # Windows (WSL2)
   sudo apt-get install python3
   ```

3. **Add Python to PATH** (if installed but not found):
   ```bash
   export PATH="/usr/local/bin:$PATH"
   ```

4. **Use python instead of python3**:
   ```bash
   python --version
   python system_health_check.py
   ```

### Issue: "No such file or directory: db/canonical.json"

**Symptoms**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'db/canonical.json'
```

**Causes**:
- Database not initialized
- Wrong working directory
- Directory structure not created

**Solutions**:

1. **Create directory structure**:
   ```bash
   mkdir -p db out markdown logs
   ```

2. **Initialize database**:
   ```bash
   python3 << 'EOF'
   import json
   db = {
       "videos": [],
       "metadata": {
           "total_videos": 0,
           "total_channels": 0,
           "last_sync": None,
           "version": "1.0"
       }
   }
   with open("db/canonical.json", "w") as f:
       json.dump(db, f, indent=2)
   EOF
   ```

3. **Verify working directory**:
   ```bash
   pwd
   ls -la db/canonical.json
   ```

### Issue: "Permission denied: export.sh"

**Symptoms**:
```
bash: ./export.sh: Permission denied
```

**Causes**:
- Script not executable
- File system read-only

**Solutions**:

1. **Make script executable**:
   ```bash
   chmod +x *.sh
   chmod +x src/*.py
   ```

2. **Check file permissions**:
   ```bash
   ls -la export.sh
   # Should show: -rwxr-xr-x
   ```

3. **If on read-only filesystem**:
   ```bash
   # Check mount
   mount | grep "$(pwd)"
   
   # Try remounting read-write
   sudo mount -o remount,rw /path/to/mount
   ```

### Issue: "Disk quota exceeded"

**Symptoms**:
```
IOError: [Errno 28] No space left on device
```

**Causes**:
- Disk is full
- Quota exceeded
- Large downloads taking space

**Solutions**:

1. **Check disk space**:
   ```bash
   df -h
   du -sh ./out ./markdown ./db
   ```

2. **Clean old data**:
   ```bash
   # Remove old channel downloads (example)
   rm -rf out/channel_name_old/
   
   # Remove temporary files
   rm -rf .tmp/*
   
   # Clean old exports
   find markdown -mtime +30 -delete
   ```

3. **Move to larger disk**:
   ```bash
   # Move data directory
   mv out /mnt/larger_disk/
   ln -s /mnt/larger_disk/out ./out
   ```

4. **Increase quota** (if on shared system):
   ```bash
   # Contact system administrator
   # Check current quota
   quota
   ```

### Issue: "YouTube API quota exceeded"

**Symptoms**:
```
HttpError: 403 Client Error: Forbidden
quota exceeded
```

**Causes**:
- Used all daily quota (10,000 units/day by default)
- Too many requests too quickly
- API key rate limited

**Solutions**:

1. **Wait for quota reset**:
   - Quota resets daily at midnight PT
   - Check your quota at [Google Cloud Console](https://console.cloud.google.com/apis/dashboard)

2. **Implement exponential backoff** (automatic in latest version):
   ```bash
   # Re-run download (will wait and retry)
   ./download_parallel.sh CHANNEL_URL
   ```

3. **Increase quota limits**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/apis/api/youtube.googleapis.com/quota)
   - Request quota increase (usually approved in 1-2 days)

4. **Use multiple API keys** (for production):
   ```bash
   # Edit config.json
   {
     "youtube_api_keys": [
       "KEY1",
       "KEY2",
       "KEY3"
     ]
   }
   ```

5. **Optimize API usage**:
   ```bash
   # Use caching
   ./download_parallel.sh CHANNEL_URL --use-cache

   # Download only new videos
   ./download_parallel.sh CHANNEL_URL --incremental
   ```

### Issue: "Connection timeout"

**Symptoms**:
```
TimeoutError: Download timed out after 300 seconds
urllib.error.URLError: _ssl.c:1129: The handshake operation timed out
```

**Causes**:
- Network latency
- Server slow response
- Firewall blocking
- ISP throttling

**Solutions**:

1. **Increase timeout**:
   ```bash
   # Edit config.json
   {
     "download_timeout": 600  # 10 minutes instead of 5
   }
   ```

2. **Check network**:
   ```bash
   # Test connectivity
   ping youtube.com
   
   # Check DNS
   nslookup youtube.com
   
   # Test YouTube directly
   curl -I https://www.youtube.com
   ```

3. **Try VPN/proxy** (if YouTube blocked):
   ```bash
   # Configure in config.json
   {
     "proxy": "http://proxy.example.com:8080"
   }
   ```

4. **Retry with backoff**:
   ```bash
   # Automatic retry (built-in)
   # Or manual retry with delay
   sleep 60 && ./download_parallel.sh CHANNEL_URL
   ```

5. **Check ISP throttling**:
   - Change download time (off-peak hours)
   - Reduce parallel workers: `--workers 1`

### Issue: "Invalid JSON in database"

**Symptoms**:
```
json.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Causes**:
- Corrupted database file
- Incomplete write
- Disk error

**Solutions**:

1. **Backup and restore**:
   ```bash
   # Backup
   cp db/canonical.json db/canonical.json.backup
   
   # Check last good backup
   ls -lh db/canonical.json*
   ```

2. **Repair database**:
   ```bash
   python3 << 'EOF'
   import json
   import sys
   
   try:
       with open("db/canonical.json") as f:
           data = json.load(f)
       print("✓ Database is valid")
   except json.JSONDecodeError as e:
       print(f"✗ JSON Error: {e}")
       print("Attempting recovery...")
       
       # Try to fix
       with open("db/canonical.json", "r") as f:
           content = f.read()
       
       # Remove trailing invalid characters
       content = content.rstrip('\n').rstrip('}')
       if not content.endswith('}'):
           content += '}'
       
       with open("db/canonical.json", "w") as f:
           f.write(content)
       
       try:
           with open("db/canonical.json") as f:
               json.load(f)
           print("✓ Database repaired")
       except:
           print("✗ Cannot repair. Restore from backup or reinitialize.")
   EOF
   ```

3. **Reinitialize** (last resort, will lose data):
   ```bash
   python3 << 'EOF'
   import json
   db = {
       "videos": [],
       "metadata": {
           "total_videos": 0,
           "total_channels": 0,
           "last_sync": None,
           "version": "1.0"
       }
   }
   with open("db/canonical.json", "w") as f:
       json.dump(db, f, indent=2)
   EOF
   ```

### Issue: "Missing transcript"

**Symptoms**:
```
⚠️ Video X has no transcript
```

**Causes**:
- Video has no captions
- Captions are in another language
- YouTube disabled captions for video
- Transcript not available for this video

**Solutions**:

1. **Check if captions exist**:
   ```bash
   # Check YouTube directly
   # Visit video on YouTube, check "Subtitles" button
   ```

2. **Try automatic captions**:
   ```bash
   # Edit download script to enable auto-captions
   # Note: Requires yt-dlp, not YouTube API
   ```

3. **Skip videos without transcripts**:
   ```bash
   # Edit config.json
   {
     "skip_no_transcript": true
   }
   ```

4. **Use fallback to speech-to-text**:
   ```bash
   # Not implemented yet, would require external API
   # Consider filing feature request
   ```

### Issue: "Markdown generation incomplete"

**Symptoms**:
```
⚠️ CRITICAL: 2 channels in DB but missing markdown folders! (21/23)
```

**Causes**:
- Partial generation interrupted
- Disk space filled mid-process
- Permission issues during write

**Solutions**:

1. **Check what's missing**:
   ```bash
   python3 system_health_check.py
   
   # Check which channels are missing
   python3 << 'EOF'
   import json
   import os
   
   with open("db/canonical.json") as f:
       db = json.load(f)
   
   channels = set()
   for video in db["videos"]:
       channels.add(video.get("channel", "Unknown"))
   
   missing = []
   for ch in channels:
       md_dir = f"markdown/{ch}"
       if not os.path.exists(md_dir):
           missing.append(ch)
   
   print("Missing markdown for channels:")
   for ch in missing:
       print(f"  - {ch}")
   EOF
   ```

2. **Regenerate markdown**:
   ```bash
   # Full regeneration
   ./export.sh --markdown --force
   
   # Or for specific channel
   python3 << 'EOF'
   from src.markdown_generator import MarkdownGenerator
   import json
   
   gen = MarkdownGenerator()
   
   # Filter and regenerate
   with open("db/canonical.json") as f:
       db = json.load(f)
   
   videos = [v for v in db["videos"] if v["channel"] == "ChannelName"]
   for video in videos:
       gen.generate(video)
   EOF
   ```

3. **Check permissions**:
   ```bash
   ls -ld markdown/
   # Should show: drwxr-xr-x
   
   chmod -R u+w markdown/
   ```

### Issue: "Performance is slow"

**Symptoms**:
- Downloads taking very long
- Health check takes > 30 seconds
- Markdown generation is slow

**Solutions**:

1. **Increase parallelism**:
   ```bash
   ./download_parallel.sh CHANNEL_URL --workers 8
   ```

2. **Check system resources**:
   ```bash
   # CPU usage
   top -b -n 1 | head -20
   
   # Memory usage
   free -h
   
   # Disk I/O
   iostat -x 1 5
   ```

3. **Reduce batch size** (if out of memory):
   ```bash
   # Edit config.json
   {
     "batch_size": 50  # Default: 100
   }
   ```

4. **Use SSD** (if on slow disk):
   - Move `db/` and `out/` to faster storage
   - Or use symlinks: `ln -s /mnt/ssd/db ./db`

5. **Optimize database** (for large datasets):
   ```bash
   python3 << 'EOF'
   import json
   
   # Defragment database
   with open("db/canonical.json") as f:
       db = json.load(f)
   
   # Write back compactly
   with open("db/canonical.json", "w") as f:
       json.dump(db, f, separators=(',', ':'))
   EOF
   ```

### Issue: "Export format is wrong"

**Symptoms**:
- Markdown has wrong structure
- Obsidian vault not working
- Notion database import fails

**Solutions**:

1. **Check format version**:
   ```bash
   ./export.sh --markdown --version
   ```

2. **Regenerate with latest version**:
   ```bash
   git pull origin main
   ./export.sh --markdown --force
   ```

3. **Check documentation**:
   - Markdown format: See [README.md](README.md)
   - Obsidian setup: See [API.md](API.md)
   - Notion setup: See [API.md](API.md)

## Debug Mode

Enable verbose logging:

```bash
# Set debug environment variable
export DEBUG=1
python3 system_health_check.py

# Or edit scripts to add debug output
# Add this to shell scripts:
set -x  # Print each command

# In Python scripts:
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Getting More Help

If you can't find a solution here:

1. **Check the logs**:
   ```bash
   tail -100 logs/transcript_exporter.log
   grep ERROR logs/transcript_exporter.log
   ```

2. **Run diagnostic**:
   ```bash
   python3 system_health_check.py > diagnostic.txt 2>&1
   ```

3. **Search GitHub Issues**:
   - Go to [Issues](https://github.com/your-repo/issues)
   - Use keywords from your error

4. **Create a new issue** with:
   - Error message (full output)
   - Output of `python3 system_health_check.py`
   - Last 100 lines of log file
   - Python version: `python3 --version`
   - OS info: `uname -a`
   - Steps to reproduce

## Performance Benchmarks

Expected performance on modern hardware:

```
Operation              | Time/1000 videos | Time/1000 channels
--------------------- | --------------- | ------------------
Download transcripts  | ~15-30 minutes   | ~1-3 hours
Generate markdown     | ~5-10 minutes    | ~30-60 minutes
Health check          | ~1-5 seconds     | ~2-10 seconds
Database queries      | <100ms           | <500ms
```

Actual times depend on:
- Network speed
- YouTube API rate limits
- Disk speed (SSD vs HDD)
- Parallel workers (default: 4)

## Reporting Bugs

Found a bug? Help us fix it!

**Bug report template**:

```
Title: Brief description of bug

Description:
[Detailed description]

Steps to reproduce:
1. ...
2. ...
3. ...

Expected behavior:
[What should happen]

Actual behavior:
[What actually happens]

Environment:
- Python version: [output of python3 --version]
- OS: [Linux/macOS/Windows]
- Platform: [x86_64/ARM64/etc]

Logs:
[Output of health check]
[Relevant error messages]
```

Thanks for helping make this project better!
