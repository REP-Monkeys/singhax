"""Chat conversation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
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
from app.agents.graph import create_conversation_graph, get_or_create_checkpointer, clean_markdown
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
        
        # Check if user message is a simple greeting
        user_message_lower = request.message.lower().strip()
        greeting_words = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "howdy"]
        is_greeting = any(word in user_message_lower for word in greeting_words) and len(user_message_lower.split()) <= 3
        
        # If it's a greeting, respond friendly instead of showing error
        if is_greeting:
            return ChatMessageResponse(
                session_id=request.session_id,
                message="Hello! How can I help you today? I can help you get a travel insurance quote, explain your policy, or assist with claims.",
                state={},
                quote=None,
                requires_human=False
            )
        
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
    
    # Clean markdown formatting, but preserve plan card formatting (frontend needs it)
    # Check if response contains plan cards (has plan emojis and ** pattern)
    has_plan_cards = any(emoji in agent_response for emoji in ['🌟', '⭐', '💎']) and '**' in agent_response
    if not has_plan_cards:
        agent_response = clean_markdown(agent_response)
    
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
        
        # Get the full accumulated state - get_state() should return all messages
        # LangGraph accumulates messages across checkpoints automatically
        state = graph.get_state(config)
        
        # Debug logging
        print(f"\n🔍 [DEBUG] Retrieving session state for: {session_id[:8]}...")
        print(f"   🔍 Graph state object: {state}")
        print(f"   🔍 Has values: {hasattr(state, 'values')}")
        if state:
            messages = state.values.get("messages", [])
            print(f"   📊 Found {len(messages)} messages in state")
            print(f"   🔍 State values keys: {list(state.values.keys())}")
            if messages:
                # Count user vs assistant messages
                user_count = sum(1 for m in messages if isinstance(m, HumanMessage))
                assistant_count = sum(1 for m in messages if isinstance(m, AIMessage))
                print(f"   📝 Message breakdown: {user_count} user, {assistant_count} assistant")
                print(f"   📝 First message: {type(messages[0]).__name__} - {str(messages[0].content)[:50]}...")
                print(f"   📝 Last message: {type(messages[-1]).__name__} - {str(messages[-1].content)[:50]}...")

                # Print all message types and first 30 chars
                print(f"   📋 All messages:")
                for i, msg in enumerate(messages):
                    msg_type = type(msg).__name__
                    content_preview = str(msg.content)[:30] if hasattr(msg, 'content') else str(msg)[:30]
                    print(f"      [{i}] {msg_type}: {content_preview}...")
                
                # If we're missing assistant messages, that's a problem - get_state() should include them
                # Don't try reconstruction if we have assistant messages but just few total messages
                if assistant_count == 0 and user_count > 0:  # Missing assistant messages is a real issue
                    print(f"   ⚠️ Missing assistant messages! Found {user_count} user but 0 assistant - checking checkpoints...")
                    try:
                        # Access the checkpointer directly to list all checkpoints
                        checkpointer = get_or_create_checkpointer()
                        if checkpointer:
                            # Try to get all checkpoints for this thread
                            checkpoints = list(checkpointer.list(config, limit=None))
                            print(f"   📋 Found {len(checkpoints)} checkpoints")
                            
                            # Reconstruct full message history from all checkpoints
                            # CheckpointTuple structure: (checkpoint, metadata) where checkpoint has channel_values
                            all_messages = []
                            seen_contents = set()  # For deduplication by content
                            
                            # Try to get state from the latest checkpoint (should have all accumulated messages)
                            # Process checkpoints in reverse order (newest first) - latest should have all messages
                            if checkpoints:
                                # Debug: inspect checkpoint structure
                                latest_cp = checkpoints[-1]  # Last checkpoint should be latest
                                print(f"   🔍 Latest checkpoint type: {type(latest_cp)}")
                                if hasattr(latest_cp, '_fields'):
                                    print(f"   🔍 CheckpointTuple fields: {latest_cp._fields}")
                                
                                # Try to get state from latest checkpoint - it should have full accumulated messages
                                latest_checkpoint_success = False
                                try:
                                    # Access the latest checkpoint's channel_values directly
                                    latest_checkpoint_obj = None
                                    if hasattr(latest_cp, 'checkpoint'):
                                        latest_checkpoint_obj = latest_cp.checkpoint
                                    elif hasattr(latest_cp, '_asdict'):
                                        cp_dict = latest_cp._asdict()
                                        latest_checkpoint_obj = cp_dict.get('checkpoint', latest_cp)
                                    elif isinstance(latest_cp, tuple) and len(latest_cp) >= 1:
                                        latest_checkpoint_obj = latest_cp[0]
                                    else:
                                        latest_checkpoint_obj = latest_cp
                                    
                                    # Get channel_values from latest checkpoint
                                    latest_channel_values = None
                                    if hasattr(latest_checkpoint_obj, 'channel_values'):
                                        latest_channel_values = latest_checkpoint_obj.channel_values
                                    elif isinstance(latest_checkpoint_obj, dict):
                                        latest_channel_values = latest_checkpoint_obj.get('channel_values')
                                    else:
                                        latest_channel_values = getattr(latest_checkpoint_obj, 'channel_values', None)
                                    
                                    if latest_channel_values:
                                        latest_messages = []
                                        if isinstance(latest_channel_values, dict):
                                            latest_messages = latest_channel_values.get('messages', [])
                                        elif hasattr(latest_channel_values, 'get'):
                                            latest_messages = latest_channel_values.get('messages', [])
                                        elif hasattr(latest_channel_values, 'messages'):
                                            latest_messages = latest_channel_values.messages
                                        
                                        if latest_messages and len(latest_messages) > len(messages):
                                            latest_user_count = sum(1 for m in latest_messages if isinstance(m, HumanMessage))
                                            latest_assistant_count = sum(1 for m in latest_messages if isinstance(m, AIMessage))
                                            print(f"   📊 Latest checkpoint: {len(latest_messages)} messages ({latest_user_count} user, {latest_assistant_count} assistant)")
                                            
                                            if latest_assistant_count > 0:  # Only use if we have assistant messages
                                                print(f"   ✅ Got {len(latest_messages)} messages from latest checkpoint (was {len(messages)})")
                                                messages = latest_messages
                                                state.values["messages"] = messages
                                                latest_checkpoint_success = True
                                            else:
                                                print(f"   ⚠️  Latest checkpoint missing assistant messages - skipping")
                                except Exception as e:
                                    print(f"   ⚠️ Could not get state from latest checkpoint: {e}")
                                    import traceback
                                    traceback.print_exc()
                            
                            # Fallback: manually reconstruct from all checkpoints if latest checkpoint didn't work
                            if not latest_checkpoint_success:
                                for checkpoint_tuple in checkpoints:
                                    try:
                                        # CheckpointTuple is a named tuple: (checkpoint, metadata)
                                        # Access the checkpoint object - try different access patterns
                                        checkpoint_obj = None
                                        if hasattr(checkpoint_tuple, 'checkpoint'):
                                            checkpoint_obj = checkpoint_tuple.checkpoint
                                        elif hasattr(checkpoint_tuple, '_asdict'):
                                            # Named tuple - convert to dict to access
                                            cp_dict = checkpoint_tuple._asdict()
                                            checkpoint_obj = cp_dict.get('checkpoint', checkpoint_tuple)
                                        elif isinstance(checkpoint_tuple, tuple) and len(checkpoint_tuple) >= 1:
                                            # Regular tuple - first element is checkpoint
                                            checkpoint_obj = checkpoint_tuple[0]
                                        else:
                                            checkpoint_obj = checkpoint_tuple
                                        
                                        # Get channel_values from checkpoint
                                        channel_values = None
                                        if hasattr(checkpoint_obj, 'channel_values'):
                                            channel_values = checkpoint_obj.channel_values
                                        elif isinstance(checkpoint_obj, dict):
                                            channel_values = checkpoint_obj.get('channel_values')
                                        else:
                                            # Try accessing as attribute
                                            channel_values = getattr(checkpoint_obj, 'channel_values', None)
                                        
                                        if channel_values:
                                            # Extract messages from channel_values
                                            checkpoint_messages = []
                                            if isinstance(channel_values, dict):
                                                checkpoint_messages = channel_values.get('messages', [])
                                            elif hasattr(channel_values, 'get'):
                                                checkpoint_messages = channel_values.get('messages', [])
                                            elif hasattr(channel_values, 'messages'):
                                                checkpoint_messages = channel_values.messages
                                            
                                            # Add unique messages to our list
                                            for msg in checkpoint_messages:
                                                if msg:
                                                    msg_content = msg.content if hasattr(msg, 'content') else str(msg)
                                                    # Deduplicate by content hash
                                                    content_hash = hash(msg_content)
                                                    if content_hash not in seen_contents:
                                                        seen_contents.add(content_hash)
                                                        all_messages.append(msg)
                                    except Exception as e:
                                        print(f"   ⚠️ Error processing checkpoint: {e}")
                                        continue
                                
                                # Count messages by type in reconstructed list
                                reconstructed_user_count = sum(1 for m in all_messages if isinstance(m, HumanMessage))
                                reconstructed_assistant_count = sum(1 for m in all_messages if isinstance(m, AIMessage))
                                print(f"   📊 Reconstructed breakdown: {reconstructed_user_count} user, {reconstructed_assistant_count} assistant")
                                
                                # Only use reconstructed messages if:
                                # 1. We have more total messages, AND
                                # 2. We have at least some assistant messages (to avoid losing assistant responses)
                                if len(all_messages) > len(messages) and reconstructed_assistant_count > 0:
                                    print(f"   ✅ Reconstructed {len(all_messages)} messages from checkpoints (was {len(messages)})")
                                    messages = all_messages
                                    # Update state with full messages
                                    state.values["messages"] = messages
                                elif len(all_messages) > len(messages) and reconstructed_assistant_count == 0:
                                    print(f"   ⚠️  Reconstructed more messages but missing assistant messages - keeping original")
                                    # Keep original messages if reconstruction lost assistant messages
                                else:
                                    print(f"   ℹ️  Checkpoint reconstruction found {len(all_messages)} messages (same or fewer than get_state)")
                    except Exception as checkpoint_error:
                        print(f"   ⚠️ Could not reconstruct from checkpoints: {checkpoint_error}")
                        import traceback
                        traceback.print_exc()
        else:
            print(f"   ⚠️ State is None")
            
    except Exception as e:
        print(f"❌ Error retrieving session state: {e}")
        import traceback
        traceback.print_exc()
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
    messages_list = state.values.get("messages", [])
    
    # Final validation: ensure we have both user and assistant messages if there are user messages
    final_user_count = sum(1 for m in messages_list if isinstance(m, HumanMessage))
    final_assistant_count = sum(1 for m in messages_list if isinstance(m, AIMessage))
    print(f"   📤 Formatting {len(messages_list)} messages for response ({final_user_count} user, {final_assistant_count} assistant)")
    
    # If we have user messages but no assistant messages, that's a problem
    if final_user_count > 0 and final_assistant_count == 0:
        print(f"   ⚠️ WARNING: Final message list has {final_user_count} user messages but 0 assistant messages!")
        print(f"   ⚠️ This indicates a problem with message retrieval - assistant responses may be missing")
    
    for msg in messages_list:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        content = msg.content if hasattr(msg, 'content') else str(msg)
        formatted_messages.append({"role": role, "content": content})
    
    print(f"   ✅ Returning {len(formatted_messages)} formatted messages")
    
    # Query for policy associated with this session
    policy_data = None
    policy_confirmed = False
    
    try:
        from app.models.trip import Trip
        from app.models.policy import Policy
        
        # Find trip by session_id
        trip = db.query(Trip).filter(Trip.session_id == session_id).first()
        
        if trip:
            # Find policy via trip -> quotes -> policy
            # Get the most recent confirmed quote for this trip
            from app.models.quote import Quote
            quote = db.query(Quote).filter(
                Quote.trip_id == trip.id
            ).order_by(Quote.created_at.desc()).first()
            
            if quote:
                # Find policy for this quote
                policy = db.query(Policy).filter(
                    Policy.quote_id == quote.id
                ).first()
                
                if policy:
                    policy_confirmed = True
                    # Prepare policy data for response
                    policy_data = {
                        "id": str(policy.id),
                        "policy_number": policy.policy_number,
                        "status": policy.status.value if hasattr(policy.status, 'value') else str(policy.status),
                        "effective_date": policy.effective_date.isoformat() if policy.effective_date else None,
                        "expiry_date": policy.expiry_date.isoformat() if policy.expiry_date else None,
                        "coverage": policy.coverage,
                        "named_insureds": policy.named_insureds,
                        "selected_tier": quote.selected_tier if quote else None
                    }
                    print(f"   ✅ Found confirmed policy {policy.policy_number} for session")
    except Exception as e:
        print(f"   ⚠️ Error querying policy: {e}")
        # Don't fail the whole endpoint if policy lookup fails
    
    return ChatSessionState(
        session_id=session_id,
        state=state.values,
        messages=formatted_messages,
        policy=policy_data,
        policy_confirmed=policy_confirmed
    )


@router.post("/upload-image", response_model=ImageUploadResponse)
async def upload_image(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    user_message: Optional[str] = Form(None),  # Optional user message context
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
        if user_message:
            print(f"📝 User message context: {user_message}")
        
        try:
            extracted_json = json_extractor.extract(
                ocr_text=ocr_text,
                session_id=session_id,
                filename=file.filename or "uploaded_file",
                user_message=user_message  # Pass user message as context
            )
        except Exception as e:
            print(f"❌ JSON extraction failed: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract document data: {str(e)}"
            )
        
        # Check for extraction errors
        if extracted_json.get("error"):
            error_msg = extracted_json.get("error", "Unknown error")
            print(f"⚠️  Extraction returned error: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Document extraction failed: {error_msg}"
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

        # Step 5: Store document data in graph state WITHOUT invoking the graph
        # The graph will only be invoked when the user sends "Yes, confirm" message
        if ocr_text:
            try:
                graph = get_conversation_graph(db)
                config = {"configurable": {"thread_id": session_id}}

                # Load existing state
                try:
                    existing_state = graph.get_state(config)
                    state_values = existing_state.values if existing_state else {}
                except:
                    state_values = {}

                # Store extracted JSON in state for later processing
                if "document_data" not in state_values:
                    state_values["document_data"] = []
                state_values["document_data"].append({
                    "filename": file.filename,
                    "extracted_json": extracted_json,
                    "document_type": extracted_json.get("document_type"),
                    "uploaded_at": datetime.now().isoformat()
                })

                # Ensure messages exist in state (required for session to be retrievable)
                # Helper function to get assistant message based on document type
                def get_assistant_message_for_doc_type(doc_type: str) -> str:
                    if doc_type == "flight_confirmation":
                        return "I've extracted the information from your flight booking. Please review the details below:"
                    elif doc_type == "hotel_booking":
                        return "I've extracted the information from your hotel booking. Please review the details below:"
                    elif doc_type == "visa_application":
                        return "I've extracted the information from your visa. Please review the details below:"
                    elif doc_type == "itinerary":
                        return "I've extracted the information from your itinerary. Please review the details below:"
                    else:
                        return "I've extracted the information from your document. Please review the details below:"
                
                # Create user message about the upload
                upload_message = user_message if user_message else f"[User uploaded a document: {file.filename}]"
                user_msg = HumanMessage(content=upload_message)
                
                # Create assistant response message
                assistant_msg_content = get_assistant_message_for_doc_type(document_type or "document")
                assistant_msg = AIMessage(content=assistant_msg_content)
                
                # If this is a new session, create initial messages
                if "messages" not in state_values or not state_values.get("messages"):
                    state_values["messages"] = [user_msg, assistant_msg]
                    print(f"✅ Created initial messages for new session")
                else:
                    # Session already exists, just add the user upload message and assistant response
                    state_values["messages"].append(user_msg)
                    state_values["messages"].append(assistant_msg)
                    print(f"✅ Added upload messages to existing session")

                # Update state WITHOUT invoking the graph (no questions asked yet)
                # Use graph.update_state to store document_data and messages without triggering execution
                graph.update_state(config, {
                    "document_data": state_values["document_data"],
                    "messages": state_values["messages"]
                })

                print(f"✅ Document data stored in state (not processed yet - waiting for user confirmation)")

            except Exception as e:
                print(f"⚠️  Could not store document data: {e}")
                import traceback
                traceback.print_exc()

        # Prepare response - Human-friendly message to trigger card display
        # Frontend will use the extracted_json from ocr_result to display the card
        document_type = extracted_json.get("document_type", "document")
        if document_type == "flight_confirmation":
            message_suggestion = "I've extracted the information from your flight booking. Please review the details below:"
        elif document_type == "hotel_booking":
            message_suggestion = "I've extracted the information from your hotel booking. Please review the details below:"
        elif document_type == "visa_application":
            message_suggestion = "I've extracted the information from your visa. Please review the details below:"
        elif document_type == "itinerary":
            message_suggestion = "I've extracted the information from your itinerary. Please review the details below:"
        else:
            message_suggestion = "I've extracted the information from your document. Please review the details below:"
        
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
            message=message_suggestion,
            document_id=str(storage_result.get("id")) if storage_result.get("id") else None
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
