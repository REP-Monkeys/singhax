# Manual Testing Guide for ConvoTravelInsure

This guide provides step-by-step instructions for manually testing all features of the ConvoTravelInsure application.

---

## 🚀 Prerequisites

### 1. Start the Backend Server

```bash
cd apps/backend

# Option 1: With uvicorn directly
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Option 2: Using Docker (if configured)
docker-compose up backend

# Verify server is running
curl http://localhost:8000/health
# Expected: {"status": "healthy", "version": "1.0.0"}
```

### 2. Start the Database (if needed)

```bash
# Using Docker
docker-compose up -d db

# Run migrations
cd apps/backend
alembic upgrade head
```

### 3. Set Environment Variables

Ensure `.env` file exists with:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/convo_travel_insure
GROQ_API_KEY=your-groq-api-key  # Optional but recommended
SECRET_KEY=your-secret-key
```

---

## 📋 Testing Checklist

### ✅ 1. API Health & Documentation

#### Test 1.1: Root Endpoint
```bash
curl http://localhost:8000/
```
**Expected:**
```json
{
  "message": "Welcome to ConvoTravelInsure",
  "version": "1.0.0",
  "docs": "/docs"
}
```

#### Test 1.2: Health Check
```bash
curl http://localhost:8000/health
```
**Expected:** `{"status": "healthy", "version": "1.0.0"}`

#### Test 1.3: Chat Service Health
```bash
curl http://localhost:8000/api/v1/chat/health
```
**Expected:** `{"status": "healthy", "service": "chat"}`

#### Test 1.4: API Documentation
- Open browser: `http://localhost:8000/docs`
- Should show Swagger UI with all endpoints
- Check that all 9 routers are listed

---

### ✅ 2. Authentication Endpoints

#### Test 2.1: User Registration
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "name": "Test User",
    "password": "testpassword123"
  }'
```
**Expected:**
- Status: `201 Created`
- Response includes user ID, email, name
- `is_verified: false`

#### Test 2.2: User Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "testpassword123"
  }'
```
**Expected:**
- Status: `200 OK`
- Response includes `access_token` and `token_type: "bearer"`
- **Save the token for authenticated requests**

#### Test 2.3: Get Current User (Authenticated)
```bash
# Replace <token> with token from login
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <token>"
```
**Expected:**
- Status: `200 OK`
- Returns user information

**Test Invalid Token:**
```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer invalid-token"
```
**Expected:** Status `401 Unauthorized`

---

### ✅ 3. Chat/Conversation Endpoints

#### Test 3.1: Basic Chat Message
```bash
# Generate a session ID (or use any UUID)
SESSION_ID="test-session-$(uuidgen)"  # or use: python -c "import uuid; print(uuid.uuid4())"

curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"Hello, I need travel insurance\"
  }"
```
**Expected:**
- Status: `200 OK`
- Response includes:
  - `session_id`: Same as sent
  - `message`: AI response
  - `state`: Conversation state object
  - `requires_human`: Boolean

**Verify:**
- AI response is relevant to travel insurance
- State includes `current_intent` (should be "quote" or similar)

#### Test 3.2: Quote Intent Detection
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"I need a quote for my trip to France\"
  }"
```
**Expected:**
- `state.current_intent`: "quote"
- Response asks for trip details (dates, travelers, etc.)

#### Test 3.3: Policy Explanation Intent
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"What does the medical coverage include?\"
  }"
```
**Expected:**
- `state.current_intent`: "policy_explanation"
- Response includes policy information or asks for clarification

#### Test 3.4: Claims Guidance Intent
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"I need to file a medical claim\"
  }"
```
**Expected:**
- `state.current_intent`: "claims_guidance"
- Response includes claim requirements (documents, information needed)

#### Test 3.5: Human Handoff Intent
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"I need to speak to a human agent\"
  }"
```
**Expected:**
- `state.current_intent`: "human_handoff"
- `requires_human`: `true`
- Response indicates connection to human agent

#### Test 3.6: Multi-Turn Conversation
```bash
# Message 1: Initial request
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"I need travel insurance\"
  }"

# Message 2: Follow-up (use SAME session_id)
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"I'm traveling to France for 7 days\"
  }"
```
**Expected:**
- Conversation context is maintained
- Second response builds on first message
- State progresses through quote collection

#### Test 3.7: Invalid Session ID
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "not-a-valid-uuid",
    "message": "Hello"
  }'
```
**Expected:**
- Status: `400 Bad Request`
- Error message about invalid session_id format

#### Test 3.8: Missing Required Fields
```bash
# Missing message
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\"
  }"

# Missing session_id
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello"
  }'
