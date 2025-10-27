#!/usr/bin/env python3
"""Check all database tables."""

from app.core.config import settings
from sqlalchemy import create_engine, text

def check_all_tables():
    """Check all tables in the database."""
    try:
        engine = create_engine(settings.database_url)
        conn = engine.connect()
        
        # Get all tables
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result]
        print(f"All tables in database:")
        for table in tables:
            print(f"  - {table}")
        
        conn.close()
        return tables
        
    except Exception as e:
        print(f"Error checking database: {e}")
        return []

if __name__ == "__main__":
    tables = check_all_tables()
    print(f"Total tables: {len(tables)}")
