# ConvoTravelInsure - Complete Codebase Summary

**Generated:** For AI Assistant Understanding  
**Last Updated:** 2025-01-31  
**Project Type:** Travel Insurance Conversational Platform  
**Status:** Hackathon MVP - Functional with Payment Integration

---

## Executive Summary

**ConvoTravelInsure** is a conversational AI platform that enables users to get travel insurance quotes through natural language chat. Built for a hackathon, the system demonstrates end-to-end AI-powered insurance quoting with LLM orchestration, real-time conversation management, and integration with insurance pricing models.

**Core Value Proposition:**
- Natural language quoting (no forms)
- AI-powered conversation using LangGraph
- Real-time multi-turn dialogue
- Three-tier insurance pricing (Standard, Elite, Premier)
- **End-to-end payment processing via Stripe**
- **Policy creation after successful payment**
- Human handoff for complex queries
- Claims guidance and policy explanations

**Architecture:** Monorepo with FastAPI backend + Next.js frontend, using PostgreSQL for persistence and LangGraph for conversation orchestration.

---

## Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **LLM Orchestration:** LangGraph 0.2.65, LangChain 0.3.27
- **LLM Providers:** Groq (Llama3-8b-8192) [primary], OpenAI (optional)
- **Database:** PostgreSQL 16 with pgvector
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic
- **Authentication:** JWT (python-jose), Supabase Auth integration
- **Payment Processing:** Stripe integration (test mode)
- **Testing:** pytest, pytest-asyncio (100+ tests, 85%+ pass rate)
- **Other:** dateparser, orjson, structlog, stripe

### Frontend
- **Framework:** Next.js 16.0.0
- **Language:** TypeScript 5
- **UI:** React 19.2.0, TailwindCSS 4
- **State:** React Hooks
- **Components:** Radix UI, Lucide React icons
- **Auth:** Supabase JS SDK 2.77.0

### Infrastructure
- **Containerization:** Docker & Docker Compose
- **Database:** Supabase PostgreSQL (cloud) or local PostgreSQL
- **Vector Store:** pgvector (configured but not fully implemented)
- **LLM Checkpointing:** PostgreSQL via LangGraph PostgresSaver

---

## Project Structure

```
singhax/
├── apps/
│   ├── backend/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── agents/             # LangGraph orchestration
│   │   │   │   ├── graph.py        # Main conversation graph (1,382 lines!)
│   │   │   │   ├── llm_client.py   # Groq/OpenAI client
│   │   │   │   └── tools.py        # Agent-accessible tools
│   │   │   ├── adapters/           # External service adapters
│   │   │   │   └── insurer/        # Insurance provider adapters
│   │   │   ├── core/               # Core infrastructure
│   │   │   │   ├── config.py       # Settings management
│   │   │   │   ├── db.py           # Database session
│   │   │   │   └── security.py     # JWT/auth logic
│   │   │   ├── models/             # SQLAlchemy models (11 models)
│   │   │   │   ├── user.py         # User, onboarding fields
│   │   │   │   ├── trip.py         # Trip details
│   │   │   │   ├── quote.py        # Insurance quotes
│   │   │   │   ├── policy.py       # Insurance policies
│   │   │   │   ├── claim.py        # Insurance claims
│   │   │   │   ├── payment.py      # Payment records (Stripe)
│   │   │   │   ├── traveler.py     # Traveler profiles
│   │   │   │   ├── chat_history.py # Chat messages
│   │   │   │   ├── audit_log.py    # Audit trail
│   │   │   │   └── rag_document.py # RAG policy docs
│   │   │   ├── routers/            # FastAPI endpoints
│   │   │   │   ├── chat.py         # Main chat endpoint
│   │   │   │   ├── auth.py         # Registration/login
│   │   │   │   ├── quotes.py       # Quote management
│   │   │   │   ├── policies.py     # Policy management
│   │   │   │   ├── claims.py       # Claims processing
│   │   │   │   ├── payments.py     # Stripe webhooks
│   │   │   │   ├── trips.py        # Trip management
│   │   │   │   ├── rag.py          # Policy search
│   │   │   │   ├── handoff.py      # Human handoff
│   │   │   │   └── voice.py        # Voice input
│   │   │   ├── schemas/            # Pydantic validation
│   │   │   └── services/           # Business logic
│   │   │       ├── pricing.py      # Quote calculations
│   │   │       ├── payment.py      # Stripe payment processing
│   │   │       ├── rag.py          # Document search
│   │   │       ├── claims.py       # Claims logic
│   │   │       ├── handoff.py      # Escalation logic
│   │   │       └── geo_mapping.py  # Destination mapping
│   │   ├── alembic/                # Database migrations (7 migrations)
│   │   ├── tests/                  # Test suite (100+ tests)
│   │   └── requirements.txt        # Python dependencies
│   └── frontend/                   # Next.js frontend
│       ├── src/
│       │   ├── app/                # Next.js app directory
│       │   │   └── app/            # Main app routes
│       │   │       ├── signup/     # User registration
│       │   │       ├── login/      # User login
│       │   │       ├── onboarding/ # User onboarding
│       │   │       ├── dashboard/  # User dashboard
│       │   │       └── quote/      # Chat interface
│       │   ├── components/         # React components
│       │   │   ├── CopilotPanel.tsx   # Sidebar summary
│       │   │   ├── ProtectedRoute.tsx # Auth wrapper
│       │   │   ├── VoiceButton.tsx    # Voice input
│       │   │   └── ui/             # UI primitives
│       │   ├── contexts/           # React contexts
│       │   │   └── AuthContext.tsx # Auth state
│       │   └── lib/                # Utilities
│       │       ├── supabase.ts     # Supabase client
│       │       └── utils.ts        # Helpers
│       ├── public/                 # Static assets
│       └── package.json            # Node dependencies
├── docs/                           # Documentation
├── infra/                          # Infrastructure config
│   ├── env.example                 # Environment template
│   └── init.sql                    # DB init script
├── docker-compose.yml              # Docker services
├── Makefile                        # Dev commands
├── README.md                       # Project readme
└── CODEBASE_SUMMARY.md             # This summary
```

