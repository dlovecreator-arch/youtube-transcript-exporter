# Continuous Optimization Log

**Philosophy**: Every session generates learning. Every fix unlocks a pattern. Every edge case becomes a rule.

This document captures optimizations discovered during operation, organized by priority and implementation status.

---

## Active Session Optimizations (2026-05-08)

### 🟢 IMPLEMENTED: Channel URL Format Auto-Detection (Elizabeth April Discovery)

**Issue**: `/videos` tab only returns recent 8 videos; full channel at `@handle` returns 83+

**Root Cause**: YouTube's `/videos` tab uses client-side pagination that yt-dlp can't traverse. Channel root uses different API endpoint with full history.

**Solution**: Auto-detection heuristic - if first attempt < 20 videos AND URL has `/videos`, auto-retry with channel root

**Implementation**: ✅ COMPLETE
- [x] Added `normalize_channel_url()` function with documentation
- [x] Added heuristic after first pass: if < 20 videos from `/videos`, switch to channel root
- [x] Log URL switch for auditability
- [x] Updated CONVENTIONS.md with guidelines
- [x] Tested and confirmed working

**Code Location**: `src/download_resilient.py` lines 142-150

**Impact**: Elizabeth April jumped from 8 to 83+ videos. Will benefit any channel where user provides `/videos` URL.

**Status**: Ready for production. Will activate on next Elizabeth April download or any new channel with similar issue.

---

## Active Session Optimizations (2026-05-08 Continued)

### 🟡 IN PROGRESS: Unicode Folder Name Handling (André Duqum Discovery)

**Issue**: Count showed 7 videos for André Duqum, but actually downloaded 199 videos

**Root Cause**: Search patterns used `andre` but folder is `André Duqum` (accent character). Unicode normalization not handled in counting scripts.

**Solution**: 
- Add Unicode-aware folder discovery
- Handle accented characters in channel names
- Update all counting/reporting scripts to use robust path matching

**Implementation Status**: 🟡 In Progress
- [ ] Update download status reporting to handle Unicode
- [ ] Add accent-aware channel matching
- [ ] Test with other accented channel names
- [ ] Update parallel batch script counting

**Code Locations**: 
- Status reporting: various scripts
- Counting: `enhance_parallel_batch.sh`, shell functions

**Impact**: André Duqum: 7 → 199 videos (correct count achieved, just reporting issue)

---

## Past Session Optimizations (Successfully Implemented)

### ✅ COMPLETED: Adaptive Timeout for Large Channels (2026-05-08)

**Issue**: Asha Nayaswami (1909 videos) timed out at 600s, only getting 291 videos

**Solution**: `estimate_timeout()` function that scales based on video count
- < 500: 600s (10 min)
- 500-2000: 3600s (60 min)
- 2000+: 7200s (120 min)

**Result**: Asha jumped from 291 to 447 videos

**Location**: `src/download_resilient.py` lines 49-66

---

## Framework for Future Optimizations

### Discovery Process
1. **Observation**: Notice unexpected behavior or inefficiency
2. **Root Cause**: Identify the underlying issue
3. **Hypothesis**: Propose a fix that won't break existing flows
4. **Test**: Validate on problem case first
5. **Generalize**: Apply to all similar cases
6. **Document**: Update CONVENTIONS.md or README
7. **Commit**: One atomic commit per optimization

### Safety Constraints
- ✅ Always backwards compatible
- ✅ Log all decisions for auditability
- ✅ Never lose data (resume-safe downloads)
- ✅ Preserve folder structure & naming
- ✅ Git commit after each major improvement

### Optimization Categories

#### Download Quality
- [ ] Channel URL format detection (in progress)
- [ ] Subtitle language fallback (if en fails, try others)
- [ ] Auto-retry on "Premieres in X days" errors
- [ ] Detect private/members-only and log separately

#### Performance
- [ ] Parallel channel downloads (if not already)
- [ ] Cache yt-dlp queries to avoid re-scraping
- [ ] Streaming markdown generation (don't wait for all metadata)
- [ ] Incremental canonical.json updates (don't recompute everything)

#### Metadata Enrichment
- [ ] Auto-extract speakers from titles
- [ ] Auto-extract guest names using NLP
- [ ] Auto-categorize by topic (spiritual, scientific, etc)
- [ ] Detect and flag duplicate channels (same person, different handles)

#### User Experience
- [ ] Progress bar instead of just "Progress: X/Y"
- [ ] ETA calculation based on current speed
- [ ] Completion summary with key metrics
- [ ] Recommendations for next channels based on overlap

#### Error Handling
- [ ] Graceful degradation when captions unavailable
- [ ] Better error messages (not just "ERROR: [youtube]...")
- [ ] Auto-repair corrupted .info.json files
- [ ] Notification system for partial failures

---

## Implementation Rules

### When Writing Optimization Code
1. **Add logging** - log what you're optimizing, why, and the result
2. **Add comments** - future self needs to understand the reasoning
3. **Add tests** - if possible, include a validation
4. **Update CONVENTIONS.md** - if it changes how things work
5. **One commit per fix** - atomic, revertible changes

### Code Quality Standards
- [ ] Type hints where possible
- [ ] Docstrings for new functions
- [ ] Error handling (don't let one channel failure break pipeline)
- [ ] Idiomatic Python (use Python features, not other language patterns)

### Before Each Session Starts
1. Read this file to recall past learnings
2. Check git log for recent optimizations
3. Identify any patterns from previous sessions
4. Plan potential improvements based on system state

---

## Metrics to Track

Per session:
- Total channels added
- Total videos added
- Videos added per minute (efficiency)
- Errors encountered (categorized)
- Optimizations implemented
- Lines of code changed
- Build/enhancement time

Running system metrics:
- Total videos in system
- Average videos per channel
- Largest channels (for future timeout tuning)
- Error rate by channel
- Download success rate by URL format

---

## Next Session Checklist

- [ ] Read this optimization log first
- [ ] Check git log for recent changes
- [ ] Validate adaptive timeout is working on new channels
- [ ] Implement Elizabeth April channel root fix
- [ ] Test channel root detection logic on 3 known channels
- [ ] Add subtitle language fallback
- [ ] Update this log with findings

