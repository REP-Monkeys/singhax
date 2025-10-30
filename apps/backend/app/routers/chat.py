"""Chat conversation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import uuid
from datetime import datetime

from app.core.db import get_db
from app.core.security import get_current_user_supabase
from app.models.user import User
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
        print("INFO: Initializing conversation graph...")
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
    current_user: User = Depends(get_current_user_supabase),
    db: Session = Depends(get_db)
) -> ChatMessageResponse:
    """
    Send a message and get intelligent AI response using LangGraph.
    
    This endpoint uses the full LangGraph conversation flow with:
    - Groq LLM for intent classification and extraction
    - 6-question structured flow
    - Real quote generation
    - Session persistence via PostgreSQL checkpointing
    """
    
    # Validate session_id format
    try:
        uuid.UUID(request.session_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid session_id format. Must be a valid UUID."
        )
    
    # Get conversation graph (cached singleton)
    try:
        graph = get_conversation_graph(db)
    except Exception as e:
        error_str = str(e).lower()
        if "relation" in error_str or "table" in error_str:
            raise HTTPException(
                status_code=503,
                detail="Chat service is initializing. Please try again."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize conversation: {str(e)}"
        )
    
    # Invoke LangGraph with real conversation intelligence
    # The checkpointer automatically handles state persistence
    config = {"configurable": {"thread_id": request.session_id}}

    try:
        print(f"\n💬 Processing message for session {request.session_id[:8]}...")
        print(f"   User message: '{request.message[:80]}...'")

        # Load existing state from checkpointer to preserve conversation context
        try:
            existing_state = graph.get_state(config)
        except Exception as e:
            print(f"   ⚠️  Could not load existing state: {e}")
            existing_state = None

        if existing_state and existing_state.values and existing_state.values.get("messages"):
            # Continuing existing conversation - append new message to existing state
            print(f"   📂 Loaded existing state with {len(existing_state.values.get('messages', []))} messages")
            # Get the messages list and append new message
            existing_messages = list(existing_state.values.get("messages", []))
            existing_messages.append(HumanMessage(content=request.message))

            # Create input with updated messages
            current_state = {"messages": existing_messages}
        else:
            # New conversation - initialize state
            print(f"   🆕 Starting new conversation")
            current_state = {
                "messages": [HumanMessage(content=request.message)],
                "user_id": str(current_user.id),
                "session_id": request.session_id,
            }

        # Invoke graph with messages - graph will handle merging with checkpoint state
        result = graph.invoke(current_state, config)
        
        print(f"✅ LangGraph execution complete")
        print(f"   State keys: {list(result.keys())}")
        
    except Exception as e:
        print(f"❌ LangGraph invocation error:")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail="I encountered an error processing your message. Please try again or start a new session."
        )
    
    # Extract agent's response safely
    agent_response = "I'm processing your request. Please try again."
    messages = result.get("messages", [])
    
    if messages:
        # Find last AI message (skip user messages)
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                agent_response = msg.content if hasattr(msg, 'content') else str(msg)
                print(f"   Agent response: '{agent_response[:80]}...'")
                break
    
    # Extract quote data if available
    quote_data = result.get("quote_data")
    
    if quote_data:
        print(f"💰 Quote generated successfully")
        print(f"   Destination: {quote_data.get('destination')}")
        print(f"   Tiers available: {list(quote_data.get('quotes', {}).keys())}")
    
    # Build response with comprehensive state
    return ChatMessageResponse(
        session_id=request.session_id,
        message=agent_response,
        state={
            "current_intent": result.get("current_intent", ""),
            "trip_details": result.get("trip_details", {}),
            "travelers_data": result.get("travelers_data", {}),
            "preferences": result.get("preferences", {}),
            "awaiting_confirmation": result.get("awaiting_confirmation", False),
            "confirmation_received": result.get("confirmation_received", False),
            "awaiting_field": result.get("awaiting_field", "")
        },
        quote=quote_data,
        requires_human=result.get("requires_human", False),
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


@router.get("/health")
async def chat_health():
    """Chat service health check endpoint."""
    return {
        "status": "healthy", 
        "service": "chat",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
