# RAG and Obsidian Workflows

This project is designed to support two related second-brain workflows:

1. **Human browsing in Obsidian** using the generated markdown vault.
2. **Machine retrieval / RAG** using timestamped JSONL chunks.

## Obsidian dashboard notes

Generate vault-level index notes without rewriting transcript notes:

```bash
python3 -m ytx obsidian
```

This writes:

- `markdown/_dashboard.md`
- `markdown/_channels.md`
- `markdown/_guests.md`
- `markdown/_topics.md`
- `markdown/_years.md`
- `markdown/_missing_markdown.md`

Use `--out` to test or generate into another vault:

```bash
python3 -m ytx obsidian --out /path/to/ObsidianVault
```

## RAG chunk export

For embeddings, use timestamped chunks rather than one giant transcript per video:

```bash
python3 -m ytx export chunks --out exports/chunks.jsonl
```

Each JSONL row includes:

- stable video metadata: title, channel, date, tags, guest, URL
- `chunk_id` and `chunk_index`
- `start_seconds` and `end_seconds`
- `url_at_timestamp` for direct citation back to YouTube
- `text`
- approximate `token_count`
- `transcript_source`

Useful variants:

```bash
# sample a few records for inspection
python3 -m ytx export chunks --max-videos 10 --out exports/sample_chunks.jsonl

# export only a channel
python3 -m ytx export chunks --channel "Chris Williamson" --out exports/chris_chunks.jsonl

# tune chunk size and overlap
python3 -m ytx export chunks --chunk-tokens 600 --overlap-tokens 80 --out exports/chunks_600.jsonl
```

## Video-level JSONL export

For archive or metadata use:

```bash
python3 -m ytx export jsonl --out exports/videos.jsonl
```

This can include whole transcript text when available. For embeddings, `export chunks` is usually better.

## Run reports

Create a timestamped maintenance report:

```bash
python3 -m ytx report
```

Reports go to `logs/runs/` by default and include status, quick audit, doctor output, git commit, and recommended safe next steps. Use `--out` to write a specific path.

## Whisper fallback

Whisper is opt-in for videos without usable YouTube captions:

```bash
# optional dependencies
brew install ffmpeg
pip install faster-whisper

# then transcribe a small batch first
python3 -m ytx transcribe --limit 5 --model small
```

The project intentionally treats Whisper dependencies as optional. `python3 -m ytx doctor` will warn if they are missing but still passes when the required downloader environment is healthy.

## Recommended maintenance cadence

```bash
python3 -m ytx status
python3 -m ytx audit --quick --warn-ok
python3 -m ytx fix              # dry-run only
python3 -m ytx report
```

Only run downloads when you actually want new data:

```bash
python3 -m ytx update
```

Then rebuild derived artifacts as needed:

```bash
python3 -m ytx metadata
python3 -m ytx markdown --missing-only
python3 -m ytx export chunks --out exports/chunks.jsonl
python3 -m ytx obsidian
```
