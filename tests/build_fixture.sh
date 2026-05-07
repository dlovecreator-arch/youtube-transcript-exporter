#!/usr/bin/env bash
###############################################################################
# Build a tiny fake `out/` fixture so CI can smoke-test the full pipeline
# without hitting YouTube. Mirrors the real yt-dlp output structure exactly.
###############################################################################

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

VIDEO_ID="testVideo01"   # 11 chars, matches CONVENTIONS.md rule
CHANNEL="Test Channel"
TITLE="Test Episode -- Hello World"

VIDEO_DIR="out/${CHANNEL}/${VIDEO_ID}"
mkdir -p "$VIDEO_DIR"

# Fake .info.json (mirrors yt-dlp output schema)
cat > "${VIDEO_DIR}/${TITLE} [${VIDEO_ID}].info.json" <<EOF
{
  "id": "${VIDEO_ID}",
  "title": "${TITLE}",
  "channel": "${CHANNEL}",
  "channel_id": "UCTestChannelID00000000",
  "uploader": "${CHANNEL}",
  "upload_date": "20250115",
  "duration": 60,
  "view_count": 1000,
  "like_count": 50,
  "description": "A test episode used by CI for pipeline smoke tests.",
  "tags": ["test", "ci", "fixture"],
  "categories": ["Education"]
}
EOF

# Fake .en.vtt (mirrors YouTube auto-caption format)
cat > "${VIDEO_DIR}/${TITLE} [${VIDEO_ID}].en.vtt" <<'EOF'
WEBVTT
Kind: captions
Language: en

00:00:00.000 --> 00:00:03.000
Hello world.

00:00:03.000 --> 00:00:06.000
This is a test transcript.

00:00:06.000 --> 00:00:09.000
The pipeline should turn this into clean markdown.
EOF

echo "Fixture built at ${VIDEO_DIR}"
ls -la "${VIDEO_DIR}"
