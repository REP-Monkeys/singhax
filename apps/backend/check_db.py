#!/usr/bin/env python3
"""Check database for LangGraph checkpoint tables."""

from app.core.config import settings
from sqlalchemy import create_engine, text

def check_checkpoint_tables():
    """Check if LangGraph checkpoint tables exist."""
    try:
        engine = create_engine(settings.database_url)
        conn = engine.connect()
        
        # Check for checkpoint tables
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%checkpoint%'
        """))
        
        tables = [row[0] for row in result]
        print(f"Checkpoint tables found: {tables}")
        
        # Check for LangGraph specific tables
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND (table_name LIKE '%langgraph%' OR table_name LIKE '%thread%')
        """))
        
        langgraph_tables = [row[0] for row in result]
        print(f"LangGraph tables found: {langgraph_tables}")
        
        conn.close()
        return len(tables) > 0 or len(langgraph_tables) > 0
        
    except Exception as e:
        print(f"Error checking database: {e}")
        return False

if __name__ == "__main__":
    has_tables = check_checkpoint_tables()
    print(f"Has checkpoint tables: {has_tables}")
