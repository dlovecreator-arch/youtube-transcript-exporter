# API Documentation

## Overview

This document describes the programmatic interfaces for the YouTube Transcript Exporter. All major components can be used as libraries in Python scripts.

## Core Modules

### 1. Download Module (`src/download_resilient.py`)

Download and process YouTube transcripts with automatic retry logic.

#### Usage

```python
from src.download_resilient import ResientDownloader

downloader = ResilientDownloader(
    max_retries=3,
    timeout=300,
    workers=4
)

# Download from channel
videos = downloader.download_channel(
    channel_url="https://www.youtube.com/c/ChannelName",
    force_refresh=False
)

# Download specific video
transcript = downloader.download_video(
    video_id="dQw4w9WgXcQ",
    include_metadata=True
)
```

#### Returns

```python
{
    "video_id": "dQw4w9WgXcQ",
    "title": "Video Title",
    "transcript": "Full transcript text...",
    "metadata": {
        "duration": 300,
        "upload_date": "2024-01-01",
        "views": 1000000
    },
    "status": "success"
}
```

### 2. Markdown Generator (`src/markdown_generator.py`)

Convert transcripts to markdown format with metadata.

#### Usage

```python
from src.markdown_generator import MarkdownGenerator

generator = MarkdownGenerator(
    include_timestamps=True,
    include_metadata=True
)

# Generate markdown for video
markdown = generator.generate(
    video_data={
        "title": "Video Title",
        "transcript": "...",
        "metadata": {...}
    }
)

# Generate markdown vault (all videos)
generator.generate_vault(
    output_dir="markdown",
    db_path="db/canonical.json"
)
```

#### Output

```markdown
# Video Title

**Duration**: 5m 30s  
**Channel**: Channel Name  
**Upload Date**: 2024-01-01  
**Views**: 1,000,000  

## Transcript

[00:00:00] - Introduction...
[00:00:30] - Main content...
```

### 3. Metadata Extractor (`src/metadata_extractor.py`)

Extract and normalize video metadata.

#### Usage

```python
from src.metadata_extractor import MetadataExtractor

extractor = MetadataExtractor()

# Extract from raw data
metadata = extractor.extract(raw_response)

# Normalize metadata
normalized = extractor.normalize(metadata)
```

### 4. RAG Schema Enhancement (`src/enhance_rag_schema.py`)

Enhance database with RAG (Retrieval-Augmented Generation) metadata.

#### Usage

```python
from src.enhance_rag_schema import RAGEnhancer

enhancer = RAGEnhancer(
    db_path="db/canonical.json",
    chunk_size=500,
    overlap=50
)

# Enhance existing database
enhancer.enhance_all()

# Add RAG metadata to video
enhancer.enhance_video(video_id="dQw4w9WgXcQ")
```

### 5. Obsidian Formatter (`src/obsidian_formatter.py`)

Format transcripts for Obsidian vault integration.

#### Usage

```python
from src.obsidian_formatter import ObsidianFormatter

formatter = ObsidianFormatter(
    vault_dir="obsidian_vault",
    create_backlinks=True
)

# Format single video
formatter.format_video(video_data)

# Format entire vault
formatter.format_vault(db_path="db/canonical.json")
```

### 6. Notion Exporter (`src/notion_exporter.py`)

Export transcripts to Notion database.

#### Usage

```python
from src.notion_exporter import NotionExporter

exporter = NotionExporter(
    notion_token="YOUR_TOKEN",
    database_id="YOUR_DATABASE_ID"
)

# Export video
exporter.export_video(video_data)

# Batch export
exporter.export_batch(db_path="db/canonical.json")
```

## Database Schema

### Canonical Database (`db/canonical.json`)

