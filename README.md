<div align="center">

<img src="docs/images/banner.svg" alt="YouTube Transcript Exporter" width="100%"/>

<p>
<a href="https://github.com/dlovecreator-arch/youtube-transcript-exporter/actions/workflows/ci.yml"><img src="https://github.com/dlovecreator-arch/youtube-transcript-exporter/actions/workflows/ci.yml/badge.svg" alt="CI"/></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="license"/></a>
<a href="#"><img src="https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="python"/></a>
<a href="#"><img src="https://img.shields.io/badge/yt--dlp-required-red?style=flat-square" alt="yt-dlp"/></a>
<a href="#"><img src="https://img.shields.io/badge/Whisper-optional-7C3AED?style=flat-square&logo=openai&logoColor=white" alt="Whisper"/></a>
<a href="#"><img src="https://img.shields.io/badge/Obsidian-ready-7C3AED?style=flat-square&logo=obsidian&logoColor=white" alt="Obsidian"/></a>
</p>

<h3>Drop in a YouTube channel. Walk away. Get a clean, RAG-ready local dataset.</h3>

<p><em>Production-tested on 60+ channels, 24,000+ videos, ~1.4 GB of indexed transcripts.</em></p>

</div>

---

## Why this exists

You watch a lot of YouTube. Across dozens of channels, the same ideas, guests, and frameworks come up over and over. But you can't search across them. You can't ask *"every time Lex, Huberman, and Joe Hudson talked about attention"*. You can't quote them properly. And every other tool either trickles one video at a time, breaks at channel scale, or locks you into a SaaS.

This tool turns YouTube channels into a **searchable, structured, RAG-friendly dataset** you can:

- read like a library (Markdown vault, Obsidian-ready)
- analyze like a database (one canonical JSON)
- index for semantic search / RAG (JSONL export)
- never re-download (idempotent download archive)

## One command UX

```bash
# Add a channel and walk away
python -m ytx add https://www.youtube.com/@LexFridman

# Add a list of channels
python -m ytx add channels.txt

# Refresh everything you've ever added
python -m ytx update

# Quick local dashboard
python -m ytx status

# Safe self-healing dry-run / apply
python -m ytx fix
python -m ytx fix --apply

# Fast health check or full health check
python -m ytx audit --quick --warn-ok
python -m ytx audit

# Generate markdown only for missing channel folders or one channel
python -m ytx markdown --missing-only
python -m ytx markdown --channel "Chris Williamson"

# Fill caption gaps with Whisper (opt-in)
python -m ytx transcribe --model small

# Export for RAG / embeddings
python -m ytx export jsonl --out exports/transcripts.jsonl

# Diagnose your environment
python -m ytx doctor
```

That's it. No SaaS, no API keys, no vendor lock-in.

## What makes it reliable at scale

YouTube actively fights bulk extraction. Naive scripts break in 10+ ways. This tool was hardened against all of them across 60+ real channels:

| Problem | Fix |
|---|---|
| `/videos` tab only returns 8 recent items | Auto-detect under-20 result count; retry with channel root URL |
| Asha Nayaswami (1,900+ videos) times out at 600s | Adaptive timeout: 600s / 3600s / 7200s / 14400s based on observed channel size |
| Rate limiting after ~2 hours | Cookies-from-browser opt-in (`--cookies-from-browser chrome`) plus rotating UAs, polite sleep intervals, retry-with-backoff |
| PO token / age-gated / region-locked videos | `--extractor-args youtube:player_client=android,web,ios` cascades clients |
| Half-downloaded `.part` orphans | `--ignore-errors --no-abort-on-error`, partial files quarantined to `.trash/` on cleanup |
| Re-runs re-downloading what's already there | Global `--download-archive db/downloaded.txt` makes re-runs O(1) skips |
| Channel-listing folders (`@handle`, `UCxxx`) leaking into `out/` | Auto-quarantined into `_channel_meta/` |
| Caption-less videos (Shorts, music, foreign-lang) | Optional Whisper fallback (`ytx transcribe`) generates `.en.vtt` |
| Mid-flight kills corrupting state | All writes idempotent; canonical.json rebuildable; `.bak` snapshot before destructive ops |
| Whitespace / Unicode drift in folder names | `ytx audit` detects + reports them |

Every one of these came from a real incident. Every fix is documented in `CONVENTIONS.md`.

## Project layout

