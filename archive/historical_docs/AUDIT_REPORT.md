# Project Audit Report - 2026-05-12

## Executive Summary
- **Status**: 75% complete with critical data misalignment issues
- **Total videos downloaded**: 28,574 .info.json files
- **Total videos in DB**: 23,257 (5,317 orphaned/unindexed)
- **Total markdown files**: 35,275 (but many for channels not yet ingested)
- **Critical issue**: 11 channels with significant video counts NOT in canonical.json

---

## 🔴 CRITICAL ISSUES

### 1. Missing from Database (HIGH PRIORITY)
These channels have videos downloaded but are NOT in `db/canonical.json`:

| Channel | Videos | Status |
|---------|--------|--------|
| GaryVee | 2,784 | Large, established channel |
| Joe Hudson \| Art of Accomplishment | 497 | Recently added |
| Peter Crone Official | 499 | Recently added |
| The Human Design System w/ Dr. Archers | 349 | Recently added |
| EmilioOrtiz | 333 | Recently added |
| Wake The Fake Up with Chervin Jafarieh | 344 | Recently added |
| Bryan Johnson | 463 | Incomplete download |
| Dan Martell | 82 | Incomplete download |
| Amar Energy | 63 | Recently added |
| VivianeChauvetGalacticHealer | 85 | Recently added |
| Stefan Burns.backup | 3 | Backup/test folder |

**Action needed**: Ingest these channels into canonical.json before markdown generation

---

## 🟡 WARNINGS

### 2. Empty/Test Folders (should be cleaned)
- `Dave Shap/` - 0 videos
- `Indy Dev Dan/` - 0 videos
- `Jordan B. Peterson/` - 0 videos
- `test_bryan/` - 6 test videos

**Action needed**: Remove these folders

### 3. Folder Naming Inconsistencies
- `Joe Hudson ｜ Art of Accomplishment` (full-width pipe ｜)
  - Database might have regular pipe `|`
  - Need to verify exact naming in canonical.json

---

## ✅ HEALTHY SECTIONS

### 4. Fully Synced Channels
65 channels are properly indexed in the database with complete markdown coverage.

---

## 📊 Detailed Inventory

### Downloads Status
- **Total .info.json files**: 28,574
- **Folders in out/**: 75
- **Folders in markdown/**: 67
- **Orphaned files**: ~5,317 (in out/ but not in DB)

### Markdown Status
- **Total .md files**: 35,275
- **Average per channel**: ~527 files/channel

---

## TODO - Fix in Order

- [ ] **Step 1**: Verify folder names in DB (check `Joe Hudson` naming)
- [ ] **Step 2**: Ingest 11 missing channels into canonical.json from their .info.json files
- [ ] **Step 3**: Generate markdown for missing channels
- [ ] **Step 4**: Delete empty test folders (Dave Shap, Indy Dev Dan, Jordan B. Peterson, test_bryan, Stefan Burns.backup)
- [ ] **Step 5**: Run validation script to verify 100% alignment
- [ ] **Step 6**: Commit all changes

---

## Commands to Run

```bash
# Check exact naming
grep -i "joe hudson\|peter crone\|emilio" db/canonical.json | head -3

# Ingest missing channels
python3 src/metadata_extractor.py "out/GaryVee"
python3 src/metadata_extractor.py "out/Bryan Johnson"
# ... etc for each

# Generate missing markdown
python3 src/markdown_generator.py

# Validate alignment
python3 tools/validate_alignment.py
```
