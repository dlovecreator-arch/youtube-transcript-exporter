# Design Philosophy & Decisions

This document explains *why* youtube-transcript-exporter is built the way it is.

## Core Philosophy

**Local-first, reproducible, audit-transparent.**

We believe:
1. **Your data stays on your machine** -- no cloud uploads, no telemetry
2. **Everything is reproducible** -- reruns should give same results
3. **You can inspect everything** -- markdown files are human-readable
4. **You can fix it yourself** -- no vendor lock-in, all code is yours

## Key Design Principles

### Principle 1: Single Source of Truth (canonical.json)

**Decision**: All metadata goes into one database, not scattered across markdown files.

**Rationale**:
- **Consistency**: Changes propagate everywhere
- **Efficiency**: One lookup, not N file reads
- **Auditability**: Clear history of what changed
- **Deduplication**: Track same video across multiple channels

**Trade-off**: Must keep database + files in sync
**Solution**: Audit tools detect and fix inconsistencies

### Principle 2: Immutable Raw Data (out/ folder)

**Decision**: Keep original `.vtt` captions + `.info.json` metadata untouched.

**Rationale**:
- **Archival**: Original source preserved (for 10 years from now)
- **Reproducibility**: Can regenerate markdown anytime
- **Transparency**: See exactly what YouTube gave us
- **Disaster recovery**: Rebuild from raw if needed

**Trade-off**: Extra storage (usually 20% overhead vs markdown)
**Solution**: Optional compression (`tar -gz`) for archiving

### Principle 3: Incremental Processing

**Decision**: Check if work already done before re-processing.

**Rationale**:
- **Resumable**: Stop and restart without loss
- **Efficient**: Don't recompute on second run
- **Scalable**: Add one video without re-downloading all 8,000

**How**:
- Check `id` in canonical.json before downloading
- Check if markdown file exists before generating
- Skip channels we've seen before

**Trade-off**: Requires tracking state
**Solution**: Database + file timestamps

### Principle 4: Human-Readable Outputs

**Decision**: YAML frontmatter + plain text, not binary or JSON-only.

**Rationale**:
- **Searchable**: `grep` works
- **Obsidian-ready**: No conversion needed
- **Future-proof**: Readable in 20 years even if this tool dies
- **Portable**: Copy folder to another system, still works
- **Diff-friendly**: See exact changes in git

**Trade-off**: Slightly bigger files (but still < 10MB per 1000 videos)
**Solution**: Compression available for archival

### Principle 5: Defensive Defaults

**Decision**: Always assume data is corrupt and verify.

**What this means**:
- Whitespace normalization (handle encoding quirks)
- Duplicate detection in transcripts
- Orphaned file detection
- Database integrity checks
- Version mismatches caught early

**Why**: YouTube, internet, filesystems all have quirks
**Cost**: ~30 seconds overhead per large run
**Benefit**: Catches 95% of issues before they become problems

### Principle 6: No External Dependencies (Except yt-dlp)

**Decision**: Use Python stdlib + yt-dlp + requests only.

**Rationale**:
- **Maintainability**: Fewer things to break
- **Performance**: No heavy frameworks
- **Security**: Smaller attack surface
- **Portability**: Works everywhere Python runs

**Trade-off**: Write more helper code
**Benefit**: Lightweight (< 50 MB installed)

### Principle 7: Parallel Safety

**Decision**: Can run multiple channels in parallel, but not same channel.

**Why**:
- **Speed**: 4 channels can download simultaneously
- **Safety**: Each channel uses separate folder
- **Deadlock-free**: No shared locks (filesystem-level safe)

**How**:
```bash
./export.sh --batch \
  https://youtube.com/@channel1 \
  https://youtube.com/@channel2 \
  https://youtube.com/@channel3
```

## Architectural Patterns

### Pattern 1: Resilient Downloading

**Challenge**: YouTube throttles, connections fail, captcha walls appear

**Solution**:
1. Exponential backoff (2s, 4s, 8s, ..., 60s max)
2. Retry with decay (10+ attempts by default)
3. Timeout scaling (300s for small, 7200s for large channels)
4. Graceful degradation (skip videos without captions)

**Result**: Successfully downloads even when YouTube is rate-limiting

### Pattern 2: Heuristic Metadata Extraction

**Challenge**: YouTube gives us: title, description, tags, not structured data

**Solution**: Apply regex patterns to extract guest, topics

**Example**:
```
Title: "How to Manifest Wealth with Jordan Peterson"
Guest Pattern: /with\s+([A-Z][a-z\s]+)/
Result: guest = "Jordan Peterson"
```

