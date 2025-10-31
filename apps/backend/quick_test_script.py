"""Quick test to verify Phase 4 setup and API keys."""

import sys
print("=" * 60)
print("Phase 4 Quick Test")
print("=" * 60)

# Test 1: Environment
print("\n1. Checking environment variables...")
try:
    from app.core.config import settings
    
    if settings.groq_api_key:
        print("   ✓ GROQ_API_KEY is set")
    else:
        print("   ✗ GROQ_API_KEY is NOT set")
        sys.exit(1)
    
    if settings.database_url:
        print("   ✓ DATABASE_URL is set")
    else:
        print("   ✗ DATABASE_URL is NOT set")
        sys.exit(1)
    
    print(f"   ✓ Using model: {settings.groq_model}")
except Exception as e:
    print(f"   ✗ Error loading config: {e}")
    sys.exit(1)

# Test 2: Imports
print("\n2. Testing Phase 4 imports...")
try:
    from app.routers.chat import router
    from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
    print("   ✓ Chat router and schemas import successfully")
except Exception as e:
    print(f"   ✗ Import error: {e}")
    sys.exit(1)

# Test 3: Groq API connection
print("\n3. Testing Groq API connection...")
try:
    from app.agents.llm_client import GroqLLMClient
    
    client = GroqLLMClient()
    print("   ✓ Groq client initialized")
    
    # Try a simple classification
    test_result = client.classify_intent("I need travel insurance", [])
    print(f"   ✓ Groq API working! Intent detected: {test_result['intent']}")
except Exception as e:
    print(f"   ✗ Groq API error: {e}")
    print("   → Check your GROQ_API_KEY is valid")
    sys.exit(1)

# Test 4: Database connection
print("\n4. Testing database connection...")
try:
    from app.core.db import engine
    from sqlalchemy import text
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        result.fetchone()
    print("   ✓ Database connection successful")
except Exception as e:
    print(f"   ✗ Database error: {e}")
    print("   → Check your DATABASE_URL is correct")
    sys.exit(1)

# Test 5: LangGraph setup
print("\n5. Testing LangGraph configuration...")
try:
    from app.agents.graph import create_conversation_graph
    from app.core.db import SessionLocal
    
    db = SessionLocal()
    graph = create_conversation_graph(db)
    db.close()
    print("   ✓ LangGraph with checkpointing configured")
except Exception as e:
    print(f"   ✗ LangGraph error: {e}")
    sys.exit(1)

# Success!
print("\n" + "=" * 60)
print("✓ ALL TESTS PASSED!")
print("=" * 60)
print("\nYour Phase 4 implementation is ready!")
print("\nNext steps:")
print("1. Start server:")
print("   python -m uvicorn app.main:app --reload")
print("\n2. In another terminal, test chat:")
print("   python scripts/test_conversation.py interactive")
print("\n3. Or run integration tests:")
print("   pytest tests/test_chat_integration.py -v")
print("\n4. View API docs at: http://localhost:8000/docs")
print("=" * 60)

