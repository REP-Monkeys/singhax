#!/bin/bash

# Migration script to set up Supabase database
# Run this after creating your Supabase project and updating .env

echo "🚀 Migrating to Supabase..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it first."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set in .env file"
    exit 1
fi

echo "📊 Database URL: $DATABASE_URL"

# Navigate to backend directory
cd apps/backend

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create initial migration
echo "🔄 Creating initial migration..."
alembic revision --autogenerate -m "Initial migration for Supabase"

# Run migrations
echo "🚀 Running migrations..."
alembic upgrade head

echo "✅ Migration complete!"
echo ""
echo "Next steps:"
echo "1. Update your .env file with actual Supabase credentials"
echo "2. Test your application: docker-compose up"
echo "3. Check your Supabase dashboard to see the tables"
