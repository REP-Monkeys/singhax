#!/usr/bin/env python3
"""Mark the JSON storage fields migration as applied in Alembic version table."""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def mark_migration_applied():
    """Mark migration a1b2c3d4e5f6 as applied."""
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found")
        sys.exit(1)
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                # Check current version
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                current_version = result.scalar()
                print(f"📋 Current Alembic version: {current_version}")
                
                # Check if our migration is already applied
                check_result = conn.execute(text("""
                    SELECT version_num FROM alembic_version WHERE version_num = 'a1b2c3d4e5f6'
                """))
                
                if check_result.scalar():
                    print("✅ Migration a1b2c3d4e5f6 is already marked as applied")
                else:
                    # Update to our migration version
                    conn.execute(text("UPDATE alembic_version SET version_num = 'a1b2c3d4e5f6'"))
                    trans.commit()
                    print("✅ Marked migration a1b2c3d4e5f6 as applied")
                    
            except Exception as e:
                trans.rollback()
                # If alembic_version table doesn't exist or migration already applied, that's okay
                print(f"ℹ️  Note: {e}")
                
    except Exception as e:
        print(f"⚠️  Could not update Alembic version (this is okay): {e}")

if __name__ == "__main__":
    mark_migration_applied()

