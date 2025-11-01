"""Test RAG search functionality."""

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
from app.services.rag import RAGService

def main():
    db = SessionLocal()
    rag = RAGService(db=db)
    
    print("="*60)
    print("Testing RAG Vector Search")
    print("="*60)
    
    # Test queries
    test_queries = [
        "What is covered under medical expenses?",
        "Am I covered for skiing and adventure sports?",
        "What are the baggage coverage limits?",
        "What happens if I need to cancel my trip?",
        "Tell me about pre-existing conditions"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        print("-" * 60)
        
        try:
            results = rag.search(query=query, limit=3)  # Uses default min_similarity=0.5
            
            if results:
                print(f"✅ Found {len(results)} results:\n")
                for i, result in enumerate(results, 1):
                    print(f"[{i}] Section {result['section_id']}: {result['heading']}")
                    print(f"    From: {result['title']}")
                    print(f"    Pages: {result['pages']}")
                    print(f"    Similarity: {result['similarity']:.3f}")
                    print(f"    Text: {result['text'][:150]}...")
                    print()
            else:
                print("❌ No results found (similarity < 0.5)")
                
        except Exception as e:
            print(f"❌ Search failed: {e}")
    
    print("="*60)
    print("✅ Search test complete!")
    print("="*60)
    
    db.close()

if __name__ == "__main__":
    main()

