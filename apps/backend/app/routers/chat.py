"""Chat router for conversation API."""

import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from app.core.db import get_db
from app.agents.graph import create_conversation_graph


router = APIRouter(prefix="/chat", tags=["chat"])


# Global graph cache
_graph_cache: Dict[str, Any] = {}


def get_conversation_graph(db: Session):
    """Get or create cached conversation graph."""
    if "graph" not in _graph_cache:
        print("INFO: Initializing conversation graph...")
        _graph_cache["graph"] = create_conversation_graph(db)
    return _graph_cache["graph"]


class ChatMessageRequest(BaseModel):
    """Request schema for chat message."""
    session_id: str
    message: str


class ChatMessageResponse(BaseModel):
    """Response schema for chat message."""
    session_id: str
    message: str
    state: Dict[str, Any]
    quote: Optional[Dict[str, Any]] = None
    requires_human: bool = False


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
) -> ChatMessageResponse:
    """Send message and get AI response using real LangGraph.

    Args:
        request: Chat message request with session_id and message
        db: Database session

    Returns:
        Chat response with agent message, state, and quote data
    """

    # Validate session_id
    try:
        uuid.UUID(request.session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")

    # Get graph
    try:
        graph = get_conversation_graph(db)
    except Exception as e:
        print(f"ERROR: Graph initialization failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Graph initialization failed: {str(e)}")

    # Prepare config with thread_id for checkpointing
    config = {"configurable": {"thread_id": request.session_id}}

    # Invoke LangGraph
    try:
        print(f"\nUSER: [{request.session_id[:8]}...]: '{request.message[:80]}...'")

        result = graph.invoke(
            {"messages": [HumanMessage(content=request.message)]},
            config
        )

        print(f"OK: Graph execution completed")

    except Exception as e:
        print(f"ERROR: Graph execution error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    # Extract agent response from messages
    agent_response = "I'm processing your request..."
    messages = result.get("messages", [])

    if messages:
        # Get last AI message
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                agent_response = msg.content
                break

    print(f"AGENT: '{agent_response[:80]}...'")

    # Extract quote data if available
    quote_data = result.get("quote_data")
    if quote_data:
        destination = quote_data.get("destination", "Unknown")
        print(f"QUOTE: Quote generated for {destination}")

    # Build state summary for response
    state_summary = {
        "current_intent": result.get("current_intent", ""),
        "trip_details": result.get("trip_details", {}),
        "travelers_data": result.get("travelers_data", {}),
        "preferences": result.get("preferences", {}),
        "awaiting_confirmation": result.get("awaiting_confirmation", False),
        "confirmation_received": result.get("confirmation_received", False),
        "awaiting_field": result.get("awaiting_field", "")
    }

    return ChatMessageResponse(
        session_id=request.session_id,
        message=agent_response,
        state=state_summary,
        quote=quote_data,
        requires_human=result.get("requires_human", False),
    )


@router.get("/health")
async def chat_health():
    """Chat service health check."""
    return {"status": "healthy", "service": "chat"}
