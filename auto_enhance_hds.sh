#!/bin/bash

################################################################################
# Script: auto_enhance_hds.sh
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
LOG_FILE="$LOG_DIR/auto_enhance_hds_$(date +%Y%m%d_%H%M%S).log"

# Error handler with line number
trap 'ERROR_LINE=$LINENO; echo "[$$(date +"%Y-%m-%d %H:%M:%S")] ERROR at line $ERROR_LINE" | tee -a "$LOG_FILE"; exit 1' ERR

log() {
  local msg="[$$(date +"%Y-%m-%d %H:%M:%S")] $1"
  echo "$msg" | tee -a "$LOG_FILE"
}

log "Starting: $0"

# Auto-enhancement for Human Design System

set -euo pipefail

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
