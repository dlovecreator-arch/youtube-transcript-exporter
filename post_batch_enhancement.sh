#!/bin/bash
###############################################################################
# Post-Batch Enhancement Pipeline
# Runs after comprehensive re-download completes
# Upgrades schema to RAG-optimized format
###############################################################################

set -euo pipefail

REPO_ROOT="$HOME/youtube_transcript_exporter"

log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

log "PHASE 1: Waiting for batch download to complete..."
cd "$REPO_ROOT"

# The batch script should finish automatically, but let's wait just to be safe
timeout 3600 bash -c 'while ps aux | grep -E "python3.*download|yt-dlp" | grep -v grep | grep -q .; do sleep 30; done' || true

TOTAL=$(find out -name "*.info.json" | wc -l)
log "Batch download complete: $TOTAL videos total"

log "PHASE 2: Running standard pipeline (metadata + markdown)..."
./export.sh --rebuild-metadata
./export.sh --rebuild-markdown
./export.sh --audit

log "PHASE 3: Enhancing schema with RAG metadata..."
python3 src/enhance_rag_schema.py

log "PHASE 4: Regenerating markdown with RAG frontmatter..."
python3 src/enhance_markdown_rag.py

log "PHASE 5: Final audit..."
./export.sh --audit

log "✓ COMPLETE: System fully enhanced with RAG-optimized schema"
log "  - source_id: youtube_channelslug_videoid"
log "  - captured_date: ISO timestamp"
log "  - transcript_source: youtube_caption"
log "  - confidence: 0.85 (YouTube auto-captions)"
log "  - tradition: [] (ready for manual enrichment)"
log "  - All markdown frontmatter updated for RAG/semantic search"
