#!/bin/bash
# Auto-runs enhancement after Angels of Atlantis download completes

set -euo pipefail

log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

log "Waiting for Angels of Atlantis download to complete..."

# Wait for process to finish
timeout 3600 bash -c 'while ps aux | grep -E "yt-dlp.*TheAngelsOfAtlantis|download_resilient.*TheAngelsOfAtlantis" | grep -v grep | grep -q .; do sleep 30; done' || true

TOTAL=$(find ~/youtube_transcript_exporter/out -path "*Angels*" -name "*.info.json" | wc -l)
log "✓ Download complete: $TOTAL videos captured"

log "Running enhancement pipeline..."
cd ~/youtube_transcript_exporter

log "  1/4: Rebuilding metadata..."
./export.sh --rebuild-metadata

log "  2/4: Rebuilding markdown..."
./export.sh --rebuild-markdown

log "  3/4: Enhancing RAG schema..."
python3 src/enhance_rag_schema.py

log "  4/4: Running audit..."
./export.sh --audit

log "✓ COMPLETE: Angels of Atlantis fully integrated!"
FINAL=$(python3 -c "import json; data = json.load(open('db/canonical.json')); print(len(data.get('videos', [])))")
log "System now at $FINAL total videos"
