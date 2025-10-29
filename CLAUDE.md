# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ConvoTravelInsure is a conversational travel insurance platform that provides AI-powered quoting, policy explanation, and claims guidance through natural language interaction. Built as a hackathon MVP, it uses LangGraph for conversation orchestration and Groq's LLM for natural language understanding.

## Essential Commands

### Development Setup
```bash
# Initial setup
cp infra/env.example .env
# Edit .env with your API keys (GROQ_API_KEY, DATABASE_URL, etc.)

# Start all services with Docker (recommended)
make up

# Install dependencies locally
make install

# Start database only
docker-compose up -d db
```

### Backend Development
```bash
cd apps/backend

# Run backend locally (requires database running)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Database migrations
alembic upgrade head                    # Apply all migrations
alembic revision --autogenerate -m "msg"  # Create new migration
alembic downgrade -1                    # Rollback one migration
alembic current                         # Check current version

# Run tests
pytest                                  # Run all tests
pytest tests/test_pricing.py           # Run specific test file

# Seed database with sample data
python -m app.scripts.seed_data
```

### Frontend Development
```bash
cd apps/frontend

# Run frontend locally
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

### Docker Operations
```bash
make up           # Start all services
make down         # Stop all services
make logs         # View logs
make migrate      # Run database migrations in container
make test         # Run all tests
make clean        # Clean up containers and volumes
make restart      # Quick restart
```

### Database Access
```bash
# Access database shell
make db-shell
# or
docker-compose exec db psql -U postgres -d convo_travel_insure

# Access backend container shell
make backend-shell

# Test Supabase connection
python scripts/test_supabase_connection.py
```

## Architecture

### Tech Stack
- **Backend**: FastAPI (Python 3.11), LangGraph, LangChain, SQLAlchemy
- **Frontend**: Next.js 14, TypeScript, TailwindCSS, Radix UI
- **Database**: PostgreSQL 16 with pgvector extension (local or Supabase)
- **LLM**: Groq API (Llama 3.1 70B Versatile)
- **Infrastructure**: Docker Compose

### Key Architectural Patterns

**1. LangGraph Conversation Flow**
The core conversation logic uses LangGraph state machines in `apps/backend/app/agents/graph.py`:
- **Orchestrator Node**: Routes user intents (quote, policy_explanation, claims_guidance, human_handoff)
- **Quote Flow**: Multi-step conversation collecting trip details → risk assessment → pricing
- **State Management**: Uses `ConversationState` TypedDict with fields for trip details, travelers, preferences
- **Loop Protection**: `_loop_count` and explicit exit flags (`_pricing_complete`) prevent infinite loops
- **No Checkpointing**: Phase 1 has checkpointing disabled (line 47-52); will use PostgresSaver in Phase 2

**2. Conversation State Structure**
```python
{
    "messages": [HumanMessage, AIMessage],  # Conversation history
    "current_intent": "quote|policy_explanation|claims_guidance",
    "trip_details": {"destination", "departure_date", "return_date", "area", "base_rate"},
    "travelers_data": {"ages": [30, 35, 8], "count": 3},
    "preferences": {"adventure_sports": bool},
    "quote_data": {...},  # Full pricing result
    "_ready_for_pricing": bool,  # Internal flow control
    "_pricing_complete": bool    # Prevents re-entry
}
```

**3. Router Structure**
API routers are organized by domain in `apps/backend/app/routers/`:
- `auth.py` - User registration/login
- `quotes.py` - Quote generation and retrieval
- `chat.py` - Main LangGraph conversation endpoint
- `trips.py` - Trip management
- `claims.py` - Claims submission and guidance
- `policies.py` - Policy document management
- `rag.py` - RAG search for policy documents
- `handoff.py` - Human agent handoff system
- `voice.py` - Voice input support

All routers are imported in `app/routers/__init__.py` and mounted in `app/main.py` with prefix `/api/v1`.

**4. Database Models**
SQLAlchemy models in `apps/backend/app/models/`:
- `user.py` - User accounts with hashed passwords
- `trip.py` - Trip details (destination, dates, status)
- `traveler.py` - Individual travelers with ages
- `quote.py` - Insurance quotes with pricing tiers
- `policy.py` - Purchased policies
- `claim.py` - Filed claims with status tracking
- `rag_document.py` - Policy documents with pgvector embeddings
- `chat_history.py` - Conversation persistence
- `audit_log.py` - Audit trail for compliance

**5. Pricing Service Architecture**
`apps/backend/app/services/pricing.py`:
- Geographic area mapping via `GeoMapper` (Japan=asia_developed, Thailand=asia_developing, etc.)
- Base rates by area (asia_developed: 50 SGD, asia_developing: 40 SGD, etc.)
- Three pricing tiers: Standard (1x), Elite (1.5x), Premier (2x)
- Age-based multipliers: 0-17 (0.8x), 18-64 (1.0x), 65+ (1.5x)
- Adventure sports add 30% to premium
- Maximum trip duration: 182 days

**6. Configuration Management**
Settings in `apps/backend/app/core/config.py` using pydantic-settings:
- Loads from `.env` in project root (referenced as `../../.env`)
- Critical variables: `DATABASE_URL`, `GROQ_API_KEY`, `SECRET_KEY`
- Optional Supabase configs: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
- LangGraph checkpoint DB: `LANGGRAPH_CHECKPOINT_DB` (currently unused)

### Database Connection Options

**Local PostgreSQL** (default for development):
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/convo_travel_insure
```

