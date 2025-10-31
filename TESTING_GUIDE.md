# Testing Guide - Claims Intelligence System

**Quick reference for testing frontend and backend**

---

## 🚀 Quick Start (Local Development)

### Backend Testing

**1. Start Backend Server:**

```bash
# Navigate to backend directory
cd apps/backend

# Option 1: Using uvicorn directly
uvicorn app.main:app --reload --port 8000

# Option 2: Using python -m
python -m uvicorn app.main:app --reload --port 8000

# Backend will start at: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**2. Test Claims Intelligence Demo:**

```bash
# In apps/backend directory
python demo_claims_intelligence.py
```

**Expected Output:**
```
✅ Connected to claims database: 72592 claims available
🚀 Claims Intelligence System - Demo

======================================================================
DEMO: Skiing Trip to Japan
======================================================================

✅ Found 4,188 historical claims
💰 Average claim: $1,358.37
⚠️ Risk Score: 7.5/10 (HIGH)
✅ Recommended Tier: ELITE
```

**3. Test Backend API:**

```bash
# In another terminal
curl http://localhost:8000/health
# Should return: {"status":"healthy","version":"1.0.0"}

# Check API docs
open http://localhost:8000/docs
```

**4. Test Claims Database Connection:**

```bash
cd apps/backend
python -c "
from app.core.claims_db import check_claims_db_health
print('✅ Claims DB healthy' if check_claims_db_health() else '❌ Claims DB unavailable')
"
```

---

### Frontend Testing

**1. Start Frontend Server:**

```bash
# Navigate to frontend directory
cd apps/frontend

# Install dependencies (if not done already)
npm install

# Start development server
npm run dev

# Frontend will start at: http://localhost:3000
```

**2. Open Browser:**

```
http://localhost:3000
```

**3. Test Flow:**

1. Navigate to Quote page (`/app/quote`)
2. Type message: **"I need insurance for skiing in Japan with my 8-year-old"**
3. Watch conversation unfold
4. **Look for claims intelligence in the quote response!**

---

## 🧪 End-to-End Test Scenario

### Demo Test: Japan Skiing Trip

**Step-by-step:**

1. **Start Backend:**
   ```bash
   cd apps/backend
   python -m uvicorn app.main:app --reload --port 8000
   ```

2. **Start Frontend:**
   ```bash
   cd apps/frontend
   npm run dev
   ```

3. **Open Browser:** `http://localhost:3000/app/quote`

4. **Send Test Message:**
   ```
   I'm planning a skiing trip to Japan next month with my 8-year-old daughter
   ```

5. **Expected Bot Responses:**

   **First Response:**
   ```
   Great! I'd love to help you with travel insurance for your trip to Japan. 
   Let me gather a few details about your trip...
   ```

   **Bot collects:**
   - Departure date
   - Return date
   - All travelers and ages
   - Adventure sports confirmation

   **Final Quote Response (with Claims Intelligence):**
   ```
   Great! Here are your travel insurance options for Japan:

   🌟 Standard Plan: $210 SGD
   ⭐ Elite Plan: $378 SGD
   💎 Premier Plan: $525 SGD

   📊 Risk Analysis:
   Based on analysis of 4,188 historical claims to Japan, I've identified 
   some important considerations for your trip. Japan has an average claim 
   amount of $1,358, with 95th percentile reaching $3,350. Given you're 
   planning skiing (an adventurous activity), this suggests elevated risk...

   💡 Based on historical data, we recommend the Elite plan for optimal 
   coverage.
   ```

---

## 🐍 Python Unit Tests

**Run Backend Tests:**

```bash
cd apps/backend

# Run all tests
python -m pytest tests/ -v

# Run claims intelligence tests only
python -m pytest tests/test_claims_intelligence.py -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

**Expected Test Results:**

```
tests/test_claims_intelligence.py::TestClaimsIntelligenceService::test_get_destination_stats_japan PASSED
tests/test_claims_intelligence.py::TestClaimsAnalyzer::test_calculate_risk_score_high_risk PASSED
tests/test_claims_intelligence.py::TestNarrativeGenerator::test_generate_risk_narrative PASSED
```

---

## 🌐 API Testing (Postman/curl)

**Health Check:**

```bash
curl http://localhost:8000/health
```

**Chat Endpoint:**

```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need insurance for skiing in Japan",
    "session_id": "test-123"
  }'
