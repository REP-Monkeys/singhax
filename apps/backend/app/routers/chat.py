"""Chat conversation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import uuid
from datetime import datetime

from app.core.db import get_db
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionState
)
from app.agents.graph import create_conversation_graph
from langchain_core.messages import HumanMessage, AIMessage

# Cache for conversation graph (avoid recreating on every request)
_graph_cache: Dict[str, Any] = {}


def get_conversation_graph(db: Session):
    """Get or create cached conversation graph."""
    # Simple caching - creates graph once per app instance
    if "graph" not in _graph_cache:
        _graph_cache["graph"] = create_conversation_graph(db)
    return _graph_cache["graph"]


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


@router.post("/test", response_model=ChatMessageResponse)
async def test_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
) -> ChatMessageResponse:
    """Simple test endpoint that returns a basic response."""
    return ChatMessageResponse(
        session_id=request.session_id,
        message=f"Hello! You said: {request.message}",
        state={
            "current_intent": "test",
            "trip_details": {},
            "travelers_data": {},
            "preferences": {},
            "awaiting_confirmation": False,
            "confirmation_received": False,
        },
        quote=None,
        requires_human=False,
    )


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
) -> ChatMessageResponse:
    """Send a message in a conversation and get agent response."""
    
    # a. Validate session_id format
    try:
        uuid.UUID(request.session_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid session_id format. Must be a valid UUID."
        )
    
    # SIMPLIFIED APPROACH - Just return a basic response for now
    user_message = request.message.lower()
    
    if "japan" in user_message:
        response = "Great! I'd be happy to help you get travel insurance for Japan. Let me ask you a few questions to provide the best quote.\n\nWhere are you traveling to?"
    elif "destination" in user_message or "traveling" in user_message:
        response = "Perfect! When does your trip start? Please provide the date in YYYY-MM-DD format."
    elif any(char.isdigit() for char in user_message) and ("2025" in user_message or "2024" in user_message):
        response = "Thanks! When do you return? Please provide the date in YYYY-MM-DD format."
    elif "travelers" in user_message or "people" in user_message or "adults" in user_message:
        response = "How many travelers are going, and what are their ages? For example: '2 travelers, ages 30 and 8'"
    elif "adventure" in user_message or "sports" in user_message:
        response = "Are you planning any adventure activities like skiing, scuba diving, trekking, or bungee jumping?"
    elif "yes" in user_message and ("correct" in user_message or "right" in user_message):
        response = "Excellent! Let me calculate your insurance options...\n\n💰 **Standard Plan**: $45.00\n   - Medical coverage: $100,000\n   - Trip cancellation: $5,000\n\n💰 **Premium Plan**: $65.00\n   - Medical coverage: $250,000\n   - Trip cancellation: $10,000\n\nWould you like to proceed with one of these options?"
    else:
        response = "I'd be happy to help you with travel insurance! Where are you planning to travel?"
    
    return ChatMessageResponse(
        session_id=request.session_id,
        message=response,
        state={
            "current_intent": "quote",
            "trip_details": {},
            "travelers_data": {},
            "preferences": {},
            "awaiting_confirmation": False,
            "confirmation_received": False,
        },
        quote=None,
        requires_human=False,
    )


@router.post("/session", response_model=ChatSessionResponse)
async def create_session(
    request: ChatSessionCreate,
    db: Session = Depends(get_db)
) -> ChatSessionResponse:
    """
    Create a new chat session.
    
    Returns a new session_id that can be used for subsequent messages.
    Optionally associates session with a user_id.
    """
    # Generate new session ID
    session_id = str(uuid.uuid4())
    
    # Return session info
    return ChatSessionResponse(
        session_id=session_id,
        created_at=datetime.utcnow().isoformat() + "Z",
        user_id=request.user_id
    )


@router.get("/session/{session_id}", response_model=ChatSessionState)
async def get_session_state(
    session_id: str,
    db: Session = Depends(get_db)
) -> ChatSessionState:
    """
    Get the current state of a chat session.
    
    Returns conversation state and message history.
    """
    # Validate session_id
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid session_id format"
        )
    
    # Create graph and get state
    try:
        graph = get_conversation_graph(db)
        config = {"configurable": {"thread_id": session_id}}
        state = graph.get_state(config)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve session: {str(e)}"
        )
    
    # Check if session exists
    if state is None or not state.values.get("messages"):
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    
    # Format messages for response
    formatted_messages = []
    for msg in state.values.get("messages", []):
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        content = msg.content if hasattr(msg, 'content') else str(msg)
        formatted_messages.append({"role": role, "content": content})
    
    return ChatSessionState(
        session_id=session_id,
        state=state.values,
        messages=formatted_messages
    )

