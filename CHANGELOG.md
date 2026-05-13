# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] -- 2026-05-13

Major rebuild for production-grade reliability and a "drop-channel-walk-away" UX.

### Added
- New `ytx/` Python package with friendly CLI: `python -m ytx <command>`
  - `ytx add <url|file>`: full pipeline (download + extract + markdown) with cookies/proxy/retry flags
  - `ytx update`: re-runs every URL in `channels.txt` (idempotent via download-archive)
  - `ytx audit`: alignment + caption + media-bloat + .part + whitespace report
  - `ytx doctor`: env check (yt-dlp, ffmpeg, faster-whisper, disk)
  - `ytx transcribe`: opt-in Whisper fallback for caption-less videos
  - `ytx export jsonl`: RAG-friendly export with VTT->plain-text cleaner + adjacent-line dedup
- Resilient downloader (`ytx/downloader.py`):
  - Global `--download-archive db/downloaded.txt` makes re-runs O(1) skips
  - Adaptive timeout: 600s / 3600s / 7200s / 14400s buckets
  - Multi-client extractor `youtube:player_client=android,web,ios` for PO-token resilience
  - Cookies-from-browser opt-in (massive reliability win vs rate limits)
  - Quarantines stray `@handle` / `UCxxx` folders into `_channel_meta/`
  - `/videos` -> root URL auto-fallback (recovers full channel history)
- `tests/smoke_test.sh` 7-step sanity check, runs in <60s
- `logs/ytx.jsonl` structured logging
- `.trash/` quarantine directory (gitignored) for safe destructive ops

### Changed
- README, QUICKSTART, INSTALL, TROUBLESHOOTING fully rewritten around the new CLI
- `requirements.txt` trimmed (stdlib-first, pyyaml the only required dep)
- `src/metadata_extractor.py` uses folder name as canonical channel name (humans curate folders for clean naming) with safe fallback chain
- CI workflow runs ytx smoke test on every PR

### Removed
- Notion exporter -- moved to `archive/historical_docs/` (project now Obsidian-first)
- Stale top-level docs (API.md, DESIGN.md, ARCHITECTURE.md, DEPLOYMENT.md, etc.) moved to `archive/historical_docs/`

### Fixed
- 30 GB of stray `.mp4` files in `out/Next Level Soul Podcast/` quarantined to `.trash/` (default flags now subs+info-json only)
- 10 partial `.part` orphans from killed downloads moved to `.trash/parts/`
- Trailing-space folder names (`THE REAL ISMAEL PEREZ `) normalized
- 626 whitespace fields in `db/canonical.json` stripped
- 11 channels previously in `out/` but missing from DB now ingested (Chris Williamson, Dr Joe Dispenza, Nero Knowledge, Bryan Johnson, Jordan B Peterson, etc.)
- DB videos: 24,146 -> 29,055+; channels: 58 -> 68

## [0.1.0] -- 2026-05-07

Initial public release.

### Added
- Single-command pipeline: `./export.sh --full-pipeline <URL>`
- Canonical JSON database (`db/canonical.json`) as single source of truth
- Obsidian-ready markdown vault with YAML frontmatter (id, title, channel, guest, date, duration, views, tags)
- `CONVENTIONS.md` enforcing one canonical layout
- Folder-layout audit built into `./export.sh --audit`
- Notion exporter (`./export.sh --export-notion`)
- Guest extraction with confidence scores
- Cross-channel duplicate detection
- Support for 8+ channels in production tests
