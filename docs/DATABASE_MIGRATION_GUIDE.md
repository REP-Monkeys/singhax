# Database Migration Guide

Quick reference for managing database migrations with Alembic and Supabase.

## Initial Setup

```bash
cd apps/backend
source venv/bin/activate
pip install alembic sqlalchemy psycopg2-binary pgvector python-dotenv pydantic-settings
```

## Running Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Check current version
alembic current

# View migration history
alembic history
```

## Creating Migrations

1. Edit models in `app/models/`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review generated file in `alembic/versions/`
4. Apply: `alembic upgrade head`

## Rollback

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision>
```

## Verify in Supabase

1. Open Supabase dashboard
2. Go to Table Editor
3. Check that tables exist

## Common Commands

- `alembic upgrade head` - Apply all pending migrations
- `alembic downgrade -1` - Rollback last migration  
- `alembic current` - Show current version
- `alembic history` - Show all migrations
- `alembic revision --autogenerate -m "msg"` - Create new migration
