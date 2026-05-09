#!/bin/bash
###############################################################################
# YouTube Transcript Exporter -- Production Orchestrator
#
# Usage:
#   ./export.sh --new-channel https://www.youtube.com/@Channel
#   ./export.sh --rebuild-markdown
#   ./export.sh --export-notion [--max 100]
#   ./export.sh --audit
###############################################################################

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$REPO_ROOT/src"
OUT_DIR="$REPO_ROOT/out"
DB_DIR="$REPO_ROOT/db"
MARKDOWN_DIR="$REPO_ROOT/markdown"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}✓${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}!${NC} $*"
}

log_error() {
    echo -e "${RED}✗${NC} $*"
}

###############################################################################
# PHASE 1: Download + Metadata Extraction
###############################################################################

download_channel() {
    local url="$1"

    log_info "Downloading from: $url"
    log_info "Using resilient downloader with rate limiting + user agent rotation"

    # Append channel URL to channels.txt (avoid duplicates)
    if ! grep -q "^${url}$" "$REPO_ROOT/channels.txt" 2>/dev/null; then
        echo "$url" >> "$REPO_ROOT/channels.txt"
        log_info "Added to channels.txt"
    fi

    # Use the resilient Python downloader
    # It handles: exponential backoff, rotating user agents, batched downloads, hard timeouts
    cd "$REPO_ROOT"
    # Important: when this script runs detached (CI/background jobs),
    # stdin may be closed which can cause Python to fail initializing
    # sys.stdin/sys.stdout/sys.stderr with "Bad file descriptor".
    # Redirect stdin from /dev/null to guarantee a valid FD.
    python3 "$SRC_DIR/download_resilient.py" "$url" 5 </dev/null

    # Quarantine any channel-listing folders yt-dlp may have created
    # (folders named @handle or UCxxx are channel metadata, not videos).
    find "$OUT_DIR" -type d \( -name "@*" -o -name "UC*" \) -mindepth 2 -maxdepth 2 2>/dev/null | while read -r d; do
        local parent
        parent=$(dirname "$d")
        mkdir -p "$parent/_channel_meta"
        mv "$d" "$parent/_channel_meta/" 2>/dev/null && log_info "Quarantined channel-meta: $d"
    done

    log_info "Download complete"
}

extract_metadata() {
    log_info "Extracting metadata from all .info.json files..."
    cd "$REPO_ROOT"
    python3 "$SRC_DIR/metadata_extractor.py" </dev/null
}

###############################################################################
# PHASE 2: Generate Markdown
###############################################################################

regenerate_markdown() {
    log_info "Regenerating Markdown files with optimized frontmatter..."
    cd "$REPO_ROOT"
    # Incremental by default (non-destructive). Use `python3 src/markdown_generator.py --clean`
    # only if you explicitly want to wipe/rebuild the markdown vault.
    python3 "$SRC_DIR/markdown_generator.py" </dev/null
    
    log_info "Formatting Obsidian vault structure..."
    python3 "$SRC_DIR/obsidian_formatter.py" </dev/null
}

###############################################################################
# PHASE 3: Export to Notion
###############################################################################

export_to_notion() {
    local max_records="${1:-}"
    
    if [ -z "$NOTION_TOKEN" ]; then
        log_error "NOTION_TOKEN environment variable not set"
        log_warn "Get token from: https://www.notion.so/my-integrations"
        return 1
    fi
    
    log_info "Exporting to Notion..."
    cd "$REPO_ROOT"
    
    if [ -n "$max_records" ]; then
        log_warn "Limiting to $max_records records"
        NOTION_DATABASE_ID="${NOTION_DATABASE_ID:-}" \
            python3 "$SRC_DIR/notion_exporter.py" --max "$max_records" </dev/null
    else
        NOTION_DATABASE_ID="${NOTION_DATABASE_ID:-}" \
            python3 "$SRC_DIR/notion_exporter.py" </dev/null
    fi
}

###############################################################################
# PHASE 4: Quality Audit
###############################################################################

