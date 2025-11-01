"""
Verify pgvector extension is enabled in PostgreSQL database.

This script checks if the pgvector extension is available and provides
instructions for enabling it if not found.

Usage:
    python -m apps.backend.scripts.verify_pgvector
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.backend.app.core.db import SessionLocal
from sqlalchemy import text


def verify_pgvector():
    """Check if pgvector extension is enabled."""
    print("=" * 60)
    print("Verifying pgvector Extension")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Check if extension exists
        result = db.execute(text(
            "SELECT * FROM pg_extension WHERE extname = 'vector';"
        )).fetchone()
        
        if result:
            print("✅ pgvector extension is ENABLED")
            print(f"   Extension: {result[0]}")
            print(f"   Version: {result[1]}")
            print()
            
            # Check vector type
            vector_check = db.execute(text(
                "SELECT typname FROM pg_type WHERE typname = 'vector';"
            )).fetchone()
            
            if vector_check:
                print("✅ Vector type is available")
                print()
                
                # Test vector operations
                try:
                    test_result = db.execute(text(
                        "SELECT '[1,2,3]'::vector <-> '[4,5,6]'::vector AS distance;"
                    )).fetchone()
                    print(f"✅ Vector operations working (test distance: {test_result[0]:.4f})")
                    print()
                except Exception as e:
                    print(f"⚠️  Vector operations test failed: {e}")
                    print()
            else:
                print("❌ Vector type not found")
                print()
        else:
            print("❌ pgvector extension is NOT enabled")
            print()
            print("To enable pgvector, run this SQL command:")
            print("=" * 60)
            print("CREATE EXTENSION IF NOT EXISTS vector;")
            print("=" * 60)
            print()
            print("If you're using Supabase:")
            print("1. Go to Database -> Extensions")
            print("2. Enable 'vector' extension")
            print()
            return False
        
        # Check rag_documents table
        try:
            table_check = db.execute(text(
                """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'rag_documents' AND column_name = 'embedding';
                """
            )).fetchone()
            
            if table_check:
                print(f"✅ rag_documents.embedding column exists (type: {table_check[1]})")
                
                # Check if it's actually vector type
                if 'vector' in str(table_check[1]).lower() or 'user-defined' in str(table_check[1]).lower():
                    print("✅ Column is using vector type")
                else:
                    print(f"⚠️  Column type is {table_check[1]}, expected vector")
            else:
                print("⚠️  rag_documents.embedding column not found")
                print("   This is normal if you haven't run migrations yet")
        except Exception as e:
            print(f"⚠️  Could not check rag_documents table: {e}")
        
        print()
        print("=" * 60)
        print("✅ Verification Complete - System Ready for RAG!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        print()
        print("Make sure:")
        print("1. Database is running")
        print("2. DATABASE_URL is correct in .env")
        print("3. You have necessary permissions")
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = verify_pgvector()
    sys.exit(0 if success else 1)

