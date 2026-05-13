"""ytx -- YouTube to second-brain pipeline.

A best-in-class, idempotent, resumable YouTube channel exporter that
turns YouTube channels into a clean, RAG-ready Markdown + JSON dataset.

Modules:
  config       -- repo paths, defaults
  downloader   -- resilient yt-dlp wrapper (cookies, archive, adaptive)
  transcriber  -- Whisper fallback for caption-less videos (opt-in)
  metadata     -- extract canonical.json from .info.json
  markdown     -- generate Obsidian-ready markdown
  exporters    -- JSONL/RAG export, Obsidian helpers
  audit        -- health / alignment / orphan reports
  cli          -- argparse entrypoint, used as `python -m ytx ...`
"""

__version__ = "1.0.0"
