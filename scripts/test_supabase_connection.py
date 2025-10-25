#!/usr/bin/env python3
"""Test script to verify Supabase database connection."""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend'))

from sqlalchemy import create_engine, text
from app.core.config import settings


def test_connection():
    """Test the database connection."""
    print("🔍 Testing Supabase connection...")
    print(f"📍 Database URL: {settings.database_url.replace(settings.database_url.split('@')[0].split(':')[2], '***')}")
    
    try:
        # Create engine
        engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            connect_args={
                "sslmode": "prefer" if "supabase.co" in settings.database_url else "disable"
            }
        )
        
        # Test connection
        print("\n📡 Attempting to connect...")
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print("✅ Connection successful!")
            print(f"📊 PostgreSQL version: {version[:50]}...")
            
            # Check if we're connected to Supabase
            if "supabase.co" in settings.database_url:
                print("🎉 Connected to Supabase!")
            else:
                print("📍 Connected to local database")
            
            # List tables
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = result.fetchall()
            
            if tables:
                print(f"\n📋 Found {len(tables)} table(s):")
                for table in tables:
                    print(f"   - {table[0]}")
            else:
                print("\n⚠️  No tables found. Run migrations to create tables.")
                print("   Run: cd apps/backend && alembic upgrade head")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check your .env file has the correct DATABASE_URL")
        print("   2. Verify your Supabase credentials")
        print("   3. Check firewall settings in Supabase dashboard")
        print("   4. Ensure your IP is whitelisted in Supabase")
        sys.exit(1)


if __name__ == "__main__":
    test_connection()
