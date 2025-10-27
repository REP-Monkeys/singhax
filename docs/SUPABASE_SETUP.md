# Connecting to Supabase

This guide will help you connect your application to Supabase's PostgreSQL database.

## Prerequisites

- A Supabase account ([https://supabase.com](https://supabase.com))
- A Supabase project created

## Step 1: Get Your Supabase Connection String

1. Go to your Supabase dashboard
2. Navigate to **Project Settings** → **Database**
3. Scroll down to **Connection string** section
4. Select **URI** format
5. Copy the connection string (it will look like this):

```
postgresql://postgres:[YOUR-PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres
```

**Note:** You'll need to replace `[YOUR-PASSWORD]` with your actual database password and `[PROJECT-REF]` with your project reference ID.

## Step 2: Configure Environment Variables

### Create `.env` File

Create a `.env` file in the root of your project (or in `apps/backend/` if running from there):

```bash
# Copy the example file
cp infra/env.example .env
```

### Update `.env` with Supabase Credentials

```env
# Database Configuration - Replace with your Supabase connection string
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres

# Optional: Test database (can use same URL or a different database)
DATABASE_TEST_URL=postgresql://postgres:[YOUR-PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External APIs
GROQ_API_KEY=your-groq-api-key-here
STRIPE_SECRET_KEY=your-stripe-secret-key-here
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key-here

# Application Settings
DEBUG=true
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## Step 3: Run Database Migrations

### Option A: Using the Migration Script

```bash
chmod +x scripts/migrate-to-supabase.sh
./scripts/migrate-to-supabase.sh
```

### Option B: Manual Migration

```bash
cd apps/backend

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head
```

## Step 4: Verify Connection

### Check Tables in Supabase Dashboard

1. Go to **Table Editor** in your Supabase dashboard
2. You should see all your tables created (users, trips, quotes, policies, claims, etc.)

### Test the Connection

```bash
cd apps/backend

# Start the backend
python -m app.main
```

## Important Security Notes

### 1. Password Security

- Never commit your `.env` file to version control
- Use Supabase's **Connection Pooling** for production
- Consider using **transactions** mode for connection pooling

### 2. Connection Pooling (Recommended for Production)

Supabase provides a connection pooling endpoint. Update your connection string to:

```
postgresql://postgres:[YOUR-PASSWORD]@[PROJECT-REF].supabase.co:6543/postgres?pgbouncer=true
```

Note the port change from `5432` to `6543` and the `pgbouncer=true` parameter.

### 3. SSL Connection (Recommended)

Supabase requires SSL for secure connections. Update your connection string:

```
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres?sslmode=require
```

## Troubleshooting

### Connection Refused

- Check that your IP is not blocked in Supabase firewall settings
- Verify the connection string is correct
- Ensure you're using the right port (5432 for direct, 6543 for pooling)

### Migration Errors

- Make sure your database is empty or use `alembic downgrade -1` to rollback
- Check that all required dependencies are installed
- Verify the database URL is accessible

### SSL/TLS Issues

- Add `?sslmode=require` to your connection string
- For connection pooling, use the `pgbouncer=true` parameter

## Additional Resources

- [Supabase Database Documentation](https://supabase.com/docs/guides/database)
- [Supabase Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
