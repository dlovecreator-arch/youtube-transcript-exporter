# Installation Guide

## Requirements

- **Python**: 3.9 or higher
- **OS**: Linux, macOS, or Windows (with WSL2 recommended)
- **Disk Space**: 10GB+ for initial dataset
- **Internet**: Required for YouTube API access

## Quick Start (5 minutes)

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/youtube_transcript_exporter.git
cd youtube_transcript_exporter
```

### 2. Verify Python version

```bash
python3 --version  # Should be 3.9 or higher
```

### 3. Set up the environment

```bash
# Create necessary directories
mkdir -p db out markdown

# Create a .env file (optional, for YouTube API key)
touch .env
```

### 4. Verify installation

```bash
python3 system_health_check.py
```

You should see:
```
================================================================================
SYSTEM HEALTH CHECK - COMPREHENSIVE
================================================================================
[1] CANONICAL DATABASE
  ✓ Database initialized (0 videos initially)
```

## Configuration

### YouTube API Setup (Recommended)

To access transcripts and metadata, you need a YouTube API key:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable YouTube Data API v3
4. Create an API key (Credentials > API Key)
5. Add to your `.env` file:

```env
YOUTUBE_API_KEY=your_key_here
```

### Configuration Options

Create a `config.json` file in the project root:

```json
{
  "youtube_api_key": "YOUR_KEY_HERE",
  "max_workers": 4,
  "download_timeout": 300,
  "retry_attempts": 3,
  "retry_delay": 5,
  "output_dir": "out",
  "markdown_dir": "markdown",
  "db_path": "db/canonical.json"
}
```

Default values will be used if not specified.

## Usage

### Basic Operations

#### Download transcripts from a channel

```bash
./download_parallel.sh "https://www.youtube.com/c/YourChannelName"
```

#### Export to different formats

```bash
# Export to markdown (recommended)
./export.sh --markdown

# Export to Notion
./export.sh --notion

# Export to Obsidian
./export.sh --obsidian

# Full audit
./export.sh --audit
```

#### Check system health

```bash
python3 system_health_check.py
```

### Batch Operations

#### Download multiple channels

```bash
./batch_redownload_parallel.sh
```

#### Enhancement pipeline

```bash
./enhance_parallel_batch.sh
```

## Docker Setup (Optional)

For isolated environments:

```bash
docker build -t yt-transcript-exporter .
docker run -it -v $(pwd):/data yt-transcript-exporter
```

## Troubleshooting

### Common Issues

**Issue**: "Python 3 not found"
```bash
# Use python3 explicitly
python3 system_health_check.py

# Or verify installation
which python3
python3 --version
```

**Issue**: "YouTube API quota exceeded"
- Wait 24 hours for quota reset
- Or implement exponential backoff (see TROUBLESHOOTING.md)

**Issue**: "Disk space full"
- Check available space: `df -h`
- Clean old downloads: `rm -rf out/old_channel_*`

**Issue**: "Network timeout"
- Increase timeout in config.json: `"download_timeout": 600`
- Or re-run download (idempotent by design)

### Check Logs

```bash
# View recent logs
tail -f logs/transcript_exporter.log

# Search for errors
grep ERROR logs/transcript_exporter.log
```

## Updating

```bash
# Pull latest changes
git pull origin main

# Run health check to verify
python3 system_health_check.py
```

## Getting Help

- **Documentation**: See [README.md](README.md)
- **Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **API Reference**: See [API.md](API.md)
- **Issues**: Open a GitHub issue with:
  - Python version
  - OS/Platform
  - Output of `system_health_check.py`
  - Last 50 lines of error log

## Next Steps

1. Read the [README.md](README.md) for project overview
2. Try a test download with a small channel
3. Review [API.md](API.md) for programmatic usage
4. Check [CONTRIBUTING.md](CONTRIBUTING.md) if you want to contribute