```
youtube_transcript_exporter/
├── README.md, QUICKSTART.md, INSTALL.md, TROUBLESHOOTING.md
├── CONVENTIONS.md           # The rules. Read before contributing.
├── ytx/                     # Modern Python package (the masterpiece)
│   ├── __main__.py          # CLI: `python -m ytx ...`
│   ├── config.py            # Paths + defaults
│   ├── downloader.py        # yt-dlp wrapper, idempotent
│   ├── transcriber.py       # Whisper fallback (opt-in)
│   ├── metadata...          # canonical.json builder (in src/)
│   ├── audit.py             # alignment / health
│   ├── doctor.py            # env diagnostics
│   └── exporters/           # JSONL / RAG export
├── src/                     # Legacy stable scripts (still supported)
├── tools/                   # One-off maintenance utilities
├── out/                     # Raw downloads: <channel>/<video_id>/*.info.json, *.vtt
├── db/canonical.json        # Single source of truth
├── db/downloaded.txt        # yt-dlp idempotency archive
├── markdown/                # Obsidian-ready vault
├── archive/                 # Historical reports, never read by code
├── tests/smoke_test.sh      # 7-step sanity check
└── export.sh                # Stable shell entrypoint (legacy)
```

## Output: one canonical record per video

Every video lands in `db/canonical.json`:

```json
{
  "id": "BcWXVnZwJjA",
  "title": "...",
  "channel": "Chris Williamson",
  "guest": "Andrew Huberman",
  "date": "20251022",
  "duration": 7200,
  "views": 250000,
  "url": "https://youtu.be/BcWXVnZwJjA",
  "tags": ["focus", "attention", "neuroscience"],
  "category": "Education",
  "description": "...",
  "sources": ["BcWXVnZwJjA"]
}
```

...and a matching markdown file at `markdown/<Channel>/<slug>_<id>.md` with full transcript and YAML frontmatter.

## RAG export

```bash
python -m ytx export jsonl --out exports/transcripts.jsonl
```

Produces one JSON record per line with:
- canonical metadata
- cleaned transcript text (VTT parsed + adjacent-line deduped)
- stable `source_id` for citation back to YouTube

Drop the JSONL into any embedding pipeline (LlamaIndex, LangChain, Vectara, custom).

## Quickstart

```bash
# 1. Clone
git clone https://github.com/dlovecreator-arch/youtube-transcript-exporter.git
cd youtube-transcript-exporter

# 2. Install (Python deps minimal; yt-dlp required; Whisper optional)
pip install -r requirements.txt
brew install yt-dlp ffmpeg     # macOS; or: pipx install yt-dlp

# 3. Sanity check
python -m ytx doctor

# 4. Add your first channel
python -m ytx add https://www.youtube.com/@LexFridman

# 5. See what you've got
python -m ytx audit
```

See [`QUICKSTART.md`](QUICKSTART.md) and [`INSTALL.md`](INSTALL.md) for details.

## Whisper fallback (optional, opt-in)

Some videos have no captions. To fill them:

```bash
pip install faster-whisper
python -m ytx transcribe --model small --limit 50
```

It will scan `out/` for caption-less videos, download audio-only, transcribe locally (no API), and emit `.en.vtt` in the same format yt-dlp uses. The rest of the pipeline is unchanged.

Recommended models:
- `tiny` -- fastest, ok accuracy, good for triage
- `small` -- the sweet spot for podcasts (default)
- `medium` / `large-v3` -- best accuracy if you have GPU

## Cookies (the single biggest reliability win)

```bash
python -m ytx add https://www.youtube.com/@channel --cookies-from-browser chrome
```

This dramatically reduces rate limiting because yt-dlp authenticates as you. Stays local. Other supported browsers: `safari`, `firefox`, `brave`, `edge`, `vivaldi`.

## Common use cases

1. **Personal second brain** -- export to Obsidian, search across all channels you follow
2. **RAG corpus** -- chunk + embed the JSONL, query with any LLM
3. **Research / journalism** -- search across guests, topics, dates
4. **Team enablement** -- turn long-form content into a browseable library

## Documentation

| File | Purpose |
|------|---------|
| [`QUICKSTART.md`](QUICKSTART.md) | 5-minute setup |
| [`INSTALL.md`](INSTALL.md) | Detailed install per OS |
| [`CONVENTIONS.md`](CONVENTIONS.md) | The single source of truth for layout + naming + lessons learned |
| [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) | Solve common problems |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | How to help |
| [`CHANGELOG.md`](CHANGELOG.md) | What changed |
| [`archive/historical_docs/`](archive/historical_docs/) | Older design docs, audit reports, deployment notes |

## License

MIT. Use it, fork it, build on it.

## Built by

[Daniel Love](https://github.com/dlovecreator-arch) -- with painful lessons distilled from 60+ channels and 24,000+ videos extracted.
