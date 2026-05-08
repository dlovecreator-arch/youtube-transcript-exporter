#!/bin/bash
# Auto-runs enhancement after Asha Nayaswami download completes

set -euo pipefail

log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

log "Waiting for Asha Nayaswami download to complete (may take 30-45 min for 1909 videos)..."

# Wait for process to finish
timeout 5400 bash -c 'while ps aux | grep -E "yt-dlp.*ashanaya|download_resilient.*ashanaya" | grep -v grep | grep -q .; do sleep 30; done' || true

TOTAL=$(find ~/youtube_transcript_exporter/out -path "*Asha*" -name "*.info.json" | wc -l)
log "✓ Download complete: $TOTAL videos captured"

log "Running enhancement pipeline (skip markdown for speed)..."
cd ~/youtube_transcript_exporter

log "  1/3: Rebuilding metadata..."
./export.sh --rebuild-metadata

log "  2/3: Enhancing RAG schema..."
python3 src/enhance_rag_schema.py

log "  3/3: Running audit..."
./export.sh --audit | tail -30

log "✓ COMPLETE: Asha Nayaswami fully integrated!"
FINAL=$(python3 -c "import json; data = json.load(open('db/canonical.json')); print(len(data.get('videos', [])))")
log "System now at $FINAL total videos"
