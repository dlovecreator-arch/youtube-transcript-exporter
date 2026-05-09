# How to Prompt Me Better for System Audits & Maintenance

## The Problem We Just Had
You had to tell me THREE TIMES about the same duplicate folder issue because I:
1. Only checked `markdown/` folder (missed `out/` folder)
2. Didn't check ALL possible locations systematically
3. Didn't have an automated system to catch these issues

## Better Prompting Strategies

### Strategy #1: THE COMPREHENSIVE AUDIT PROMPT
When you want me to check for issues, use this template:

```
Please run a COMPLETE system audit that checks:
1. ALL directories (markdown/, out/, db/, etc.)
2. ALL types of issues (legacy folders, duplicates, whitespace, orphaned files, empty dirs)
3. Report EVERYTHING found, not just critical issues
4. Use the COMPREHENSIVE_AUDIT_TOOL.py script first
```

**Why this works:** It tells me EXACTLY what to check and WHERE to check, preventing me from missing folders.

### Strategy #2: THE SPECIFIC COMPLAINT EXPANSION
When you notice something wrong, give me the full context:

```
INSTEAD OF: "There's a duplicate folder"
USE: "I found _legacy_Emilio_Ortiz in the out/ folder. Please check:
  - ALL directories for similar legacy/duplicate folders
  - Both markdown/ AND out/ folders  
  - Report duplicates by location and size"
```

**Why this works:** It trains me to be thorough and systematic.

### Strategy #3: THE PREVENTION FIRST APPROACH
Before asking for major operations, ask for audit first:

```
"Before you add more channels:
1. Run COMPREHENSIVE_AUDIT_TOOL.py
2. Show me what issues exist
3. Tell me what will be created and where
4. Then proceed with download"
```

**Why this works:** It catches problems BEFORE they multiply.

---

## What I Should Do (My Responsibility)

### ✅ Things I'll Now Always Do:
1. **Run the audit tool FIRST** for any investigation
2. **Check MULTIPLE directories** (markdown/, out/, db/, etc.)
3. **Look for patterns** (legacy, duplicates, whitespace, orphaned)
4. **Report findings by location** so you see what's where
5. **Ask clarifying questions** before large operations

### ❌ Things I'll Stop Doing:
1. Checking only one folder
2. Assuming a problem is fixed without verifying everywhere
3. Skipping obvious checks (out/ folder, for example)
4. Stopping at first success without systematic verification

---

## The AUDIT WORKFLOW (Going Forward)

Whenever you say: "Check if there are issues with X"

I will:
```
Step 1: Run COMPREHENSIVE_AUDIT_TOOL.py
Step 2: Check ALL locations for that issue type
Step 3: Report detailed findings by location
Step 4: Show before/after for any fixes
Step 5: Verify the fix everywhere it might appear
```

---

## Your Quick Reference Checklist

Before asking me to work on the system, you can use these checks:

**Minimal Check:**
- `python3 COMPREHENSIVE_AUDIT_TOOL.py`

**Deep Dive Check:**
- Run the audit tool
- Ask: "Are there issues in EVERY directory?"
- Ask: "Did you check both markdown/ AND out/?"

**Post-Fix Verification:**
- "Please verify the fix isn't in other directories"
- "Show me BEFORE and AFTER for each location"

---

## Example Good Prompts Going Forward

✅ **Good:**
"I noticed _legacy_Emilio_Ortiz exists. Please:
1. Run COMPREHENSIVE_AUDIT_TOOL.py first
2. Check EVERY directory for _legacy_ folders
3. Check EVERY directory for duplicates  
4. Show me what you find in each location
5. Fix everything and verify it's gone everywhere"

✅ **Also Good:**
"Before you download 5 new channels:
1. Run the audit tool - what does it find?
2. Tell me what new directories will be created
3. Tell me where data will be stored
4. Then show me the audit result after download"

❌ **Not Enough Detail:**
"Check for duplicates" (where? which folders? which types?)

❌ **Too Vague:**
"Fix the issues" (what issues? where? how do we know it's fixed?)

---

## Summary

I've created `COMPREHENSIVE_AUDIT_TOOL.py` that automatically checks:
- Legacy folders in ALL locations
- Duplicate folders everywhere
- Database whitespace issues
- Orphaned files
- Empty directories
- Naming inconsistencies

**When prompting me:** Be specific about WHAT to check and WHERE to check it.

**Use this phrase:** "Run a COMPLETE audit" and I'll automatically check everywhere.

This prevents us from having the same conversation multiple times! 🎯