```

**Watch for Claims Intelligence in Response:**

Look for these fields in the JSON response:
- `claims_insights` - Full risk analysis data
- `risk_narrative` - LLM-generated narrative

---

## 🔍 Debugging Tips

### Backend Issues

**Problem: Claims database connection fails**

```bash
# Check if database is accessible
cd apps/backend
python -c "
import psycopg2
conn = psycopg2.connect(
    host='hackathon-db.ceqjfmi6jhdd.ap-southeast-1.rds.amazonaws.com',
    port=5432,
    database='hackathon_db',
    user='hackathon_user',
    password='[PASSWORD]'
)
print('✅ Connection works')
"
```

**Problem: LLM not generating narratives**

```bash
# Test LLM client
python -c "
from app.agents.llm_client import GroqLLMClient
client = GroqLLMClient()
result = client.generate('Test prompt', max_tokens=50)
print(f'✅ LLM works: {result[:50]}')
"
```

**Problem: No claims intelligence in response**

- Check logs for: `🔍 Analyzing claims data for...`
- Check if `claims_insights` appears in state
- Verify `ENABLE_CLAIMS_INTELLIGENCE=true` in .env

---

### Frontend Issues

**Problem: Chat not loading**

```bash
# Check if backend is running
curl http://localhost:8000/health

# Check browser console for errors
# Press F12 in browser
```

**Problem: Claims narrative not showing**

- Check Network tab in browser DevTools
- Look for `/api/v1/chat/message` response
- Verify response includes `claims_insights` field

---

## 📊 Monitoring During Tests

**Backend Logs:**

Watch for these log messages:
```
✅ Connected to claims database: 72592 claims available
🔍 Analyzing claims data for Japan...
✅ Risk: high, Tier: elite
```

**Frontend Network:**

Monitor `/api/v1/chat/message` POST requests:
- Response time should be < 5 seconds
- Response should include `claims_insights`

---

## ✅ Success Criteria

**Backend:**

- [ ] Server starts without errors
- [ ] `/health` endpoint returns 200
- [ ] Demo script runs successfully
- [ ] Claims database queries return data
- [ ] LLM narrative generation works (or falls back gracefully)

**Frontend:**

- [ ] Chat interface loads
- [ ] Message sends successfully
- [ ] Bot responds within 10 seconds
- [ ] Claims intelligence appears in quote response
- [ ] Risk narrative displayed to user

**End-to-End:**

- [ ] User can complete full quote flow
- [ ] Claims narrative enhances quote presentation
- [ ] Tier recommendation is clear and compelling
- [ ] No errors in browser console
- [ ] No errors in backend logs

---

## 🎯 Quick Test Commands

**One-liner test:**

```bash
# Backend
cd apps/backend && python demo_claims_intelligence.py && echo "✅ Claims Intelligence working"

# Frontend  
cd apps/frontend && npm run dev &
sleep 5 && curl http://localhost:3000 && echo "✅ Frontend running"
```

**Integration test:**

```bash
# Terminal 1: Backend
cd apps/backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd apps/frontend
npm run dev

# Browser: http://localhost:3000/app/quote
# Test message: "skiing in Japan with my 8-year-old"
```

---

## 🐛 Common Issues

### Issue: "Claims database not initialized"

**Fix:** Check `.env` file has `CLAIMS_DATABASE_URL` set correctly

### Issue: "No module named app"

**Fix:** Run from `apps/backend` directory, not root

### Issue: Frontend can't connect to backend

**Fix:** Verify backend running on port 8000, check CORS settings

### Issue: LLM narrative is fallback only

**Fix:** Verify `GROQ_API_KEY` in `.env`, check API quota

---

## 📈 Performance Benchmarks

**Expected Timings:**

- Claims DB query: ~30ms
- Risk calculation: ~10ms
- LLM narrative: ~2-5 seconds
- **Total added latency: ~2-5 seconds**

---

**Happy Testing! 🚀**

