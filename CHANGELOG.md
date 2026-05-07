# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] -- 2026-05-07

Initial public release.

### Added
- Single-command pipeline: `./export.sh --full-pipeline <URL>`
- Canonical JSON database (`db/canonical.json`) as single source of truth
- Obsidian-ready markdown vault with YAML frontmatter (id, title, channel, guest, date, duration, views, tags)
- `CONVENTIONS.md` enforcing one canonical layout
- Folder-layout audit built into `./export.sh --audit`
- Notion exporter (`./export.sh --export-notion`)
- Guest extraction with confidence scores
- Cross-channel duplicate detection
- Support for 8+ channels in production tests