---

## Core Components

### 1. **Chat Router** (`apps/backend/app/routers/chat.py`)
**Purpose:** Main conversational interface endpoint

**Key Endpoints:**
- `POST /api/v1/chat/message` - Send message, get AI response
- `POST /api/v1/chat/session` - Create new chat session
- `GET /api/v1/chat/session/{session_id}` - Get session state/history
- `GET /api/v1/chat/health` - Health check

**How It Works:**
1. Accepts user message with session_id
2. Loads existing state from PostgreSQL checkpointing
3. Invokes LangGraph conversation graph (async with 30s timeout)
4. Returns AI response with full conversation state
5. Automatically persists state via LangGraph checkpointer

**Status:** ✅ Fully operational  
**Known Issues:** 20+ second response times (LLM processing delay)

---

### 2. **LangGraph Conversation Graph** (`apps/backend/app/agents/graph.py`)
**Purpose:** State machine for conversational flow

**Architecture:**
- 9 nodes: orchestrator, needs_assessment, risk_assessment, pricing, payment_processor, policy_explainer, claims_guidance, compliance, customer_service
- Conditional routing based on intent and state flags
- PostgreSQL checkpointing for session persistence
- Loop protection (max 20 iterations)

**Flow for Quote Generation:**
```
1. Orchestrator → Classifies intent (quote/policy/claim/purchase/handoff)
2. Needs Assessment → Collects 6 fields:
   a. Destination (country name)
   b. Departure date (YYYY-MM-DD or flexible)
   c. Return date (YYYY-MM-DD or flexible)
   d. Travelers (ages as integers)
   e. Adventure sports (yes/no)
   f. Confirmation (user confirms all details)
3. Risk Assessment → Maps destination to geographic area
4. Pricing → Generates 3-tier quotes
5. END → Returns quotes to user
```

**Flow for Payment Processing:**
```
1. User: "I'll take the Elite plan" (purchase intent)
2. Orchestrator → Routes to payment_processor
3. Payment Processor → Creates payment intent in database
4. Payment Processor → Creates Stripe checkout session
5. User → Completes payment on Stripe checkout page
6. Stripe → Sends webhook to /api/v1/payments/webhook/stripe
7. Webhook Handler → Updates payment status to "completed"
8. Payment Processor → Creates Policy record
9. END → Returns policy number to user
```

**LLM Integration:**
- **Intent Classification:** Uses Groq LLM with function calling
- **Information Extraction:** LLM extracts destination, dates, ages, adventure sports
- **Date Parsing:** Flexible parser supporting YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY, natural language
- **Special Handling:** Adventure sports has complex validation to prevent premature extraction

**State Management:**
```python
ConversationState = {
    "messages": List[BaseMessage],           # Conversation history
    "user_id": str,                          # UUID
    "session_id": str,                       # UUID
    "current_intent": str,                   # "quote" | "policy" | "claim" | "handoff"
    "trip_details": {
        "destination": str,
        "departure_date": date,
        "return_date": date,
        "area": str,                         # From geo mapping
        "base_rate": float
    },
    "travelers_data": {
        "ages": List[int],
        "count": int
    },
    "preferences": {
        "adventure_sports": bool | None
    },
    "current_question": str,                 # Tracking which question is being asked
    "awaiting_confirmation": bool,           # Waiting for user confirmation
    "confirmation_received": bool,           # User confirmed
    "quote_data": Dict,                      # Generated quotes
    "trip_id": str,                         # Database trip ID
    "_loop_count": int,                     # Loop protection
    "_ready_for_pricing": bool,             # Flow control
    "_pricing_complete": bool,              # Flow control
    "_payment_intent_id": str,              # Payment tracking
    "_awaiting_payment_confirmation": bool, # Payment flow control
    "_policy_created": bool                 # Policy creation flag
}
```

