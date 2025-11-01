"""Debug RAG search to see similarity scores."""

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
    print("Testing RAG Search (Lower Threshold for Debugging)")
    print("="*60)
    
    query = "What is covered under medical expenses?"
    print(f"\n🔍 Query: {query}\n")
    
    # Test with very low threshold to see all results
    results = rag.search(query=query, limit=10, min_similarity=0.0)
    
    print(f"Found {len(results)} results (no threshold):\n")
    
    for i, result in enumerate(results, 1):
        print(f"[{i}] Similarity: {result['similarity']:.4f}")
        print(f"    Section {result['section_id']}: {result['heading']}")
        print(f"    From: {result['title']}")
        print(f"    Text: {result['text'][:100]}...")
        print()
    
    # Test a direct policy keyword
    print("\n" + "="*60)
    query2 = "medical coverage emergency treatment hospitalization"
    print(f"🔍 Query 2 (keywords): {query2}\n")
    
    results2 = rag.search(query=query2, limit=5, min_similarity=0.0)
    
    for i, result in enumerate(results2, 1):
        print(f"[{i}] Similarity: {result['similarity']:.4f}")
        print(f"    Section {result['section_id']}: {result['heading']}")
        print()
    
    print("="*60)
    
    db.close()

if __name__ == "__main__":
    main()

