# ConvoTravelInsure - Codebase Summary for Claude

**Date:** January 2025  
**Purpose:** Comprehensive overview of the codebase for AI assistant context and future development planning

---

## 🎯 Project Intention & Purpose

**ConvoTravelInsure** is a conversational AI-powered travel insurance platform that revolutionizes how users get insurance quotes and interact with insurance services. The core value proposition is:

1. **Natural Language Interaction**: Users can have a conversation (chat interface) to get travel insurance quotes instead of filling out traditional forms
2. **AI-Powered Quote Generation**: Collects trip information through conversational flow (destination, dates, travelers, activities) and generates instant quotes
3. **Policy Document Search (RAG)**: Allows users to ask questions about coverage and get answers from policy documents using Retrieval-Augmented Generation
4. **Claims Guidance**: Provides step-by-step assistance for filing claims with document checklists
5. **Human Handoff**: Seamlessly escalates complex queries to human agents when needed

### Key Differentiators
- **Conversational UX**: No forms, just chat - making insurance accessible and friendly
- **Multi-turn Conversations**: Handles complex, multi-part information gathering naturally
- **Intelligent Routing**: Uses LangGraph state machine to route conversations based on intent
- **Instant Pricing**: Real-time quote calculation with tiered coverage options (Standard, Elite, Premier)

---

## 🏗️ Tech Stack

### Backend (Python/FastAPI)
- **Framework**: FastAPI 0.104+ (Python 3.11+)
- **LLM Orchestration**: 
  - LangGraph 0.2.65 (conversation state machine)
  - LangChain 0.3.27 (LLM abstractions)
  - LangGraph Checkpoint Postgres (conversation persistence)
- **LLM Providers**: 
  - Groq (default) - Llama3/Mixtral models
  - OpenAI (optional fallback)
- **Database**: 
  - PostgreSQL 16 with pgvector extension (vector search for RAG)
  - SQLAlchemy 2.0 (ORM)
  - Alembic (migrations)
- **Authentication**: 
  - JWT (python-jose, passlib)
  - Supabase Auth integration ready
- **API Architecture**: RESTful API with OpenAPI/Swagger docs

### Frontend (Next.js/React)
- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript 5+
- **Styling**: TailwindCSS 4
- **UI Components**: Radix UI, Lucide React icons
- **State Management**: React hooks, Context API
- **Authentication**: Supabase client-side auth

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Database**: PostgreSQL (local or Supabase cloud)
- **Vector Search**: pgvector for semantic document search
- **File Storage**: Local filesystem (ready for cloud storage integration)

### Development Tools
- **Testing**: pytest, pytest-asyncio, httpx
- **Code Quality**: black, isort, flake8, mypy
- **Environment**: python-dotenv for configuration

---

## 🏛️ Architecture Overview

### High-Level Architecture

```
┌─────────────────┐
│   Next.js UI    │  ← User interacts via chat interface
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│   FastAPI API   │  ← Main backend server
└────────┬────────┘
         │
         ├──► LangGraph State Machine ← Conversation orchestration
         │         │
         │         ├──► Needs Assessment ← Collects trip info
         │         ├──► Risk Assessment ← Evaluates risk factors
         │         ├──► Pricing ← Generates quotes
         │         ├──► Policy Explainer ← RAG search
         │         ├──► Claims Guidance ← Claim assistance
         │         └──► Customer Service ← Human handoff
         │
         ├──► PostgreSQL Database ← Persistence
         │         ├──► Users, Trips, Quotes, Policies
         │         ├──► Chat History (LangGraph checkpoints)
         │         └──► RAG Documents (policy chunks)
         │
         └──► External Services
                   ├──► Groq LLM API ← Text generation
                   ├──► OpenAI (optional) ← Embeddings
                   └──► Stripe (configured, not implemented)
```

### Key Architectural Patterns

1. **Layered Architecture**: Routers → Services → Models
2. **Agent-Based**: LangGraph state machine for conversation flow
3. **Adapter Pattern**: Insurer adapters for pricing abstraction (currently MockInsurerAdapter)
4. **RAG Pattern**: Vector search for policy document retrieval
5. **Repository Pattern**: SQLAlchemy models with service layer abstraction