```
**Expected:**
- Status: `422 Unprocessable Entity`
- Validation error details

---

### ✅ 4. Trip Management

#### Test 4.1: Create Trip (Authenticated)
```bash
# Use token from login
curl -X POST http://localhost:8000/api/v1/trips/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "start_date": "2024-06-15",
    "end_date": "2024-06-22",
    "destinations": ["France", "Italy"],
    "flight_refs": [{"airline": "AF", "flight_number": "123"}],
    "accommodation_refs": [{"hotel": "Hotel Paris"}],
    "total_cost": "2500.00"
  }'
```
**Expected:**
- Status: `201 Created`
- Returns trip object with ID
- **Save trip_id for next tests**

#### Test 4.2: List Trips
```bash
curl http://localhost:8000/api/v1/trips/ \
  -H "Authorization: Bearer <token>"
```
**Expected:**
- Status: `200 OK`
- Returns array of trips (should include the one just created)

#### Test 4.3: Get Specific Trip
```bash
# Replace <trip_id> with ID from created trip
curl http://localhost:8000/api/v1/trips/<trip_id> \
  -H "Authorization: Bearer <token>"
```
**Expected:**
- Status: `200 OK`
- Returns trip details

---

### ✅ 5. Quote Management

#### Test 5.1: Create Quote
```bash
# Use trip_id from Test 4.1
curl -X POST http://localhost:8000/api/v1/quotes/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "trip_id": "<trip_id>",
    "product_type": "single",
    "travelers": [
      {
        "name": "John Doe",
        "age": 35,
        "is_primary": true,
        "preexisting_conditions": []
      }
    ],
    "activities": [
      {"type": "sightseeing", "description": "City tours"}
    ]
  }'
```
**Expected:**
- Status: `201 Created`
- Returns quote with `price_min` and `price_max`
- **Save quote_id**

#### Test 5.2: Get Quote
```bash
curl http://localhost:8000/api/v1/quotes/<quote_id> \
  -H "Authorization: Bearer <token>"
```
**Expected:**
- Status: `200 OK`
- Returns full quote details

#### Test 5.3: Calculate Firm Price
```bash
curl -X POST http://localhost:8000/api/v1/quotes/<quote_id>/price \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "quote_id": "<quote_id>"
  }'
```
**Expected:**
- Status: `200 OK`
- Returns `price` (firm price), `breakdown`, `explanation`
- Price should be between min and max from quote

---

### ✅ 6. RAG (Policy Document Search)

#### Test 6.1: Search Policy Documents
```bash
curl "http://localhost:8000/api/v1/rag/search?q=medical%20coverage&limit=5" \
  -H "Authorization: Bearer <token>"
```
**Expected:**
- Status: `200 OK`
- Returns array of documents matching query
- Each document has: `title`, `text`, `section_id`, `citations`

#### Test 6.2: Search with Product Type Filter
```bash
curl "http://localhost:8000/api/v1/rag/search?q=trip%20cancellation&limit=5&product_type=COMP_TRAVEL" \
  -H "Authorization: Bearer <token>"
```
**Expected:**
- Only returns documents for specified product type

#### Test 6.3: Ingest Document (Admin)
```bash
curl -X POST http://localhost:8000/api/v1/rag/ingest \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "title": "Test Policy Document",
    "insurer_name": "Demo Insurer",
    "product_code": "COMP_TRAVEL",
    "content": "Medical coverage includes emergency services up to $100,000. Trip cancellation is covered for qualified reasons.",
    "split_by_sections": true
  }'
```
**Expected:**
- Status: `201 Created`
- Returns array of created document chunks

---

### ✅ 7. Claims Management

#### Test 7.1: Get Claim Requirements (via Chat)
Use chat endpoint to get claim requirements:
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"What do I need for a medical claim?\"
  }"
```
**Expected:**
- Lists required documents (medical report, bills, receipts)
- Lists required information (date, treatment, expenses)

#### Test 7.2: Create Claim (Authenticated)
```bash
# First, create a policy (if you have a quote_id)
# Then create a claim
curl -X POST http://localhost:8000/api/v1/claims/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "policy_id": "<policy_id>",
    "claim_type": "medical",
    "amount": 500.00,
    "currency": "USD"
  }'
```
**Expected:**
- Status: `201 Created`
- Returns claim with requirements included

---

### ✅ 8. Handoff Service

#### Test 8.1: Create Handoff Request
```bash
curl -X POST http://localhost:8000/api/v1/handoff/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "reason": "complex_query"
  }'
```
**Expected:**
- Status: `201 Created`
- Returns handoff request with status "pending"

#### Test 8.2: Get Handoff Reasons
```bash
curl http://localhost:8000/api/v1/handoff/reasons \
  -H "Authorization: Bearer <token>"
```
**Expected:**
- Status: `200 OK`
- Returns list of available handoff reasons

