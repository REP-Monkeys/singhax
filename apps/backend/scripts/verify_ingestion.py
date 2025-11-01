"""Verify RAG document ingestion results."""

import sys
from pathlib import Path

# Setup path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))
project_root = Path(__file__).parent.parent.parent.parent

# Load environment
from dotenv import load_dotenv
env_path = project_root / '.env'
load_dotenv(env_path)

from app.core.db import SessionLocal
from app.models.rag_document import RagDocument

def main():
    db = SessionLocal()
    
    try:
        print("="*60)
        print("RAG Document Ingestion Verification")
        print("="*60)
        
        # Total count
        total = db.query(RagDocument).count()
        print(f"\n✅ Total documents: {total}")
        
        # Count by title
        from sqlalchemy import text
        results = db.execute(
            text("SELECT title, COUNT(*) as count FROM rag_documents GROUP BY title ORDER BY title")
        ).fetchall()
        
        print("\n📚 Documents by title:")
        for title, count in results:
            print(f"   {title}: {count} chunks")
        
        # Sample documents
        print("\n📄 Sample documents:")
        samples = db.query(RagDocument).limit(3).all()
        for doc in samples:
            print(f"\n   ID: {doc.id}")
            print(f"   Title: {doc.title}")
            print(f"   Section: {doc.section_id} - {doc.heading}")
            print(f"   Text: {doc.text[:100]}...")
            print(f"   Embedding dimension: {len(doc.embedding) if doc.embedding is not None else 0}")
            if doc.citations:
                print(f"   Pages: {doc.citations.get('pages', [])}")
        
        print("\n" + "="*60)
        print("✅ Verification Complete!")
        print("="*60)
        
    finally:
        db.close()

if __name__ == "__main__":
    main()

