# Naming Convention Standard - ENFORCE THIS

**Last Updated**: 2026-05-09  
**Status**: ACTIVE - This is the law of the land

## The Rule

**ALL markdown folders MUST match OUT folder names EXACTLY.**

### Example
```
out/Asha Nayaswami/         ← Source of truth
markdown/Asha Nayaswami/    ← MUST match exactly (WITH spaces)
```

**NOT:**
```
markdown/Asha_Nayaswami/    ← WRONG - causes duplicates
markdown/Asha-Nayaswami/    ← WRONG - causes duplicates
```

## Why This Matters

When folders don't match:
- ✗ Duplicates are created (wasted storage)
- ✗ Export tools get confused
- ✗ Obsidian/Notion sync breaks
- ✗ Data consistency fails

## Channel Naming Examples

| OUT folder | Markdown folder | Notes |
|---|---|---|
| `19KEYS NETWORK` | `19KEYS NETWORK` | All caps, with space |
| `Asha Nayaswami` | `Asha Nayaswami` | Title case, with space |
| `André Duqum` | `André Duqum` | Special characters preserved |
| `Suzanne Giesemann - Messages of Hope` | `Suzanne Giesemann - Messages of Hope` | Dashes and spaces preserved |
| `The Human Design System w⧸ Dr. Archers` | `The Human Design System w⧸ Dr. Archers` | Special characters (⧸) preserved |
| `THE REAL ISMAEL PEREZ ` | `THE REAL ISMAEL PEREZ ` | Trailing space (weird but exact) |
| `EmilioOrtiz` | `EmilioOrtiz` | CamelCase, no space |
| `LeeHarrisEnergy` | `LeeHarrisEnergy` | Concatenated, no space |

## Rules for Creating Markdown Folders

When adding a new channel:

1. **Copy the exact channel name from OUT**
   ```bash
   ls out/  # Get the EXACT name
   mkdir "markdown/EXACT_NAME_HERE"
   ```

2. **Never convert to underscores**
   ```bash
   # ✓ DO THIS
   mkdir "markdown/Asha Nayaswami"
   
   # ✗ DON'T DO THIS
   mkdir "markdown/Asha_Nayaswami"
   ```

3. **Never normalize special characters**
   ```bash
   # ✓ Keep accents
   mkdir "markdown/André Duqum"
   
   # ✗ Don't remove accents
   mkdir "markdown/Andre Duqum"
   ```

4. **Verify before generating files**
   ```bash
   ls -la markdown/ | grep "^d"  # Check folder names
   ls -la out/ | grep "^d"       # Compare with out/
   # They should match exactly
   ```

## Automated Check (Do This Before Committing)

```bash
#!/bin/bash
# Check for duplicates
cd markdown
python3 << 'EOF'
import os
channels = os.listdir('.')
normalized = {}
for ch in channels:
    if os.path.isdir(ch):
        norm = ch.lower().replace(' ', '_').replace('-', '_')
        if norm in normalized:
            print(f"DUPLICATE: {ch} and {normalized[norm]}")
        normalized[norm] = ch
EOF
```

## History: Why This Rule Exists

**Problem**: On 2026-05-09, I created 42 markdown channels but with inconsistent naming:
- Some with spaces: `Asha Nayaswami` (447 files)
- Some with underscores: `Asha_Nayaswami` (894 files)
- This created 26+ duplicate channels
- Wasted storage and broke alignment

**Fix**: Unified all to match OUT folder exactly
- Merged 9,100+ files
- Removed all duplicates
- Achieved 100% alignment
- Documented this rule

**Prevention**: This rule now applies to ALL future markdown generation.

## Enforcement

### Before Any Markdown Generation
```bash
# 1. Get OUT channel names
OUT_CHANNELS=$(ls -1 out/)

# 2. Verify markdown names match
for ch in $OUT_CHANNELS; do
    [ ! -d "markdown/$ch" ] && echo "MISSING: $ch"
done

# 3. Check for duplicates
python3 -c "
import os
channels = [d for d in os.listdir('markdown') if os.path.isdir(f'markdown/{d}')]
out_chs = set(os.listdir('out'))
md_chs = set(channels)
if out_chs == md_chs:
    print('✅ ALIGNMENT OK')
else:
    print('❌ MISALIGNMENT')
"
```

### In Scripts

All generation scripts MUST:
1. Read channel names FROM OUT folder
2. Use those names AS-IS for markdown
3. Never modify names (no underscores, no normalization)
4. Verify alignment after generation

## Current State (After Fix)

✅ **42 channels**
✅ **20,901 markdown files**
✅ **100% alignment with OUT**
✅ **Zero duplicates**
✅ **Rule documented and enforced**

---

**This rule is non-negotiable. Duplicates break the entire system.**
