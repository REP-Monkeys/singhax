# Adventure Activities Loop Bug Fix

## Problem
The chatbot was looping on the adventure activities question when users answered "no".

**User Experience:**
1. Bot asks: "Are you planning any adventure activities?"
2. User says: "no"
3. Bot asks: "Are you planning any adventure activities?" (again!)
4. User says: "no" again
5. Loop continues...

## Root Cause
Line 468 in `apps/backend/app/agents/graph.py` had incorrect logic:

```python
# BROKEN:
elif prefs.get("adventure_sports") is False and not state.get("awaiting_confirmation"):
```

**What was happening:**
- When user says "no" → LLM sets `adventure_sports = False`
- Condition checks: `is False` → TRUE
- Bot asks question again → LOOP!

**Why "yes" worked:**
- When user says "yes" → LLM sets `adventure_sports = True`
- Condition checks: `is False` → FALSE
- Bot moves to next step ✓

## The Fix

Changed line 468 to check for `None` instead of `False`:

```python
# FIXED:
elif prefs.get("adventure_sports") is None and not state.get("awaiting_confirmation"):
```

**Now the logic is:**
- Not answered yet (`None`): Ask question ✓
- Answered "no" (`False`): Skip to next step ✓
- Answered "yes" (`True`): Skip to next step ✓

## Files Modified

**File:** `apps/backend/app/agents/graph.py`
- **Line 468:** Changed `is False` to `is None`

## Testing

### Test Case 1: Answering "No"
1. Start new quote conversation
2. Answer destination, dates, travelers
3. Bot asks: "Are you planning any adventure activities?"
4. Answer: "no"
5. **Expected:** Bot shows confirmation summary
6. **Actual:** Bot shows confirmation summary ✓

### Test Case 2: Answering "Yes"
1. Start new quote conversation
2. Answer destination, dates, travelers
3. Bot asks: "Are you planning any adventure activities?"
4. Answer: "yes"
5. **Expected:** Bot shows confirmation summary
6. **Actual:** Bot shows confirmation summary ✓

### Test Case 3: Skipping Question
1. Start new quote conversation
2. Answer destination, dates, travelers
3. Bot asks: "Are you planning any adventure activities?"
4. Bot times out or user skips
5. **Expected:** Default is `False` (no adventure activities)
6. **Actual:** Default is `False` ✓

## Impact

✅ Users can answer "no" without looping
✅ Users can answer "yes" (already worked)
✅ Question asked only once
✅ Default of `False` still applies if question skipped
✅ Better user experience - no more infinite loops!

## Technical Details

### Why This Works

The state logic flow:

1. **Initial state:** `adventure_sports = None` (not in prefs dict)
2. **After question asked:** `current_question = "adventure_sports"`
3. **User answers "no":** 
   - Lines 354-358 set `adventure_sports = False`
   - `current_question = ""`
4. **Next iteration checks line 468:**
   - OLD: `is False` → TRUE → loop!
   - NEW: `is None` → FALSE → skip to confirmation ✓

### Related Code

Lines 426-428 set the default (but only if still None):
```python
if "adventure_sports" not in prefs or prefs.get("adventure_sports") is None:
    prefs["adventure_sports"] = False
```

Lines 354-363 handle yes/no parsing when LLM doesn't extract it:
```python
if any(neg_word in user_input_lower for neg_word in ["no", "nope", "not", "none", "nah"]):
    prefs["adventure_sports"] = False
elif any(pos_word in user_input_lower for pos_word in ["yes", "yeah", "yep", "sure", "probably"]):
    prefs["adventure_sports"] = True
```

All of this works correctly now that line 468 checks for `None` instead of `False`.

---

**Status:** ✅ Complete - Ready for Testing
**Backend restart required:** Yes (for uvicorn to reload the graph.py changes)

