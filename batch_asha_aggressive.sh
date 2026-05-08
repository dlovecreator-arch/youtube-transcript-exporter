#!/bin/bash
# Aggressive 5-pass redownload for massive Asha Nayaswami channel

set -euo pipefail

CHANNEL="https://www.youtube.com/@ashanayaswami/videos"

log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

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
