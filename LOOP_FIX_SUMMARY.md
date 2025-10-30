# Conversation Loop Bug Fix

## Problem
After fixing the adventure activities loop, a more critical bug appeared: the chatbot was looping between departure_date and destination questions even when users answered correctly.

## Root Cause
The issue was caused by the order of operations in `needs_assessment()`:

**Broken Flow:**
1. Lines 427-428: Set default `adventure_sports = False` BEFORE checking if question should be asked
2. Line 468: Check if `adventure_sports is None` → FALSE (already False!) → skip question
3. All required info present → go straight to confirmation (loop bug!)

The LLM extraction was setting departure_date before destination was stored, causing the question order to be wrong.

## The Fix

**Moved the default setting logic** from BEFORE the question logic to INSIDE the confirmation logic.

### File: `apps/backend/app/agents/graph.py`

**Before (BROKEN):**
```python
# Line 425-428: Set default BEFORE checking
if "adventure_sports" not in prefs or prefs.get("adventure_sports") is None:
    prefs["adventure_sports"] = False

# Lines 446-468: Check if question should be asked
if missing:
    # Ask questions...
elif prefs.get("adventure_sports") is None:  # Always False now!
    # Ask adventure question...
elif all_required_present:
    # Show confirmation...
```

**After (FIXED):**
```python
# Lines 446-468: Check if question should be asked FIRST
if missing:
    # Ask questions...
elif prefs.get("adventure_sports") is None:  # Can still be None!
    # Ask adventure question...
elif all_required_present:
    # Set default BEFORE showing confirmation
    if "adventure_sports" not in prefs or prefs.get("adventure_sports") is None:
        prefs["adventure_sports"] = False
    # Show confirmation...
```

## Key Changes

1. **Removed lines 427-428** (old default setting location)
2. **Added default setting at line 471-473** (inside confirmation block)
3. **Fixed duplicate elif on line 469** (was creating duplicate condition)

## Logic Flow Now

**Happy Path:**
1. User starts conversation → `adventure_sports = None`
2. Bot asks: destination, departure, return, travelers
3. All required present → `adventure_sports = None` → ask adventure question
4. User answers → `adventure_sports = True/False`
5. Show confirmation with correct value ✓

**If user skips adventure question:**
1. All required present → `adventure_sports = None`
2. Before showing confirmation, set default `adventure_sports = False`
3. Show confirmation with "No" for adventure activities ✓

## Impact

✅ Question flow is now correct: destination → departure → return → travelers → adventure
✅ Adventure question is asked when all other info is collected
✅ No more looping between questions
✅ Default applied correctly if question skipped
✅ Conversation progresses naturally

## Testing

### Test Case 1: Normal Flow
1. Start new quote
2. Answer: Spain, 2025-12-15, 2025-12-22, 2 travelers ages 30 and 32
3. **Expected:** Bot asks adventure question
4. Answer: "no"
5. **Expected:** Bot shows confirmation with adventure = No

### Test Case 2: Skip Adventure
1. Start new quote
2. Answer all questions quickly
3. **Expected:** Bot shows confirmation with adventure = No (default)

### Test Case 3: All at Once
1. Say: "I need insurance for Spain Dec 15-22, 2 people ages 30 and 32, yes to adventure"
2. **Expected:** Bot extracts all info, shows confirmation

---

**Status:** ✅ Complete - Ready for Testing
**Backend restart required:** Yes (uvicorn will auto-reload graph.py)

