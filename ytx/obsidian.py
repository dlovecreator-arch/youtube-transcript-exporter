"""Obsidian vault helpers.

Generates lightweight dashboard notes from db/canonical.json without touching existing
video transcript notes.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .config import DB_FILE, MARKDOWN_DIR, OUT_DIR


def _date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _md_channel_name(channel: str) -> str:
    return channel


def generate_dashboards(output_dir: Path = MARKDOWN_DIR) -> list[Path]:
    """Write Obsidian dashboard/index notes. Returns written paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    db = json.loads(DB_FILE.read_text())
    videos = db.get("videos", [])
    channels = db.get("channels", {})

    by_channel = Counter(v.get("channel") or "Unknown" for v in videos)
    by_year = Counter((v.get("date") or "0000")[:4] for v in videos if v.get("date"))
    guests = Counter(v.get("guest") for v in videos if v.get("guest"))
    tags = Counter(tag for v in videos for tag in v.get("tags", []) if tag)
    md_channels = {p.name for p in output_dir.iterdir() if p.is_dir()}
    out_channels = {p.name for p in OUT_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")} if OUT_DIR.exists() else set()
    missing_md = sorted(out_channels - md_channels)

    written: list[Path] = []

    dashboard = output_dir / "_dashboard.md"
    dashboard.write_text(
        "\n".join([
            "# YouTube Transcript Vault Dashboard",
            "",
            f"_Generated: {_date()}_",
            "",
            "## Snapshot",
            f"- Videos in DB: **{len(videos):,}**",
            f"- Channels in DB: **{len(channels):,}**",
            f"- Markdown channel folders: **{len(md_channels):,}**",
            f"- Raw channel folders: **{len(out_channels):,}**",
            f"- Channels missing markdown folders: **{len(missing_md):,}**",
            "",
            "## Open dashboards",
            "- [[_channels]]",
            "- [[_guests]]",
            "- [[_topics]]",
            "- [[_years]]",
            "- [[_missing_markdown]]",
            "",
            "## Top channels",
            *[f"- [[{_md_channel_name(ch)}/_index|{ch}]]: {count:,} videos" for ch, count in by_channel.most_common(20)],
            "",
            "## Recommended maintenance",
            "```bash",
            "python3 -m ytx status",
            "python3 -m ytx audit --quick --warn-ok",
            "python3 -m ytx fix",
            "```",
            "",
        ]),
        encoding="utf-8",
    )
    written.append(dashboard)

    channels_note = output_dir / "_channels.md"
    channels_note.write_text(
        "# Channels\n\n" + "\n".join(
            f"- [[{_md_channel_name(ch)}/_index|{ch}]]: {count:,} videos"
            for ch, count in by_channel.most_common()
        ) + "\n",
        encoding="utf-8",
    )
    written.append(channels_note)

    guests_note = output_dir / "_guests.md"
    guests_note.write_text(
        "# Guests\n\n" + "\n".join(f"- {guest}: {count:,}" for guest, count in guests.most_common(250)) + "\n",
        encoding="utf-8",
    )
    written.append(guests_note)

    topics_note = output_dir / "_topics.md"
    topics_note.write_text(
        "# Topics / Tags\n\n" + "\n".join(f"- #{tag.replace(' ', '_')}: {count:,}" for tag, count in tags.most_common(250)) + "\n",
        encoding="utf-8",
    )
    written.append(topics_note)

    years_note = output_dir / "_years.md"
    years_note.write_text(
        "# Years\n\n" + "\n".join(f"- {year}: {count:,}" for year, count in sorted(by_year.items(), reverse=True)) + "\n",
        encoding="utf-8",
    )
    written.append(years_note)

    missing_note = output_dir / "_missing_markdown.md"
    missing_note.write_text(
        "# Channels Missing Markdown Folders\n\n"
        + ("\n".join(f"- {ch}" for ch in missing_md) if missing_md else "All raw channel folders have markdown folders.")
        + "\n",
        encoding="utf-8",
    )
    written.append(missing_note)

    return written
