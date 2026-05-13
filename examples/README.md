# Examples

Small, self-contained worked examples to show the pipeline working end-to-end.

## Tiny channel: Rick Astley

A 1-video test for fastest sanity-check:

```bash
python3 -m ytx add "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
python3 -m ytx audit
ls markdown/
```

Expected: one folder, one .md file with YAML frontmatter and a transcript.

## Full channel: Lex Fridman

A medium-sized channel (~500 videos, lots of captions):

```bash
python3 -m ytx add https://www.youtube.com/@LexFridman --cookies-from-browser chrome
python3 -m ytx audit
python3 -m ytx export jsonl --out exports/lex.jsonl --channel "Lex Fridman"
```

Expected: ~500 .md files, ~95%+ caption coverage, one jsonl with 500 records.

## Whisper fallback for a caption-less channel

For music or Shorts-heavy channels:

```bash
pip install faster-whisper
python3 -m ytx add https://www.youtube.com/@SomeMusicChannel
python3 -m ytx transcribe --model small
python3 -m ytx markdown
```

Expected: the videos that had no .vtt now have one, generated locally by Whisper.

## RAG pipeline starter

```bash
python3 -m ytx export jsonl --out exports/full.jsonl

# 100 records to peek
head -100 exports/full.jsonl > exports/preview.jsonl

# embed with your favorite tool, e.g. llamaindex/langchain
python3 -c "
import json
for line in open('exports/full.jsonl'):
    rec = json.loads(line)
    print(rec['source_id'], len(rec.get('transcript') or ''))
" | head
```

The `source_id` field is stable across re-runs and traces back to YouTube via `url`.

## Verify your install

```bash
bash tests/smoke_test.sh
```

7 steps, < 60s, fully offline-friendly.
