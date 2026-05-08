#!/bin/bash
###############################################################################
# Parallel Channel Downloader
# Safe parallel downloads with sequential enhancement
# 
# Usage: ./download_parallel.sh URL1 URL2 URL3
# Max recommended: 3 channels in parallel
###############################################################################

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

if [ $# -eq 0 ]; then
    echo "Usage: $0 <URL1> [URL2] [URL3]"
    echo ""
    echo "Examples:"
    echo "  $0 https://www.youtube.com/@channel1/videos"
    echo "  $0 https://www.youtube.com/@channel1/videos https://www.youtube.com/@channel2/videos"
    echo "  $0 https://www.youtube.com/@ch1/videos https://www.youtube.com/@ch2/videos https://www.youtube.com/@ch3/videos"
    echo ""
    echo "⚠️  CAUTION: Do not exceed 3 channels in parallel"
    exit 1
fi

if [ $# -gt 3 ]; then
    log "ERROR: Maximum 3 channels in parallel (you provided $#)"
    log "Reason: YouTube rate limiting, canonical.json contention"
    exit 1
fi

log "Starting parallel downloads for $# channel(s)"
log "Memory: ~${#}00-120 MB per channel"
log "Duration: ~10-15 min per channel (parallel = faster)"
log ""

URLS=("$@")
PIDs=()

# Start all downloads in parallel
for i in "${!URLS[@]}"; do
    URL="${URLS[$i]}"
    log "Channel $((i+1)): Starting download of $URL"
    
    python3 src/download_resilient.py "$URL" 1 \
        2>&1 | tee -a archive/logs/parallel_download_ch$((i+1))_$(date +%Y%m%d_%H%M%S).log &
    
    PIDs+=($!)
    sleep 2  # Stagger starts by 2 seconds
done

log "All downloads started. Waiting for completion..."
log ""

# Wait for all to complete
for i in "${!PIDs[@]}"; do
    PID=${PIDs[$i]}
    log "Waiting for channel $((i+1)) (PID: $PID)..."
    wait $PID
    log "Channel $((i+1)) download complete"
done

log ""
log "✓ All downloads complete!"
TOTAL=$(find out -name "*.info.json" | wc -l)
log "Total videos now: $TOTAL"
log ""

# Now run enhancement pipeline once for all new downloads
log "Running enhancement pipeline (metadata → RAG → audit)..."
log ""

log "Step 1/3: Rebuilding metadata..."
./export.sh --rebuild-metadata

log "Step 2/3: Enhancing RAG schema..."
python3 src/enhance_rag_schema.py

log "Step 3/3: Running audit..."
./export.sh --audit | tail -40

FINAL=$(python3 -c "import json; data = json.load(open('db/canonical.json')); print(len(data.get('videos', [])))")
log ""
log "✓ COMPLETE: System now at $FINAL total videos"
log ""
