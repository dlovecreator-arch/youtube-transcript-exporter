"""ytx -- unified CLI.

    python -m ytx add <url|file>         # download + extract + markdown
    python -m ytx update                 # re-run for all channels.txt
    python -m ytx audit                  # health report
    python -m ytx status                # quick dashboard
    python -m ytx doctor                 # env check
    python -m ytx transcribe [--limit N] # whisper fallback
    python -m ytx export jsonl [--out path]
    python -m ytx version

Design: keep flags few and friendly. Delegate to existing scripts where
they already work (metadata + markdown), use new modules for the masterpiece
parts (download, transcribe, audit, export).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from . import __version__, audit as audit_mod, doctor as doctor_mod, status as status_mod
from .config import CHANNELS_FILE, REPO_ROOT
from .downloader import DownloadOptions, download_channel, download_from_file


def _run_metadata() -> int:
    return subprocess.call([sys.executable, str(REPO_ROOT / "src" / "metadata_extractor.py")], cwd=REPO_ROOT)


def _run_markdown() -> int:
    return subprocess.call([sys.executable, str(REPO_ROOT / "src" / "markdown_generator.py")], cwd=REPO_ROOT)


def cmd_add(args: argparse.Namespace) -> int:
    opts = DownloadOptions(
        cookies_from_browser=args.cookies_from_browser,
        cookies_file=Path(args.cookies_file) if args.cookies_file else None,
        proxy=args.proxy,
        max_attempts=args.max_attempts,
    )
    target = args.target
    p = Path(target)
    if p.exists() and p.is_file():
        download_from_file(p, opts)
    else:
        download_channel(target, opts)
        # remember it for next `ytx update`
        try:
            existing = CHANNELS_FILE.read_text().splitlines() if CHANNELS_FILE.exists() else []
            if target not in existing:
                with CHANNELS_FILE.open("a") as fh:
                    fh.write(target + "\n")
        except OSError:
            pass

    if args.skip_metadata:
        return 0
    rc = _run_metadata()
    if rc != 0:
        return rc
    if args.skip_markdown:
        return 0
    return _run_markdown()


def cmd_update(args: argparse.Namespace) -> int:
    if not CHANNELS_FILE.exists():
        print("channels.txt missing -- nothing to update", file=sys.stderr)
        return 1
    opts = DownloadOptions(
        cookies_from_browser=args.cookies_from_browser,
        cookies_file=Path(args.cookies_file) if args.cookies_file else None,
        proxy=args.proxy,
    )
    download_from_file(CHANNELS_FILE, opts)
    rc = _run_metadata()
    if rc != 0:
        return rc
    return _run_markdown()


def cmd_audit(args: argparse.Namespace) -> int:
    rep = audit_mod.run()
    out = rep.render()
    print(out)
    if args.write:
        Path(args.write).write_text(out + "\n")
    return 0 if rep.ok else 2


def cmd_status(_: argparse.Namespace) -> int:
    print(status_mod.render(status_mod.collect()))
    return 0


def cmd_doctor(_: argparse.Namespace) -> int:
    checks = doctor_mod.run()
    print(doctor_mod.render(checks))
    return 0 if all(c.ok for c in checks) else 2


def cmd_transcribe(args: argparse.Namespace) -> int:
    from .transcriber import TranscribeOptions, transcribe_all
    opts = TranscribeOptions(model=args.model, language=args.language)
    n = transcribe_all(opts, limit=args.limit)
    print(f"transcribed {n} videos")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    if args.format != "jsonl":
        print(f"unknown format: {args.format}", file=sys.stderr)
        return 2
    from .exporters import export
    out_path = Path(args.out)
    n = export(out_path, include_transcript=not args.no_transcript, channels=args.channel or None)
    print(f"wrote {n} records to {out_path}")
    return 0


def cmd_metadata(_: argparse.Namespace) -> int:
    return _run_metadata()


def cmd_markdown(_: argparse.Namespace) -> int:
    return _run_markdown()


def cmd_version(_: argparse.Namespace) -> int:
    print(__version__)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ytx", description="YouTube to second-brain pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)

    common_dl = lambda sp: (
        sp.add_argument("--cookies-from-browser", help="e.g. chrome, safari, firefox"),
        sp.add_argument("--cookies-file", help="Path to cookies.txt"),
        sp.add_argument("--proxy", help="Proxy URL"),
    )

    a = sub.add_parser("add", help="Add a channel URL or file of URLs")
    a.add_argument("target", help="Channel URL, video URL, or path to a file of URLs")
    a.add_argument("--max-attempts", type=int, default=5)
    a.add_argument("--skip-metadata", action="store_true")
    a.add_argument("--skip-markdown", action="store_true")
    common_dl(a)
    a.set_defaults(func=cmd_add)

    u = sub.add_parser("update", help="Re-run downloads for all channels.txt")
    common_dl(u)
    u.set_defaults(func=cmd_update)

    ad = sub.add_parser("audit", help="Print health/alignment report")
    ad.add_argument("--write", help="Also write to file")
    ad.set_defaults(func=cmd_audit)

    st = sub.add_parser("status", help="Show quick local dataset dashboard")
    st.set_defaults(func=cmd_status)

    d = sub.add_parser("doctor", help="Diagnose environment")
    d.set_defaults(func=cmd_doctor)

    t = sub.add_parser("transcribe", help="Whisper-fill caption-less videos (opt-in)")
    t.add_argument("--model", default="small")
    t.add_argument("--language", default="en")
    t.add_argument("--limit", type=int, default=None)
    t.set_defaults(func=cmd_transcribe)

    e = sub.add_parser("export", help="Export the dataset")
    e.add_argument("format", choices=["jsonl"])
    e.add_argument("--out", default="exports/transcripts.jsonl")
    e.add_argument("--channel", action="append", help="Filter to one or more channels (repeat)")
    e.add_argument("--no-transcript", action="store_true", help="Skip transcript text")
    e.set_defaults(func=cmd_export)

    m = sub.add_parser("metadata", help="Rebuild canonical.json from out/")
    m.set_defaults(func=cmd_metadata)

    md = sub.add_parser("markdown", help="Generate markdown vault from canonical.json")
    md.set_defaults(func=cmd_markdown)

    v = sub.add_parser("version", help="Print ytx version")
    v.set_defaults(func=cmd_version)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
