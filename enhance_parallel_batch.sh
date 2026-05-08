#!/bin/bash
# Master Enhancement - Handles all 3 parallel downloads

set -euo pipefail

log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

log "=== MASTER ENHANCEMENT FOR 3 CHANNELS ==="
log ""
log "Waiting for all downloads to complete..."
log ""

# Wait for all to finish
timeout 7200 bash -c 'while ps aux | grep -E "download_resilient.*@" | grep -v grep | grep -q .; do 
  HDS=$(find out -ipath "*human*design*" -name "*.info.json" 2>/dev/null | wc -l)
  SJ=$(find out -ipath "*steve*judd*" -name "*.info.json" 2>/dev/null | wc -l)
  ANDRE=$(find out -ipath "*andre*" -name "*.info.json" 2>/dev/null | wc -l)
  log "Progress: HDS=$HDS, Steve Judd=$SJ, Andreduqum=$ANDRE"
  sleep 60
done' || true

log ""
log "All downloads complete!"

HDS=$(find out -ipath "*human*design*" -name "*.info.json" 2>/dev/null | wc -l)
SJ=$(find out -ipath "*steve*judd*" -name "*.info.json" 2>/dev/null | wc -l)
ANDRE=$(find out -ipath "*andre*" -name "*.info.json" 2>/dev/null | wc -l)

log "Final Counts:"
log "  Human Design System: $HDS videos"
log "  Steve Judd Astrology: $SJ videos"
log "  Andreduqum: $ANDRE videos"
log "  TOTAL: $(($HDS + $SJ + $ANDRE)) new videos"
log ""

log "Running enhancement pipeline (metadata → RAG → audit)..."
log ""

cd ~/youtube_transcript_exporter

log "Step 1/3: Rebuilding metadata..."
./export.sh --rebuild-metadata

log "Step 2/3: Enhancing RAG schema..."
python3 src/enhance_rag_schema.py

log "Step 3/3: Running audit..."
./export.sh --audit | tail -50

FINAL=$(python3 -c "import json; data = json.load(open('db/canonical.json')); print(len(data.get('videos', [])))")
log ""
log "✓ COMPLETE!"
log "System now at $FINAL total videos"
log ""
