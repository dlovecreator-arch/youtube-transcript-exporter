# System Architecture

This document describes the design and data flow of youtube-transcript-exporter.

## High-Level Overview

```
YouTube Channel URLs
        ↓
   Download Layer
        ↓
Metadata Extraction Layer
        ↓
   Database Layer (canonical.json)
        ↓
Markdown Generation Layer
        ↓
Output (Markdown + JSON)
```

## Component Breakdown

### 1. Download Layer (`src/download_resilient.py`)

**Purpose**: Fetch transcript caption files and metadata from YouTube

**Key Functions**:
- `download_with_backoff()` -- Resilient HTTP requests with exponential backoff
- `normalize_channel_url()` -- Convert various URL formats to standard form
- `estimate_timeout()` -- Adaptive timeout based on channel size

**Flow**:
1. Accept channel URL
2. Fetch video listings with pagination
3. For each video: Download `.vtt` captions + `.info.json` metadata
4. Store in `out/[CHANNEL_NAME]/[VIDEO_ID]/`

**Error Handling**:
- Rate limit detection: Exponential backoff (2s, 4s, 8s, ... up to 60s)
- Transient failures: Automatic retry (up to `MAX_RETRIES`)
- Missing captions: Graceful skip with logging
- Network timeout: Adaptive based on channel size (300s-7200s)

**Output**:
```
out/
├── 19KEYS_NETWORK/
│   ├── ABC123/
│   │   ├── captions.vtt
│   │   └── info.json
│   └── XYZ789/
│       ├── captions.vtt
│       └── info.json
└── Alignment_of_Light/
    └── ...
```

### 2. Metadata Extraction Layer (`src/metadata_extractor.py`)

**Purpose**: Extract structured metadata from downloaded files

**Key Functions**:
- `extract_guest()` -- Identifies guest names from titles/descriptions
- `extract_topics()` -- Extracts tags and keywords
- `build_canonical_db()` -- Creates unified database entry

**Flow**:
1. Read `info.json` for each video
2. Parse title, description, publish date, view count, likes
3. Apply heuristics to extract guest name
4. Extract topics from tags and title ALL_CAPS words
5. Merge into single canonical entry

**Guest Extraction Heuristics**:
- Pattern: "Title with GUEST_NAME - Speaker Name"
- Pattern: "First line of description if capitalized"
- Fallback: Extract first proper noun from title

**Example Entry** (canonical.json):
```json
{
  "id": "youtube_19keys_network_ABC123",
  "title": "How to Become a Higher Man",
  "url": "https://youtube.com/watch?v=ABC123",
  "channel": "19KEYS_NETWORK",
  "guest": null,
  "published_date": "2021-03-15",
  "duration_seconds": 1834,
  "view_count": 125000,
  "like_count": 3400,
  "topics": ["mindset", "personal development", "spirituality"],
  "captions_available": true,
  "sources": ["https://youtube.com/..."]
}
```

**Output**:
- `db/canonical.json` -- Master database (13K+ entries for 8,300+ videos)

### 3. Database Layer (`db/canonical.json`)

**Purpose**: Single source of truth for all metadata

**Structure**:
- **Index**: By `source_id` (e.g., `youtube_channel_slug_videoid`)
- **Size**: ~16-40 MB for 8,300 videos
- **Immutable**: Only appended to, never overwritten
- **Deduplicated**: Same video in multiple channels tracked with `sources` list

**Key Fields**:
| Field | Type | Example |
|-------|------|---------|
| `id` | string | `youtube_19keys_network_ABC123` |
| `title` | string | `How to Become a Higher Man` |
| `url` | string | `https://youtube.com/watch?v=...` |
| `channel` | string | `19KEYS_NETWORK` |
| `guest` | string \| null | `Jordan Peterson` |
| `published_date` | ISO 8601 | `2021-03-15` |
| `duration_seconds` | int | `1834` |
| `view_count` | int | `125000` |
| `topics` | array | `["mindset", "personal growth"]` |
| `captions_available` | bool | `true` |
| `transcript_path` | string | `out/19KEYS_NETWORK/ABC123/captions.vtt` |

**Durability**:
- Incrementally built (safe to interrupt and resume)
- Whitespace-normalized for consistency
- Validated by audit tools

### 4. Markdown Generation Layer (`src/markdown_generator.py`)

**Purpose**: Convert database entries + transcripts into readable markdown files

