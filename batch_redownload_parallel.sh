#!/bin/bash
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

log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

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
