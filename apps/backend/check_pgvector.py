#!/usr/bin/env python3
"""Check if pgvector extension is enabled in Supabase database."""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_pgvector():
    """Check if pgvector extension is installed and enabled."""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL not found in environment variables")
        print("Please set DATABASE_URL in your .env file")
        sys.exit(1)
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check if pgvector extension exists
            result = conn.execute(text("""
                SELECT 
                    extname as extension_name,
                    extversion as version
                FROM pg_extension 
                WHERE extname = 'vector';
            """))
            
            extension = result.fetchone()
            
            if extension:
                print("✅ pgvector extension is ENABLED")
                print(f"   Extension: {extension[0]}")
                print(f"   Version: {extension[1]}")
                
                # Check if we can create a test vector column
                try:
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS _pgvector_test (
                            id SERIAL PRIMARY KEY,
                            embedding vector(1536)
                        );
                    """))
                    conn.execute(text("DROP TABLE IF EXISTS _pgvector_test;"))
                    conn.commit()
                    print("✅ Vector type is functional - can create vector columns")
                except Exception as e:
                    print(f"⚠️  WARNING: Vector type may not be fully functional: {e}")
                    conn.rollback()
                
            else:
                print("❌ pgvector extension is NOT ENABLED")
                print("\nTo enable it:")
                print("1. Go to Supabase Dashboard → SQL Editor")
                print("2. Run: CREATE EXTENSION IF NOT EXISTS vector;")
                print("3. Or run migrations: alembic upgrade head")
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ ERROR connecting to database: {e}")
        print("\nTroubleshooting:")
        print("1. Check DATABASE_URL is correct")
        print("2. Verify Supabase project is active")
        print("3. Check network connectivity")
        sys.exit(1)

if __name__ == "__main__":
    check_pgvector()

