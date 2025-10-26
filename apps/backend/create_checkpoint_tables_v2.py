#!/usr/bin/env python3
"""Create LangGraph checkpoint tables by using the checkpointer."""

from app.core.config import settings
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import StateGraph, END
from typing import TypedDict

def create_checkpoint_tables():
    """Create LangGraph checkpoint tables by using the checkpointer."""
    try:
        print("Creating LangGraph checkpoint tables...")
        
        # Create a simple graph to trigger table creation
        class SimpleState(TypedDict):
            messages: list
        
        def simple_node(state: SimpleState) -> SimpleState:
            state["messages"].append("test")
            return state
        
        # Create graph
        graph = StateGraph(SimpleState)
        graph.add_node("test", simple_node)
        graph.set_entry_point("test")
        graph.add_edge("test", END)
        
        # Create checkpointer and compile graph
        checkpointer = PostgresSaver.from_conn_string(settings.database_url)
        compiled_graph = graph.compile(checkpointer=checkpointer)
        
        # Invoke the graph to trigger table creation
        result = compiled_graph.invoke(
            {"messages": []},
            {"configurable": {"thread_id": "test-session"}}
        )
        
        print("✓ Graph executed successfully")
        print("✓ Checkpoint tables should now exist")
        
        return True
        
    except Exception as e:
        print(f"Error creating checkpoint tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_checkpoint_tables()
    print(f"Success: {success}")
