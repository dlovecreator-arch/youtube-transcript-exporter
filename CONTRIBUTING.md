# Contributing

Thanks for considering a contribution! This project tries to be small, focused, and predictable. Please read these notes before opening a PR.

## Ground rules

1. **Read [CONVENTIONS.md](./CONVENTIONS.md) first.** It defines the only correct layout. Don't fight it.
2. **One CLI, one workflow.** Everything goes through `./export.sh`. Don't add side-channel scripts.
3. **Idempotent or it's a bug.** Every step must be safely re-runnable.
4. **No data in the repo.** `out/`, `markdown/`, and `db/canonical.json` are user data and stay gitignored.

## Development setup

```bash
git clone https://github.com/dlovecreator-arch/youtube-transcript-exporter.git
cd youtube-transcript-exporter

# Required: yt-dlp
brew install yt-dlp        # macOS
# or: pip install yt-dlp

# Optional (for Notion sync)
pip install requests

# Smoke-test the CLI
./export.sh --help
```

## Testing your change

There are no unit tests yet (PRs welcome). The current verification flow:

```bash
# Pick a small channel for testing.
./export.sh --full-pipeline https://www.youtube.com/@SOME_SMALL_CHANNEL

# Verify the audit passes with 0 violations.
./export.sh --audit
```

The layout audit at the bottom must report:
- `Non-id-named folders (should be 0): 0`
- `Extra/legacy files in video folders (should be 0): 0`

If your change breaks that, fix it before submitting.

## Style

- Python: standard PEP 8. Use `pathlib`, type hints where helpful.
- Bash: `set -euo pipefail`. No silent failures.
- Markdown: no em dashes (use `--`).
- Commits: conventional-ish (`feat:`, `fix:`, `docs:`, `chore:`).

## Opening a PR

1. Fork, branch from `main`.
2. Run the audit. Make sure layout is clean.
3. Update `CHANGELOG.md` under "Unreleased."
4. Open the PR with a clear description of what changed and why.

## Reporting bugs

Open an issue with:
- What you ran
- What you expected
- What actually happened
- Output of `./export.sh --audit`