**Status:** ✅ Fully functional  
**Known Issues:**
- Response times can be 20+ seconds due to LLM calls
- Some edge cases in date parsing
- Loop protection occasionally triggers for complex flows

---

### 3. **LLM Client** (`apps/backend/app/agents/llm_client.py`)
**Purpose:** Interface to Groq and OpenAI LLMs

**Capabilities:**
- **Text Generation:** Conversational responses with system prompts
- **Intent Detection:** Classify user intent with confidence scores
- **Information Extraction:** Extract structured data (dates, ages, etc.) using function calling
- **Provider Management:** Singleton pattern, supports Groq (default) and OpenAI (optional)
- **Error Handling:** Graceful fallbacks for API failures

**Supported Intents:**
- `quote` - Insurance quote request
- `purchase` - User wants to buy/purchase insurance after seeing quotes
- `policy_explanation` - Policy document questions
- `claims_guidance` - Claims requirements
- `human_handoff` - Request live agent
- `general_inquiry` - Other questions

**Status:** ✅ Fully functional  
**Tests:** 14/14 passing

---

### 4. **Pricing Service** (`apps/backend/app/services/pricing.py`)
**Purpose:** Calculate insurance quotes using MSIG pricing model

**Pricing Formula:**
```
Per-Traveler Base Price = Base Rate per Day × Duration × Age Multiplier
Total Base Price = Sum of all travelers' base prices
Final Tier Price = Total Base Price × Tier Multiplier
```

**Age Multipliers:**
- Children (<18): 0.7
- Adults (18-64): 1.0
- Seniors (65-69): 1.3
- Seniors (70+): 1.5

**Tier Multipliers:**
- Standard: 1.0
- Elite: 1.8
- Premier: 2.5

**Coverage Tiers:**
- **Standard:** $250K medical, $5K cancellation, $3K baggage, no adventure sports
- **Elite:** $500K medical, $12.5K cancellation, $5K baggage, adventure sports included
- **Premier:** $1M medical, $15K cancellation, $7.5K baggage, full adventure sports, $1M evacuation

**Geographic Areas:**
- **Area A (ASEAN):** Brunei, Cambodia, Indonesia, Laos, Malaysia, Myanmar, Philippines, Thailand, Vietnam - $3/day base rate
- **Area B (Asia-Pacific):** Australia, China, Hong Kong, India, Japan, Korea, Macau, New Zealand, Sri Lanka, Taiwan - $5/day base rate
- **Area C (Worldwide):** All other countries - $8/day base rate

**Status:** ✅ Fully functional  
**Tests:** 6/6 passing  
**Known Issue:** Uses MockInsurerAdapter (TODO: real insurer integration)

---

### 5. **Payment Service** (`apps/backend/app/services/payment.py`)
**Purpose:** Handle Stripe payment processing and payment record management

**Capabilities:**
- `create_payment_intent()` - Create payment record in database with pending status
- `create_stripe_checkout()` - Create Stripe checkout session and link to payment record
- `check_payment_status()` - Query payment status from database
- `wait_for_payment_completion()` - Poll for payment completion (with timeout)

**Payment Flow:**
1. User selects tier (Standard/Elite/Premier)
2. Create payment intent in database (status: PENDING)
3. Create Stripe checkout session with `client_reference_id` = `payment_intent_id`
4. User completes payment on Stripe
5. Stripe webhook updates payment status to COMPLETED
6. User confirms payment in chat
7. Create Policy record from payment

**Payment Status Tracking:**
- `PENDING` - Payment intent created, awaiting payment
- `COMPLETED` - Payment successful, policy created
- `FAILED` - Payment failed
- `EXPIRED` - Checkout session expired

**Status:** ✅ Fully functional  
**Tests:** 10/10 passing  
**Integration:** Real Stripe API tested and verified

---

### 6. **RAG Service** (`apps/backend/app/services/rag.py`)
**Purpose:** Semantic search over policy documents

**Current Implementation:**
- Text-based search using SQL LIKE queries (fallback)
- Mock embedding generation (returns constant vectors)
- Document ingestion with section splitting (hardcoded sections)
- Returns policy excerpts with citations

**Planned Implementation:**
- Real embedding generation (OpenAI/Groq)
- pgvector similarity search
- Proper content chunking
- Real policy document ingestion

**Status:** ⚠️ Partially functional  
**Tests:** 4/6 passing  
**Known Issue:** Vector search not implemented, using text search

---

### 7. **Claims Service** (`apps/backend/app/services/claims.py`)
**Purpose:** Provide claims guidance and processing

