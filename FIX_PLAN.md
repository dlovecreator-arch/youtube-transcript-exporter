# Fix Plan - May 12, 2026

## Phase 1: Rename Folders to Match DB Names
These folders have videos in DB but with different names:

```
GaryVee → Gary Vaynerchuk
EmilioOrtiz → Emilio Ortiz
Peter Crone Official → Peter Crone
Amar Energy → Amar
Viviane ChauvetGalacticHealer → Viviane Chauvet Arcturian Ambassador
Joe Hudson ｜ Art of Accomplishment → Joe Hudson | Art of Accomplishment (fix pipe)
The Human Design System w⧸ Dr. Archers → The Human Design System w/ Dr. Archers (fix slash)
```

## Phase 2: Delete Empty/Test Folders
- Dave Shap (empty)
- Indy Dev Dan (empty)
- Jordan B. Peterson (empty)
- test_bryan (test data)
- Stefan Burns.backup (backup)

## Phase 3: Add Missing Channels to DB
These need to be extracted from .info.json files and added to canonical.json:

- Bryan Johnson (463 videos)
- Dan Martell (82 videos)
- Wake The Fake Up with Chervin Jafarieh (344 videos)

## Phase 4: Regenerate Markdown
- Run markdown generator for renamed channels
- Run markdown generator for newly added channels

## Phase 5: Validate
- Verify all out/ folders have matching markdown/ folders
- Verify all DB channels have at least one video
- Count total videos and markdown files
