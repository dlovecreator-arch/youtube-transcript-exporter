# Quick Start

Get a YouTube channel into a clean local dataset in 5 minutes. No API keys. No SaaS.

## 1. Install (2 min)

```bash
git clone https://github.com/dlovecreator-arch/youtube-transcript-exporter.git
cd youtube-transcript-exporter

# Python deps (minimal -- pyyaml only required for one optional tool)
pip install -r requirements.txt

# yt-dlp is required
# macOS:    brew install yt-dlp ffmpeg
# Linux:    pipx install yt-dlp && sudo apt install ffmpeg
# Windows:  winget install yt-dlp.yt-dlp
```

## 2. Sanity check

```bash
python -m ytx doctor
```

You should see green checkmarks for `yt-dlp`, `python3`, and `disk free`. ffmpeg is optional (only needed for the Whisper fallback). faster_whisper is optional too.

## 3. Add your first channel

```bash
python -m ytx add https://www.youtube.com/@LexFridman
```

This will:
1. Resilient-download metadata + captions (no media) for every video
2. Build `db/canonical.json` with deduplicated records
3. Generate Obsidian-ready Markdown under `markdown/Lex Fridman/`
4. Add the URL to `channels.txt` for future `ytx update`

## 4. Check what you've got

```bash
python -m ytx status
python -m ytx audit --quick --warn-ok
python -m ytx fix          # dry-run safe repair plan
```

Reports counts, caption coverage, alignment, and any drift. Exit code is 0 when healthy.

## 5. Use it

Open `markdown/` as an Obsidian vault, or:

```bash
# Export everything as JSONL for RAG / embeddings
python -m ytx export jsonl --out exports/transcripts.jsonl
python -m ytx export chunks --out exports/chunks.jsonl

# Generate Obsidian dashboard notes
python -m ytx obsidian

# Write a timestamped maintenance report
python -m ytx report

# Refresh all channels
python -m ytx update

# Fast markdown generation modes
python -m ytx markdown --missing-only
python -m ytx markdown --channel "Channel Name"

# Fill caption gaps with Whisper (optional)
pip install faster-whisper
python -m ytx transcribe --model small --limit 50
```

## Common flags

```bash
# Use your browser cookies for higher reliability (big win against rate limits)
python -m ytx add <url> --cookies-from-browser chrome

# Use a proxy (works great with a VPN)
python -m ytx add <url> --proxy http://localhost:1080

# Bulk-add from a file (one URL per line)
python -m ytx add channels.txt
```

## What's next

- [`README.md`](README.md) for the philosophy + full reliability story
- [`docs/RAG_AND_OBSIDIAN.md`](docs/RAG_AND_OBSIDIAN.md) for chunk exports, Obsidian dashboards, and run reports
- [`CONVENTIONS.md`](CONVENTIONS.md) for the layout rules and lessons learned
- [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) if anything fights you
- [`CONTRIBUTING.md`](CONTRIBUTING.md) to add features or new exporters