audit_transcripts() {
    log_info "Running quality audit..."
    
    cd "$REPO_ROOT"
    python3 << 'PYTHON'
import json
from pathlib import Path

db_file = Path("db/canonical.json")
if not db_file.exists():
    print("Error: canonical.json not found. Run --rebuild-metadata first.")
    exit(1)

db = json.loads(db_file.read_text())
videos = db.get("videos", [])

stats = {
    "total": len(videos),
    "with_guest": sum(1 for v in videos if v.get("guest")),
    "with_tags": sum(1 for v in videos if v.get("tags")),
    "zero_views": sum(1 for v in videos if v.get("views", 0) == 0),
    "zero_likes": sum(1 for v in videos if v.get("likes", 0) == 0),
    "by_channel": {},
}

for v in videos:
    channel = v.get("channel", "Unknown")
    if channel not in stats["by_channel"]:
        stats["by_channel"][channel] = 0
    stats["by_channel"][channel] += 1

print("\n" + "="*60)
print("TRANSCRIPT AUDIT REPORT")
print("="*60)
print(f"Total videos: {stats['total']}")
print(f"Videos with guest: {stats['with_guest']} ({100*stats['with_guest']//stats['total']}%)")
print(f"Videos with tags: {stats['with_tags']} ({100*stats['with_tags']//stats['total']}%)")
print(f"Videos with 0 views: {stats['zero_views']}")
print(f"Videos with 0 likes: {stats['zero_likes']}")
print(f"\nBy Channel:")
for channel, count in sorted(stats["by_channel"].items()):
    print(f"  - {channel}: {count}")

# Check for duplicates
dups = db.get("duplicates", {})
if dups:
    print(f"\nDuplicates found: {len(dups)}")
    for vid_id, sources in list(dups.items())[:5]:
        print(f"  - {vid_id}: {sources}")

print("="*60)

# Layout audit -- enforce CONVENTIONS.md rules
print("\n[ Folder Layout Audit ]")
import re as _re
out = Path("out")
non_id_folders = []
extra_files = []
total_video_folders = 0
for chan in out.iterdir():
    if not chan.is_dir():
        continue
    for v in chan.iterdir():
        if not v.is_dir() or v.name == "_channel_meta":
            continue
        total_video_folders += 1
        if not _re.fullmatch(r"[A-Za-z0-9_\-]{11}", v.name):
            non_id_folders.append(str(v))
        for f in v.iterdir():
            if f.is_dir():
                continue
            n = f.name
            if n == "transcript.en.txt":
                continue
            if n.endswith(".info.json"):
                continue
            if _re.search(r"\[[A-Za-z0-9_\-]{11}\]\.en\.vtt$", n):
                continue
            extra_files.append(str(f))
print(f"Video folders in out/: {total_video_folders}")
print(f"Non-id-named folders (should be 0): {len(non_id_folders)}")
print(f"Extra/legacy files in video folders (should be 0): {len(extra_files)}")
if non_id_folders[:3]:
    print("  Examples:", non_id_folders[:3])
if extra_files[:3]:
    print("  Examples:", extra_files[:3])
print("="*60)
PYTHON
}

###############################################################################
# Main CLI
###############################################################################

show_help() {
    cat << 'EOF'
YouTube Transcript Exporter -- Production Workflow

COMMANDS:

  --new-channel <URL>        FULL PIPELINE: download + metadata + markdown + validate
                             (this is the one-shot "just works" command)
  --rebuild-metadata         Extract metadata from all .info.json files
  --rebuild-markdown         Regenerate Markdown (incremental, with validation)
  --validate                 Check markdown/out alignment for duplicates
  --export-notion [--max N]  Export to Notion database
  --audit                    Run quality audit
  --full-pipeline <URL>      Same as --new-channel (alias)

EXAMPLES:

  # Add new channel
  ./export.sh --new-channel https://www.youtube.com/@SomeChannel

  # Rebuild database and Markdown (after adding channel)
  ./export.sh --rebuild-metadata
  ./export.sh --rebuild-markdown

  # Export to Notion
  NOTION_TOKEN=xxx NOTION_DATABASE_ID=yyy ./export.sh --export-notion

  # Audit quality
  ./export.sh --audit

  # Full pipeline (download + all processing)
  ./export.sh --full-pipeline https://www.youtube.com/@Channel

EOF
    exit 0
}

main() {
    mkdir -p "$OUT_DIR" "$DB_DIR" "$MARKDOWN_DIR"
    
    case "${1:-}" in
        --new-channel)
            if [ -z "${2:-}" ]; then
                log_error "Usage: --new-channel <URL>"
                exit 1
            fi
            log_info "Phase 1/4: Downloading channel..."
            download_channel "$2" "${3:-10}"
            log_info "Phase 2/4: Extracting metadata..."
            extract_metadata
            log_info "Phase 3/4: Generating markdown..."
            regenerate_markdown
            log_info "Phase 4/4: Validating alignment..."
            if python3 "$REPO_ROOT/tools/validate_alignment.py"; then
                log_info "✅ Channel added cleanly. Markdown ready in: $MARKDOWN_DIR"
            else
                log_warn "⚠️  Alignment issues detected -- review output above."
                exit 1
            fi
            ;;
        --rebuild-metadata)
            extract_metadata
            ;;
        --rebuild-markdown)
            regenerate_markdown
            python3 "$REPO_ROOT/tools/validate_alignment.py" || log_warn "Alignment issues -- see above"
            ;;
        --validate)
            python3 "$REPO_ROOT/tools/validate_alignment.py"
            ;;
        --export-notion)
            export_to_notion "${2:-}"
            ;;
        --audit)
            audit_transcripts
            ;;
        --full-pipeline)
            if [ -z "${2:-}" ]; then
                log_error "Usage: --full-pipeline <URL>"
                exit 1
            fi
            download_channel "$2" 10
            extract_metadata
            regenerate_markdown
            audit_transcripts
            log_info "Pipeline complete! Markdown ready in: $MARKDOWN_DIR"
            ;;
        --help | -h | "")
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            ;;
    esac
}

main "$@"
