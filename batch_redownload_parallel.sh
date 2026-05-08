#!/bin/bash

################################################################################
# Script: batch_redownload_parallel.sh
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
LOG_FILE="$LOG_DIR/batch_redownload_parallel_$(date +%Y%m%d_%H%M%S).log"

# Error handler with line number
trap 'ERROR_LINE=$LINENO; echo "[$$(date +"%Y-%m-%d %H:%M:%S")] ERROR at line $ERROR_LINE" | tee -a "$LOG_FILE"; exit 1' ERR

log() {
  local msg="[$$(date +"%Y-%m-%d %H:%M:%S")] $1"
  echo "$msg" | tee -a "$LOG_FILE"
}

log "Starting: $0"

###############################################################################
# Fast Comprehensive Re-Download
# 3 passes per channel, with smarter parallelization
###############################################################################

set -euo pipefail

REPO_ROOT="$HOME/youtube_transcript_exporter"

# Array of channels
CHANNELS=(
  "https://www.youtube.com/@EmilioOrtiz/videos"
  "https://www.youtube.com/@iamkerryk/videos"
  "https://www.youtube.com/@LeeHarrisEnergy/videos"
  "https://www.youtube.com/@PamGregoryOfficial/videos"
  "https://www.youtube.com/@PortalToAscension/videos"
  "https://www.youtube.com/@officialthealchemist/videos"
  "https://www.youtube.com/@VivianeChauvetGalacticHealer/videos"
  "https://www.youtube.com/@Wizard-of-Wivenhoe/videos"
  "https://www.youtube.com/@myrisingrose/videos"
  "https://www.youtube.com/@THEREALISMAELPEREZ/videos"
  "https://www.youtube.com/@twcjr44/videos"
  "https://www.youtube.com/@Robert_Edward_Grant/videos"
  "https://www.youtube.com/@TealSwanOfficial/videos"
  "https://www.youtube.com/@igor_galibov/videos"
)

download_channel_multipass() {
  local url="$1"
  local max_passes=3
  
  for pass in $(seq 1 $max_passes); do
    log "Pass $pass/3: $url"
    timeout 600 python3 "$REPO_ROOT/src/download_resilient.py" "$url" 1 >/dev/null 2>&1 || true
    sleep 30
  done
}

log "STARTING: Comprehensive 3-pass re-download of all 14 channels"

for channel in "${CHANNELS[@]}"; do
  download_channel_multipass "$channel" &
done

# Wait for all background jobs
wait

log "All download passes complete. Running final pipeline..."
cd "$REPO_ROOT"
./export.sh --rebuild-metadata
./export.sh --rebuild-markdown
./export.sh --audit

log "DONE: All channels re-downloaded with full metadata + markdown"