**Supabase** (for cloud deployment):
```bash
DATABASE_URL=postgresql://postgres:[PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres?sslmode=require
```

See `docs/QUICK_START_SUPABASE.md` for Supabase setup instructions.

## Important Implementation Details

### Database Migrations
- Always create migrations from `apps/backend` directory
- Use `alembic revision --autogenerate` to detect model changes
- Review generated migrations before applying (check `alembic/versions/`)
- Alembic configuration is in `apps/backend/alembic/env.py`
- Migration files follow pattern: `{revision}_{description}.py`

### LangGraph Flow Control
When modifying conversation logic in `apps/backend/app/agents/graph.py`:
- Always update loop protection counter `_loop_count` to prevent infinite loops
- Use explicit completion flags (`_pricing_complete`, `_ready_for_pricing`) to control flow
- The `should_continue()` function handles routing between nodes - update conditional edges there
- Test quote flow end-to-end: greeting → destination → dates → travelers → sports → confirmation → pricing → END
- Avoid adding AI messages in routing functions; only add messages in node functions

### Adding New API Endpoints
1. Create router file in `apps/backend/app/routers/`
2. Import and register in `app/routers/__init__.py`
3. Mount in `app/main.py` with `app.include_router(router, prefix=settings.api_v1_prefix)`
4. Define Pydantic schemas in `app/schemas/`
5. Add database models in `app/models/` if needed
6. Create migration: `alembic revision --autogenerate -m "add_new_feature"`

### Frontend Structure
- App Router pattern: pages in `apps/frontend/src/app/`
- UI components: `apps/frontend/src/components/` (custom) and `apps/frontend/src/components/ui/` (Radix/shadcn)
- API calls to backend via `NEXT_PUBLIC_API_URL` environment variable
- TailwindCSS v4 configuration

### Testing Strategy
- Backend tests use pytest in `apps/backend/tests/`
- Test database: `DATABASE_TEST_URL` from `.env`
- Key test files: `test_pricing.py` (pricing logic), `test_rag.py` (document search)
- Integration tests via `make test` run in Docker containers

## Common Issues and Solutions

### Alembic Migration Conflicts
If you see "multiple heads" or conflicts:
```bash
alembic merge heads -m "merge"
alembic upgrade head
```

### Database Connection Issues
- Verify `.env` is in project root (not `infra/`)
- Check DATABASE_URL format matches your setup (local vs Supabase)
- For Supabase, ensure `?sslmode=require` is appended
- Test connection: `python scripts/test_supabase_connection.py`

### LangGraph Infinite Loops
- Check `_loop_count` limit (currently 20 in `should_continue()`)
- Verify `_pricing_complete` is set after pricing node completes
- Review conditional edges in graph definition
- Enable debug logging: look for `🔀 Routing` messages

### Port Conflicts
If ports 3000 or 8000 are in use:
```bash
# Find process using port
lsof -i :8000
# Kill process
kill -9 <PID>
```

## Environment Variables Reference

Required:
- `DATABASE_URL` - PostgreSQL connection string
- `GROQ_API_KEY` - Groq API key for LLM (get from console.groq.com)

Optional but recommended:
- `SECRET_KEY` - JWT signing secret (change in production)
- `STRIPE_SECRET_KEY` - Stripe API key for payments
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key

## Project Status

This is a hackathon MVP with the following status:
- ✅ Conversational quote flow with LangGraph
- ✅ Multi-step information collection (6 questions)
- ✅ Geographic risk assessment and tiered pricing
- ✅ Policy document RAG search
- ✅ Claims guidance wizard
- ✅ Human handoff system
- ⚠️ Checkpointing disabled (Phase 1) - will enable with PostgresSaver in Phase 2
- 🔄 Real payment processing (Stripe integration stubbed)
- 🔄 Production authentication (currently basic JWT)

## References

- Full setup instructions: `README.md`
- Database migration guide: `docs/DATABASE_MIGRATION_GUIDE.md`
- Supabase quick start: `docs/QUICK_START_SUPABASE.md`
- Database setup summary: `docs/DATABASE_SETUP_SUMMARY.md`
- API documentation: http://localhost:8000/docs (when running)
