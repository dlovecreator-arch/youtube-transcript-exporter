# Masterpiece Plan -- One-Shot YouTube to Second Brain

**Goal**: Drop in a channel URL, get a perfect, RAG-ready local dataset. Forever.

## Phases

### Phase 0 -- Safety net (no destruction)
- [ ] Snapshot DB + create `.trash/` for any moves
- [ ] Commit current state so we have a rollback

### Phase 1 -- Audit + reality check
- [ ] Run system_health_check, audit_tool, validate_alignment, capture deltas
- [ ] List orphan info.json files (in out/ but not in DB)
- [ ] Identify the 172 .mp4 files (should not exist) and the 10 .part files
- [ ] Identify caption-less videos (no .vtt) per channel
- [ ] Output: AUDIT_2026-05-13.md

### Phase 2 -- Cleanup
- [ ] Quarantine .mp4 files to `.trash/videos/` (then user can delete)
- [ ] Remove .part orphans
- [ ] Resolve remaining naming drift / orphan folders
- [ ] Drop Notion exporter (user moved to Obsidian)

### Phase 3 -- Pipeline hardening (the masterpiece)
- [ ] New `src/downloader.py`: best-in-class yt-dlp wrapper
  - cookies-from-browser (opt-in)
  - download-archive (idempotent, fast re-runs)
  - --extractor-args "youtube:player_client=android,web" (PO token resilience)
  - --sleep-requests, --sleep-interval, --max-sleep-interval
  - --retries 10, --fragment-retries 10, --file-access-retries 5
  - --ignore-errors --no-abort-on-error
  - subtitles only (no media) by default: --skip-download --write-info-json --write-subs --write-auto-subs --sub-langs "en.*"
  - adaptive timeout based on channel size
  - /videos -> root auto-fallback (already exists, refine)
  - playlist-end checkpoint for resume
  - structured JSONL log per channel
- [ ] New `src/transcriber.py`: Whisper fallback (opt-in --whisper)
  - Detect videos with no .vtt and no auto-subs
  - Download audio-only (m4a), transcribe with faster-whisper, delete audio
  - Emit .en.vtt + transcript.en.txt in identical format
- [ ] Unify `src/metadata_extractor.py` + `src/markdown_generator.py` behind one CLI
- [ ] Add `src/exporters/jsonl.py` for RAG embedding pipelines
- [ ] Add `src/exporters/obsidian.py` (verify wikilinks, dataview-friendly frontmatter)

### Phase 4 -- One command UX
- [ ] `ytx add <url|file>` -- full pipeline, resumable, idempotent
- [ ] `ytx update` -- check all channels for new videos
- [ ] `ytx audit` -- health report
- [ ] `ytx export obsidian|jsonl` -- second-brain exports
- [ ] `ytx doctor` -- diagnose env (yt-dlp version, ffmpeg, whisper, cookies)

### Phase 5 -- Docs consolidation
- [ ] One canonical `README.md` (rewrite the top)
- [ ] One `docs/USAGE.md`, one `docs/ARCHITECTURE.md`, one `docs/TROUBLESHOOTING.md`
- [ ] Archive every stale doc to `archive/reports/`
- [ ] CONVENTIONS.md kept and updated

### Phase 6 -- Self-validation
- [ ] `tests/smoke_test.sh` -- 1 small channel, end-to-end, < 2 min
- [ ] GitHub Actions: smoke test on PR
- [ ] Pre-commit hooks (ruff, mypy-lite)

### Phase 7 -- Repo polish for public use
- [ ] Banner + screenshots updated
- [ ] Examples folder with one fully exported small channel
- [ ] CONTRIBUTING + CHANGELOG + SECURITY current
- [ ] Push 40+ pending commits to origin

## Done means
- I can run `ytx add https://youtube.com/@channel` and walk away.
- It downloads, falls back to Whisper if needed, deduplicates, generates Obsidian markdown, audits, and commits.
- Anyone else can clone the repo and have it working in 5 minutes.
- The README explains why this is the best YouTube to second-brain tool that exists.
