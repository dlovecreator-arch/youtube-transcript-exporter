---
id: dQw4w9WgXcQ
title: "Example Episode: How to Read This Vault"
slug: example-episode-how-to-read-this-vault
channel: "Example Channel"
guest: "Sample Guest"
guest_confidence: 0.95
date: 2025-01-15
duration_seconds: 1234
duration_human: "20:34"
views: 50000
likes: 1200
tags: [example, documentation, demo]
category: Education
url: https://youtu.be/dQw4w9WgXcQ
word_count: 4823
reading_time_minutes: 24
token_count_estimate: 6100
---

# Example Episode: How to Read This Vault

> **Guest**: Sample Guest -- _confidence 0.95_
> **Channel**: Example Channel
> **Published**: 2025-01-15 -- 20:34
> **YouTube**: https://youtu.be/dQw4w9WgXcQ

## Transcript

This is a sample of what every generated `.md` file looks like.

The YAML frontmatter at the top is consumed by:

- **Obsidian Dataview** -- query by tag, guest, channel, or date
- **Notion API** -- fields map 1:1 to a Notion database
- **Any LLM RAG pipeline** -- structured context plus full text in one file

The body below the frontmatter is the cleaned transcript text, with caption
duplicates removed, timestamps stripped, and HTML tags cleaned.

You can search across thousands of these files in Obsidian with a single
Dataview query, for example:

```dataview
TABLE channel, guest, date FROM "markdown" WHERE contains(tags, "astrology")
SORT date DESC
```

(The full transcript continues here for thousands of words in real files.)
