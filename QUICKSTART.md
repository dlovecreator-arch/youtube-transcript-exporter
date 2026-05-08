# Quick Start Guide

Get YouTube transcripts up and running in 5 minutes.

## Step 1: Clone & Setup (2 minutes)

```bash
# Clone repository
git clone https://github.com/dlovecreator-arch/youtube-transcript-exporter.git
cd youtube-transcript-exporter

# Create required directories
mkdir -p db out markdown logs

# Verify Python 3.9+
python3 --version
```

## Step 2: Get YouTube API Key (2 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable **YouTube Data API v3**
4. Create an API Key under Credentials
5. Save your key

## Step 3: Configure (1 minute)

```bash
# Copy .env template
cp .env.example .env

# Edit .env with your API key
# (or set environment variable: export YOUTUBE_API_KEY=your_key)
```

## Step 4: Test Installation

```bash
# Run health check
python3 system_health_check.py

# You should see:
# ✓ Database initialized (0 videos initially)
# ✓ All checks passed
```

## Step 5: Download Your First Channel

```bash
# Download from a YouTube channel
./download_parallel.sh "https://www.youtube.com/c/CHANNEL_NAME"

# Then export to markdown
./export.sh --markdown
```

Done! Check the `markdown/` folder for your transcripts.

## Next Steps

- **Download more channels**: `./batch_redownload_parallel.sh`
- **Export formats**: See [API.md](API.md) for all export options
- **Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Full docs**: See [README.md](README.md)

## Need Help?

```bash
# Check system status
python3 system_health_check.py

# View recent logs
tail -50 logs/*.log

# See detailed documentation
cat TROUBLESHOOTING.md | grep "Issue:"
```

## Docker Alternative

```bash
# Build and run in Docker
docker-compose up

# Or with API key
YOUTUBE_API_KEY=your_key docker-compose up
```

That's it! You now have YouTube transcripts locally. See [API.md](API.md) for programmatic usage.
