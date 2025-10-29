"""Quick validation script for Phase 4 implementation."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

print("=" * 60)
print("Phase 4 Implementation Validation")
print("=" * 60)

# Test 1: Import schemas
print("\n1. Testing schema imports...")
try:
    from app.schemas.chat import (
        ChatMessageRequest,
        ChatMessageResponse,
        ChatSessionCreate,
        ChatSessionResponse,
        ChatSessionState
    )
    print("   ✅ All 5 new schemas imported successfully")
except ImportError as e:
    print(f"   ❌ Schema import failed: {e}")
    sys.exit(1)

# Test 2: Import router
print("\n2. Testing router import...")
try:
    from app.routers.chat import router
    print("   ✅ Chat router imported successfully")
except ImportError as e:
    print(f"   ❌ Router import failed: {e}")
    sys.exit(1)

# Test 3: Check router registration
print("\n3. Testing router registration...")
try:
    from app.routers import chat_router
    print("   ✅ Chat router exported from routers package")
except ImportError as e:
    print(f"   ❌ Router registration failed: {e}")
    sys.exit(1)

# Test 4: Check main app includes router
print("\n4. Testing main app integration...")
try:
    from app.main import app
    routes = [route.path for route in app.routes]
    chat_routes = [r for r in routes if '/chat' in r]
    if chat_routes:
        print(f"   ✅ Chat routes found: {chat_routes}")
    else:
        print("   ❌ No chat routes found in app")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Main app check failed: {e}")
    sys.exit(1)

# Test 5: Check environment
print("\n5. Checking environment configuration...")
try:
    from app.core.config import settings
    
    issues = []
    if not settings.groq_api_key:
        issues.append("GROQ_API_KEY not set")
    else:
        print("   ✅ GROQ_API_KEY is set")
    
    if not settings.database_url:
        issues.append("DATABASE_URL not set")
    else:
        print("   ✅ DATABASE_URL is set")
    
    if issues:
        print("\n   ⚠️  Environment issues (may cause runtime errors):")
        for issue in issues:
            print(f"      - {issue}")
    else:
        print("   ✅ All required environment variables set")
except Exception as e:
    print(f"   ❌ Environment check failed: {e}")

# Test 6: Check graph has checkpointing
print("\n6. Verifying LangGraph checkpointing...")
try:
    import inspect
    from app.agents.graph import create_conversation_graph
    
    source = inspect.getsource(create_conversation_graph)
    if "PostgresSaver" in source and "checkpointer" in source:
        print("   ✅ Checkpointing configured in graph")
    else:
        print("   ⚠️  Checkpointing may not be configured")
        print("      (Session persistence may not work)")
except Exception as e:
    print(f"   ⚠️  Could not verify checkpointing: {e}")

# Test 7: Test basic schema validation
print("\n7. Testing schema validation...")
try:
    # Test ChatMessageRequest validation
    request = ChatMessageRequest(
        session_id="550e8400-e29b-41d4-a716-446655440000",
        message="Test message"
    )
    print("   ✅ ChatMessageRequest validation works")
    
    # Test invalid message (too short)
    try:
        invalid = ChatMessageRequest(
            session_id="550e8400-e29b-41d4-a716-446655440000",
            message=""
        )
        print("   ⚠️  Schema validation may be too permissive")
    except:
        print("   ✅ Schema validation catches empty messages")
except Exception as e:
    print(f"   ❌ Schema validation test failed: {e}")

# Test 8: Check test files exist
print("\n8. Checking test files...")
test_integration = os.path.join(os.path.dirname(__file__), '..', 'tests', 'test_chat_integration.py')
test_script = os.path.join(os.path.dirname(__file__), 'test_conversation.py')

if os.path.exists(test_integration):
    print("   ✅ Integration test file exists")
else:
    print("   ❌ Integration test file missing")

if os.path.exists(test_script):
    print("   ✅ Test conversation script exists")
else:
    print("   ❌ Test conversation script missing")

# Final summary
print("\n" + "=" * 60)
print("Validation Complete!")
print("=" * 60)
print("\nNext steps:")
print("1. Start server: uvicorn app.main:app --reload")
print("2. Test API: python scripts/test_conversation.py interactive")
print("3. Run tests: pytest tests/test_chat_integration.py -v")
print("4. View docs: http://localhost:8000/docs")
print("\nIf you see any ❌ or ⚠️  above, check PHASE_4_IMPLEMENTATION_SUMMARY.md")
print("=" * 60)