---

## 📁 Project Structure

```
Singhacks/
├── apps/
│   ├── backend/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── agents/            # LangGraph conversation graph
│   │   │   │   ├── graph.py      # Main state machine (1410 lines)
│   │   │   │   ├── llm_client.py # LLM integration (Groq/OpenAI)
│   │   │   │   └── tools.py      # Agent-accessible tools
│   │   │   ├── adapters/         # External service adapters
│   │   │   │   └── insurer/      # Insurance provider adapters
│   │   │   ├── core/             # Core configuration
│   │   │   │   ├── config.py     # Settings management
│   │   │   │   ├── db.py         # Database connection
│   │   │   │   └── security.py   # JWT/auth utilities
│   │   │   ├── models/           # SQLAlchemy database models
│   │   │   │   ├── user.py
│   │   │   │   ├── trip.py
│   │   │   │   ├── quote.py
│   │   │   │   ├── policy.py
│   │   │   │   ├── claim.py
│   │   │   │   ├── chat_history.py
│   │   │   │   └── rag_document.py
│   │   │   ├── routers/          # FastAPI route handlers
│   │   │   │   ├── chat.py       # Main chat endpoint
│   │   │   │   ├── quotes.py
│   │   │   │   ├── trips.py
│   │   │   │   ├── policies.py
│   │   │   │   ├── claims.py
│   │   │   │   ├── rag.py
│   │   │   │   └── handoff.py
│   │   │   ├── schemas/          # Pydantic validation schemas
│   │   │   └── services/         # Business logic services
│   │   │       ├── pricing.py    # Quote calculation
│   │   │       ├── rag.py        # Document search
│   │   │       ├── claims.py     # Claims assistance
│   │   │       └── handoff.py    # Human escalation
│   │   ├── alembic/              # Database migrations
│   │   ├── tests/                # Test suite (87 tests, 86% pass)
│   │   └── requirements.txt
│   │
│   └── frontend/                 # Next.js frontend
│       ├── src/
│       │   ├── app/              # Next.js app router pages
│       │   │   └── app/
│       │   │       ├── dashboard/ # User dashboard
│       │   │       └── quote/    # Quote chat interface
│       │   ├── components/       # React components
│       │   ├── contexts/         # React contexts (Auth)
│       │   └── lib/              # Utilities (Supabase client)
│       └── package.json
│
├── docs/                         # Documentation
├── infra/                        # Infrastructure config
└── docker-compose.yml            # Docker services
```

---

## 🔄 Core Conversation Flow (Quote Generation)

### Current Flow (6-Step Question Sequence)

1. **User Initiates**: "I need travel insurance" or similar
2. **Orchestrator**: Classifies intent as "quote" (uses LLM intent detection)
3. **Needs Assessment**: Collects information through conversation:
   - **Destination** (country name)
   - **Departure Date** (flexible date parsing)
   - **Return Date** (flexible date parsing)
   - **Travelers** (ages as integers)
   - **Adventure Sports** (yes/no - asked after all required fields)
4. **Confirmation**: Shows summary and asks user to confirm
5. **Risk Assessment**: Maps destination to geographic area, calculates base rates
6. **Pricing**: Generates three-tier quotes (Standard, Elite, Premier)

### Information Extraction

- **LLM-Based Extraction**: Uses Groq LLM with function calling to extract structured data from natural language
- **Flexible Parsing**: Handles dates in various formats ("Dec 20, 2025", "20/12/2025", "in 2 weeks")
- **Context-Aware**: Can extract multiple fields from a single message ("Going to France Dec 20 - Jan 3 with 2 travelers ages 30 and 32")
- **Validation**: Validates dates, ages (0.08-110 years), and required fields

### State Management

- **LangGraph State Machine**: Maintains conversation state across turns
- **PostgreSQL Checkpointing**: Persists state using LangGraph's PostgresSaver
- **Session-Based**: Each conversation has a unique `session_id` (UUID)
- **Multi-Turn Support**: Handles complex, back-and-forth conversations

---

