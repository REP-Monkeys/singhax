"""Minimal test to isolate the SASL issue."""
import sys
from app.core.config import settings
import psycopg2

print("Testing minimal connection...")
try:
    conn_string = settings.langgraph_checkpoint_db or settings.database_url
    print(f"Connection string: {conn_string[:50]}...")
    
    conn = psycopg2.connect(conn_string)
    print("✅ Direct psycopg2 connection works")
    conn.close()
    
    # Now test PostgresSaver
    from langgraph.checkpoint.postgres import PostgresSaver
    conn = psycopg2.connect(conn_string)
    conn.autocommit = True
    
    checkpointer = PostgresSaver(conn)
    print("✅ PostgresSaver created")
    
    checkpointer.setup()
    print("✅ Checkpoint tables setup")
    
    conn.close()
    print("✅ All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
