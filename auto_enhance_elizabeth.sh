#!/bin/bash

################################################################################
# Script: auto_enhance_elizabeth.sh
# Generated with enhanced error handling
# Features:
#   - set -euo pipefail (exit on error, undefined vars, pipe failures)
#   - Automatic error trap with line numbers
#   - Structured logging with timestamps
#   - Automatic log file creation
################################################################################

set -euo pipefail

# Create logs directory
LOG_DIR="logs"
mkdir -p "$LOG_DIR"

# Set up error logging
LOG_FILE="$LOG_DIR/auto_enhance_elizabeth_$(date +%Y%m%d_%H%M%S).log"

# Error handler with line number
trap 'ERROR_LINE=$LINENO; echo "[$$(date +"%Y-%m-%d %H:%M:%S")] ERROR at line $ERROR_LINE" | tee -a "$LOG_FILE"; exit 1' ERR

log() {
  local msg="[$$(date +"%Y-%m-%d %H:%M:%S")] $1"
  echo "$msg" | tee -a "$LOG_FILE"
}

log "Starting: $0"

# Auto-enhancement for Elizabeth April (after channel root retry completed)

set -euo pipefail

log "Waiting for Elizabeth April channel root download to complete..."

# Wait for process
timeout 7200 bash -c 'while ps aux | grep -E "yt-dlp.*Elizabeth|download_resilient.*Elizabeth" | grep -v grep | grep -q .; do sleep 30; done' || true

TOTAL=$(find ~/youtube_transcript_exporter/out -path "*Elizabeth*" -name "*.info.json" | wc -l)
log "✓ Download complete: $TOTAL videos captured from channel root"

log "Running enhancement pipeline..."
cd ~/youtube_transcript_exporter

log "  1/3: Rebuilding metadata..."
./export.sh --rebuild-metadata

log "  2/3: Enhancing RAG schema..."
python3 src/enhance_rag_schema.py

log "  3/3: Running audit..."
./export.sh --audit | tail -40

log "✓ COMPLETE: Elizabeth April enhanced!"
FINAL=$(python3 -c "import json; data = json.load(open('db/canonical.json')); eliz = len([v for v in data.get('videos', []) if 'elizabeth' in v.get('channel', '').lower()]); print(eliz)")
log "Elizabeth April now has $FINAL videos in system"
