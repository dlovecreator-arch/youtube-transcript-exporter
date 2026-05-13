#!/usr/bin/env bash
# Smoke test for ytx -- end-to-end on one small video. Designed to be < 60s.
# Used by CI and as a local sanity check after changes.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'
pass() { echo -e "${GREEN}PASS${NC} $*"; }
fail() { echo -e "${RED}FAIL${NC} $*"; exit 1; }

echo "[1/10] ytx version"
python3 -m ytx version >/dev/null || fail "ytx version"
pass "ytx version"

echo "[2/10] ytx doctor"
python3 -m ytx doctor >/dev/null || fail "ytx doctor"
pass "ytx doctor (optional deps are warnings)"

echo "[3/10] importable modules"
python3 -c "from ytx import audit, downloader, transcriber, doctor, exporters" || fail "import"
pass "modules import"

echo "[4/10] audit module runs"
python3 -c "from ytx import audit; audit.run()" >/dev/null || fail "audit"
pass "audit runs"

echo "[5/10] yt-dlp available"
yt-dlp --version >/dev/null 2>&1 || fail "yt-dlp not installed"
pass "yt-dlp available"

echo "[6/10] downloader builds argv"
python3 -c "
from ytx.downloader import DownloadOptions, _build_argv
argv = _build_argv('https://youtu.be/dQw4w9WgXcQ', DownloadOptions(), 1)
assert '--download-archive' in argv, 'archive flag missing'
assert '--write-info-json' in argv, 'info-json flag missing'
assert '--no-abort-on-error' in argv, 'no-abort flag missing'
" || fail "argv build"
pass "downloader argv shape"

echo "[7/10] exporter dry-run (no transcripts needed)"
python3 -c "
from ytx.exporters import _vtt_to_text
sample = '''WEBVTT
Kind: captions
Language: en

00:00:00.000 --> 00:00:02.000
Hello world

00:00:02.000 --> 00:00:04.000
Hello world

00:00:04.000 --> 00:00:06.000
Goodbye'''
out = _vtt_to_text(sample)
assert 'Hello world' in out and 'Goodbye' in out, out
assert out.count('Hello world') == 1, 'dedup failed: ' + out
" || fail "vtt parsing"
pass "vtt parse + dedup"

echo "[8/10] ytx quick audit JSON is parseable"
python3 -m ytx audit --quick --json --warn-ok | python3 -c "import json,sys; d=json.load(sys.stdin); assert 'videos_in_db' in d"
pass "quick audit JSON"

echo "[9/10] ytx fix dry-run works"
python3 -m ytx fix >/dev/null || fail "ytx fix"
pass "fix dry-run"

echo "[10/10] VTT chunk parser removes progressive-caption duplicates"
python3 -c "
from ytx.exporters import parse_vtt_segments
vtt='''WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nhello<00:00:00.5><c> world</c>\n\n00:00:01.000 --> 00:00:02.000\nhello world\n\n00:00:02.000 --> 00:00:03.000\nhello world again\n'''
segs=parse_vtt_segments(vtt)
text=' '.join(s.text for s in segs)
assert text == 'hello world again', text
" || fail "chunk parser"
pass "chunk parser"

echo
echo "${GREEN}ALL SMOKE TESTS PASSED${NC}"
