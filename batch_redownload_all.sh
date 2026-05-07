#!/bin/bash
###############################################################################
# Comprehensive Re-Download of All 14 Channels
# Strategy: Multiple retry passes to accumulate ALL videos including livestreams
# Each channel gets 5 full download attempts with 2-minute inter-attempt delays
###############################################################################

set -euo pipefail

REPO_ROOT="$HOME/youtube_transcript_exporter"
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

download_all_passes() {
  local url="$1"
  local max_passes=5
  local pass=1
  
  while [ $pass -le $max_passes ]; do
    log "Channel: $url | Pass $pass/$max_passes"
    
    timeout 900 python3 "$REPO_ROOT/src/download_resilient.py" "$url" 1 2>&1 | tail -3
    
    local count
    count=$(find "$REPO_ROOT/out" -name "*.info.json" -type f | wc -l)
    log "Total videos in system: $count"
    
    if [ $pass -lt $max_passes ]; then
      log "Sleeping 120s before next pass..."
      sleep 120
    fi
    
    pass=$((pass + 1))
  done
}

main() {
  cd "$REPO_ROOT"
  
  log "Starting comprehensive re-download of all 14 channels"
  log "Strategy: 5 passes per channel to accumulate livestreams + missing videos"
  
  for channel_url in "${CHANNELS[@]}"; do
    download_all_passes "$channel_url"
    log "---"
  done
  
  log "All download passes complete. Running final pipeline..."
  ./export.sh --rebuild-metadata
  ./export.sh --rebuild-markdown
  ./export.sh --audit
  
  log "COMPLETE: All channels re-downloaded and processed"
}

main "$@"