## 💼 Key Features & Capabilities

### ✅ Implemented Features

1. **Conversational Quote Flow**
   - Multi-turn conversation for collecting trip information
   - LLM-based intent detection and information extraction
   - Structured 6-question flow with confirmation
   - Real-time quote generation with tiered pricing

2. **Pricing System**
   - Three coverage tiers: Standard, Elite, Premier
   - Geographic area-based pricing (Area 1-4)
   - Age-based multipliers (children: 0.7x, adults: 1.0x, seniors: 1.3-1.5x)
   - Adventure sports coverage detection
   - Price breakdown explanations

3. **Policy Document Search (RAG)**
   - Document ingestion and chunking
   - Text-based search (vector search pending)
   - Policy explanations with citations
   - Question-answering over policy documents

4. **Claims Guidance**
   - Support for 5 claim types: Trip Delay, Medical, Baggage, Theft, Cancellation
   - Requirements lookup and document checklists
   - Claim completeness checking
   - Claim packet generation

5. **Human Handoff System**
   - Escalation triggers (low confidence, user request)
   - Handoff request creation with conversation summary
   - Priority assignment

6. **User Management**
   - JWT-based authentication
   - Supabase Auth integration ready
   - User profiles with traveler management
   - Trip history tracking

### ⚠️ Known Limitations & TODOs

1. **Intent Detection**: Currently uses LLM classification but could be enhanced
2. **RAG Vector Search**: Currently text-based; pgvector similarity search pending
3. **Mock Insurer Adapter**: Uses mock pricing; real insurer integration pending
4. **Payment Processing**: Stripe configured but not implemented
5. **WebSocket Support**: Session-based chat works; real-time WebSocket pending

---

## 🔌 Integration Points

### Current Integrations

- **Groq LLM API**: Text generation, intent classification, information extraction
- **PostgreSQL**: Data persistence, conversation checkpoints, vector storage
- **Supabase**: Authentication (configured, optional)

### Adapter Pattern

The system uses an adapter pattern for insurer integrations:

```python
# Base adapter interface
class InsurerAdapter:
    def quote_range(...) -> Dict
    def price_firm(...) -> Dict
    def get_products(...) -> List

# Current implementation
class MockInsurerAdapter(InsurerAdapter):
    # Returns mock pricing data
```

This makes it easy to swap in real insurer APIs without changing core pricing logic.

---

## 📊 Data Models

### Core Entities

1. **User**: Authentication, profile, relationships
2. **Trip**: Destination, dates, travelers, status
3. **Quote**: Pricing data, tiers, risk breakdown, status (DRAFT, PRICED, ACCEPTED, EXPIRED)
4. **Policy**: Coverage details, effective dates, status (ACTIVE, PENDING, CANCELLED, EXPIRED)
5. **Claim**: Claim type, amount, documents, status (DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED)
6. **ChatHistory**: Conversation messages with metadata
7. **RagDocument**: Policy document chunks with embeddings

### Relationships

```
User
├── has_many Travelers
├── has_many Trips
├── has_many Quotes
├── has_many Policies
├── has_many ChatHistory
└── has_many AuditLogs

Trip ──has_many──> Quote ──has_many──> Policy ──has_many──> Claim
```

---

## 🚀 Planned Feature: OCR Document Scanning for Instant Quotes

### Feature Intent

**Goal**: Enable users to upload travel documents (e.g., flight confirmations, hotel bookings, itinerary PDFs/images) and automatically extract trip information to generate INSTANT quotes without manual conversation.

### Use Cases

1. **Flight Confirmation**: User uploads PDF/image of flight confirmation email
   - Extract: Departure date, return date, destination(s), passenger names/ages
   - Generate quote immediately

2. **Travel Itinerary**: User uploads comprehensive travel itinerary
   - Extract: All trip details, dates, destinations, travelers
   - Generate quote with all information pre-filled

3. **Hotel Booking**: User uploads hotel confirmation
   - Extract: Travel dates, destination
   - Combine with previously entered traveler info

4. **Multi-Document Upload**: User uploads multiple documents
   - Extract and merge information from all documents
   - Generate comprehensive quote