**Key Functions**:
- `clean_vtt_text()` -- Remove VTT timestamps, deduplicate overlapping lines
- `generate_markdown()` -- Create YAML frontmatter + transcript body
- `process_all_transcripts()` -- Batch process all videos

**Flow**:
1. For each database entry, check if markdown exists
2. If not: read `.vtt` caption file
3. Clean transcript (remove timing codes, deduplicate)
4. Create YAML frontmatter with metadata
5. Write to `markdown/[CHANNEL]/[title]_[videoid].md`

**Output Format**:
```markdown
---
id: youtube_19keys_network_ABC123
title: "How to Become a Higher Man"
channel: "19KEYS_NETWORK"
guest: null
url: "https://youtube.com/watch?v=ABC123"
published_date: "2021-03-15"
duration: "30:34"
topics: ["mindset", "personal development"]
views: 125000
likes: 3400
---

This is the cleaned transcript text starting here...
```

**Performance**:
- Incremental: Skips already-generated files
- Parallel: Can batch-process multiple channels
- Efficient: One pass through database

**Output**:
```
markdown/
├── 19KEYS_NETWORK/
│   ├── How_to_Become_a_Higher_Man_[ABC123].md
│   └── ...
└── Alignment_of_Light/
    └── ...
```

### 5. Export Layer (`src/notion_exporter.py`, `src/obsidian_formatter.py`)

**Purpose**: Export data to external systems (optional)

**Notion Export**:
- Requires `NOTION_TOKEN` and `NOTION_DATABASE_ID`
- Creates database row per video
- Syncs metadata + truncated transcript (~2K chars)

**Obsidian Export**:
- Creates index files for navigation
- Maintains folder structure for discovery
- Supports Obsidian dataview queries

## Data Flow Diagram

```
Download Layer
├── normalize_channel_url()
├── download_with_backoff()
└── → out/[CHANNEL]/[VIDEO_ID]/{captions.vtt, info.json}
        ↓
Metadata Extraction
├── parse info.json
├── extract_guest()
├── extract_topics()
└── → db/canonical.json (incremental)
        ↓
Markdown Generation
├── clean_vtt_text()
├── create YAML frontmatter
└── → markdown/[CHANNEL]/[TITLE]_[ID].md
        ↓
Export (Optional)
├── Notion API
└── Obsidian vault
```

## Key Design Decisions

### 1. Single Canonical Database
**Why**: Prevents data inconsistency, enables deduplication, provides audit trail

**Trade-off**: Must keep in sync with file system

**Mitigation**: Audit tools detect and fix inconsistencies

### 2. Separate `out/` and `markdown/` Directories
**Why**: 
- `out/` = raw, unprocessed (backup source)
- `markdown/` = processed, human-readable (for Obsidian/Notion)

**Benefit**: Can regenerate markdown without re-downloading

### 3. Incremental Processing
**Why**: Allows resumable downloads, partial channel updates

**How**: Check `id` in canonical.json before processing

### 4. VTT Caption Cleaning
**Why**: YouTube captions overlap and repeat for timing precision

**Solution**: Deduplication logic removes redundant lines

### 5. Guest Extraction Heuristics
**Why**: YouTube doesn't expose guest data; must infer from text

**Challenge**: False positives (e.g., "AMAZING Interview" → guest="Amazing")

**Mitigation**: Confidence scores, manual review for important videos

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Download 100 videos | 5-10 min | Sequential, rate-limited |
| Parallel 4 channels | 30-60 min | 1000s videos total |
| Process metadata | 1-2 min | CPU-bound |
| Generate markdown | 2-5 min | I/O-bound |
| Audit 8,300 videos | 30-60 sec | Scan mode |

## Extension Points

### Adding Custom Guest Detection
Edit `src/metadata_extractor.py`:
```python
GUEST_PATTERNS = [
    r"(?:with|feat\.?|featuring)\s+([A-Z][a-z\s]+)",
    r"^([A-Z][a-z\s]+)(?:\s*[-:])",
]
```

### Adding Custom Topics
Extend `extract_topics()`:
```python
def extract_topics(title, tags, description):
    # Your custom logic here
    return topics
```

### Adding Custom Export Format
Create `src/custom_exporter.py`:
```python
def export_to_markdown_extended(entries):
    # Custom format with additional fields
    pass
```

## Testing & Validation

See [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md) for:
- Unit test coverage
- Integration tests
- Audit procedures
- Production validation checklist
