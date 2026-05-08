#!/bin/bash
# Auto-enhancement for Human Design System

set -euo pipefail

log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

log "Waiting for Human Design System download to complete..."

# Wait for process
timeout 7200 bash -c 'while ps aux | grep -E "yt-dlp.*HumanDesign|download_resilient.*HumanDesign" | grep -v grep | grep -q .; do sleep 30; done' || true

TOTAL=$(find ~/youtube_transcript_exporter/out -ipath "*human*design*" -name "*.info.json" 2>/dev/null | wc -l)
log "✓ Download complete: $TOTAL videos captured"

log "Running enhancement pipeline..."
cd ~/youtube_transcript_exporter

log "  1/3: Rebuilding metadata..."
./export.sh --rebuild-metadata

log "  2/3: Enhancing RAG schema..."
python3 src/enhance_rag_schema.py

log "  3/3: Running audit..."
./export.sh --audit | tail -40

log "✓ COMPLETE: Human Design System integrated!"
FINAL=$(python3 -c "import json; data = json.load(open('db/canonical.json')); hds = len([v for v in data.get('videos', []) if 'human' in v.get('channel', '').lower() and 'design' in v.get('channel', '').lower()]); print(hds)")
log "Human Design System now has $FINAL videos in system"
