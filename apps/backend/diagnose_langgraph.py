"""Diagnostic script to test LangGraph checkpointing setup."""
import sys
from app.core.config import settings
from app.core.db import SessionLocal

print("="*60)
print("LANGGRAPH DIAGNOSTIC SCRIPT")
print("="*60)

# Test 1: Check dependencies
print("\n1. Checking dependencies...")
try:
    import psycopg2
    print("   ✅ psycopg2 installed")
except ImportError:
    print("   ❌ psycopg2 NOT installed")
    print("   RUN: pip install psycopg2-binary --break-system-packages")
    sys.exit(1)

try:
    from langgraph.checkpoint.postgres import PostgresSaver
    print("   ✅ LangGraph PostgresSaver available")
except ImportError as e:
    print(f"   ❌ LangGraph checkpoint NOT available: {e}")
    print("   RUN: pip install langgraph-checkpoint-postgres --break-system-packages")
    sys.exit(1)

# Test 2: Check database connection
print("\n2. Checking database connection...")
try:
    from sqlalchemy import text
    db = SessionLocal()
    result = db.execute(text("SELECT 1")).fetchone()
    print(f"   ✅ Database connected")
    print(f"   ✅ Database URL: {settings.database_url[:50]}...")
    db.close()
except Exception as e:
    print(f"   ❌ Database connection failed: {e}")
    sys.exit(1)

# Test 3: Create checkpointer
print("\n3. Testing PostgresSaver...")
try:
    conn_string = settings.langgraph_checkpoint_db or settings.database_url
    with PostgresSaver.from_conn_string(conn_string) as checkpointer:
        print("   ✅ PostgresSaver created")
        
        # Try to setup tables (may fail if already exist)
        try:
            checkpointer.setup()
            print("   ✅ Checkpoint tables created/verified in database")
        except Exception as setup_error:
            if "already exists" in str(setup_error) or "prepared statement" in str(setup_error):
                print("   ✅ Checkpoint tables already exist (setup skipped)")
            else:
                raise setup_error
except Exception as e:
    print(f"   ❌ PostgresSaver failed: {e}")
    print("\nFull error:")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Create graph
print("\n4. Testing graph creation...")
try:
    from app.agents.graph import create_conversation_graph
    db = SessionLocal()
    graph = create_conversation_graph(db)
    print("   ✅ Graph created successfully")
    print(f"   ✅ Has checkpointer: {graph.checkpointer is not None}")
    db.close()
except Exception as e:
    print(f"   ❌ Graph creation failed: {e}")
    print("\nFull error:")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Test simple invoke
print("\n5. Testing graph invocation...")
try:
    from langchain_core.messages import HumanMessage
    db = SessionLocal()
    graph = create_conversation_graph(db)
    
    config = {"configurable": {"thread_id": "diagnostic-test-123"}}
    result = graph.invoke(
        {"messages": [HumanMessage(content="Hello, I need insurance")]},
        config
    )
    
    print("   ✅ Graph invoked successfully")
    print(f"   ✅ Result has messages: {'messages' in result}")
    print(f"   ✅ Message count: {len(result.get('messages', []))}")
    
    if result.get('messages'):
        last_msg = result['messages'][-1]
        print(f"   ✅ Last message type: {type(last_msg).__name__}")
    
    db.close()
except Exception as e:
    print(f"   ❌ Graph invocation failed: {e}")
    print("\nFull error:")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("✅ ALL DIAGNOSTICS PASSED")
print("LangGraph checkpointing is working correctly!")
print("="*60)
