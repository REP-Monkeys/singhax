# ConvoTravelInsure

A conversational travel insurance platform that provides AI-powered quoting, policy explanation, and claims guidance through natural language interaction.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- Supabase account (optional, for cloud database)

### Running with Docker (Recommended)

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd Singhacks
   cp infra/env.example .env
   # Edit .env with your API keys
   ```

2. **Connect to Supabase (Optional):**
   See [docs/QUICK_START_SUPABASE.md](docs/QUICK_START_SUPABASE.md) for quick setup.

3. **Start all services:**
   ```bash
   make up
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Local Development

1. **Setup environment:**
   ```bash
   cp infra/env.example .env
   # Edit .env with your configuration
   ```

2. **Install dependencies:**
   ```bash
   make install
   ```

3. **Start database:**
   ```bash
   docker-compose up -d db
   ```

4. **Run migrations:**
   ```bash
   make migrate
   ```

5. **Start backend:**
   ```bash
   cd apps/backend
   uvicorn app.main:app --reload
   ```

6. **Start frontend:**
   ```bash
   cd apps/frontend
   npm run dev
   ```

## 🏗️ Architecture

### Tech Stack

- **Frontend:** Next.js 14, TypeScript, TailwindCSS
- **Backend:** FastAPI, Python 3.11, LangGraph, LangChain
- **Database:** PostgreSQL 16 with pgvector
- **LLM:** Groq (Llama3/Mixtral)
- **Infrastructure:** Docker, docker-compose

### Project Structure

```
├── apps/
│   ├── frontend/          # Next.js frontend application
│   └── backend/           # FastAPI backend application
├── packages/
│   └── shared/            # Shared types and schemas
├── infra/                 # Infrastructure configuration
│   ├── docker-compose.yml
│   ├── init.sql
│   └── env.example
├── docs/                  # Documentation
└── Makefile              # Development commands
```

## 🔧 Configuration

### Environment Variables

Copy `infra/env.example` to `.env` and configure:

```bash
# Database (Supabase or Local)
DATABASE_URL=postgresql://postgres:password@localhost:5432/convo_travel_insure
# Or for Supabase:
# DATABASE_URL=postgresql://postgres:[PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres?sslmode=require

# External APIs
GROQ_API_KEY=your-groq-api-key
STRIPE_SECRET_KEY=your-stripe-secret-key
ANCILEO_MSIG_API_KEY=your-ancileo-api-key
ANCILEO_API_BASE_URL=https://dev.api.ancileo.com

# Security
SECRET_KEY=your-secret-key-change-in-production
```

### Connecting to Supabase

For cloud database hosting, see our [Supabase Setup Guide](docs/QUICK_START_SUPABASE.md).

### API Keys

1. **Groq API Key:** Get from https://console.groq.com/
2. **Stripe Keys:** Get from https://dashboard.stripe.com/
3. **Ancileo MSIG API Key:** Contact Ancileo for hackathon API access

## 📚 API Documentation

### Authentication

```bash
# Register user
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "password123"
}

# Login
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}
```

### Quotes

```bash
# Create quote
POST /api/v1/quotes/
{
  "trip_id": "uuid",
  "product_type": "single",
  "travelers": [...],
  "activities": [...]
}

# Get firm price
POST /api/v1/quotes/{quote_id}/price
```

### RAG Search

```bash
# Search policy documents
GET /api/v1/rag/search?q=medical coverage&limit=5
```

## 🧪 Testing

### Backend Tests

```bash
cd apps/backend
pytest
```

### Frontend Tests

```bash
cd apps/frontend
npm test
```

### Integration Tests

```bash
make test
```

## 🐳 Docker Commands

```bash
# Start all services
make up

# Stop all services
make down

# View logs
make logs

# Run migrations
make migrate

# Load seed data
make seed

# Clean up
make clean
```

## 🔍 Development

### Adding New Features

1. **Backend:** Add new routers in `apps/backend/app/routers/`
2. **Frontend:** Add new pages in `apps/frontend/src/app/`
3. **Database:** Create migrations with `alembic revision --autogenerate`

### Database Migrations

See [docs/DATABASE_MIGRATION_GUIDE.md](docs/DATABASE_MIGRATION_GUIDE.md) for detailed instructions.

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 📖 Features

### Current Features

- ✅ **Real Ancileo MSIG API Integration**
  - Live insurance quotations via Ancileo API
  - 3-tier pricing (Standard/Elite/Premier)
  - Automatic policy issuance after payment
  - Fresh quotes to avoid expiration
- ✅ **Conversational quote flow**
  - AI-powered multi-turn dialogue
  - Natural language processing with Groq LLM
  - Flexible date parsing
- ✅ **Payment Processing**
  - Stripe checkout integration
  - Webhook-based confirmation
  - Automatic policy creation
- ✅ **Price range and firm pricing**
- ✅ **Policy document search (RAG)**
- ✅ **Claims guidance wizard**
- ✅ **Claims intelligence**
  - 72K+ historical claims analysis
  - Data-driven risk assessment
- ✅ **Voice input support**
- ✅ **Human handoff system**
- ✅ **Multi-traveler support**

### Pricing Strategy

The system uses a **3-tier pricing model** integrated with Ancileo MSIG API:

1. **Elite Tier (Baseline)**: Price directly from Ancileo API
2. **Standard Tier**: Elite price ÷ 1.8 (~56% of Elite)
3. **Premier Tier**: Elite price × 1.39 (~139% of Elite)

This ensures:
- Real market pricing from Ancileo
- Competitive Standard tier for budget travelers
- Premium tier for maximum coverage

### TODO Features

- 🔄 Traveler details collection in conversation flow
- 🔄 Vector-based RAG search (pgvector)
- 🔄 Real-time chat (WebSockets)
- 🔄 Mobile app
- 🔄 Voice input (speech-to-text)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is for hackathon purposes. See LICENSE file for details.

## 🆘 Support

For questions or issues:

1. Check the documentation in `/docs`
2. Review API documentation at `/docs`
3. Create an issue in the repository
4. Contact the development team

## 🚀 Deployment

### Production Deployment

1. **Build production images:**
   ```bash
   make build
   ```

2. **Deploy:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Environment Setup

- Set production environment variables
- Configure SSL certificates
- Set up monitoring and logging
- Configure backup strategies

---

**Note:** This is a hackathon MVP. For production use, additional security, monitoring, and compliance features would be required.
