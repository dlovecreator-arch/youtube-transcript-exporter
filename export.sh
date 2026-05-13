#!/usr/bin/env bash
# Compatibility wrapper. The canonical CLI is now:
#   python3 -m ytx ...
#
# This script preserves old muscle memory while delegating to ytx.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

show_help() {
  cat <<'EOF'
YouTube Transcript Exporter

Canonical CLI:
  python3 -m ytx <command>

Compatibility mappings:
  ./export.sh --new-channel URL        -> python3 -m ytx add URL
  ./export.sh --full-pipeline URL      -> python3 -m ytx add URL
  ./export.sh --rebuild-metadata       -> python3 -m ytx metadata
  ./export.sh --rebuild-markdown       -> python3 -m ytx markdown
  ./export.sh --audit                  -> python3 -m ytx audit
  ./export.sh --doctor                 -> python3 -m ytx doctor
  ./export.sh --status                 -> python3 -m ytx status
  ./export.sh --export-jsonl OUT       -> python3 -m ytx export jsonl --out OUT

Notion export was removed from the active workflow. Historical code lives in
archive/historical_docs/ if you ever want to resurrect it as a plugin.
EOF
}

case "${1:-}" in
  --new-channel|--full-pipeline)
    if [[ -z "${2:-}" ]]; then echo "Usage: $0 $1 <URL>" >&2; exit 2; fi
    exec python3 -m ytx add "$2" "${@:3}"
    ;;
  --rebuild-metadata)
    exec python3 -m ytx metadata "${@:2}"
    ;;
  --rebuild-markdown)
    exec python3 -m ytx markdown "${@:2}"
    ;;
  --audit)
    exec python3 -m ytx audit "${@:2}"
    ;;
  --doctor)
    exec python3 -m ytx doctor "${@:2}"
    ;;
  --status)
    exec python3 -m ytx status "${@:2}"
    ;;
  --export-jsonl)
    out="${2:-exports/transcripts.jsonl}"
    exec python3 -m ytx export jsonl --out "$out" "${@:3}"
    ;;
  --export-notion)
    echo "Notion export is no longer part of the active workflow." >&2
    echo "Use Obsidian markdown or: python3 -m ytx export jsonl --out exports/transcripts.jsonl" >&2
    exit 2
    ;;
  --help|-h|"")
    show_help
    ;;
  *)
    echo "Unknown legacy command: $1" >&2
    echo >&2
    show_help >&2
    exit 2
    ;;
esac
