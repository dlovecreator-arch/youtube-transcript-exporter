#!/bin/bash
# Batch process 5 user-specified NEW channels with bounded parallelism, then rebuild once.
# Safe/resumable: each channel uses export.sh --new-channel (yt-dlp resume).
set -euo pipefail

CHANNELS=(
  "https://www.youtube.com/@johnburgos"
  "https://www.youtube.com/@19KEYS"
  "https://www.youtube.com/@Rianarendse"
  "https://www.youtube.com/@TheFourWindsSociety"
  "https://www.youtube.com/@jordanthornton"
)

# Keep concurrency modest to reduce throttling and RAM spikes.
MAX_JOBS=${MAX_JOBS:-2}

log(){ echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"; }

run_one(){
  local url="$1"
  log "Starting: $url"
  ./export.sh --new-channel "$url"
  log "Finished: $url"
}

log "Starting downloads for ${#CHANNELS[@]} channels with MAX_JOBS=$MAX_JOBS"

pids=()
fail=0

for url in "${CHANNELS[@]}"; do
  # wait for an available slot
  while [ "$(jobs -pr | wc -l | tr -d ' ')" -ge "$MAX_JOBS" ]; do
    sleep 5
  done

  run_one "$url" &
  pids+=("$!")
  sleep 2
done

log "Waiting for all channel jobs to finish..."
for pid in "${pids[@]}"; do
  if ! wait "$pid"; then
    fail=1
  fi
done

if [ "$fail" -ne 0 ]; then
  log "One or more channel downloads failed. Continuing with rebuild steps for whatever succeeded."
fi

log "Rebuilding metadata (single pass)..."
./export.sh --rebuild-metadata

log "Rebuilding markdown (incremental, non-destructive)..."
./export.sh --rebuild-markdown

log "Audit..."
./export.sh --audit

log "Health check..."
python3 system_health_check.py

log "DONE"