---

### ✅ 9. End-to-End Workflow Tests

#### Workflow 1: Complete Quote Flow via Chat
```bash
SESSION_ID="workflow-$(uuidgen)"

# Step 1: Initial inquiry
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"I need travel insurance for my trip to France\"
  }"

# Step 2: Provide trip dates
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"I'm traveling from June 15 to June 22\"
  }"

# Step 3: Provide traveler info
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"Just me, I'm 35 years old\"
  }"

# Step 4: Request quote
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"Can you calculate a firm price?\"
  }"
```

**Expected Flow:**
1. Intent detected as "quote"
2. Asks for trip details
3. Collects dates
4. Collects traveler information
5. Provides price range
6. Calculates firm price

**Verify:**
- Each response builds on previous context
- State progresses through needs_assessment → risk_assessment → pricing
- Quote data is eventually populated in response

---

#### Workflow 2: Policy Question → Search
```bash
SESSION_ID="policy-$(uuidgen)"

# Ask policy question
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"What does trip cancellation coverage include?\"
  }"
```
**Expected:**
- Intent detected as "policy_explanation"
- Response includes relevant policy document excerpts
- Includes source citations (section numbers)

---

#### Workflow 3: Claims Guidance
```bash
SESSION_ID="claims-$(uuidgen)"

# Ask about claim requirements
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"What documents do I need for a trip delay claim?\"
  }"
```
**Expected:**
- Intent detected as "claims_guidance"
- Lists required documents
- Lists required information
- Provides clear guidance

---

## 🔍 Testing Error Scenarios

### Test Error Handling

#### Invalid JSON
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d 'invalid json'
```
**Expected:** Status `422` or `400` with error message

#### Missing Authentication
```bash
curl http://localhost:8000/api/v1/trips/
```
**Expected:** Status `401 Unauthorized`

#### Invalid Endpoint
```bash
curl http://localhost:8000/api/v1/invalid-endpoint
```
**Expected:** Status `404 Not Found`

---

## 📊 Monitoring & Debugging

### Check Server Logs
Watch the terminal where uvicorn is running for:
- Request logs
- Graph execution logs
- Error messages
- Database queries

### Check Database
```bash
# If using Docker
docker-compose exec db psql -U postgres -d convo_travel_insure

# Check tables
\dt

# Check recent records
SELECT * FROM chat_history ORDER BY created_at DESC LIMIT 10;
SELECT * FROM quotes ORDER BY created_at DESC LIMIT 10;
```

### Debug Mode
Enable debug in `.env`:
```env
DEBUG=true
```
This provides more detailed error messages.

---

## ✅ Success Criteria

Your application is working correctly if:

1. ✅ All health checks return `200 OK`
2. ✅ Authentication endpoints work (register, login, me)
3. ✅ Chat endpoint responds to messages
4. ✅ Intent detection works (quote, policy, claims, handoff)
5. ✅ Multi-turn conversations maintain context
6. ✅ Quote flow collects information and calculates prices
7. ✅ RAG search returns relevant documents
8. ✅ Error handling returns appropriate status codes
9. ✅ Authenticated endpoints require valid tokens
10. ✅ API documentation is accessible at `/docs`

---

## 🐛 Common Issues & Solutions

### Issue: Database Connection Error
**Symptom:** `sqlalchemy.exc.OperationalError`
**Solution:**
- Ensure database is running: `docker-compose up -d db`
- Check DATABASE_URL in `.env`
- Run migrations: `alembic upgrade head`

### Issue: LLM Not Responding
**Symptom:** Generic responses or errors
**Solution:**
- Check GROQ_API_KEY in `.env`
- Verify API key is valid
- Check network connectivity

### Issue: Graph Execution Errors
**Symptom:** `500 Internal Server Error` on chat endpoint
**Solution:**
- Check server logs for specific error
- Verify ConversationTools are initialized
- Ensure database session is available

### Issue: UUID Validation Errors
**Symptom:** `400 Bad Request - Invalid session_id format`
**Solution:**
- Use proper UUID format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- Generate with: `python -c "import uuid; print(uuid.uuid4())"`

---

## 📝 Testing Report Template

After manual testing, document:

```
Date: [DATE]
Tester: [NAME]
Environment: Development/Production

Test Results:
- Health Checks: ✅/❌
- Authentication: ✅/❌
- Chat Endpoints: ✅/❌
- Quote Flow: ✅/❌
- Policy Search: ✅/❌
- Claims: ✅/❌

Issues Found:
1. [Description]
2. [Description]

Notes:
[Any observations]
```

---

**End of Manual Testing Guide**

Use this guide to systematically test all features and ensure the application works as expected!

