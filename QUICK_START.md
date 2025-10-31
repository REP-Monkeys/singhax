# Quick Start - Claims Intelligence Testing

## Fastest Way to Test

### Option 1: Claims Intelligence Demo Only (30 seconds)

```bash
cd apps/backend
python demo_claims_intelligence.py
```

This runs the demo without starting servers.

---

### Option 2: Full Stack Testing (5 minutes)

**Terminal 1 - Backend:**
```bash
cd apps/backend
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd apps/frontend
npm run dev
```

**Browser:**
```
http://localhost:3000/app/quote
```

**Test Message:**
```
I need insurance for skiing in Japan with my 8-year-old daughter
```

---

## What to Look For

### In Backend Logs:

```
✅ Connected to claims database: 72592 claims available
🔍 Analyzing claims data for Japan...
✅ Risk: high, Tier: elite
```

### In Browser Response:

Look for this section in the bot's quote response:

```
📊 Risk Analysis:
Based on analysis of 4,188 historical claims to Japan...

💡 Based on historical data, we recommend the Elite plan
```

---

## Quick Health Check

```bash
# Backend health
curl http://localhost:8000/health

# Claims DB health
cd apps/backend
python -c "
from app.core.claims_db import check_claims_db_health
print('✅ Claims DB OK' if check_claims_db_health() else '❌ Claims DB DOWN')
"
```

---

**That's it! The claims intelligence automatically appears in quotes.** 🎉
