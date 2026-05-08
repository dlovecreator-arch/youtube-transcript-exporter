#!/bin/bash

################################################################################
# Script: batch_asha_aggressive.sh
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
LOG_FILE="$LOG_DIR/batch_asha_aggressive_$(date +%Y%m%d_%H%M%S).log"

# Error handler with line number
trap 'ERROR_LINE=$LINENO; echo "[$$(date +"%Y-%m-%d %H:%M:%S")] ERROR at line $ERROR_LINE" | tee -a "$LOG_FILE"; exit 1' ERR

log() {
  local msg="[$$(date +"%Y-%m-%d %H:%M:%S")] $1"
  echo "$msg" | tee -a "$LOG_FILE"
}

log "Starting: $0"

# Aggressive 5-pass redownload for massive Asha Nayaswami channel

set -euo pipefail

CHANNEL="https://www.youtube.com/@ashanayaswami/videos"

log "Starting aggressive 5-pass download for Asha Nayaswami (1909 videos)..."

for pass in 1 2 3 4 5; do
  BEFORE=$(find out -path "*Asha*" -name "*.info.json" | wc -l)
  log "Pass $pass: Starting (currently have $BEFORE videos)"
  
  timeout 900 python3 src/download_resilient.py "$CHANNEL" $pass 2>&1 | tail -5 || true
  
  AFTER=$(find out -path "*Asha*" -name "*.info.json" | wc -l)
  GAINED=$((AFTER - BEFORE))
  log "Pass $pass: Complete (gained $GAINED videos, total $AFTER)"
  
  if [ $GAINED -eq 0 ]; then
    log "No new videos gained, stopping."
    break
  fi
  
  sleep 10
done

FINAL=$(find out -path "*Asha*" -name "*.info.json" | wc -l)
log "✓ All passes complete: $FINAL videos total"