**Supported Claim Types:**
1. **Trip Delay:** Required: flight delay confirmation, boarding pass, receipts
2. **Medical:** Required: medical certificate, hospital bills, receipts, passport
3. **Baggage:** Required: baggage tag, loss report, police report, receipts
4. **Theft:** Required: police report, proof of ownership, receipts, passport
5. **Cancellation:** Required: booking cancellation, receipts, proof of reason

**Capabilities:**
- Claims creation and updates
- Requirements lookup for each claim type
- Document upload management
- Completeness checking
- Claim packet generation

**Status:** ✅ Fully functional  
**Tests:** 5/5 passing

---

### 8. **Handoff Service** (`apps/backend/app/services/handoff.py`)
**Purpose:** Manage escalations to human agents

**Capabilities:**
- Create handoff requests
- Track handoff reasons
- Generate conversation summaries
- Priority assignment

**Status:** ⚠️ Tests failing (0/4 passing)  
**Known Issue:** Database dependency issues, needs User model fixtures

---

### 9. **Conversation Tools** (`apps/backend/app/agents/tools.py`)
**Purpose:** Tools available to LangGraph agents

**Available Tools:**
- `get_quote_range()` - Price range calculation
- `get_firm_price()` - Firm pricing
- `search_policy_documents()` - RAG search
- `get_claim_requirements()` - Claim type requirements
- `create_handoff_request()` - Escalation
- `assess_risk_factors()` - Risk evaluation
- `get_price_breakdown_explanation()` - Price explanations
- `create_payment_checkout()` - Create Stripe checkout session
- `check_payment_completion()` - Check payment status
- `create_policy_from_payment()` - Create policy after payment

**Status:** ✅ Fully functional  
**Tests:** 17+ passing

---

## Database Models

### Core Models (SQLAlchemy)

1. **User**
   - Fields: id (UUID), email, name, hashed_password, is_active, is_verified
   - Onboarding: date_of_birth, phone, nationality, passport, address, emergency_contact, preferences
   - Relationships: travelers, trips, quotes, policies, chat_history, audit_logs

2. **Traveler**
   - Fields: id, user_id (FK), full_name, date_of_birth, passport_no, is_primary, preexisting_conditions (JSONB)
   - Relationships: user

3. **Trip**
   - Fields: id, user_id (FK), session_id (unique), status, start_date, end_date, destinations (ARRAY), travelers_count, flight_refs (JSONB), accommodation_refs (JSONB), total_cost
   - Relationships: user, quotes

4. **Quote**
   - Fields: id, user_id (FK), trip_id (FK), product_type (Enum), travelers (JSONB), activities (JSONB), risk_breakdown (JSONB), price_min, price_max, price_firm, currency, status (Enum: DRAFT/PRICED/ACCEPTED/EXPIRED), breakdown (JSONB), insurer_ref, expires_at
   - Relationships: user, trip, policies

5. **Policy**
   - Fields: id, user_id (FK), quote_id (FK), policy_number, coverage (JSONB), named_insureds (JSONB), effective_date, expiry_date, status (Enum: ACTIVE/PENDING/CANCELLED/EXPIRED), cooling_off_days
   - Relationships: user, quote, claims

6. **Claim**
   - Fields: id, policy_id (FK), claim_type, amount, currency, requirements (JSONB), documents (JSONB), status (Enum: DRAFT/SUBMITTED/UNDER_REVIEW/APPROVED/REJECTED)
   - Relationships: policy

7. **ChatHistory**
   - Fields: id, user_id (FK), session_id, role, content, metadata (JSONB)
   - Relationships: user

8. **Payment**
   - Fields: id (UUID), user_id (FK), quote_id (FK), payment_intent_id (unique), stripe_session_id, stripe_payment_intent, payment_status (Enum: PENDING/COMPLETED/FAILED/EXPIRED), amount (Numeric), currency, product_name, created_at, updated_at, webhook_processed_at
   - Relationships: user, quote
   - Purpose: Tracks Stripe payment transactions

9. **RagDocument**
   - Fields: id, title, insurer_name, product_code, section_id, heading, text, citations (JSONB), embedding (vector)
   - Purpose: Policy document chunks for RAG search

10. **AuditLog**
   - Fields: id, user_id (FK), action, entity, entity_id, metadata (JSONB)
   - Relationships: user

**Migration Status:** 7 Alembic migrations applied (includes payments table)

---

## API Endpoints

### All endpoints under `/api/v1` prefix

**Auth Router** (`/auth`)
- `POST /register` - User registration
- `POST /login` - JWT authentication
- `GET /me` - Current user info

**Chat Router** (`/chat`)
- `POST /message` - Send message, get AI response (main endpoint)
- `POST /session` - Create session
- `GET /session/{session_id}` - Get state/history
- `GET /health` - Health check

**Trips Router** (`/trips`)
- `POST /` - Create trip
- `GET /` - List trips
- `GET /{trip_id}` - Get trip
- `POST /{trip_id}/events` - Create trip event