```json
{
  "videos": [
    {
      "video_id": "dQw4w9WgXcQ",
      "title": "Video Title",
      "channel": "Channel Name",
      "channel_id": "UCxxxxxx",
      "transcript": "Full text...",
      "duration": 330,
      "upload_date": "2024-01-01",
      "views": 1000000,
      "description": "Video description...",
      "thumbnail": "https://...",
      "rag_metadata": {
        "chunks": ["chunk1", "chunk2"],
        "embeddings": [...],
        "summary": "..."
      },
      "markdown_generated": true,
      "obsidian_formatted": false,
      "notion_exported": false,
      "last_updated": "2024-01-15T10:30:00Z"
    }
  ],
  "metadata": {
    "total_videos": 1,
    "total_channels": 1,
    "last_sync": "2024-01-15T10:30:00Z",
    "version": "1.0"
  }
}
```

## Command-Line Interfaces

### export.sh

```bash
./export.sh [OPTIONS]

Options:
  --markdown    Export to markdown vault
  --notion      Export to Notion database
  --obsidian    Export to Obsidian vault
  --audit       Run system audit
  --force       Force re-generation of existing exports
  --channel     CHANNEL_NAME - Export specific channel only
  --help        Show help message
```

### download_parallel.sh

```bash
./download_parallel.sh [CHANNEL_URL] [OPTIONS]

Options:
  --force       Force re-download
  --workers     NUMBER - Number of parallel workers (default: 4)
  --timeout     SECONDS - Download timeout (default: 300)
  --help        Show help message
```

## Health Checks & Monitoring

### System Health Check

```bash
python3 system_health_check.py
```

Returns:
- Database integrity status
- Download coverage
- Export completion rates
- File system alignment
- Data quality metrics

## Error Handling

All modules follow consistent error handling:

```python
try:
    result = downloader.download_video(video_id)
except TimeoutError:
    # Handle timeout
    print("Download timed out, retrying...")
except Exception as e:
    # Handle other errors
    print(f"Error: {e}")
```

## Configuration

### Environment Variables

```bash
export YOUTUBE_API_KEY=your_key
export NOTION_TOKEN=your_token
export OUTPUT_DIR=out
export DB_PATH=db/canonical.json
```

### Configuration File

Create `config.json`:

```json
{
  "youtube_api_key": "YOUR_KEY",
  "notion_token": "YOUR_TOKEN",
  "max_workers": 4,
  "download_timeout": 300,
  "retry_attempts": 3,
  "retry_delay": 5,
  "output_dir": "out",
  "markdown_dir": "markdown",
  "db_path": "db/canonical.json"
}
```

## Examples

### Example 1: Download and Convert to Markdown

```python
import json
from src.download_resilient import ResilientDownloader
from src.markdown_generator import MarkdownGenerator

# Download
downloader = ResilientDownloader()
videos = downloader.download_channel("https://www.youtube.com/c/TestChannel")

# Generate markdown
generator = MarkdownGenerator()
for video in videos:
    markdown = generator.generate(video)
    print(markdown)
```

### Example 2: RAG-Enhanced Search

```python
import json
from src.enhance_rag_schema import RAGEnhancer

# Load database
with open("db/canonical.json") as f:
    db = json.load(f)

# Search with RAG
enhancer = RAGEnhancer()
results = enhancer.search("specific topic", top_k=5)

for result in results:
    print(f"Video: {result['title']}")
    print(f"Relevance: {result['score']}")
    print(f"Chunk: {result['text'][:200]}...")
```

### Example 3: Batch Export

```python
from src.notion_exporter import NotionExporter
import json

exporter = NotionExporter(
    notion_token="YOUR_TOKEN",
    database_id="YOUR_DB_ID"
)

# Export all videos
with open("db/canonical.json") as f:
    db = json.load(f)

for video in db["videos"]:
    exporter.export_video(video)
```

## Testing

Run the test suite:

```bash
python3 -m pytest tests/
```

## Versioning

This project follows Semantic Versioning (MAJOR.MINOR.PATCH).

Current version: Check `package_version.txt` or git tags.

## Support

For issues, questions, or feature requests:

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Search existing [GitHub Issues](https://github.com/your-repo/issues)
3. Create a new issue with:
   - Detailed description
   - Steps to reproduce
   - Output of `system_health_check.py`
   - Relevant logs
