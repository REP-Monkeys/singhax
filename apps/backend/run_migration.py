#!/usr/bin/env python3
"""Script to add JSON storage columns directly to database."""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_json_columns():
    """Add JSONB columns to quotes and trips tables."""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("Please set DATABASE_URL in your .env file")
        sys.exit(1)
    
    print(f"📊 Connecting to database...")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                print("🔄 Adding columns to quotes table...")
                conn.execute(text("""
                    ALTER TABLE quotes 
                    ADD COLUMN IF NOT EXISTS ancileo_quotation_json JSONB,
                    ADD COLUMN IF NOT EXISTS ancileo_purchase_json JSONB
                """))
                
                print("🔄 Adding column to trips table...")
                conn.execute(text("""
                    ALTER TABLE trips 
                    ADD COLUMN IF NOT EXISTS metadata_json JSONB
                """))
                
                # Commit transaction
                trans.commit()
                print("✅ Successfully added JSON columns!")
                
                # Verify columns were added
                print("\n📋 Verifying columns...")
                result = conn.execute(text("""
                    SELECT 
                        table_name,
                        column_name, 
                        data_type 
                    FROM information_schema.columns 
                    WHERE table_name IN ('quotes', 'trips') 
                        AND column_name IN ('ancileo_quotation_json', 'ancileo_purchase_json', 'metadata_json')
                    ORDER BY table_name, column_name
                """))
                
                rows = result.fetchall()
                if rows:
                    print("\n✅ Columns successfully added:")
                    for row in rows:
                        print(f"   - {row[0]}.{row[1]} ({row[2]})")
                else:
                    print("⚠️  Warning: Could not verify columns (but migration may have succeeded)")
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error adding columns: {e}")
                raise
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_json_columns()