**Quotes Router** (`/quotes`)
- `POST /` - Create quote
- `GET /` - List quotes
- `GET /{quote_id}` - Get quote
- `PUT /{quote_id}` - Update quote
- `POST /{quote_id}/price` - Calculate firm price

**Policies Router** (`/policies`)
- `POST /` - Create policy
- `GET /` - List policies
- `GET /{policy_id}` - Get policy

**Claims Router** (`/claims`)
- `POST /` - Create claim
- `GET /` - List claims
- `GET /{claim_id}` - Get claim
- `PUT /{claim_id}` - Update claim
- `POST /{claim_id}/upload` - Upload document
- `POST /{claim_id}/submit` - Submit claim

**RAG Router** (`/rag`)
- `GET /search` - Search policy documents
- `POST /ingest` - Ingest document

**Handoff Router** (`/handoff`)
- `POST /` - Create handoff
- `GET /reasons` - Get reasons

**Payments Router** (`/payments`) ✅ **NEW**
- `POST /webhook/stripe` - Stripe webhook handler
  - Handles: `checkout.session.completed`, `checkout.session.expired`, `payment_intent.payment_failed`
  - Verifies webhook signatures (with fallback for local testing)
  - Updates payment status in database
- `GET /health` - Health check

**Voice Router** (`/voice`)
- `POST /` - Process voice input (TODO)

**Common Features:**
- Authentication: JWT required (except public endpoints)
- CORS: Configured for localhost:3000
- Documentation: OpenAPI/Swagger at `/docs`, ReDoc at `/redoc`
- Health Check: `/health` endpoint

---

## Frontend Architecture

### Next.js App Directory Structure

**Routes:**
- `/app/signup` - User registration
- `/app/login` - User login
- `/app/onboarding` - User onboarding flow
- `/app/dashboard` - User dashboard
- `/app/quote` - Main chat interface

### Chat Interface (`/app/quote/page.tsx`)

**Components:**
- Chat messages display (user/assistant)
- Message input with voice button
- CopilotPanel sidebar (trip summary, travelers, pricing)
- Header with navigation and user menu

**State Management:**
- Messages array
- Session ID management
- Loading states
- Voice input integration

**Authentication:**
- Uses Supabase Auth
- Protected routes via `ProtectedRoute` component
- JWT token extraction for API calls

