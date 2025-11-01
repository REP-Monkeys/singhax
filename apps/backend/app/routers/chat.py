"""Chat conversation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Dict, Any
import uuid
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import os
from datetime import datetime, date
from pathlib import Path

from app.core.db import get_db
from app.core.security import get_current_user_supabase
from app.models.user import User
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionState,
    ImageUploadResponse
)
from app.agents.graph import create_conversation_graph
from app.services.ocr import OCRService, JSONExtractor
from langchain_core.messages import HumanMessage, AIMessage

# Cache for conversation graph (avoid recreating on every request)
_graph_cache: Dict[str, Any] = {}

# Thread pool executor for running synchronous graph operations
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="graph_exec")


def serialize_dates(obj: Any) -> Any:
    """Recursively serialize date objects to ISO format strings."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_dates(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_dates(item) for item in obj]
    return obj


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
    
    # Extract quote data if available
    quote_data = result.get("quote_data")
    
    if quote_data:
        print(f"💰 Quote generated successfully")
        print(f"   Destination: {quote_data.get('destination')}")
        print(f"   Tiers available: {list(quote_data.get('quotes', {}).keys())}")
    
    # Build response with comprehensive state (serialize date objects)
    trip_details_serialized = serialize_dates(result.get("trip_details", {}))
    quote_data_serialized = serialize_dates(quote_data) if quote_data else None

    # Debug: Log the state being sent to frontend
    print(f"📤 Sending to frontend:")
    print(f"   trip_details: {trip_details_serialized}")
    print(f"   travelers_data: {result.get('travelers_data', {})}")
    print(f"   preferences: {result.get('preferences', {})}")
    print(f"   quote_data: {quote_data_serialized}")

    return ChatMessageResponse(
        session_id=request.session_id,
        message=agent_response,
        state={
            "current_intent": result.get("current_intent", ""),
            "trip_details": trip_details_serialized,
            "travelers_data": result.get("travelers_data", {}),
            "preferences": result.get("preferences", {}),
            "awaiting_confirmation": result.get("awaiting_confirmation", False),
            "confirmation_received": result.get("confirmation_received", False),
            "awaiting_field": result.get("awaiting_field", ""),
        },
        quote=quote_data_serialized,
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


@router.post("/upload-image", response_model=ImageUploadResponse)
async def upload_image(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_supabase),
    db: Session = Depends(get_db)
) -> ImageUploadResponse:
    """
    Upload an image or PDF document and extract text using OCR.
    
    The extracted text will be available for use in the chat conversation.
    Supports: PNG, JPEG, PDF formats (max 10MB).
    """
    # Validate session_id
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")
    
    # Validate file type
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.pdf', '.tiff', '.bmp'}
    file_ext = Path(file.filename).suffix.lower() if file.filename else ''
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (10MB max)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    file_bytes = await file.read()
    
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: 10MB"
        )
    
    try:
        # Initialize services
        ocr_service = OCRService()
        json_extractor = JSONExtractor()
        
        # Step 1: Extract text from document
        ocr_result = ocr_service.extract_text(file_bytes, file.filename or "uploaded_file")
        
        # Check for errors
        if ocr_result.get("error"):
            raise HTTPException(
                status_code=500,
                detail=f"OCR processing failed: {ocr_result.get('error')}"
            )
        
        ocr_text = ocr_result.get("text", "")
        if not ocr_text:
            raise HTTPException(
                status_code=500,
                detail="No text could be extracted from the document"
            )
        
        # Step 2: Extract structured JSON data
        print(f"📄 Extracting structured data from document...")
        extracted_json = json_extractor.extract(
            ocr_text=ocr_text,
            session_id=session_id,
            filename=file.filename or "uploaded_file"
        )
        
        # Safety check: Ensure extracted_json is a dict, not a list
        if isinstance(extracted_json, list):
            print(f"⚠️  Warning: extracted_json is a list, attempting to extract first element")
            if len(extracted_json) > 0 and isinstance(extracted_json[0], dict):
                extracted_json = extracted_json[0]
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to extract document data: Invalid response format"
                )
        elif not isinstance(extracted_json, dict):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract document data: Unexpected type {type(extracted_json)}"
            )
        
        # Step 3: Check document type and reject if unknown
        document_type = extracted_json.get("document_type")
        if document_type == "unknown":
            raise HTTPException(
                status_code=400,
                detail="Sorry, I can only process travel-related documents. Please upload a flight confirmation, hotel booking, itinerary, or visa application."
            )
        
        # Step 4: Store document file permanently and save to database
        print(f"\n{'='*70}")
        print(f"📤 STORING DOCUMENT")
        print(f"{'='*70}")
        print(f"👤 User ID: {current_user.id}")
        print(f"💬 Session ID: {session_id}")
        print(f"📄 Document Type: {document_type}")
        print(f"📝 Filename: {file.filename}")
        print(f"📦 File Size: {len(file_bytes)} bytes")
        print(f"{'='*70}\n")
        
        from app.services.document_storage import DocumentStorageService
        storage_service = DocumentStorageService()
        
        # Store file permanently
        print(f"💾 Storing file...")
        file_storage_info = storage_service.store_document_file(
            user_id=str(current_user.id),
            document_type=document_type,
            file_bytes=file_bytes,
            original_filename=file.filename or "uploaded_file",
            content_type=file.content_type or "application/pdf"
        )
        print(f"✅ File stored successfully")
        print(f"   Storage Type: {file_storage_info.get('storage_type', 'unknown')}")
        print(f"   File Path: {file_storage_info.get('file_path', 'N/A')}")
        
        # Store extracted data in database
        print(f"\n💾 Storing document data in database...")
        storage_result = storage_service.store_extracted_document(
            db=db,
            user_id=str(current_user.id),
            session_id=session_id,
            extracted_json=extracted_json,
            file_storage_info=file_storage_info,
            json_file_path=extracted_json.get("json_file_path")
        )
        print(f"✅ Document data stored successfully")
        print(f"   Document ID: {storage_result.get('id', 'N/A')}")
        print(f"   Document Type: {storage_result.get('type', 'N/A')}")
        
        # Final summary
        print(f"\n{'='*70}")
        print(f"✅ DOCUMENT UPLOAD COMPLETE")
        print(f"{'='*70}")
        print(f"📄 Document ID: {storage_result.get('id', 'N/A')}")
        print(f"📋 Document Type: {storage_result.get('type', 'N/A')}")
        print(f"💬 Session ID: {session_id}")
        print(f"👤 User ID: {current_user.id}")
        print(f"📁 File stored at: {file_storage_info.get('file_path', 'N/A')}")
        print(f"💾 Database record created: ✅")
        
        # Check trip connection
        from app.models.trip import Trip
        trip = db.query(Trip).filter(Trip.session_id == session_id).first()
        if trip:
            print(f"🔗 Connected to Trip: ✅")
            print(f"   Trip ID: {trip.id}")
            print(f"   Trip Status: {trip.status}")
        else:
            print(f"🔗 Connected to Trip: ⚠️  No trip found for this session")
        print(f"{'='*70}\n")
        
        # Generate image ID for response (keeping for compatibility)
        image_id = f"img_{uuid.uuid4().hex[:12]}"
        
        # Step 5: Auto-process document via graph
        graph_result = None
        agent_message = None
        
        if ocr_text:
            try:
                graph = get_conversation_graph(db)
                config = {"configurable": {"thread_id": session_id}}
                
                # Create message indicating document upload (like ChatGPT - no raw OCR text shown)
                # The structured JSON is stored in state and processed by the graph
                import json
                ocr_message = f"[User uploaded a document: {file.filename}]"
                
                # Load existing state
                try:
                    existing_state = graph.get_state(config)
                    existing_messages = list(existing_state.values.get("messages", [])) if existing_state else []
                    state_values = existing_state.values if existing_state else {}
                except:
                    existing_messages = []
                    state_values = {}
                
                # Store extracted JSON in state for processing (not in message content)
                if "document_data" not in state_values:
                    state_values["document_data"] = []
                state_values["document_data"].append({
                    "filename": file.filename,
                    "extracted_json": extracted_json,
                    "document_type": extracted_json.get("document_type"),
                    "uploaded_at": datetime.now().isoformat()
                })
                
                # Add simple document upload message (like ChatGPT)
                existing_messages.append(HumanMessage(content=ocr_message))
                
                # Invoke graph to auto-process with structured JSON in state
                current_state = {
                    "messages": existing_messages,
                    "document_data": state_values.get("document_data", []),
                    "uploaded_filename": file.filename
                }
                graph_result = graph.invoke(current_state, config)
                
                # Extract agent response
                if graph_result.get("messages"):
                    for msg in reversed(graph_result.get("messages", [])):
                        if isinstance(msg, AIMessage):
                            agent_message = msg.content
                            break
                
                print(f"✅ Document processed by agent")
                
            except Exception as e:
                print(f"⚠️  Could not auto-process document: {e}")
                import traceback
                traceback.print_exc()
        
        # Prepare response
        message_suggestion = agent_message or (
            f"I've uploaded a {extracted_json.get('document_type', 'document')} ({file.filename}). "
            f"I've extracted the information. Please review and confirm."
        )
        
        # Enhance OCR result with extracted JSON
        enhanced_ocr_result = {
            **ocr_result,
            "extracted_json": extracted_json,
            "document_type": extracted_json.get("document_type"),
            "json_file_path": extracted_json.get("json_file_path")
        }
        
        return ImageUploadResponse(
            session_id=session_id,
            image_id=image_id,
            filename=file.filename or "uploaded_file",
            ocr_result=enhanced_ocr_result,
            message=message_suggestion
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Image upload error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process image: {str(e)}"
        )


@router.get("/health")
async def chat_health():
    """Chat service health check endpoint."""
    return {
        "status": "healthy", 
        "service": "chat",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
