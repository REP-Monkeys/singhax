"""Chat conversation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import uuid
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

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

# Thread pool executor for running synchronous graph operations
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="graph_exec")


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
    
    # Validate session_id
    try:
        uuid.UUID(request.session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")
    
    # Get graph
    try:
        graph = get_conversation_graph(db)
    except Exception as e:
        print(f"❌ Graph initialization failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Chat service is temporarily unavailable. Please try again."
        )
    
    # Invoke LangGraph with real conversation intelligence
    # The checkpointer automatically handles state persistence
    config = {"configurable": {"thread_id": request.session_id}}

    try:
        print(f"\n💬 Processing message for session {request.session_id[:8]}...")
        print(f"   User message: '{request.message[:80]}...'")

        # LangGraph's checkpointer handles state loading automatically
        # Just pass the new message and essential metadata
        current_state = {
            "messages": [HumanMessage(content=request.message)],
            "user_id": str(current_user.id),
            "session_id": request.session_id,
        }
        # Run in thread pool executor to prevent blocking the async event loop
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                _executor, graph.invoke, current_state, config
            ),
            timeout=30.0
        )
        
        print(f"✅ Graph execution complete")
        
    except asyncio.TimeoutError:
        print(f"⏱️  Graph execution timeout (30s limit exceeded)")
        # Return graceful timeout message to user
        return ChatMessageResponse(
            session_id=request.session_id,
            message="I'm taking longer than expected to process your request. Please try again or rephrase your question.",
            state={},
            quote=None,
            requires_human=True
        )
    
    except RecursionError as e:
        print(f"❌ Recursion limit hit: {e}")
        # Return graceful error to user
        return ChatMessageResponse(
            session_id=request.session_id,
            message="I apologize, but I'm having trouble processing that. Could you rephrase your question?",
            state={},
            quote=None,
            requires_human=True
        )
    
    except Exception as e:
        print(f"❌ Graph execution error: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to return a helpful error message
        error_message = "I encountered an issue processing your message. "
        
        if "LLM" in str(e) or "Groq" in str(e):
            error_message += "Our AI service is experiencing issues. Please try again."
        elif "database" in str(e).lower():
            error_message += "We're having database connectivity issues. Please try again."
        else:
            error_message += "Please try rephrasing or contact support."
        
        return ChatMessageResponse(
            session_id=request.session_id,
            message=error_message,
            state={},
            quote=None,
            requires_human=True
        )
    
    # Extract agent response (existing code continues...)
    agent_response = "I'm processing your request..."
    messages = result.get("messages", [])
    
    if messages:
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                agent_response = msg.content
                break
    
    # Extract quote
    quote_data = result.get("quote_data")
    
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
