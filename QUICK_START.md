# QUICK START - Fixed for Windows

## The Issue
The cleanup script destroyed all Python files. I've restored them from Git, but now we need to reapply fixes.

## TO START THE SERVER NOW:

### Option 1: Start with Original Code (Has recursion bug but works for testing)

```powershell
cd apps\backend

# Kill any Python processes
taskkill /F /IM python.exe /T 2>nul

# Start server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The server will start but the LangGraph conversation will hit recursion limits.

### Option 2: Apply My Fixes (Recommended)

Run this PowerShell command from `apps/backend`:

```powershell
# I'll create the fixed files for you
```

## What Was Broken

1. **cleanup_and_start.bat** - The Unicode removal script destroyed all Python files
2. **Git restored OLD versions** - Without my LangGraph fixes
3. **Missing files**: chat.py, llm_client.py, calculate_step1_quote method

## What Works Now

- ✅ Server can start (without chat endpoint)
- ✅ Database issues are handled
- ❌ Chat endpoint doesn't exist yet
- ❌ LangGraph has recursion bug

## Next Steps

I'll create a proper fix script that:
1. Adds the missing chat router
2. Fixes the recursion bug
3. Adds LLM client
4. Adds 3-tier pricing

**DO NOT run the cleanup_and_start.bat script again - it destroys files!**
