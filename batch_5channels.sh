#!/bin/bash
# Run 5 channel downloads in parallel, then rebuild metadata/markdown once.
set -euo pipefail

CHANNELS=(
  "https://www.youtube.com/@LibraryoftheUntold"
  "https://www.youtube.com/@InspiredEvolution"
  "https://www.youtube.com/@VivianeChauvetGalacticHealer"
  "https://www.youtube.com/@Wizard-of-Wivenhoe"
  "https://www.youtube.com/@LeeHarrisEnergy"
)

log(){ echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"; }

log "Starting parallel downloads for ${#CHANNELS[@]} channels..."

pids=()
for url in "${CHANNELS[@]}"; do
  log "Launching download: $url"
  ./export.sh --new-channel "$url" &
  pids+=("$!")
  sleep 2
done

log "Waiting for all downloads to finish..."
fail=0
for pid in "${pids[@]}"; do
  if ! wait "$pid"; then
    fail=1
  fi
done

if [ "$fail" -ne 0 ]; then
  log "One or more downloads failed; continuing to rebuild metadata/markdown on what succeeded."
fi

log "Rebuilding metadata (single pass)..."
./export.sh --rebuild-metadata

log "Rebuilding markdown (incremental)..."
./export.sh --rebuild-markdown

log "Audit..."
./export.sh --audit

log "Health check..."
python3 system_health_check.py

log "DONE"
