# Deprecation Warnings Fix Guide

## Summary

The codebase currently has deprecation warnings from Pydantic V2 and SQLAlchemy 2.0 migrations. These are **non-critical warnings** that:
- ✅ **Won't cause merge conflicts**
- ✅ **Won't break functionality** (code works fine)
- ⚠️ **Should be fixed** for future compatibility

## Warnings Status

### ✅ Already Fixed:
1. **`app/core/config.py`** - Updated to use `ConfigDict` instead of `class Config:`
2. **`app/core/db.py`** - Updated to use `sqlalchemy.orm.declarative_base`

### ⚠️ Remaining (Optional):
- 8 schema files in `app/schemas/` still use `class Config:` pattern
- These can be fixed incrementally or left as-is (they're just warnings)

## How to Fix Schema Files (Optional)

### Pattern:
**Before (Pydantic V1):**
```python
class ChatMessageRequest(BaseModel):
    session_id: str
    message: str
    
    class Config:
        from_attributes = True
        json_schema_extra = {"example": {...}}
```

**After (Pydantic V2):**
```python
from pydantic import ConfigDict

class ChatMessageRequest(BaseModel):
    session_id: str
    message: str
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {...}}
    )
```

### Files to Update (if desired):
- `app/schemas/chat.py` (6 instances)
- `app/schemas/user.py` (1 instance)
- `app/schemas/traveler.py` (1 instance)
- `app/schemas/trip.py` (1 instance)
- `app/schemas/rag.py` (1 instance)
- `app/schemas/quote.py` (1 instance)
- `app/schemas/policy.py` (1 instance)
- `app/schemas/claim.py` (1 instance)

## Priority

**Low Priority** - These are deprecation warnings, not errors:
- Code functions correctly
- No merge conflicts
- Can be fixed incrementally
- Libraries still support old pattern (for now)

## Recommendation

1. **For immediate development:** Leave schema warnings as-is (already fixed the critical ones)
2. **For production readiness:** Fix schema files incrementally when touching them
3. **For clean slate:** Create a separate PR to fix all schema warnings at once

## Merge Impact

**No conflicts expected** - These are:
- Style/syntax changes only
- No functional changes
- Backward compatible
- Can be merged independently

