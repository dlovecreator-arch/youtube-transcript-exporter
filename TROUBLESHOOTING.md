# Troubleshooting

Start here: `python3 -m ytx doctor && python3 -m ytx audit`. Most problems are visible from those two commands.

## Cheat sheet

| Symptom | First fix |
|---|---|
| Channel only downloads 8 videos | Tool auto-retries with root URL. If still bad, use the channel ID URL or `--cookies-from-browser` |
| `HTTP Error 429: Too Many Requests` | `ytx add <url> --cookies-from-browser chrome`, slow down with `--sleep-requests 3`, or VPN |
| `Sign in to confirm you're not a bot` | Cookies-from-browser is the fastest fix |
| `yt-dlp` errors after a YouTube site change | `yt-dlp -U` or `brew upgrade yt-dlp` |
| `Bad file descriptor` in detached/background runs | Already handled in `export.sh` (stdin redirected). For new scripts, redirect `stdin=subprocess.DEVNULL` |
| `out/` has @handle or UCxxx folders | Auto-quarantined to `_channel_meta/` by the downloader. Safe to ignore |
| Partial `.part` files | Quarantined to `.trash/parts/` by cleanup; delete `.trash/` when you've verified |
| Stray `.mp4` files in `out/` | Should not happen with default flags. If they appear: `find out -name '*.mp4' -delete` |
| `faster_whisper` install fails | Needs ffmpeg dev headers; see INSTALL.md |
| Hung downloads | Adaptive timeout will kill after 10/60/120/240 min. Re-run; the archive makes it resume from where you stopped |

## Rate limiting (the big one)

YouTube rate-limits aggressive bulk extraction. Symptoms: hangs, repeated 429s, captcha pages, "sign in to confirm" errors.

In rough order of effectiveness:

1. **Cookies from your logged-in browser**:
   ```bash
   python3 -m ytx add <url> --cookies-from-browser chrome
   ```
   You authenticate as yourself. Far higher per-account rate limits.

2. **VPN / different IP**. Especially helpful after a hard block.

3. **Slow down**:
   ```bash
   python3 -m ytx add <url> --proxy http://localhost:1080
   # plus, in code or env, increase sleep_requests / sleep_interval
   ```

4. **Run during off-peak hours** (US night, your evening).

5. **Smaller batches**: split channels.txt into chunks and run sequentially.

## "I added the same channel twice"

It's idempotent. yt-dlp's `--download-archive db/downloaded.txt` skips already-downloaded videos. The metadata extractor dedupes by `id`. You can also run cleanup tools:

```bash
python3 tools/merge_channels.py --dry-run    # show plan
python3 tools/merge_channels.py              # execute
```

## "My DB and `out/` disagree"

```bash
python3 -m ytx audit --write logs/audit.md
```

Common fixes:
- Channel in `out/` but not DB: `python3 -m ytx metadata` (rebuilds canonical.json)
- Channel in DB but no markdown: `python3 -m ytx markdown`
- Trailing-space folder name: rename it manually

## "I want to start over for one channel"

Safest move:

```bash
mkdir -p .trash
mv "out/Channel Name" ".trash/"
mv "markdown/Channel Name" ".trash/"

# Remove that channel's lines from db/downloaded.txt if you want a true re-download
grep -v "^youtube " db/downloaded.txt > /tmp/da && mv /tmp/da db/downloaded.txt

python3 -m ytx add https://www.youtube.com/@channelname
```

## "Whisper output looks empty"

- Confirm the audio downloaded: look in the video's folder for a `_whisper_audio.opus` (if cleanup ran, it's gone; that's normal).
- Check the logs: `tail -50 logs/ytx.jsonl | grep transcribe`
- Try a bigger model: `--model medium`

## Logs

```bash
tail -100 logs/ytx.jsonl              # structured JSON events
ls archive/logs/yt_download_*.log     # legacy download logs
python3 -m ytx audit                  # human-readable summary
```

## Reporting bugs

Include:

1. `python3 -m ytx doctor` output
2. `python3 -m ytx audit` output
3. `yt-dlp --version`
4. The exact URL that failed
5. Last ~50 lines of `logs/ytx.jsonl`

Open an issue at https://github.com/dlovecreator-arch/youtube-transcript-exporter/issues