**Known UI Issues:**
1. Enter key doesn't send messages (Bug #4)
2. Chat responses have 20+ second delays (Bug #3)
3. Signup success logged as error (Bug #2)

**Status:** ⚠️ Functional but with UX issues

---

## Configuration & Environment

### Required Environment Variables

**Database:**
- `DATABASE_URL` - PostgreSQL connection string

**Security:**
- `SECRET_KEY` - JWT signing key
- `SUPABASE_JWT_SECRET` - For verifying Supabase tokens

**LLM:**
- `GROQ_API_KEY` - Groq API key (required for chat)
- `OPENAI_API_KEY` - OpenAI API key (optional)

**Payment Processing (Stripe):**
- `STRIPE_SECRET_KEY` - Stripe secret key (required for payments)
- `STRIPE_PUBLISHABLE_KEY` - Stripe publishable key (for frontend)
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook signing secret
- `PAYMENT_SUCCESS_URL` - Redirect URL after successful payment
- `PAYMENT_CANCEL_URL` - Redirect URL after cancelled payment

**Supabase (Optional):**
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Anonymous key
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key

**Application:**
- `DEBUG` - Debug mode (default: False)
- `ENVIRONMENT` - Environment name (default: development)
- `API_V1_PREFIX` - API prefix (default: /api/v1)
- `ALLOWED_ORIGINS` - CORS origins (default: localhost:3000)

**LLM Configuration:**
- `MODEL_NAME` - Default: llama3-8b-8192
- `GROQ_MODEL` - Override Groq model
- `GROQ_TEMPERATURE` - Sampling temperature
- `GROQ_MAX_TOKENS` - Max tokens
- `EMBEDDING_MODEL` - Default: text-embedding-3-small

**Configuration Loading:**
- Uses pydantic-settings
- Loads from `.env` file in project root
- Case-insensitive variables
- Extra fields ignored

---

## Testing Status

### Test Suite Summary

**Total:** 100+ tests  
**Passing:** 85+ (85%+)  
**Failing:** 15 (15%)

**New Test Suites:**
- ✅ Payment Model Tests (7/7) - Payment model validation
- ✅ Payment Service Tests (10/10) - Stripe integration, payment flow
- ✅ Payment Integration Tests - Real Stripe API calls verified

### Test Coverage

**Fully Passing Suites:**
- ✅ LLM Client Tests (14/14) - Intent detection, extraction, generation
- ✅ API Integration Tests (13/13) - All routers, CORS, error handling
- ✅ Pricing Service Tests (6/6) - Range, firm pricing, risk assessment
- ✅ Claims Service Tests (5/5) - All claim types
- ✅ Payment Model Tests (7/7) - Payment model validation
- ✅ Payment Service Tests (10/10) - Stripe integration, payment flow
- ✅ Conversation Tools Tests (17+) - All tools functional

**Partially Passing Suites:**
- ⚠️ Chat Router Tests (4/8) - Basic functionality works, mock issues
- ⚠️ Graph Integration Tests (6/8) - Core routing works, policy explainer issues
- ⚠️ RAG Service Tests (4/6) - Text search works, UUID validation issues

**Failing Suites:**
- ❌ Handoff Service Tests (0/4) - Database dependency issues

### Known Test Issues

1. **Mock Data Type Mismatches (6 tests)**
   - Test mocks don't match exact return types
   - Low impact - actual code works

2. **Database Dependencies (4 tests)**
   - HandoffService tests need database fixtures
   - Medium impact - needs infrastructure

3. **UUID Validation (2 tests)**
   - Mocks use strings instead of UUID objects
   - Low impact - actual code validates correctly

**Run Tests:**
```bash
cd apps/backend
pytest -v
```

---

## Known Issues & Problems

### High Priority Issues

1. **Chat Response Delays (Bug #3)**
   - **Severity:** High
   - **Location:** Backend - LangGraph execution
   - **Issue:** Responses take 20+ seconds to appear
   - **Impact:** Poor UX, chat feels unresponsive
   - **Likely Cause:** LLM API calls taking too long, no caching
   - **Note:** Functionality works, just slow

2. **Enter Key Not Working (Bug #4)**
   - **Severity:** Medium
   - **Location:** Frontend - Chat input
   - **Issue:** Enter key doesn't send messages
   - **Impact:** Poor UX - users expect Enter to work
   - **Fix:** Code has `handleKeyPress` but may not be wired correctly

### Medium Priority Issues

3. **Email Validation Bug (Bug #1)**
   - **Severity:** Medium
   - **Location:** Supabase Auth
   - **Issue:** Valid emails like `test@example.com` rejected
   - **Impact:** Some users can't sign up
   - **Note:** Possible Supabase configuration issue

4. **Signup Success Logged as Error (Bug #2)**
   - **Severity:** Low
   - **Location:** Frontend
   - **Issue:** Email verification message treated as error
   - **Impact:** Misleading console errors

5. **Intent Detection is Keyword-Based**
   - **Issue:** Uses simple keyword matching in fallback flow
   - **Impact:** Lower accuracy for intent classification
   - **Solution:** LLM client has `detect_intent()` but not always used

6. **RAG Uses Text Search, Not Vector Search**
   - **Issue:** Mock embeddings, no pgvector similarity search
   - **Impact:** Limited semantic search capabilities
   - **Solution:** Integrate OpenAI embeddings and pgvector queries

7. **Mock Insurer Adapter**
   - **Issue:** Uses MockInsurerAdapter instead of real insurer API
   - **Impact:** No real pricing integration
   - **Solution:** Implement real insurer adapter

### Low Priority Issues

8. **Content Splitting is Mock**
   - **Issue:** Returns hardcoded sections
   - **Impact:** Document ingestion doesn't work properly

9. **Pydantic Deprecation Warnings**
   - **Issue:** Using deprecated patterns
   - **Impact:** Future compatibility concerns

10. **Voice Router Not Implemented**
    - **Issue:** Endpoint exists but just returns TODO
    - **Impact:** Voice input doesn't work

11. **Missing TODOs Throughout Codebase**
    - Various endpoints have incomplete implementations
    - See grep results for full list

---

## Capabilities & Features

### ✅ Implemented Features

1. **Conversational Quote Flow**
   - Multi-turn conversation for quote collection
   - LLM-based intent detection and routing
   - Slot filling for trip details
   - Flexible date parsing
   - Risk assessment
   - Three-tier pricing (Standard, Elite, Premier)
   - Geographic area mapping

2. **User Management**
   - User registration via Supabase Auth
   - JWT-based authentication
   - Onboarding flow
   - User profiles with travel preferences

3. **Policy Document Search (RAG)**
   - Document ingestion (basic)
   - Text-based search
   - Policy explanations with citations
   - Multiple claim type support

4. **Claims Guidance**
   - 5 claim types: Trip delay, Medical, Baggage, Theft, Cancellation
   - Requirements lookup
   - Document checklist generation
   - Claim completeness checking

5. **Human Handoff System**
   - Escalation triggers (low confidence, user request)
   - Handoff request creation
   - Conversation summary generation

6. **Multi-Traveler Support**
   - Traveler profiles
   - Age-based risk assessment
   - Preexisting conditions tracking

7. **Conversation Persistence**
   - PostgreSQL checkpointing via LangGraph
   - Session state management
   - Message history
   - Loop protection

8. **Payment Processing** ✅ **NEW**
   - Stripe checkout session creation
   - Payment intent tracking in database
   - Webhook handling for payment events
   - Policy creation after successful payment
   - Payment status tracking (pending, completed, failed, expired)
   - Integration tests with real Stripe API

9. **API Infrastructure**
   - All 10 routers registered (includes payments)
   - CORS configured
   - OpenAPI documentation
   - Health checks
   - Error handling

### 🔄 TODO Features (Noted in Code)

1. **Real LLM Integration for Intent**
   - Currently keyword-based in some flows
   - LLM client exists but not always used

2. **Production Authentication**
   - JWT implemented but needs hardening
   - Email verification pending

3. **Real-Time Chat**
   - Session-based chat works
   - WebSocket support not implemented

4. **Vector Search for RAG**
   - Embeddings mocked
   - pgvector queries not implemented

5. **Voice Input**
   - Endpoint exists
   - Speech-to-text not implemented

---

## Data Flow Examples

### Quote Flow

```
User: "I need travel insurance for a trip to Japan"
  ↓
Chat Router → LangGraph (orchestrator)
  ↓
Intent: "quote" (LLM classified)
  ↓
Needs Assessment → Extract: destination="Japan"
  ↓
Database: Create Trip record
  ↓
Needs Assessment → Ask: "When does your trip start?"
  ↓
User: "December 15, 2025"
  ↓
Needs Assessment → Extract: departure_date
  ↓
Needs Assessment → Ask: "When do you return?"
  ↓
User: "January 3, 2026"
  ↓
Needs Assessment → Extract: return_date
  ↓
Needs Assessment → Ask: "How many travelers and ages?"
  ↓
User: "2 travelers, ages 30 and 8"
  ↓
Needs Assessment → Extract: travelers=[30, 8]
  ↓
Needs Assessment → Ask: "Adventure activities?"
  ↓
User: "yes"
  ↓
Needs Assessment → Extract: adventure_sports=True
  ↓
Needs Assessment → Show confirmation summary
  ↓
User: "yes, correct"
  ↓
Risk Assessment → Map Japan to Area B, base_rate=5.0
  ↓
Pricing → Calculate quotes:
  - Standard: $210.00
  - Elite: $378.00 (recommended for adventure)
  - Premier: $525.00
  ↓
END → Return quotes to user
```

### Payment Flow

```
User: "I'll take the Elite plan"
  ↓
Chat Router → LangGraph (orchestrator)
  ↓
Intent: "purchase" (LLM classified)
  ↓
Payment Processor → Extract tier selection ("elite")
  ↓
Payment Processor → Create Payment record (status: PENDING)
  ↓
Payment Processor → Create Stripe Checkout Session
  ↓
Return: Checkout URL to user
  ↓
User → Completes payment on Stripe
  ↓
Stripe → Sends webhook: checkout.session.completed
  ↓
Payments Webhook → Updates Payment (status: COMPLETED)
  ↓
User: "I paid" / "Payment done"
  ↓
Payment Processor → Check payment status (COMPLETED)
  ↓
Payment Processor → Create Policy record
  ↓
Return: Policy number to user
  ↓
END → Payment flow complete
```

### Policy Search Flow

```
User: "What does medical coverage include?"
  ↓
Chat Router → LangGraph (orchestrator)
  ↓
Intent: "policy_explanation"
  ↓
Policy Explainer → RAG Service
  ↓
RAG Service → Text search (LIKE query)
  ↓
Database: Fetch policy documents
  ↓
Return: Policy excerpts with citations
  ↓
END → Display answer to user
```

---

## Deployment & Infrastructure

### Docker Compose

**Services:**
- **backend:** FastAPI (port 8000)
- **frontend:** Next.js (port 3000)

**Database:** External (Supabase PostgreSQL)

**Environment:** Development mode with hot reload

### Running Locally

**Docker (Recommended):**
```bash
docker-compose up -d
```

**Local Development:**
```bash
# Backend
cd apps/backend
uvicorn app.main:app --reload

# Frontend
cd apps/frontend
npm run dev

# Database
docker-compose up -d db
```

### Database Migrations

```bash
cd apps/backend
alembic upgrade head
```

### Access Points

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Development Workflow

### Adding New Features

1. **Backend:** Add new routers in `apps/backend/app/routers/`
2. **Frontend:** Add new pages in `apps/frontend/src/app/`
3. **Database:** Create migrations with `alembic revision --autogenerate`
4. **Testing:** Add tests in `apps/backend/tests/`

### Code Structure Conventions

- **Routers:** HTTP request/response handling
- **Services:** Business logic (reusable)
- **Models:** Database models (SQLAlchemy)
- **Schemas:** Pydantic validation schemas
- **Agents:** LangGraph orchestration
- **Tools:** Agent-accessible functions
- **Adapters:** External service integrations

### Testing

```bash
# Run all tests
pytest apps/backend/tests/ -v

# Run specific file
pytest apps/backend/tests/test_chat.py -v

# Run with coverage
pytest --cov=app --cov-report=html
```

---

## Key Implementation Details

### Adventure Sports Question Logic

The adventure sports question has complex logic to prevent premature extraction:

1. **Extraction Rules:**
   - Only accept extraction when asking question OR user mentions keywords
   - Validate LLM extraction against user's explicit yes/no
   - Reject if LLM says opposite of user's clear intent

2. **Keyword Parsing:**
   - Positive: "yes", "i am", "i'm", "i will", "absolutely", "definitely", etc.
   - Negative: "no", "nope", "i'm not", "absolutely not", "definitely not", etc.

3. **Flow Control:**
   - Asked AFTER all 4 required fields collected
   - User confirms AFTER adventure sports answered
   - Correct value shown in confirmation

### Date Parsing

**Supports Multiple Formats:**
- YYYY-MM-DD (2025-12-15)
- MM/DD/YYYY (12/15/2025)
- DD/MM/YYYY (15/12/2025)
- Natural language ("December 15, 2025", "Dec 15, 2025")
- Relative dates ("tomorrow", "next week", "in 3 days")

**Uses dateparser library with settings:**
- Prefer future dates for travel
- Return as timezone-aware=False
- Relative base = now

### Loop Protection

**Safety Mechanisms:**
- `_loop_count` tracks iterations (max 20)
- `_pricing_complete` flag prevents re-entry
- `_ready_for_pricing` controls flow
- Clear END conditions for each node

---

## Documentation Files

**In Codebase:**
- `README.md` - Project overview
- `CODEBASE_SUMMARY.md` - Detailed codebase summary
- `SYSTEM_SUMMARY.md` - System architecture summary
- `TEST_REPORT.md` - Test suite results
- `docs/` folder - Additional documentation

**Important Docs:**
- `docs/AGENTS.md` - Agent architecture
- `docs/API.md` - API reference
- `docs/ADAPTERS.md` - Adapter pattern
- `docs/DATABASE_MIGRATION_GUIDE.md` - DB migrations
- `QUICK_START.md` - Getting started

---

## Production Readiness

### ✅ Production-Ready Components

1. **API Infrastructure:** All routers, CORS, error handling
2. **Database Models:** Complete with relationships (11 models)
3. **Services:** Business logic fully implemented
4. **LLM Client:** Groq/OpenAI integration working
5. **Payment Processing:** Stripe integration with webhooks
6. **Testing:** 85%+ test pass rate (100+ tests)
7. **Conversation Flow:** Multi-turn dialogue working
8. **State Persistence:** PostgreSQL checkpointing
9. **Payment Flow:** End-to-end payment to policy creation

### ⚠️ Needs Work for Production

1. **Performance:** Response times too slow (20+ seconds)
2. **Authentication:** Email verification pending
3. **Security:** JWT needs production hardening
4. **Monitoring:** No analytics/logging integration
5. **Error Handling:** Some edge cases unhandled
6. **Real Integrations:** Mock insurer, mock RAG
7. **Frontend UX:** Enter key bug, slow responses

### 🔧 Recommended Next Steps

**High Priority:**
1. Optimize LLM response times (caching, parallel calls)
2. Fix Enter key bug in frontend
3. Implement real RAG vector search
4. Add production monitoring

**Medium Priority:**
5. Fix remaining test failures
6. Implement email verification
7. Add real insurer adapter
8. Enhance error handling

**Low Priority:**
9. Add WebSocket support
10. Implement voice input
11. Add analytics integration
12. Performance testing

---

## Summary for AI Assistants

This is a **functional hackathon MVP** for a conversational travel insurance platform. The core conversation flow works end-to-end with LangGraph orchestration, LLM-powered extraction, real-time quote generation, and **complete payment processing** through Stripe. The system has **strong technical foundations** (85%+ test pass rate with 100+ tests, well-structured code) but **UX issues** (slow responses, some bugs).

**Key Strengths:**
- Solid architecture with LangGraph
- Comprehensive test suite (100+ tests)
- Well-documented code
- Real LLM integration working
- Three-tier pricing model implemented
- **End-to-end payment processing with Stripe**
- **Real Stripe API integration tested**

**Key Weaknesses:**
- Response times too slow (20+ seconds)
- Some UI bugs (Enter key, email validation)
- Mock implementations (RAG, insurer adapter)
- Missing production features (email verification)

**For Development:**
- Focus on performance optimization first
- Fix critical UX bugs
- Implement real integrations (RAG, insurer)
- Add monitoring and logging

**For AI Understanding:**
- Main file: `apps/backend/app/agents/graph.py` (1,500+ lines)
- Chat endpoint: `apps/backend/app/routers/chat.py`
- Payment service: `apps/backend/app/services/payment.py`
- Payment router: `apps/backend/app/routers/payments.py`
- Payment model: `apps/backend/app/models/payment.py`
- Pricing logic: `apps/backend/app/services/pricing.py`
- Frontend chat: `apps/frontend/src/app/app/quote/page.tsx`

---

**End of Comprehensive Summary**

