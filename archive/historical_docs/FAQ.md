# Frequently Asked Questions

## Getting Started

### Q: How do I install youtube-transcript-exporter?
**A:** Follow the [INSTALL.md](INSTALL.md) guide. TL;DR:
```bash
git clone https://github.com/1jehuang/youtube_transcript_exporter.git
cd youtube_transcript_exporter
pip install -r requirements.txt
./export.sh --help
```

### Q: Do I need API keys?
**A:** No! The system uses public YouTube captions (no authentication required). Optional: Notion API token if you want to export to Notion.

### Q: What Python version do I need?
**A:** Python 3.8 or later. We test on 3.9, 3.10, 3.11, and 3.12.

## Usage Questions

### Q: How long does it take to download a channel?
**A:** Depends on channel size:
- Small (< 50 videos): ~1-2 minutes
- Medium (50-500 videos): ~5-15 minutes
- Large (500+ videos): ~30-60 minutes, or longer if rate-limited

### Q: Can I pause and resume downloads?
**A:** Yes! The system is incremental. Just run the same command again, and it will skip already-downloaded videos.

### Q: What if a channel has 10,000+ videos?
**A:** The system is tested up to 8,300+ videos. For very large channels:
- Downloads may take 1-2 hours
- You can split into multiple runs (use `--batch-size 500`)
- Database stays responsive

### Q: Can I download from playlists?
**A:** Not directly. You can use YouTube's `?list=...` format as a channel URL, and the system will treat it as a virtual channel. Behavior may vary.

### Q: Why am I getting rate-limited?
**A:** YouTube throttles heavy downloaders. The system includes exponential backoff. If you still hit limits:
- Take a 30-60 minute break
- Use `--max-retries 10` to be more patient
- Run overnight when servers are less busy

## Data & Files

### Q: Where are my transcripts stored?
**A:** In the `markdown/` folder, organized by channel name:
```
markdown/
├── 19KEYS_NETWORK/
├── Alignment_of_Light/
├── Andre_Duqum/
└── ...
```

### Q: What format are the markdown files?
**A:** YAML frontmatter + plain text transcript:
```yaml
---
id: youtube_channel_slug_VIDEOID
title: "Video Title"
guest: "Guest Name"
topics: [topic1, topic2]
---
Transcript text here...
```

### Q: Can I import directly into Obsidian?
**A:** Yes! Symlink the `markdown/` folder into your Obsidian vault:
```bash
ln -s ~/youtube_transcript_exporter/markdown ~/my-vault/transcripts
```
Then use Obsidian's dataview/search to find videos.

### Q: How do I export to Notion?
**A:** See [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md) for Notion setup. TL;DR:
```bash
export NOTION_TOKEN="your_integration_token"
export NOTION_DATABASE_ID="your_db_id"
./export.sh --export-notion
```

### Q: Can I delete the `out/` folder?
**A:** Not recommended. It contains the raw `.vtt` captions and metadata (`.info.json`). If you delete it:
- You lose the original caption files
- Regenerating markdown would require re-downloading
Keep it for data integrity.

## Troubleshooting

### Q: I'm getting "OSError: Bad file descriptor"
**A:** Usually happens in background/CI environments. Fixed in recent versions. Update to latest:
```bash
git pull origin main
```

### Q: Markdown files look wrong or incomplete
**A:** Run the audit:
```bash
./export.sh --audit
```
If issues persist, regenerate:
```bash
./export.sh --rebuild-markdown
```

### Q: My database (canonical.json) is huge. Is that normal?
**A:** Yes. Each entry is ~2-5 KB. 8,300 videos ≈ 16-40 MB. If over 100 MB, something's wrong; run `--audit`.

### Q: Can I run two downloads at once?
**A:** Not recommended (they'll conflict on the same files). Use `--batch` for parallel processing:
```bash
./export.sh --batch CHANNEL_URL1 CHANNEL_URL2 CHANNEL_URL3
```
This runs up to 4 channels in parallel safely.

### Q: How do I backup my transcripts?
**A:** Simplest option:
```bash
tar -czf transcripts-backup-$(date +%Y%m%d).tar.gz markdown/ db/
```
Or use a cloud backup tool to sync `markdown/` and `db/` folders.

## Advanced

### Q: Can I customize guest/topic extraction?
**A:** Yes, edit `src/metadata_extractor.py`:
- `extract_guest()` -- modify regex patterns
- `extract_topics()` -- add your own tag logic

Then rebuild:
```bash
./export.sh --rebuild-metadata
./export.sh --rebuild-markdown
```

### Q: How do I add a new channel programmatically?
**A:** Use the Python CLI:
```python
from ytexporter import ExportManager
mgr = ExportManager()
mgr.add_channel("https://youtube.com/@channelname")
mgr.process()
```

### Q: Can I run this in Docker?
**A:** Yes! See [Dockerfile](Dockerfile). Build and run:
```bash
docker build -t ytexporter .
docker run -v $(pwd)/output:/app/out ytexporter \
  ./export.sh --new-channel "https://youtube.com/@channelname"
```

### Q: How do I contribute a fix?
**A:** See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines. Quick start:
1. Fork the repo
2. Create a branch (`git checkout -b fix/your-fix`)
3. Make changes
4. Run tests (`python tests/test_all.py`)
5. Commit and push
6. Open a pull request

## Still Have Questions?

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Review [CONVENTIONS.md](CONVENTIONS.md) for system design patterns
- Open an issue on GitHub
- Email: d.lovecreator@gmail.com
