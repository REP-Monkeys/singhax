# Plan: Make Date Parsing Flexible to Accept Any Format

## Problem Diagnosis

The chatbot loops on the departure date question because:

1. User provides a date (e.g., "December 10, 2025", "12/10/2025", "Dec 10")
2. LLM extracts it but may keep original format or convert it
3. `parse_date_safe()` only accepts `YYYY-MM-DD` format (strict `strptime`)
4. Parsing fails → returns `None`
5. Date not stored, `current_question` not cleared
6. Bot asks again → **INFINITE LOOP**

## Solution

Make `parse_date_safe()` flexible to accept multiple date formats using `dateparser` library.

## Implementation Plan

### Step 1: Add dateparser to requirements
**File:** `apps/backend/requirements.txt`

Add after line 53 (python-dateutil):
```
dateparser>=1.1.8
```

### Step 2: Update parse_date_safe() function
**File:** `apps/backend/app/agents/graph.py`

**Current implementation (lines 93-105):**
```python
def parse_date_safe(date_string: str) -> Optional[date]:
    """Safely parse date string to date object.
    
    Args:
        date_string: Date in YYYY-MM-DD format
        
    Returns:
        date object if parsing succeeds, None otherwise
    """
    try:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except:
        return None
```

**New flexible implementation:**
```python
def parse_date_safe(date_string: str) -> Optional[date]:
    """Safely parse date string to date object with flexible format support.
    
    Accepts multiple formats:
    - YYYY-MM-DD (2025-12-15)
    - MM/DD/YYYY (12/15/2025)
    - DD/MM/YYYY (15/12/2025)
    - Natural language (December 15, 2025, Dec 15, 2025)
    - Relative dates (tomorrow, next week, in 3 days)
    
    Args:
        date_string: Date in any common format
        
    Returns:
        date object if parsing succeeds, None otherwise
    """
    import dateparser
    
    try:
        # First try standard YYYY-MM-DD for efficiency
        if isinstance(date_string, str) and len(date_string) == 10 and date_string.count('-') == 2:
            try:
                return datetime.strptime(date_string, "%Y-%m-%d").date()
            except:
                pass
        
        # Use dateparser for flexible parsing
        settings = {
            'PREFER_DATES_FROM': 'future',  # Prefer future dates for travel
            'RELATIVE_BASE': datetime.now(),
            'RETURN_AS_TIMEZONE_AWARE': False,
        }
        
        parsed = dateparser.parse(date_string, settings=settings)
        
        if parsed:
            return parsed.date()
        
        return None
        
    except Exception as e:
        print(f"   ⚠️ Date parsing error: {e}")
        return None
```

### Step 3: Add import at top of file
**File:** `apps/backend/app/agents/graph.py`

Add after existing imports (around line 10):
```python
import dateparser
```

### Step 4: Test the implementation

**Test cases to verify:**
1. "2025-12-15" → December 15, 2025
2. "12/15/2025" → December 15, 2025
3. "December 15, 2025" → December 15, 2025
4. "Dec 15" → December 15, current/next year
5. "tomorrow" → tomorrow's date
6. "next Friday" → next Friday's date
7. "in 2 weeks" → 2 weeks from now

## Benefits

✅ Accepts dates in any common format
✅ Handles natural language ("tomorrow", "next week")
✅ Prevents infinite loops from unparseable dates
✅ Better user experience - no format restrictions
✅ Still fast for standard YYYY-MM-DD format
✅ Future-biased for travel dates

## Installation

After updating requirements.txt:
```bash
cd apps/backend
pip install dateparser>=1.1.8
```

Or full reinstall:
```bash
pip install -r requirements.txt
```

## Impact on Code

- Only changes: `parse_date_safe()` function
- All existing code calling it works unchanged
- Same return type: `Optional[date]`
- Graceful fallback if parsing fails
- No breaking changes

---

**Ready to implement?**