### Technical Approach

**OCR Library**: Tesseract (most likely choice)
- **Why Tesseract**: 
  - Open-source, mature, widely used
  - Python bindings (pytesseract)
  - Supports multiple image formats (PNG, JPEG, PDF)
  - Good accuracy for structured documents

**Implementation Plan**:

1. **New Endpoint**: `POST /api/v1/quotes/from-document`
   - Accepts file upload (PDF, PNG, JPEG)
   - Returns extracted trip information + instant quote

2. **OCR Service** (`app/services/ocr.py`):
   ```python
   class OCRService:
       def extract_trip_info(document: bytes) -> Dict[str, Any]:
           # 1. Preprocess image (if needed)
           # 2. Run Tesseract OCR
           # 3. Parse text for trip information
           # 4. Use LLM to extract structured data
           # 5. Return: destination, dates, travelers, etc.
   ```

3. **LLM-Assisted Extraction**:
   - OCR extracts raw text
   - LLM (Groq) parses text and extracts structured trip data
   - Reuse existing extraction logic from `llm_client.py`

4. **Integration with Existing Flow**:
   - Use same `PricingService` for quote calculation
   - Pre-populate conversation state with extracted data
   - Allow user to review/edit before confirming quote

5. **Frontend**:
   - Add file upload component to quote page
   - Show extracted information in a review UI
   - Allow editing before generating quote
   - Show "Upload Document" button alongside chat interface

### Technical Considerations

**Image Preprocessing** (may be needed):
- Deskewing
- Noise reduction
- Contrast enhancement
- PDF to image conversion

**Document Types to Support**:
- PDF files (flight confirmations, itineraries)
- PNG/JPEG images (photos of documents)
- Email exports (HTML/text)

**Error Handling**:
- Handle low-quality scans
- Partial extraction (if some fields missing, ask user)
- Validation of extracted dates/destinations
- Fallback to manual entry if OCR fails

**Performance**:
- Async processing for large documents
- Caching of OCR results
- Progress indicators for user

### Integration Points

1. **Leverage Existing Code**:
   - `PricingService.calculate_step1_quote()` - already handles quote generation
   - `LLMClient.extract_trip_info()` - can be adapted for OCR text
   - `PricingService` risk assessment and pricing logic

2. **New Components Needed**:
   - OCR service module
   - Document upload endpoint
   - Text preprocessing utilities
   - Document parsing logic

3. **Database Changes**:
   - Add `document_url` or `document_storage_path` to `Trip` model (optional)
   - Store extracted raw text for audit/debugging

### Expected User Flow

```
1. User clicks "Upload Document" button
2. User selects PDF/image file
3. Backend receives file → OCR extracts text
4. LLM parses text → Extracts: destination, dates, travelers
5. Backend generates quote instantly using PricingService
6. Frontend shows extracted info + quote tiers
7. User can:
   - Accept quote immediately
   - Edit extracted information
   - Start conversation to clarify details
```

### Benefits

- **Instant Quotes**: No conversation needed if document is clear
- **User Convenience**: Reduces manual data entry
- **Accuracy**: LLM-assisted extraction reduces errors
- **Competitive Advantage**: Faster than competitors who require forms

---

## 🔧 Development Environment

### Setup

```bash
# 1. Clone and configure
cp infra/env.example .env
# Edit .env with API keys

# 2. Start database
docker-compose up -d db

# 3. Run migrations
cd apps/backend
alembic upgrade head

# 4. Start backend
uvicorn app.main:app --reload

# 5. Start frontend
cd apps/frontend
npm run dev
```

### Environment Variables

**Required**:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT signing key

**Optional**:
- `GROQ_API_KEY` - Groq LLM API key
- `OPENAI_API_KEY` - OpenAI API key (for embeddings)
- `SUPABASE_URL`, `SUPABASE_ANON_KEY` - Supabase auth (optional)

### Testing

- **Backend**: `pytest` (87 tests, 86% pass rate)
- **Coverage**: Comprehensive test suite for services, routers, agents
- **Integration Tests**: Full conversation flow tests

---

## 📈 Current Status

### ✅ Production-Ready Components