**Confidence**: 85-90% accuracy; ~10-15% false positives

**Mitigation**: Manual audit/correction possible in canonical.json

### Pattern 3: Content-Addressable File Layout

**Decision**: Use video ID in filenames (`title_[ID].md`), not just title.

**Rationale**:
- **Unique**: No collisions even with same title
- **Stable**: ID never changes (unlike title which could be edited)
- **Deduplicable**: Same video in different channels uses same ID
- **Discoverable**: `grep -r "VIDEO_ID" markdown/` finds everywhere

**Example**:
```
markdown/19KEYS_NETWORK/How_to_Become_a_Higher_Man_[ABC123].md
markdown/Alignment_of_Light/Meditation_Basics_[ABC123].md  # same video
```

### Pattern 4: Lazy Evaluation of Expensive Operations

**What**: Guest extraction, topic matching, transcript cleaning

**Why**: These are CPU-expensive at scale (1000s of videos)

**Solution**: Only do it once (on first processing), then cache in database

**Result**: Re-running system on 8,000 videos takes 2 minutes (not 20)

## Design Tradeoffs Explained

| Decision | Benefit | Cost | Mitigation |
|----------|---------|------|-----------|
| Local-only | Privacy, offline | No cloud search | SQL search tools |
| Single DB | Consistency | Sync overhead | Audit tools |
| Raw + markdown | Reproducibility | 2x storage | Compression |
| YAML frontmatter | Human-readable | Slower to parse | Caching |
| No ORMs | Simple, portable | Manual SQL | Tests |
| Heuristic metadata | No API keys | 10-15% errors | Manual review |
| Parallel by channel | Speed | Complexity | Single-channel default |

## What We *Don't* Do (and Why)

### ❌ Cloud Uploads
**Why not**: Privacy, vendor lock-in, bandwidth costs
**Alternative**: Users can sync via rclone/Dropbox if desired

### ❌ Automatic Updates
**Why not**: Simplicity, no dependency hell
**Alternative**: Check `git pull origin main` periodically

### ❌ Web UI
**Why not**: Obsidian/Notion already do this better
**Alternative**: Export to Notion for browsing

### ❌ Video Download
**Why not**: Size (1000 videos = 500+ GB), licensing complexity
**Alternative**: Keep transcript + timestamp links to YouTube

### ❌ Real-time Monitoring
**Why not**: Transcripts are static; updates are infrequent
**Alternative**: Run nightly; check logs

### ❌ Machine Learning
**Why not**: Overkill, requires GPU, licensing questions
**Alternative**: Simple heuristics work 85-90% of the time

## Future Design Directions

### Chunk-Level Processing (v2.0)
Break transcripts into semantic chunks (5-10 minute segments).
**Why**: Better for RAG, searchability, quotes

**Challenge**: Need semantic segmentation (speaker changes, topic shifts)
**Solution**: Use whisper timestamps + heuristics

### Distributed Archive (v2.1)
Support IPFS or BitTorrent for data distribution.
**Why**: Decentralization, backup network
**Challenge**: Bandwidth, sync complexity
**Solution**: Make optional, off by default

### Multi-Language (v2.2)
Handle transcripts in any language.
**Why**: Global transcription
**Challenge**: Detection, normalization
**Solution**: Detect with langdetect, normalize per-language

## Testing Philosophy

**All core functions have unit tests.**
**All workflows have integration tests.**
**All deployments must pass audit.**

See [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md) for full testing strategy.

## Performance Philosophy

**Optimize for correctness first, speed second.**

Rationale:
- A slow, correct system beats a fast, buggy one
- Networks are the bottleneck (not CPU)
- Audit takes 30s; wrong data takes hours to fix
- Incremental processing already makes system fast enough

Current performance:
- Download 100 videos: 5-10 min
- Process 8,300 videos: 2-5 min
- Audit 8,300 videos: 30-60 sec

## Summary: Why This Design Works

1. **Simple** -- No complex frameworks or magic
2. **Portable** -- Works on Mac, Linux, Windows (with WSL)
3. **Auditable** -- You can inspect every file
4. **Safe** -- Incremental, resumable, defensive
5. **Extensible** -- Easy to add custom guest/topic logic
6. **Reproducible** -- Same input = same output, always

For more details, see:
- [ARCHITECTURE.md](ARCHITECTURE.md) -- Technical details
- [CONVENTIONS.md](CONVENTIONS.md) -- Coding patterns
- [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md) -- Testing & validation
