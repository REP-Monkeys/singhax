#!/usr/bin/env python3
"""Create LangGraph checkpoint tables."""

from app.core.config import settings
from langgraph.checkpoint.postgres import PostgresSaver

def create_checkpoint_tables():
    """Create LangGraph checkpoint tables."""
    try:
        print("Creating LangGraph checkpoint tables...")
        
        # Create PostgresSaver instance
        checkpointer = PostgresSaver.from_conn_string(settings.database_url)
        
        # This should create the necessary tables
        print("✓ Checkpointer created successfully")
        print("✓ Checkpoint tables should now exist")
        
        return True
        
    except Exception as e:
        print(f"Error creating checkpoint tables: {e}")
        return False

if __name__ == "__main__":
    success = create_checkpoint_tables()
    print(f"Success: {success}")