- API infrastructure (all routers registered, CORS configured)
- Database models (complete with relationships)
- Services (pricing, claims, RAG logic fully implemented)
- LLM client (Groq/OpenAI integration working)
- Conversation graph (operational with 8 nodes)
- Frontend UI (dashboard, quote chat interface)

### ⚠️ Areas for Enhancement

- RAG vector search (currently text-based)
- Real insurer adapter (currently mock)
- Payment processing (Stripe configured but not implemented)
- WebSocket real-time chat (session-based works)

---

## 🎯 Strategic Direction

### Current Focus
- Refining conversation flow
- Improving extraction accuracy
- Expanding policy document coverage for RAG

### Near-Term Roadmap
1. **OCR Integration** (planned feature)
   - Implement Tesseract OCR
   - Document upload endpoint
   - Instant quote generation
2. **Vector Search Enhancement**
   - Implement pgvector similarity search
   - Improve RAG accuracy
3. **Payment Integration**
   - Complete Stripe integration
   - Policy purchase flow

### Long-Term Vision
- Multi-language support
- Mobile app
- Advanced analytics and personalization
- Integration with multiple insurer APIs

---

## 📚 Key Files Reference

### Essential Files

**Backend**:
- `apps/backend/app/main.py` - FastAPI application entry
- `apps/backend/app/agents/graph.py` - Conversation state machine (1410 lines)
- `apps/backend/app/routers/chat.py` - Main chat endpoint
- `apps/backend/app/services/pricing.py` - Quote calculation logic
- `apps/backend/app/services/rag.py` - Document search service
- `apps/backend/app/agents/llm_client.py` - LLM integration

**Frontend**:
- `apps/frontend/src/app/app/dashboard/page.tsx` - User dashboard
- `apps/frontend/src/app/app/quote/page.tsx` - Quote chat interface

**Configuration**:
- `apps/backend/app/core/config.py` - Settings management
- `.env` - Environment variables

---

## 🧪 Testing Status

- **Total Tests**: 87
- **Passing**: 75 (86%)
- **Failing**: 12 (14% - mostly mock data type mismatches, low impact)

### Test Coverage
- ✅ LLM Client (14/14 passing)
- ✅ Conversation Tools (12/12 passing)
- ✅ API Integration (13/13 passing)
- ✅ Pricing Service (6/6 passing)
- ✅ Claims Service (5/5 passing)
- ⚠️ Chat Router (4/8 passing - mock issues)
- ⚠️ Graph Integration (6/8 passing)
- ⚠️ RAG Service (4/6 passing - UUID validation)
- ❌ Handoff Service (0/4 passing - database fixtures needed)

---

## 🔐 Security & Compliance

- **Authentication**: JWT tokens with Supabase Auth integration
- **Authorization**: User-scoped data access
- **Data Validation**: Pydantic schemas for all inputs
- **SQL Injection Protection**: SQLAlchemy ORM
- **CORS**: Configured for frontend origin
- **Environment Variables**: Secure credential management

---

## 📝 Notes for OCR Implementation

When implementing OCR feature:

1. **Reuse Existing Logic**: 
   - Leverage `LLMClient.extract_trip_info()` for parsing OCR text
   - Use `PricingService.calculate_step1_quote()` for instant quotes
   - Follow same validation patterns as conversation flow

2. **Error Handling**:
   - Handle OCR failures gracefully
   - Partial extraction is acceptable (ask user for missing fields)
   - Validate extracted data before generating quote

3. **User Experience**:
   - Show extracted information for review before quote generation
   - Allow editing of extracted fields
   - Provide option to start conversation if OCR fails

4. **Performance**:
   - Consider async processing for large documents
   - Cache OCR results to avoid re-processing
   - Optimize image preprocessing

5. **Dependencies**:
   - Add `pytesseract` to `requirements.txt`
   - May need `Pillow` for image processing
   - Consider `pdf2image` for PDF handling

---

**End of Summary**

This document provides a comprehensive overview of the ConvoTravelInsure codebase, its architecture, current features, and the planned OCR enhancement. Use this as context for understanding the system and implementing new features.

