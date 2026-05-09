# How to Use - Single Source of Truth

## 🎯 To Add a New YouTube Channel

```bash
./export.sh --new-channel https://www.youtube.com/@ChannelHandle
```

That's it. This single command will:
1. Download all video metadata + transcripts to `out/Channel Name/`
2. Update the canonical DB (`db/canonical.json`)
3. Generate markdown files in `markdown/Channel Name/`
4. Validate alignment between `out/` and `markdown/`

## 🔍 To Verify Everything is Aligned

```bash
python3 tools/validate_alignment.py
```

Exit code `0` = perfect. Exit code `1` = duplicates or misalignment detected.

## 🧹 To Rebuild All Markdown from Scratch

```bash
./export.sh --rebuild-markdown
```

(Safe -- has single-instance lock; only one can run at a time.)

## 📊 To See Channel Stats

```bash
python3 tools/count_channels.py
```

## 🩺 System Health Check

```bash
python3 tools/system_health_check.py
```

## 📦 Other Tools

| Command | Purpose |
|---------|---------|
| `python3 tools/audit_tool.py` | Comprehensive audit |
| `python3 tools/cleanup_data.py` | Clean orphaned data |
| `python3 tools/merge_channels.py` | Merge duplicate channels |

## 🚨 Critical Rules (Don't Break)

1. **Folder names in `markdown/` MUST match `out/` exactly** (with spaces, not underscores)
   -- See `NAMING_CONVENTION.md`
2. **Never run multiple `markdown_generator.py` simultaneously**
   -- Single-instance lock prevents this automatically
3. **Always validate after big changes**: `python3 tools/validate_alignment.py`

## 📁 Project Structure

```
youtube_transcript_exporter/
├── export.sh              # MAIN entry point
├── HOW_TO_USE.md          # ← You are here
├── README.md              # Project overview
├── src/                   # Core Python modules
│   ├── download_resilient.py
│   ├── metadata_extractor.py
│   ├── markdown_generator.py
│   ├── notion_exporter.py
│   └── ...
├── tools/                 # Utilities
│   ├── validate_alignment.py
│   ├── audit_tool.py
│   ├── count_channels.py
│   └── ...
├── tests/                 # Test suite
├── out/                   # Raw yt-dlp downloads (gitignored)
├── markdown/              # Generated .md files (gitignored)
├── db/                    # Canonical DB (gitignored)
├── archive/               # Old scripts, reports, logs
└── docs/                  # Examples, images
```

## 🆘 Troubleshooting

If duplicate folders appear (e.g., `Channel_Name` next to `Channel Name`):

```bash
# 1. Kill any zombie processes
pkill -9 -f "markdown_generator.py"
pkill -9 -f "download_resilient.py"

# 2. Remove the underscore versions (always wrong)
ls markdown/ | grep "_" | xargs -I {} rm -rf "markdown/{}"

# 3. Validate
python3 tools/validate_alignment.py
```

See also: `TROUBLESHOOTING.md`, `FAQ.md`
