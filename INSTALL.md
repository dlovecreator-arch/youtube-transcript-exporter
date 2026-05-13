# Installation

This tool is intentionally lightweight: no SaaS, no API keys, minimal Python deps.

## Requirements

| Tool | Required? | Why |
|---|---|---|
| Python 3.10+ | required | runs the CLI and pipeline |
| `yt-dlp` | required | the bulk extractor (latest, kept rolling) |
| `ffmpeg` | optional | only for the Whisper fallback (audio decode) |
| `faster-whisper` | optional | local fallback transcription for caption-less videos |
| `pyyaml` | optional | nicer YAML frontmatter in markdown output |

You do **not** need a YouTube API key.

## Install per platform

### macOS

```bash
brew install yt-dlp ffmpeg
git clone https://github.com/dlovecreator-arch/youtube-transcript-exporter.git
cd youtube-transcript-exporter
pip3 install -r requirements.txt
python3 -m ytx doctor
```

### Linux (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install python3-pip ffmpeg
pipx install yt-dlp        # or: pip3 install --user -U yt-dlp
git clone https://github.com/dlovecreator-arch/youtube-transcript-exporter.git
cd youtube-transcript-exporter
pip3 install -r requirements.txt
python3 -m ytx doctor
```

### Windows

```powershell
winget install yt-dlp.yt-dlp
winget install Gyan.FFmpeg
git clone https://github.com/dlovecreator-arch/youtube-transcript-exporter.git
cd youtube-transcript-exporter
pip install -r requirements.txt
python -m ytx doctor
```

WSL2 is also fully supported; follow the Linux instructions inside WSL.

## Optional: Whisper fallback

For caption-less videos:

```bash
pip install faster-whisper
# verify
python3 -m ytx doctor
```

`faster-whisper` builds against `av` which needs ffmpeg dev headers. If install fails:

- macOS: `brew install ffmpeg` (full install, not just the binary)
- Linux: `sudo apt install ffmpeg libavformat-dev libavcodec-dev libavutil-dev libswscale-dev`

## Optional: keep yt-dlp rolling

YouTube changes their site often. Keep yt-dlp current:

```bash
# Homebrew
brew upgrade yt-dlp

# pipx / pip
yt-dlp -U
```

The downloader uses `--extractor-args youtube:player_client=android,web,ios` to survive site changes, but the simplest fix when something breaks is `yt-dlp -U`.

## First run

```bash
# Verify environment
python3 -m ytx doctor

# Add a channel and walk away
python3 -m ytx add https://www.youtube.com/@LexFridman

# Check health
python3 -m ytx audit
```

If the audit reports drift, see [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md).

## Keeping it healthy

- `python3 -m ytx update` -- re-runs the download for every URL in `channels.txt` (idempotent)
- `python3 -m ytx audit` -- reports anything that drifted
- `tests/smoke_test.sh` -- sanity check after upgrades
- Cron-friendly: every command exits non-zero on real problems
