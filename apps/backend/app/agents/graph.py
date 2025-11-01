"""LangGraph conversation orchestration."""

from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime, date
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.checkpoint.sqlite import SqliteSaver
import os
import uuid
import dateparser

from app.agents.tools import ConversationTools
from app.agents.llm_client import GroqLLMClient
from app.services.pricing import PricingService
from app.services.geo_mapping import GeoMapper
# JSONExtractor imported lazily inside process_document to avoid circular import
from app.services.policy_recommender import PolicyRecommender
from app.core.config import settings
from app.models.trip import Trip

# Singleton checkpointer to avoid connection pool conflicts
_checkpointer_singleton = None
_checkpointer_lock = False


class PersistentCheckpointer:
    """Wrapper around PostgresSaver to handle context manager properly."""
    
    def __init__(self, conn_string):
        self.conn_string = conn_string
        self._checkpointer_context = None
        self._checkpointer = None
    
    def __getattr__(self, name):
        """Delegate all method calls to the actual checkpointer."""
        if self._checkpointer is None:
            # Lazy initialization - create checkpointer when first accessed
            from langgraph.checkpoint.postgres import PostgresSaver
            self._checkpointer_context = PostgresSaver.from_conn_string(self.conn_string)
            self._checkpointer = self._checkpointer_context.__enter__()
        return getattr(self._checkpointer, name)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._checkpointer_context:
            self._checkpointer_context.__exit__(exc_type, exc_val, exc_tb)

def get_or_create_checkpointer():
    """
    Create or retrieve PostgreSQL checkpointer for conversation state persistence.
    Uses Supabase PostgreSQL connection for checkpointing.
    """
    global _checkpointer_singleton

    if _checkpointer_singleton is not None:
        return _checkpointer_singleton

    try:
        from langgraph.checkpoint.postgres import PostgresSaver

        # Use the database URL from settings
        conn_string = settings.database_url

        # For Supabase pooler, convert from transaction pooler (6543) to session pooler (5432)
        # Session pooler supports prepared statements which LangGraph needs
        if 'pooler.supabase.com:6543' in conn_string:
            conn_string = conn_string.replace(':6543/', ':5432/')
            print(f"📦 Initializing PostgreSQL checkpointer (using session pooler)...")
        else:
            print(f"📦 Initializing PostgreSQL checkpointer...")

        print(f"   Connection: {conn_string.split('@')[1].split('?')[0] if '@' in conn_string else 'local'}")

        # Create checkpointer and setup tables
        with PostgresSaver.from_conn_string(conn_string) as checkpointer:
            # Setup creates the checkpoint tables if they don't exist
            checkpointer.setup()
            print("   ✓ Checkpoint tables verified/created")

        # Now create the persistent wrapper
        _checkpointer_singleton = PersistentCheckpointer(conn_string)

        print("✅ PostgreSQL checkpointing enabled (Phase 2)")
        return _checkpointer_singleton

    except Exception as e:
        print(f"⚠️  PostgreSQL checkpointing failed: {e}")
        print("   Falling back to stateless mode")
        import traceback
        traceback.print_exc()
        return None


def parse_date_safe(date_string: str, prefer_future: bool = True, reference_date: Optional[date] = None) -> Optional[date]:
    """Safely parse date string to date object with flexible format support.
    
    Accepts multiple formats:
    - YYYY-MM-DD (2025-12-15)
    - MM/DD/YYYY (12/15/2025)
    - DD/MM/YYYY (15/12/2025)
    - Natural language (December 15, 2025, Dec 15, 2025)
    - Dates without year (25 jan, Jan 30) - will infer year intelligently
    - Relative dates (tomorrow, next week, in 3 days)
    
    Args:
        date_string: Date in any common format
        prefer_future: If True, prefer future dates when year is ambiguous
        reference_date: Reference date for year inference (e.g., departure_date for return_date)
        
    Returns:
        date object if parsing succeeds, None otherwise
    """
    try:
        if not isinstance(date_string, str):
            return None
            
        # First try standard YYYY-MM-DD for efficiency
        if len(date_string) == 10 and date_string.count('-') == 2:
            try:
                parsed = datetime.strptime(date_string, "%Y-%m-%d").date()
                # If we have a reference date and parsed date is before it, try next year
                if reference_date and parsed < reference_date:
                    # Same month/day, next year
                    try:
                        parsed = parsed.replace(year=parsed.year + 1)
                    except ValueError:  # Feb 29 in non-leap year
                        parsed = parsed.replace(year=parsed.year + 1, day=28)
                return parsed
            except:
                pass
        
        # Use dateparser for flexible parsing
        base_date = reference_date if reference_date else datetime.now().date()
        settings = {
            'PREFER_DATES_FROM': 'future' if prefer_future else 'current_period',  # Prefer future dates for travel
            'RELATIVE_BASE': datetime.combine(base_date, datetime.min.time()),
            'RETURN_AS_TIMEZONE_AWARE': False,
        }
        
        parsed = dateparser.parse(date_string, settings=settings)
        
        if parsed:
            parsed_date = parsed.date()
            # If we have a reference date and parsed date is before it, try next year
            if reference_date and parsed_date < reference_date:
                # Same month/day, next year
                try:
                    parsed_date = parsed_date.replace(year=parsed_date.year + 1)
                except ValueError:  # Feb 29 in non-leap year
                    parsed_date = parsed_date.replace(year=parsed_date.year + 1, day=28)
            return parsed_date
        
        return None
        
    except Exception as e:
        print(f"   ⚠️ Date parsing error for '{date_string}': {e}")
        return None


class ConversationState(TypedDict):
    """State for conversation graph."""
    messages: List[BaseMessage]
    user_id: str
    session_id: str  # Chat session ID for linking to trips
    current_intent: str
    collected_slots: Dict[str, Any]
    confidence_score: float
    requires_human: bool
    quote_data: Dict[str, Any]
    policy_question: str
    claim_type: str
    handoff_reason: str
    # Fields for Step 1 quote flow
    trip_details: Dict[str, Any]  # destination, departure_date, return_date, duration_days, area, base_rate
    travelers_data: Dict[str, Any]  # ages list, count
    preferences: Dict[str, Any]  # adventure_sports
    current_question: str  # Which question we're asking
    awaiting_confirmation: bool  # Waiting for user confirmation
    confirmation_received: bool  # User confirmed details
    awaiting_field: str  # Specific field being collected
    # Loop protection and flow control
    _loop_count: int  # Safety counter to prevent infinite loops
    _ready_for_pricing: bool  # Flag when ready to generate quote
    _pricing_complete: bool  # Flag when quote has been generated
    trip_id: str  # Database trip ID (created after destination is provided)
    # Payment processing
    _payment_intent_id: str  # Payment intent ID for tracking
    _awaiting_payment_confirmation: bool  # Waiting for user to confirm payment
    _policy_created: bool  # Flag when policy has been created
    # Claims intelligence fields
    claims_insights: Optional[Dict[str, Any]]  # Store risk analysis results
    risk_narrative: Optional[str]  # LLM-generated risk narrative
    # OCR and document processing
    uploaded_images: List[Dict[str, Any]]  # Metadata about uploaded images/documents
    ocr_results: List[Dict[str, Any]]  # OCR extraction results
    document_data: List[Dict[str, Any]]  # Structured JSON data from uploaded documents
    uploaded_filename: str  # Filename of the most recently uploaded document


def create_conversation_graph(db) -> StateGraph:
    """Create the conversation state graph."""
    
    llm_client = GroqLLMClient()
    tools = ConversationTools(db, llm_client)
    pricing_service = PricingService()
    
    def orchestrator(state: ConversationState) -> ConversationState:
        """Route conversation based on LLM intent classification."""
        
        # Initialize essential state fields if missing
        if "_loop_count" not in state:
            state["_loop_count"] = 0
        if "_ready_for_pricing" not in state:
            state["_ready_for_pricing"] = False
        if "_pricing_complete" not in state:
            state["_pricing_complete"] = False
        if "trip_details" not in state:
            state["trip_details"] = {}
        if "travelers_data" not in state:
            state["travelers_data"] = {}
        if "preferences" not in state:
            state["preferences"] = {}
        if "collected_slots" not in state:
            state["collected_slots"] = {}
        if "quote_data" not in state:
            state["quote_data"] = {}
        
        # Don't increment loop_count here - it's handled in should_continue to avoid double-counting
        loop_count = state.get("_loop_count", 0)
        print(f"\n{'='*60}")
        print(f"🔀 ORCHESTRATOR (iteration {loop_count})")
        print(f"{'='*60}")
        
        messages = state.get("messages", [])
        if not messages:
            state["current_intent"] = "quote"
            return state
        
        last_message = messages[-1]
        
        # CRITICAL: Skip intent classification if last message is from AI
        # This prevents re-classifying intent after we've already responded
        if isinstance(last_message, AIMessage):
            print(f"   ⏭️  Skipping intent classification (last message is AI)")
            # Preserve existing intent if we have one, otherwise default to quote
            if "current_intent" not in state:
                state["current_intent"] = "quote"
            return state
        
        user_message = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        # Check if we're already in an active quote flow - don't re-classify unless user changes topic
        in_active_flow = (
            state.get("trip_details", {}).get("destination") or
            state.get("current_question") or
            state.get("awaiting_confirmation", False)
        )
        
        # CRITICAL: Always re-classify when pricing is complete (user might want to purchase)
        # This ensures LLM handles payment intent detection, not hardcoded keywords
        pricing_complete = state.get("_pricing_complete", False)
        
        # If we're in an active flow and user message is short/continuing the conversation, 
        # keep the quote intent without re-classifying (unless pricing is complete)
        if in_active_flow and "current_intent" in state and not pricing_complete:
            # Only re-classify if user seems to be changing topic (mentions policy, claim, etc.)
            # Note: Payment detection handled by LLM when pricing_complete is True
            user_lower = user_message.lower()
            topic_change_keywords = ["policy", "claim", "coverage", "what does", "explain", "document", "upload"]
            if not any(keyword in user_lower for keyword in topic_change_keywords):
                print(f"   ⏭️  In active quote flow, preserving intent: {state.get('current_intent')}")
                return state
        
        # Get conversation history for context
        history = []
        for msg in messages[-5:]:  # Last 5 messages
            if isinstance(msg, HumanMessage) or (hasattr(msg, 'content') and not isinstance(msg, AIMessage)):
                content = msg.content if hasattr(msg, 'content') else str(msg)
                history.append(content)
        
        # Use LLM to classify intent
        intent_result = llm_client.classify_intent(user_message, history)
        
        intent = intent_result["intent"]
        confidence = intent_result["confidence"]
        
        state["current_intent"] = intent
        state["confidence_score"] = confidence

        print(f"Intent: {intent} (confidence: {confidence:.2f})")

        # Check if human handoff needed (low confidence)
        # Exception: "quote" intent with low confidence should still proceed (common for simple trip queries)
        if confidence < 0.6 and intent != "quote":
            state["requires_human"] = True
        else:
            state["requires_human"] = False

        return state
    
    def needs_assessment(state: ConversationState) -> ConversationState:
        """Collect trip information through structured 6-question conversation."""
        try:
            # Initialize data structures if not present
            # travelers_data structure: {"ages": [30, 35, 8], "count": 3}
            if "trip_details" not in state:
                state["trip_details"] = {}
            if "travelers_data" not in state:
                state["travelers_data"] = {}
            if "preferences" not in state:
                state["preferences"] = {}
            if "awaiting_confirmation" not in state:
                state["awaiting_confirmation"] = False
            if "confirmation_received" not in state:
                state["confirmation_received"] = False
            
            # CRITICAL: Get references to dictionaries, not copies
            # This ensures changes persist in state
            if "trip_details" not in state:
                state["trip_details"] = {}
            if "travelers_data" not in state:
                state["travelers_data"] = {}
            if "preferences" not in state:
                state["preferences"] = {}
            
            trip = state["trip_details"]  # Direct reference, not .get() copy
            travelers = state["travelers_data"]  # Direct reference
            prefs = state["preferences"]  # Direct reference
            
            if not state.get("messages"):
                return state
            
            last_message = state["messages"][-1]
            user_input = last_message.content if hasattr(last_message, 'content') else str(last_message)
            
            # Prepare current slots for extraction
            current_slots = {
                "destination": trip.get("destination"),
                "departure_date": trip.get("departure_date").isoformat() if isinstance(trip.get("departure_date"), date) else trip.get("departure_date"),
                "return_date": trip.get("return_date").isoformat() if isinstance(trip.get("return_date"), date) else trip.get("return_date"),
                "travelers_ages": travelers.get("ages"),
                "adventure_sports": prefs.get("adventure_sports"),
            }
            
            # Extract information from user message using LLM
            extracted = llm_client.extract_trip_info(user_input, current_slots)

            # CRITICAL: Check if document data was uploaded and merge it
            document_data = state.get("document_data", [])
            if document_data:
                print(f"   📄 Found {len(document_data)} uploaded document(s)")
                # Process the most recent document
                latest_doc = document_data[-1]
                extracted_json = latest_doc.get("extracted_json", {})
                document_type = extracted_json.get("document_type", "unknown")

                print(f"   📋 Document type: {document_type}")
                print(f"   🔍 Merging document data with LLM extraction...")

                # Merge document data (document data takes precedence over LLM extraction from text)
                if document_type == "flight_confirmation":
                    # Map nested JSON structure to flat fields for Ancileo API
                    # Extract destination from nested structure: destination.country or destination
                    dest_field = extracted_json.get("destination")
                    if isinstance(dest_field, dict):
                        # Nested structure: {"country": "South Korea", "city": "Seoul", ...}
                        destination = dest_field.get("country")
                    elif isinstance(dest_field, str):
                        # Flat structure: "South Korea"
                        destination = dest_field
                    else:
                        destination = None

                    if destination:
                        extracted["destination"] = destination
                        print(f"      ✅ Extracted destination from document: {destination}")

                    # Extract departure date from nested structure: flight_details.departure.date or departure_date
                    flight_details = extracted_json.get("flight_details", {})
                    departure_info = flight_details.get("departure", {})
                    departure_date = departure_info.get("date") or extracted_json.get("departure_date")

                    if departure_date:
                        extracted["departure_date"] = departure_date
                        print(f"      ✅ Extracted departure_date from document: {departure_date}")

                    # Extract return date from nested structure: flight_details.return.date or return_date
                    return_info = flight_details.get("return", {})
                    return_date = return_info.get("date") or extracted_json.get("return_date")

                    if return_date:
                        extracted["return_date"] = return_date
                        print(f"      ✅ Extracted return_date from document: {return_date}")

                    # Extract travelers count from travelers array or travelers_count field
                    travelers_list = extracted_json.get("travelers", [])
                    travelers_count = len(travelers_list) if travelers_list else extracted_json.get("travelers_count")

                    if travelers_count:
                        extracted["travelers_count"] = travelers_count
                        print(f"      ✅ Extracted travelers_count from document: {travelers_count}")

                    # Store FULL document JSON in trip metadata_json
                    if state.get("trip_id"):
                        try:
                            existing_trip = db.query(Trip).filter(Trip.id == uuid.UUID(state["trip_id"])).first()
                            if existing_trip:
                                # Update or create metadata_json
                                if not existing_trip.metadata_json:
                                    existing_trip.metadata_json = {}

                                # Store full document data under "documents" key
                                if "documents" not in existing_trip.metadata_json:
                                    existing_trip.metadata_json["documents"] = []

                                existing_trip.metadata_json["documents"].append({
                                    "document_type": document_type,
                                    "uploaded_at": latest_doc.get("uploaded_at"),
                                    "filename": latest_doc.get("filename"),
                                    "full_extraction": extracted_json  # Store complete JSON
                                })

                                db.commit()
                                print(f"      ✅ Stored full document JSON in trip metadata_json")
                        except Exception as e:
                            print(f"      ⚠️  Failed to store document in metadata_json: {e}")

                # Clear document_data after processing to avoid re-processing
                state["document_data"] = []
                print(f"   ✅ Document data merged and cleared")

            # Fallback: Direct date pattern matching if LLM didn't extract dates
            # TEMPORARILY COMMENTED OUT FOR TESTING
            # import re
            # if not extracted.get("departure_date") and state.get("current_question") == "departure_date":
            #     date_pattern = r'\b(\d{4})-(\d{2})-(\d{2})\b'
            #     match = re.search(date_pattern, user_input)
            #     if match:
            #         extracted["departure_date"] = match.group(0)
            #         print(f"   📅 Fallback: Extracted departure date from pattern: {extracted['departure_date']}")

            # if not extracted.get("return_date") and state.get("current_question") == "return_date":
            #     date_pattern = r'\b(\d{4})-(\d{2})-(\d{2})\b'
            #     match = re.search(date_pattern, user_input)
            #     if match:
            #         extracted["return_date"] = match.group(0)
            #         print(f"   📅 Fallback: Extracted return date from pattern: {extracted['return_date']}")

            # Update state with extracted information
            current_q = state.get("current_question", "")
            extracted_info = False
            
            print(f"   🔍 Extracted data from LLM: {extracted}")
            print(f"   📝 Current question: {current_q}")
            
            if "destination" in extracted:
                trip["destination"] = extracted["destination"]
                print(f"   ✅ Extracted destination: {extracted['destination']}")
                if current_q == "destination":
                    extracted_info = True

                # Create trip in database after destination is provided (if not already created)
                if not state.get("trip_id") and state.get("user_id") and state.get("session_id"):
                    try:
                        # Check if trip already exists for this session
                        existing_trip = db.query(Trip).filter(Trip.session_id == state["session_id"]).first()
                        if not existing_trip:
                            # Build initial metadata JSON
                            from app.services.json_builders import build_trip_metadata_json
                            from datetime import datetime
                            
                            metadata_json = build_trip_metadata_json(
                                session_id=state["session_id"],
                                user_id=state["user_id"],
                                conversation_flow={
                                    "started_at": datetime.now().isoformat()
                                }
                            )
                            
                            new_trip = Trip(
                                user_id=uuid.UUID(state["user_id"]),
                                session_id=state["session_id"],
                                status="draft",
                                destinations=[extracted["destination"]],
                                travelers_count=1,  # Default, will update later
                                metadata_json=metadata_json
                            )
                            db.add(new_trip)
                            db.commit()
                            db.refresh(new_trip)
                            state["trip_id"] = str(new_trip.id)
                            print(f"   🆕 Created trip in database: {new_trip.id}")
                        else:
                            state["trip_id"] = str(existing_trip.id)
                            # Update destination if changed
                            existing_trip.destinations = [extracted["destination"]]
                            # Update metadata_json if not set
                            if not existing_trip.metadata_json:
                                from app.services.json_builders import build_trip_metadata_json
                                from datetime import datetime
                                existing_trip.metadata_json = build_trip_metadata_json(
                                    session_id=state["session_id"],
                                    user_id=state["user_id"],
                                    conversation_flow={
                                        "started_at": datetime.now().isoformat()
                                    }
                                )
                            db.commit()
                            print(f"   ✅ Updated existing trip: {existing_trip.id}")
                    except Exception as e:
                        print(f"   ⚠️  Failed to create/update trip: {e}")

            if "departure_date" in extracted:
                # Parse to date object with error handling
                parsed_date = parse_date_safe(extracted["departure_date"])
                if parsed_date:
                    # Validate date is in the future
                    today = date.today()
                    if parsed_date < today:
                        print(f"   ⚠️  Parsed departure_date {parsed_date} is in the past, attempting to fix...")
                        # Try parsing again with better year inference
                        parsed_date = parse_date_safe(extracted["departure_date"], prefer_future=True)
                        if parsed_date and parsed_date < today:
                            print(f"   ⚠️  Still in past after fix: {parsed_date}, skipping")
                            parsed_date = None
                    
                    if parsed_date:
                        trip["departure_date"] = parsed_date
                        if current_q == "departure_date":
                            extracted_info = True

                        # Update trip with start date
                        if state.get("trip_id"):
                            try:
                                existing_trip = db.query(Trip).filter(Trip.id == uuid.UUID(state["trip_id"])).first()
                                if existing_trip:
                                    existing_trip.start_date = parsed_date
                                    db.commit()
                                    print(f"   ✅ Updated trip start_date: {parsed_date}")
                            except Exception as e:
                                print(f"   ⚠️  Failed to update trip start_date: {e}")
                else:
                    # Date parsing failed - will ask for clarification below
                    print(f"   ⚠️  Failed to parse departure_date: {extracted.get('departure_date')}")
            
            if "return_date" in extracted:
                # Parse to date object with error handling
                parsed_date = parse_date_safe(extracted["return_date"])
                if parsed_date:
                    # Validate return_date is after departure_date
                    departure = trip.get("departure_date")
                    if departure and parsed_date <= departure:
                        print(f"   ⚠️  Parsed return_date {parsed_date} is not after departure_date {departure}, attempting to fix...")
                        # If we have a departure date, try to infer correct year for return
                        if departure:
                            # Extract month/day from return_date and use departure's year (or next year if needed)
                            return_str = extracted["return_date"]
                            # Try to fix by ensuring same year as departure, or next year if that makes it before departure
                            parsed_date = parse_date_safe(return_str, reference_date=departure)
                            if parsed_date and parsed_date <= departure:
                                # If still not after departure, add a year
                                from datetime import timedelta
                                parsed_date = departure + timedelta(days=1)  # At least one day after
                                print(f"   ⚠️  Adjusted return_date to be after departure: {parsed_date}")
                    
                    if parsed_date:
                        trip["return_date"] = parsed_date
                        if current_q == "return_date":
                            extracted_info = True

                        # Update trip with end date
                        if state.get("trip_id"):
                            try:
                                existing_trip = db.query(Trip).filter(Trip.id == uuid.UUID(state["trip_id"])).first()
                                if existing_trip:
                                    existing_trip.end_date = parsed_date
                                    db.commit()
                                    print(f"   ✅ Updated trip end_date: {parsed_date}")
                            except Exception as e:
                                print(f"   ⚠️  Failed to update trip end_date: {e}")
                else:
                    # Date parsing failed - will ask for clarification below
                    print(f"   ⚠️  Failed to parse return_date: {extracted.get('return_date')}")
            
            if "travelers_ages" in extracted:
                # Validate ages are integers in valid range
                valid_ages = [age for age in extracted["travelers_ages"] if isinstance(age, int) and 0.08 <= age <= 110]
                if valid_ages:
                    travelers["ages"] = valid_ages
                    travelers["count"] = len(valid_ages)
                    if current_q == "travelers":
                        extracted_info = True

                    # Update trip with travelers count
                    if state.get("trip_id"):
                        try:
                            existing_trip = db.query(Trip).filter(Trip.id == uuid.UUID(state["trip_id"])).first()
                            if existing_trip:
                                existing_trip.travelers_count = len(valid_ages)
                                db.commit()
                                print(f"   ✅ Updated trip travelers_count: {len(valid_ages)}")
                        except Exception as e:
                            print(f"   ⚠️  Failed to update trip travelers_count: {e}")

            # Handle travelers_count from document (when ages aren't available)
            if "travelers_count" in extracted and not travelers.get("count"):
                count = extracted["travelers_count"]
                if isinstance(count, int) and count > 0:
                    travelers["count"] = count
                    # Default to adult ages if no specific ages provided
                    # This allows the quote flow to continue without asking for ages
                    if not travelers.get("ages"):
                        travelers["ages"] = [30] * count  # Default adult age
                    print(f"   ✅ Set travelers count from document: {count} (using default adult ages)")

                    # Update trip with travelers count
                    if state.get("trip_id"):
                        try:
                            existing_trip = db.query(Trip).filter(Trip.id == uuid.UUID(state["trip_id"])).first()
                            if existing_trip:
                                existing_trip.travelers_count = count
                                db.commit()
                                print(f"   ✅ Updated trip travelers_count: {count}")
                        except Exception as e:
                            print(f"   ⚠️  Failed to update trip travelers_count: {e}")

            # Only accept adventure_sports extraction when:
            # 1. We're currently asking the adventure question, OR
            # 2. The user explicitly mentions adventure-related keywords
            if "adventure_sports" in extracted:
                user_input_lower = user_input.lower().strip()
                adventure_keywords = ["adventure", "skiing", "scuba", "diving", "trekking", "trek", 
                                     "bungee", "jumping", "extreme", "sports", "hiking", "climbing", 
                                     "skydiving", "paragliding", "rafting"]
                mentions_adventure = any(keyword in user_input_lower for keyword in adventure_keywords)
                
                # Validate extracted value against user input for yes/no responses
                # If user says yes/no but LLM extracts opposite, don't trust the extraction
                if current_q == "adventure_sports":
                    pos_words = ["yes", "yeah", "yep", "sure", "probably", "i am", "i'm", "i will", "i'll",
                                "i do", "absolutely", "definitely", "i plan", "i'm planning", "i will be",
                                "i am planning", "i do plan", "of course", "certainly", "definitely yes"]
                    neg_words = ["no", "nope", "not", "none", "nah", "i'm not", "i am not", "i won't", "i will not",
                                "i don't", "i do not", "absolutely not", "definitely not", "no way"]
                    said_yes = any(word in user_input_lower for word in pos_words)
                    said_no = any(word in user_input_lower for word in neg_words)

                    # Handle None extraction - use user's actual words
                    if extracted["adventure_sports"] is None:
                        if said_yes:
                            prefs["adventure_sports"] = True
                            extracted_info = True
                            print(f"   ✅ LLM extracted None, but user said yes - set to True")
                        elif said_no:
                            prefs["adventure_sports"] = False
                            extracted_info = True
                            print(f"   ✅ LLM extracted None, but user said no - set to False")
                        else:
                            print(f"   ⚠️  LLM extracted None and no clear yes/no detected - will re-ask")
                    # If user clearly said yes/no, validate extraction
                    elif said_yes and extracted["adventure_sports"] == False:
                        print(f"   ⚠️  LLM extracted False but user said yes - correcting to True")
                        prefs["adventure_sports"] = True
                        extracted_info = True
                    elif said_no and extracted["adventure_sports"] == True:
                        print(f"   ⚠️  LLM extracted True but user said no - correcting to False")
                        prefs["adventure_sports"] = False
                        extracted_info = True
                    else:
                        # Extraction matches user intent, accept it
                        prefs["adventure_sports"] = extracted["adventure_sports"]
                        extracted_info = True
                        print(f"   ✅ Accepted adventure_sports extraction: {extracted['adventure_sports']} (validated against user input)")
                elif mentions_adventure:
                    # User mentioned adventure keywords - accept extraction
                    prefs["adventure_sports"] = extracted["adventure_sports"]
                    print(f"   ✅ Accepted adventure_sports extraction: {extracted['adventure_sports']} (user mentioned adventure keywords)")
                else:
                    print(f"   ⏭️  Ignoring premature adventure_sports extraction: {extracted['adventure_sports']} (not asking question, no adventure keywords)")
            
            # Clear current_question if we got the answer
            if extracted_info and current_q:
                print(f"   ✅ Received answer for: {current_q}")
                state["current_question"] = ""
            
            # Special handling for adventure_sports when user says yes/no but:
            # 1. LLM doesn't extract adventure_sports, OR
            # 2. LLM extracted it but we rejected it (wrong value)
            # Check if we're asking the adventure question AND haven't successfully extracted it yet
            if current_q == "adventure_sports" and not extracted_info:
                user_input_lower = user_input.lower().strip()
                # Expanded negative keywords
                neg_words = ["no", "nope", "not", "none", "nah", "i'm not", "i am not", "i won't", "i will not",
                            "i don't", "i do not", "absolutely not", "definitely not", "no way", "nothing"]
                # Expanded positive keywords - includes phrases that indicate affirmation
                pos_words = ["yes", "yeah", "yep", "sure", "probably", "i am", "i'm", "i will", "i'll", 
                            "i do", "absolutely", "definitely", "i plan", "i'm planning", "i will be",
                            "i am planning", "i do plan", "of course", "certainly", "definitely yes",
                            "i would", "i'd like", "i want", "planning to", "going to"]
                
                # Check if user explicitly said no
                if any(neg_word in user_input_lower for neg_word in neg_words):
                    prefs["adventure_sports"] = False
                    extracted_info = True
                    state["current_question"] = ""
                    print(f"   ✅ Parsed 'no' for adventure_sports")
                elif any(pos_word in user_input_lower for pos_word in pos_words):
                    prefs["adventure_sports"] = True
                    extracted_info = True
                    state["current_question"] = ""
                    print(f"   ✅ Parsed 'yes' for adventure_sports (matched: {[w for w in pos_words if w in user_input_lower][:1]})")
            
            # Fallback: Simple keyword extraction if LLM didn't extract anything
            # TEMPORARILY COMMENTED OUT FOR TESTING
            # if not any([trip.get("destination"), trip.get("departure_date"), trip.get("return_date"), travelers.get("ages")]):
            #     user_input_lower = user_input.lower()
            #     
            #     # Simple keyword extraction
            #     if "japan" in user_input_lower:
            #         trip["destination"] = "Japan"
            #     elif "thailand" in user_input_lower:
            #         trip["destination"] = "Thailand"
            #     elif "singapore" in user_input_lower:
            #         trip["destination"] = "Singapore"
            #     
            #     # If still no information extracted, this is likely an initial greeting
            #     if not any([trip.get("destination"), trip.get("departure_date"), trip.get("return_date"), travelers.get("ages")]):
            #         # This is an initial greeting - ask for destination first
            #         response = "I'd be happy to help you with travel insurance! Where are you planning to travel?"
            #         state["current_question"] = "destination"  # CRITICAL: Set question to prevent loop
            #         print(f"   💬 Asking: {response}")
            #         state["messages"].append(AIMessage(content=response))
            #         return state
            
            # If still no information extracted, this is likely an initial greeting
            print(f"   🔍 Check: trip.get('destination') = {trip.get('destination')}")
            print(f"   🔍 Missing info check: {not any([trip.get('destination'), trip.get('departure_date'), trip.get('return_date'), travelers.get('ages')])}")
            if not any([trip.get("destination"), trip.get("departure_date"), trip.get("return_date"), travelers.get("ages")]):
                # This is an initial greeting - ask for destination first
                response = "I'd be happy to help you with travel insurance! Where are you planning to travel?"
                state["current_question"] = "destination"  # CRITICAL: Set question to prevent loop
                print(f"   💬 Asking: {response}")
                state["messages"].append(AIMessage(content=response))
                return state
            
            # Ensure departure_country is set (default to SG for Singapore market)
            if not trip.get("departure_country"):
                trip["departure_country"] = "SG"
            
            # Extract arrival_country from destination if we have destination but not arrival_country
            if trip.get("destination") and not trip.get("arrival_country"):
                try:
                    arrival_country_iso = GeoMapper.get_country_iso_code(trip["destination"])
                    trip["arrival_country"] = arrival_country_iso
                    print(f"   ✅ Extracted arrival_country: {arrival_country_iso} from destination: {trip['destination']}")
                except ValueError as e:
                    print(f"   ⚠️  Could not convert destination '{trip['destination']}' to ISO code: {e}")
                    # Will need to ask user for clarification
            
            # Calculate adults_count and children_count from ages if we have ages
            if travelers.get("ages") and not trip.get("adults_count"):
                ages = travelers["ages"]
                adults_count = sum(1 for age in ages if age >= 18)
                children_count = sum(1 for age in ages if age < 18)
                # Ensure at least 1 adult for Ancileo API
                if adults_count == 0 and children_count > 0:
                    adults_count = 1
                    children_count = max(0, children_count - 1)
                trip["adults_count"] = adults_count
                trip["children_count"] = children_count
                print(f"   ✅ Calculated adults_count: {adults_count}, children_count: {children_count}")
            
            # Debug: Print current trip state
            print(f"   🔍 Current trip state: destination={trip.get('destination')}, dep_date={trip.get('departure_date')}, ret_date={trip.get('return_date')}")
            print(f"   🔍 Current travelers state: ages={travelers.get('ages')}, count={travelers.get('count')}")
            
            # Determine what information is still missing (including Ancileo API required fields)
            missing = []
            if not trip.get("destination"):
                missing.append("destination")
            # Check for dates - handle both date objects and strings
            dep_date_value = trip.get("departure_date")
            ret_date_value = trip.get("return_date")
            if not dep_date_value or (isinstance(dep_date_value, str) and not dep_date_value.strip()):
                missing.append("departure_date")
            if not ret_date_value or (isinstance(ret_date_value, str) and not ret_date_value.strip()):
                missing.append("return_date")
            if not travelers.get("ages") and not travelers.get("count"):
                missing.append("traveler ages")
            # Ancileo API required fields
            if not trip.get("arrival_country"):
                missing.append("destination country code")  # More specific than just "destination"
            if not trip.get("adults_count") and not travelers.get("ages"):
                missing.append("number of adults")
            # departure_country defaults to "SG", so not needed in missing check
            
            # Handle confirmation flow (AFTER checking for missing info)
            # Also check if user message contains confirmation keywords even if awaiting_confirmation flag isn't set
            # This handles cases where the flag might not be properly set but user is confirming
            user_response_lower = user_input.lower() if user_input else ""
            contains_confirmation = any(word in user_response_lower for word in ["yes", "correct", "confirm", "looks good", "that's right", "yeah", "confirmed"])
            contains_rejection = any(word in user_response_lower for word in ["no", "wrong", "incorrect", "change", "fix", "reject"])
            
            if state.get("awaiting_confirmation") or (contains_confirmation and not contains_rejection and not state.get("confirmation_received")):
                # Check if user confirmed or wants to make changes
                said_yes = contains_confirmation
                said_no = contains_rejection
                
                if said_yes:
                    state["awaiting_confirmation"] = False
                    state["current_question"] = ""  # Clear the question
                    print(f"   ✅ User confirmed")
                    
                    # Ensure dates are date objects, not strings
                    if trip.get("departure_date") and isinstance(trip["departure_date"], str):
                        trip["departure_date"] = parse_date_safe(trip["departure_date"])
                    if trip.get("return_date") and isinstance(trip["return_date"], str):
                        trip["return_date"] = parse_date_safe(trip["return_date"])
                    
                    # Ensure arrival_country is set if we have destination
                    if trip.get("destination") and not trip.get("arrival_country"):
                        try:
                            arrival_country_iso = GeoMapper.get_country_iso_code(trip["destination"])
                            trip["arrival_country"] = arrival_country_iso
                            print(f"   ✅ Extracted arrival_country: {arrival_country_iso} from destination: {trip['destination']}")
                        except ValueError as e:
                            print(f"   ⚠️  Could not convert destination '{trip['destination']}' to ISO code: {e}")
                    
                    # Ensure adults_count is set if we have travelers
                    if travelers.get("ages") and not trip.get("adults_count"):
                        ages = travelers["ages"]
                        adults_count = sum(1 for age in ages if age >= 18)
                        children_count = sum(1 for age in ages if age < 18)
                        if adults_count == 0 and children_count > 0:
                            adults_count = 1
                            children_count = max(0, children_count - 1)
                        trip["adults_count"] = adults_count
                        trip["children_count"] = children_count
                        print(f"   ✅ Calculated adults_count: {adults_count}, children_count: {children_count}")
                    elif travelers.get("count") and not trip.get("adults_count"):
                        trip["adults_count"] = travelers["count"]
                        trip["children_count"] = 0
                        print(f"   ⚠️  Using travelers count as adults_count: {travelers['count']}")
                    
                    # Debug: Print what we're checking after normalization
                    print(f"   🔍 After normalization check:")
                    print(f"      destination: {trip.get('destination')}")
                    print(f"      departure_date: {trip.get('departure_date')} (type: {type(trip.get('departure_date'))})")
                    print(f"      return_date: {trip.get('return_date')} (type: {type(trip.get('return_date'))})")
                    print(f"      travelers.ages: {travelers.get('ages')}")
                    print(f"      travelers.count: {travelers.get('count')}")
                    print(f"      adults_count: {trip.get('adults_count')}")
                    print(f"      arrival_country: {trip.get('arrival_country')}")
                    
                    # Check if all required information is present (after ensuring formats are correct)
                    # Handle dates - they might be date objects or strings
                    has_dep_date_after = bool(trip.get("departure_date"))
                    has_ret_date_after = bool(trip.get("return_date"))
                    has_travelers_after = bool(travelers.get("ages") or travelers.get("count") or trip.get("adults_count") is not None)
                    
                    all_required_present = (
                        trip.get("destination") and
                        has_dep_date_after and
                        has_ret_date_after and
                        has_travelers_after and
                        trip.get("arrival_country") and
                        trip.get("adults_count") is not None
                    )
                    
                    print(f"   🔍 all_required_present (after normalization): {all_required_present}")
                    
                    if all_required_present:
                        # Check if adventure_sports still needs to be asked
                        if prefs.get("adventure_sports") is None:
                            print(f"   🔍 All required fields present, but adventure_sports not answered yet")
                            state["awaiting_confirmation"] = False
                            state["current_question"] = "adventure_sports"
                            response = "Thank you for confirming! One more question: Are you planning any adventure activities like skiing, scuba diving, trekking, or bungee jumping?"
                            state["messages"].append(AIMessage(content=response))
                            return state
                        else:
                            # All info is present including adventure - proceed to pricing
                            state["confirmation_received"] = True
                            state["_ready_for_pricing"] = True
                            print(f"   ✅ All required info present - ready for pricing")
                            response = "Great! Let me calculate your insurance options..."
                            state["messages"].append(AIMessage(content=response))
                            return state  # Return early - routing will handle going to pricing
                    else:
                        # Still missing some info - continue collecting
                        # Recalculate missing fields after normalization
                        missing_after_check = []
                        if not trip.get("destination"):
                            missing_after_check.append("destination")
                        if not trip.get("departure_date"):
                            missing_after_check.append("departure date")
                        if not trip.get("return_date"):
                            missing_after_check.append("return date")
                        if not travelers.get("ages") and not trip.get("adults_count"):
                            missing_after_check.append("traveler ages")
                        if not trip.get("arrival_country"):
                            missing_after_check.append("destination country code")
                        if not trip.get("adults_count"):
                            missing_after_check.append("number of adults")

                        print(f"   ⚠️  Still missing info: {missing_after_check} - continuing to collect")
                        # Don't set ready_for_pricing yet, continue asking questions below
                        # Update the missing list with the recalculated missing fields
                        missing = missing_after_check
                        # Clear awaiting_confirmation to allow asking next question
                        state["awaiting_confirmation"] = False
                        state["current_question"] = ""  # Will be set below when asking next question
                        state["_just_confirmed"] = True  # Flag to prepend acknowledgment to next question
                        # DON'T append message or return here - let the code continue below to ask next question
                        # The acknowledgment will be combined with the next question
                elif said_no:
                    state["awaiting_confirmation"] = False
                    state["current_question"] = ""  # Clear to ask for corrections
                    response = "No problem! What would you like to correct?"
                    state["messages"].append(AIMessage(content=response))
                    return state
                else:
                    # User didn't clearly say yes or no
                    response = "I didn't catch that. Is the information above correct? (yes/no)"
                    state["messages"].append(AIMessage(content=response))
                    return state
            
            # Check if user provided everything at once (including Ancileo API required fields)
            # Handle dates - they might be date objects or strings
            has_dep_date = bool(trip.get("departure_date"))
            has_ret_date = bool(trip.get("return_date"))
            has_travelers_info = bool(travelers.get("ages") or travelers.get("count") or trip.get("adults_count") is not None)
            
            all_required_present = (
                trip.get("destination") and
                has_dep_date and
                has_ret_date and
                has_travelers_info and
                trip.get("arrival_country") and  # Ancileo API required
                trip.get("adults_count") is not None  # Ancileo API required (can be 0, but must be set)
            )
            
            # Debug logging
            if not all_required_present:
                print(f"   🔍 all_required_present check failed:")
                print(f"      destination: {bool(trip.get('destination'))}")
                print(f"      departure_date: {has_dep_date} (value: {trip.get('departure_date')})")
                print(f"      return_date: {has_ret_date} (value: {trip.get('return_date')})")
                print(f"      travelers: {has_travelers_info} (ages: {travelers.get('ages')}, count: {travelers.get('count')}, adults_count: {trip.get('adults_count')})")
                print(f"      arrival_country: {bool(trip.get('arrival_country'))}")
                print(f"      adults_count set: {trip.get('adults_count') is not None}")
            
            # Generate appropriate response based on conversation state
            print(f"   🔍 Debug: missing={missing}, adventure_sports={prefs.get('adventure_sports')}, all_present={all_required_present}")
            print(f"   🔍 Conditions: awaiting_confirmation={state.get('awaiting_confirmation')}, adventure_is_none={prefs.get('adventure_sports') is None}")
            print(f"   🔍 Current question: {state.get('current_question')}")
            
            # Priority 1: Show confirmation card FIRST when all required fields are present
            # Adventure question comes AFTER user confirms the card
            # DO NOT ask about adventure_sports or default it yet - that comes AFTER confirmation
            if not state.get("awaiting_confirmation") and all_required_present:
                print(f"   🔍 Branch: All required fields present - showing confirmation card")

                dest = trip["destination"]
                dep_date = trip["departure_date"]
                ret_date = trip["return_date"]

                # Ensure dates are date objects for formatting
                if isinstance(dep_date, str):
                    dep_date = parse_date_safe(dep_date)
                if isinstance(ret_date, str):
                    ret_date = parse_date_safe(ret_date)

                if not dep_date or not ret_date:
                    # Can't format dates, skip confirmation for now
                    response = "I need your travel dates to proceed. When are you traveling?"
                    state["current_question"] = "departure_date"
                    state["messages"].append(AIMessage(content=response))
                    return state

                duration_days = (ret_date - dep_date).days + 1

                dep_formatted = dep_date.strftime("%B %d, %Y")
                ret_formatted = ret_date.strftime("%B %d, %Y")
                ages = ", ".join(map(str, travelers.get("ages", []))) if travelers.get("ages") else "Not specified"

                # ONLY show what was extracted from the document - NO adventure_sports yet
                response = f"""Let me confirm your trip details:

📍 Destination: {dest}
📅 Travel dates: {dep_formatted} to {ret_formatted} ({duration_days} days)
👥 Travelers: {len(travelers['ages'])} traveler(s) (ages: {ages})

Is this information correct? (yes/no)"""

                state["awaiting_confirmation"] = True
                state["current_question"] = "confirmation"
                print(f"   💬 Asking for confirmation (document extraction only - no adventure_sports yet)")
            elif missing:
                print(f"   🔍 Branch: Asking missing questions")
                # Check if we just came from confirmation - if so, prepend acknowledgment
                acknowledgment = ""
                if state.get("_just_confirmed"):
                    acknowledgment = "Thank you for confirming! I just need a few more details to get you the best quote.\n\n"
                    state["_just_confirmed"] = False  # Clear the flag

                # Ask for next missing piece of information
                if "destination" in missing:
                    response = f"{acknowledgment}Where are you traveling to?"
                    state["current_question"] = "destination"
                    print(f"   💬 Asking: {response}")
                elif "departure_date" in missing or "departure date" in missing:
                    response = f"{acknowledgment}When does your trip start? Please provide the date in YYYY-MM-DD format. For example: 2025-12-15"
                    state["current_question"] = "departure_date"
                    print(f"   💬 Asking: {response}")
                elif "return_date" in missing or "return date" in missing:
                    response = f"{acknowledgment}When do you return to Singapore? Please provide the date in YYYY-MM-DD format. For example: 2025-12-22"
                    state["current_question"] = "return_date"
                    print(f"   💬 Asking: {response}")
                elif any(x in missing for x in ["travelers", "traveler ages", "number of adults"]):
                    response = f"{acknowledgment}How many travelers are going, and what are their ages? For example: '2 travelers, ages 30 and 8'"
                    state["current_question"] = "travelers"
                    print(f"   💬 Asking: {response}")
                else:
                    # Fallback if missing list has items we don't recognize
                    response = f"{acknowledgment}I need a bit more information. Could you tell me about your travelers?"
                    state["current_question"] = "travelers"
                    print(f"   ⚠️  Unrecognized missing items: {missing}, defaulting to travelers question")
            # NOTE: This elif branch is REMOVED - confirmation card logic moved to line 962
            # This prevents duplicate/conflicting confirmation card generation
            else:
                # Shouldn't reach here, but handle gracefully
                response = "I have all the information I need. Let me calculate your quote..."
                state["confirmation_received"] = True
            
            state["messages"].append(AIMessage(content=response))
            return state
            
        except Exception as e:
            # Error handling with friendly message and logging
            import traceback
            print(f"❌ Error in needs_assessment: {e}")
            print(f"   Traceback: {traceback.format_exc()}")
            response = "I'm having trouble processing that. Could you please rephrase?"
            state["messages"].append(AIMessage(content=response))
            return state
    
    def risk_assessment(state: ConversationState) -> ConversationState:
        """Map destination to geographic area for pricing."""
        try:
            trip = state.get("trip_details", {})
            destination = trip.get("destination")
            
            if destination:
                # Use GeoMapper to get area and base rate
                dest_info = GeoMapper.validate_destination(destination)
                trip["area"] = dest_info["area"].value
                trip["base_rate"] = dest_info["base_rate"]
                state["trip_details"] = trip
            
            return state
        except Exception as e:
            state["requires_human"] = True
            return state
    
    def pricing(state: ConversationState) -> ConversationState:
        """Calculate and present insurance quotes with tiered pricing."""
        try:
            trip = state.get("trip_details", {})
            travelers = state.get("travelers_data", {})
            prefs = state.get("preferences", {})
            
            # Extract required data with validation
            destination = trip.get("destination")
            departure_date = trip.get("departure_date")
            return_date = trip.get("return_date")
            travelers_ages = travelers.get("ages", [])
            
            # Validate required fields
            if not destination:
                response = "I need your destination to calculate a quote. Where are you traveling to?"
                state["messages"].append(AIMessage(content=response))
                state["current_question"] = "destination"
                return state
            
            if not departure_date or not return_date:
                response = "I need your travel dates to calculate a quote. When are you traveling?"
                state["messages"].append(AIMessage(content=response))
                state["current_question"] = "departure_date"
                return state
            
            if not travelers_ages:
                response = "I need the ages of all travelers to calculate a quote. How many travelers and what are their ages?"
                state["messages"].append(AIMessage(content=response))
                state["current_question"] = "travelers"
                return state
            
            # Default to False if user never answered or is None
            adventure_sports = prefs.get("adventure_sports", False)
            if adventure_sports is None:
                adventure_sports = False
            
            # Claims Intelligence Integration
            try:
                import logging
                logger = logging.getLogger(__name__)
                
                if destination and travelers_ages:
                    logger.info(f"🔍 Analyzing claims data for {destination}...")
                    
                    # Pass llm_client to tools
                    tools_with_llm = ConversationTools(db=db, llm_client=llm_client)
                    claims_insights = tools_with_llm.analyze_destination_risk(
                        destination=destination,
                        travelers_ages=travelers_ages,
                        adventure_sports=adventure_sports
                    )
                    
                    if claims_insights.get("success"):
                        state["claims_insights"] = claims_insights
                        state["risk_narrative"] = claims_insights.get("narrative")
                        logger.info(f"✅ Risk: {claims_insights['risk_analysis']['risk_level']}, Tier: {claims_insights['tier_recommendation']['recommended_tier']}")
                    else:
                        logger.warning("Claims analysis unavailable")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Claims analysis error: {e}")
                # Continue without insights
            
            # Call pricing service
            quote_result = pricing_service.calculate_step1_quote(
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                travelers_ages=travelers_ages,
                adventure_sports=adventure_sports
            )
            
            if not quote_result["success"]:
                # Error in quote calculation - try fallback pricing
                error_msg = quote_result.get("error", "Unknown error")
                print(f"   ⚠️  Pricing service failed: {error_msg}")
                
                # Check if we have area and base_rate for fallback pricing
                area = trip.get("area")
                base_rate = trip.get("base_rate")
                
                if area and base_rate:
                    print(f"   🔄 Attempting fallback pricing using area={area}, base_rate={base_rate}")
                    # Calculate fallback quotes using base_rate and multipliers
                    from datetime import timedelta
                    # Handle date strings or date objects
                    if isinstance(departure_date, str):
                        departure_date_obj = parse_date_safe(departure_date)
                        if not departure_date_obj:
                            raise ValueError(f"Invalid departure date format: {departure_date}")
                    else:
                        departure_date_obj = departure_date
                    if isinstance(return_date, str):
                        return_date_obj = parse_date_safe(return_date)
                        if not return_date_obj:
                            raise ValueError(f"Invalid return date format: {return_date}")
                    else:
                        return_date_obj = return_date
                    
                    if not departure_date_obj or not return_date_obj:
                        raise ValueError("Invalid dates provided")
                    duration = (return_date_obj - departure_date_obj).days + 1
                    num_travelers = len(travelers_ages)
                    
                    # Calculate base price per traveler per day
                    base_price = base_rate * duration * num_travelers
                    
                    # Tier multipliers (matching PricingService)
                    standard_price = round(base_price * 1.0, 2)
                    elite_price = round(base_price * 1.2, 2)
                    premier_price = round(base_price * 1.5, 2)
                    
                    # Default coverage amounts (reasonable estimates)
                    coverage_standard = {
                        "medical_coverage": 50000,
                        "trip_cancellation": 10000,
                        "baggage_loss": 3000,
                        "personal_accident": 25000
                    }
                    coverage_elite = {
                        "medical_coverage": 100000,
                        "trip_cancellation": 20000,
                        "baggage_loss": 5000,
                        "personal_accident": 50000,
                        "adventure_sports": True
                    }
                    coverage_premier = {
                        "medical_coverage": 200000,
                        "trip_cancellation": 50000,
                        "baggage_loss": 10000,
                        "personal_accident": 100000,
                        "adventure_sports": True,
                        "emergency_evacuation": 500000
                    }
                    
                    # Build fallback quote_result
                    quotes = {}
                    quotes["standard"] = {
                        "tier": "standard",
                        "price": standard_price,
                        "currency": "SGD",
                        "coverage": coverage_standard,
                        "breakdown": {
                            "duration_days": duration,
                            "travelers_count": num_travelers,
                            "area": area,
                            "source": "fallback_calculation"
                        }
                    }
                    quotes["elite"] = {
                        "tier": "elite",
                        "price": elite_price,
                        "currency": "SGD",
                        "coverage": coverage_elite,
                        "breakdown": {
                            "duration_days": duration,
                            "travelers_count": num_travelers,
                            "area": area,
                            "source": "fallback_calculation"
                        }
                    }
                    quotes["premier"] = {
                        "tier": "premier",
                        "price": premier_price,
                        "currency": "SGD",
                        "coverage": coverage_premier,
                        "breakdown": {
                            "duration_days": duration,
                            "travelers_count": num_travelers,
                            "area": area,
                            "source": "fallback_calculation"
                        }
                    }
                    
                    # Ensure dates are in correct format for JSON serialization
                    dep_date_str = departure_date_obj.isoformat() if isinstance(departure_date_obj, date) else str(departure_date_obj)
                    ret_date_str = return_date_obj.isoformat() if isinstance(return_date_obj, date) else str(return_date_obj)
                    
                    quote_result = {
                        "success": True,
                        "destination": destination,
                        "area": area,
                        "departure_date": dep_date_str,
                        "return_date": ret_date_str,
                        "duration_days": duration,
                        "travelers_count": num_travelers,
                        "adventure_sports": adventure_sports,
                        "quotes": quotes,
                        "ancileo_reference": None,  # No Ancileo reference for fallback
                        "recommended_tier": "elite" if adventure_sports else "standard",
                        "fallback": True  # Flag to indicate this is a fallback quote
                    }
                    print(f"   ✅ Fallback pricing calculated successfully")
                else:
                    # No fallback possible - need human help
                    if "182 days" in error_msg:
                        response = "Your trip is a bit too long for our standard coverage (maximum 182 days). Let me connect you with a specialist who can help with extended coverage."
                    elif "age" in error_msg.lower():
                        response = "I noticed one of the ages might not be quite right. Travelers should be between 1 month and 110 years old. Could you double-check the ages?"
                    else:
                        response = f"I'm sorry, but I encountered an issue calculating your quote. Let me connect you with a human agent who can help."
                    
                    state["requires_human"] = True
                    state["messages"].append(AIMessage(content=response))
                    return state
            
            # Store full quote result
            state["quote_data"] = quote_result

            # Build and store JSON structures for quote records
            if state.get("trip_id") and state.get("user_id"):
                try:
                    from app.services.json_builders import build_ancileo_quotation_json, build_ancileo_purchase_json
                    from app.models.user import User
                    from app.models.quote import Quote, QuoteStatus, ProductType
                    from decimal import Decimal
                    
                    existing_trip = db.query(Trip).filter(Trip.id == uuid.UUID(state["trip_id"])).first()
                    if existing_trip:
                        quotes = quote_result["quotes"]
                        prices = []
                        if "standard" in quotes:
                            prices.append(quotes["standard"]["price"])
                        if "elite" in quotes:
                            prices.append(quotes["elite"]["price"])
                        if "premier" in quotes:
                            prices.append(quotes["premier"]["price"])

                        if prices:
                            min_price = min(prices)
                            max_price = max(prices)
                            existing_trip.total_cost = f"SGD {min_price:.2f} - SGD {max_price:.2f}"
                        
                        # Build Ancileo JSON structures
                        user = db.query(User).filter(User.id == uuid.UUID(state["user_id"])).first()
                        # Parse name field (User model has single 'name' field, not first_name/last_name)
                        if user and user.name:
                            name_parts = user.name.split(' ', 1)
                            first_name = name_parts[0]
                            last_name = name_parts[1] if len(name_parts) > 1 else ""
                        else:
                            first_name = ""
                            last_name = ""

                        user_data = {
                            "first_name": first_name,
                            "last_name": last_name,
                            "email": user.email if user else ""
                        }
                        
                        # Build quotation JSON
                        ancileo_quotation_json = build_ancileo_quotation_json(
                            trip_details=trip,
                            travelers_data=travelers,
                            preferences=prefs
                        )
                        
                        # Build purchase JSON
                        ancileo_purchase_json = build_ancileo_purchase_json(
                            user_data=user_data,
                            travelers_data=travelers
                        )
                        
                        # Create or update Quote record with JSON structures
                        # Check if quote already exists for this trip
                        existing_quote = db.query(Quote).filter(
                            Quote.trip_id == uuid.UUID(state["trip_id"]),
                            Quote.user_id == uuid.UUID(state["user_id"])
                        ).first()
                        
                        if existing_quote:
                            # Update existing quote with JSON structures and price range
                            existing_quote.ancileo_quotation_json = ancileo_quotation_json
                            existing_quote.ancileo_purchase_json = ancileo_purchase_json
                            existing_quote.price_min = Decimal(str(min_price)) if prices else None
                            existing_quote.price_max = Decimal(str(max_price)) if prices else None
                            existing_quote.status = QuoteStatus.RANGED
                            existing_quote.currency = "SGD"
                            db.commit()
                            print(f"   ✅ Updated existing quote with JSON structures: {existing_quote.id}")
                        else:
                            # Create new quote record
                            travelers_list = [{"age": age} for age in travelers_ages]
                            activities_list = [{"type": "general"}]
                            if adventure_sports:
                                activities_list.append({"type": "adventure_sports"})
                            
                            new_quote = Quote(
                                user_id=uuid.UUID(state["user_id"]),
                                trip_id=uuid.UUID(state["trip_id"]),
                                product_type=ProductType.SINGLE,
                                selected_tier="standard",  # Default, user selects later
                                travelers=travelers_list,
                                activities=activities_list,
                                price_min=Decimal(str(min_price)) if prices else None,
                                price_max=Decimal(str(max_price)) if prices else None,
                                currency="SGD",
                                status=QuoteStatus.RANGED,
                                ancileo_quotation_json=ancileo_quotation_json,
                                ancileo_purchase_json=ancileo_purchase_json
                            )
                            db.add(new_quote)
                            db.commit()
                            db.refresh(new_quote)
                            print(f"   ✅ Created quote with JSON structures: {new_quote.id}")
                        
                        db.commit()
                        print(f"   ✅ Updated trip total_cost: {existing_trip.total_cost}")
                except Exception as e:
                    import traceback
                    print(f"   ⚠️  Failed to create/update quote with JSON structures: {e}")
                    traceback.print_exc()

            # Format a beautiful response with all tiers
            quotes = quote_result["quotes"]
            dest_name = destination.title()
            
            response_parts = [f"Great! Here are your travel insurance options for {dest_name}:\n"]
            
            if "standard" in quotes:
                std = quotes["standard"]
                response_parts.append(f"""
🌟 **Standard Plan: ${std['price']:.2f} SGD**
   ✓ Medical coverage: ${std['coverage']['medical_coverage']:,}
   ✓ Trip cancellation: ${std['coverage']['trip_cancellation']:,}
   ✓ Baggage protection: ${std['coverage']['baggage_loss']:,}
   ✓ Personal accident: ${std['coverage']['personal_accident']:,}
""")
            
            if "elite" in quotes:
                elite = quotes["elite"]
                response_parts.append(f"""
⭐ **Elite Plan: ${elite['price']:.2f} SGD**{' (Recommended for adventure sports)' if adventure_sports else ''}
   ✓ Medical coverage: ${elite['coverage']['medical_coverage']:,}
   ✓ Trip cancellation: ${elite['coverage']['trip_cancellation']:,}
   ✓ Baggage protection: ${elite['coverage']['baggage_loss']:,}
   ✓ Personal accident: ${elite['coverage']['personal_accident']:,}
   ✓ Adventure sports coverage included
""")
            
            if "premier" in quotes:
                premier = quotes["premier"]
                response_parts.append(f"""
💎 **Premier Plan: ${premier['price']:.2f} SGD**
   ✓ Medical coverage: ${premier['coverage']['medical_coverage']:,}
   ✓ Trip cancellation: ${premier['coverage']['trip_cancellation']:,}
   ✓ Baggage protection: ${premier['coverage']['baggage_loss']:,}
   ✓ Personal accident: ${premier['coverage']['personal_accident']:,}
   ✓ Full adventure sports coverage
   ✓ Emergency evacuation: ${premier['coverage']['emergency_evacuation']:,}
""")
            
            response_parts.append("\nAll prices are in Singapore Dollars (SGD). Would you like more details about any plan?")
            
            # Add note if using fallback pricing
            if quote_result.get("fallback"):
                response_parts.append("\n\n⚠️ *Note: Quote calculated using estimated pricing. Our pricing service is temporarily unavailable, but these estimates should give you a good idea of costs.*")
            
            # Add risk narrative if available
            if state.get("risk_narrative"):
                response_parts.append(f"\n\n📊 **Risk Analysis:**\n{state['risk_narrative']}")
                
                # Highlight recommended tier
                if state.get("claims_insights"):
                    recommended = state["claims_insights"]["tier_recommendation"]["recommended_tier"]
                    if recommended != "standard":
                        response_parts.append(f"\n\n💡 **Based on historical data, we recommend the {recommended.title()} plan for optimal coverage.**")
            
            response = "\n".join(response_parts)
            state["messages"].append(AIMessage(content=response))
            
            # CRITICAL: Mark pricing as complete to prevent re-entry
            state["_pricing_complete"] = True
            state["_ready_for_pricing"] = False
            
            print(f"   ✅ Pricing complete, will route to END")
            
            return state
            
        except Exception as e:
            import traceback
            print(f"❌ Error in pricing node: {e}")
            traceback.print_exc()
            response = "I encountered an error calculating your quote. Let me connect you with a human agent."
            state["requires_human"] = True
            state["messages"].append(AIMessage(content=response))
            return state
    
    def payment_processor(state: ConversationState) -> ConversationState:
        """Process payment for insurance purchase."""
        try:
            print("\n💳 PAYMENT PROCESSOR NODE")
            
            messages = state.get("messages", [])
            last_message = messages[-1]
            user_input = last_message.content if hasattr(last_message, 'content') else str(last_message)
            user_input_lower = user_input.lower()
            
            # Check if we're awaiting payment confirmation
            awaiting_payment = state.get("_awaiting_payment_confirmation", False)
            payment_intent_id = state.get("_payment_intent_id")
            
            if awaiting_payment and payment_intent_id:
                # User is confirming payment completion
                print(f"   Checking payment confirmation for: {payment_intent_id}")
                
                # Check if user said they paid
                payment_keywords = ["paid", "done", "completed", "finished", "i paid", "payment done"]
                if any(keyword in user_input_lower for keyword in payment_keywords):
                    # Check payment status
                    payment_result = tools.check_payment_completion(payment_intent_id)
                    
                    if payment_result.get("success") and payment_result.get("is_completed"):
                        # Payment completed - create policy
                        policy_result = tools.create_policy_from_payment(payment_intent_id)
                        
                        if policy_result.get("success"):
                            policy_number = policy_result.get("policy_number")
                            response = f"🎉 Payment successful! Your policy has been created.\n\nPolicy Number: **{policy_number}**\n\nYour travel insurance is now active. You'll receive a confirmation email shortly."
                            state["_policy_created"] = True
                            state["_awaiting_payment_confirmation"] = False
                        else:
                            response = f"Payment was successful, but there was an issue creating your policy. Please contact support. Error: {policy_result.get('error')}"
                    elif payment_result.get("status") == "pending":
                        response = "Still processing your payment... Please wait 10 more seconds and let me know when it's done."
                        # Keep awaiting_payment flag set
                    elif payment_result.get("status") == "failed":
                        response = "Payment failed. Would you like to try again? I can generate a new payment link."
                        state["_awaiting_payment_confirmation"] = False
                    elif payment_result.get("status") == "expired":
                        response = "Payment session expired. I can generate a new payment link if you'd like."
                        state["_awaiting_payment_confirmation"] = False
                    else:
                        response = f"Payment status: {payment_result.get('status', 'unknown')}. Please wait a moment and try again."
                else:
                    # User hasn't confirmed payment yet
                    response = "Please complete the payment using the link I provided, then let me know when it's done."
            else:
                # First time - create payment
                quote_data = state.get("quote_data")
                if not quote_data or not quote_data.get("quotes"):
                    response = "I don't have a quote ready yet. Let me calculate your insurance options first."
                    state["messages"].append(AIMessage(content=response))
                    return state
                
                # Extract tier selection from user input
                tier = None
                if "premier" in user_input_lower or "premium" in user_input_lower:
                    tier = "premier"
                elif "elite" in user_input_lower:
                    tier = "elite"
                elif "standard" in user_input_lower or "basic" in user_input_lower:
                    tier = "standard"
                else:
                    # Default to elite if user said "buy", "purchase", etc. without specifying
                    tier = "elite"  # Default to recommended tier
                
                quotes_dict = quote_data.get("quotes", {})
                if tier not in quotes_dict:
                    # Fallback to available tier
                    tier = list(quotes_dict.keys())[0] if quotes_dict else None
                
                if not tier:
                    response = "I couldn't determine which plan you'd like. Please specify: Standard, Elite, or Premier."
                    state["messages"].append(AIMessage(content=response))
                    return state
                
                selected_quote = quotes_dict[tier]
                price = selected_quote.get("price")
                coverage = selected_quote.get("coverage", {})
                
                print(f"   Selected tier: {tier}, Price: ${price}")
                
                # Get required data from state
                user_id = state.get("user_id")
                trip_id = state.get("trip_id")
                trip_details = state.get("trip_details", {})
                travelers_data = state.get("travelers_data", {})
                
                if not user_id or not trip_id:
                    response = "I need to save your quote first. Let me do that..."
                    # TODO: Could create quote here if needed
                    state["messages"].append(AIMessage(content=response))
                    return state
                
                # Create or find Quote record
                from app.models.quote import Quote, QuoteStatus, ProductType
                from app.models.trip import Trip
                
                # Find existing quote or create new one
                quote = db.query(Quote).filter(
                    Quote.trip_id == uuid.UUID(trip_id),
                    Quote.user_id == uuid.UUID(user_id)
                ).first()
                
                if not quote:
                    # Create new quote record
                    travelers_list = [{"age": age} for age in travelers_data.get("ages", [])]
                    activities_list = [{"type": "general"}]
                    if state.get("preferences", {}).get("adventure_sports"):
                        activities_list.append({"type": "adventure_sports"})
                    
                    # Build Ancileo JSON structures
                    from app.services.json_builders import build_ancileo_quotation_json, build_ancileo_purchase_json
                    from app.models.user import User

                    # Get user data for purchase JSON
                    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
                    # Parse name field (User model has single 'name' field, not first_name/last_name)
                    if user and user.name:
                        name_parts = user.name.split(' ', 1)
                        first_name = name_parts[0]
                        last_name = name_parts[1] if len(name_parts) > 1 else ""
                    else:
                        first_name = ""
                        last_name = ""

                    user_data = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": user.email if user else ""
                    }
                    
                    # Build quotation JSON
                    ancileo_quotation_json = build_ancileo_quotation_json(
                        trip_details=trip_details,
                        travelers_data=travelers_data,
                        preferences=state.get("preferences", {})
                    )
                    
                    # Build purchase JSON
                    ancileo_purchase_json = build_ancileo_purchase_json(
                        user_data=user_data,
                        travelers_data=travelers_data
                    )
                    
                    quote = Quote(
                        user_id=uuid.UUID(user_id),
                        trip_id=uuid.UUID(trip_id),
                        product_type=ProductType.SINGLE,
                        travelers=travelers_list,
                        activities=activities_list,
                        price_firm=float(price),
                        currency="SGD",
                        status=QuoteStatus.FIRMED,
                        breakdown={
                            "tier": tier,
                            "coverage": coverage,
                            "price": price
                        },
                        ancileo_quotation_json=ancileo_quotation_json,
                        ancileo_purchase_json=ancileo_purchase_json
                    )
                    db.add(quote)
                    db.commit()
                    db.refresh(quote)
                    print(f"   Created quote: {quote.id}")
                
                # Update quote with firm price if not set
                if not quote.price_firm:
                    quote.price_firm = float(price)
                    quote.status = QuoteStatus.FIRMED
                    quote.breakdown = {
                        "tier": tier,
                        "coverage": coverage,
                        "price": price
                    }
                    db.commit()
                    db.refresh(quote)
                
                # Create payment checkout
                payment_result = tools.create_payment_checkout(
                    quote_id=str(quote.id),
                    user_id=user_id
                )
                
                if not payment_result.get("success"):
                    response = f"I encountered an issue setting up payment: {payment_result.get('error')}. Please try again or contact support."
                    state["requires_human"] = True
                else:
                    checkout_url = payment_result.get("checkout_url")
                    payment_intent_id = payment_result.get("payment_intent_id")
                    
                    # Store payment info in state
                    state["_payment_intent_id"] = payment_intent_id
                    state["_awaiting_payment_confirmation"] = True
                    state["_checkout_url_sent"] = True  # Flag to prevent re-entry

                    response = f"Great! I've set up your payment for the **{tier.title()}** plan (${price:.2f} SGD).\n\nPlease complete your payment at:\n{checkout_url}\n\nI'll wait here and confirm once payment is successful. This usually takes 10-30 seconds after you complete the payment."

                state["messages"].append(AIMessage(content=response))
            
            return state
            
        except Exception as e:
            print(f"   ⚠️  Payment processor error: {e}")
            import traceback
            traceback.print_exc()
            # Mark that payment processing failed to prevent recursion
            state["_payment_failed"] = True
            state["requires_human"] = True
            response = "I encountered an error processing the payment. Let me connect you with a human agent."
            state["messages"].append(AIMessage(content=response))
            return state
    
    def policy_explainer(state: ConversationState) -> ConversationState:
        """
        Answer policy questions with context-aware responses using RAG and user context.
        
        This node:
        1. Retrieves user's policy/tier context from database
        2. Searches policy documents using RAG
        3. Generates personalized response using Groq LLM
        4. Includes specific coverage amounts for user's tier
        """
        
        print("\n📚 POLICY EXPLAINER NODE (Context-Aware)")
        
        messages = state.get("messages", [])
        last_message = messages[-1]
        user_question = last_message.content if hasattr(last_message, 'content') else str(last_message)
        user_id = state.get("user_id")
        
        print(f"   Question: {user_question[:100]}...")
        
        # Get user's policy/tier context
        from app.agents.tools import get_user_policy_context
        user_context = get_user_policy_context(user_id, db)
        
        print(f"   User context: has_policy={user_context.get('has_policy')}, tier={user_context.get('tier')}")
        
        # Search policy documents using RAG
        from app.services.rag import RAGService
        rag_service = RAGService(db=db)
        
        try:
            # Search with tier filter if user has selected a tier
            search_results = rag_service.search(
                query=user_question,
                limit=3,
                tier=user_context.get("tier") if user_context.get("tier") else None
            )
            print(f"   Found {len(search_results)} relevant policy sections")
        except Exception as e:
            print(f"   ⚠️  RAG search failed: {e}")
            search_results = []
        
        # Format context for LLM
        if user_context.get("has_policy"):
            # User has purchased policy - be specific about their coverage
            tier_display = user_context['tier'].title() if user_context.get('tier') else "Unknown"
            context_prompt = f"""User has an ACTIVE policy:
- Tier: {tier_display}
- Policy Number: {user_context['policy_number']}
- Coverage Period: {user_context['effective_date']} to {user_context['expiry_date']}
- Destination: {user_context['destination']}
- Travelers: {len(user_context.get('travelers', []))} person(s)
- Medical Coverage: ${user_context['coverage'].get('medical_coverage', 'N/A'):,}
- Trip Cancellation: ${user_context['coverage'].get('trip_cancellation', 'N/A'):,}
- Baggage Protection: ${user_context['coverage'].get('baggage_loss', 'N/A'):,}
- Adventure Sports: {'Yes' if user_context['coverage'].get('adventure_sports') else 'No'}

Answer their question SPECIFICALLY about THEIR {tier_display} policy."""
        
        elif user_context.get("tier"):
            # User has selected a tier but not purchased yet
            tier_display = user_context['tier'].title()
            context_prompt = f"""User is considering the {tier_display} plan.
Provide information about this tier and compare with other tiers if relevant."""
        
        else:
            # User hasn't selected a tier yet - provide general comparison
            context_prompt = """User hasn't selected a tier yet. Provide general policy information and highlight differences between Standard, Elite, and Premier tiers."""
        
        # Format RAG results
        rag_context = ""
        if search_results:
            rag_context = "\n\nRelevant Policy Sections:\n\n"
            for i, result in enumerate(search_results, 1):
                pages_str = ', '.join(map(str, result.get('pages', [])))
                rag_context += f"""[{i}] {result['section_id']}: {result['heading']}
(From {result['title']}, Page {pages_str}, Similarity: {result['similarity']:.2f})

{result['text'][:500]}...

---

"""
        
        # Generate response using Groq LLM
        from app.agents.llm_client import get_llm
        llm = get_llm()
        
        system_prompt = f"""You are a helpful travel insurance policy expert. 

{context_prompt}

{rag_context}

Guidelines:
1. Be specific and direct - cite exact coverage amounts
2. Use the policy sections provided above for accurate information
3. If user has a policy, personalize the answer to THEIR coverage
4. Use bullet points for clarity
5. Include citations like "[Section 6: Medical Coverage]"
6. If asked about exclusions, be clear about what's NOT covered
7. If information isn't in the provided sections, say so clearly

Format your response with:
- Clear answer to their question
- Specific coverage amounts (if applicable)
- Relevant exclusions or conditions
- Citation to policy sections"""

        try:
            response_obj = llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ])
            
            response_text = response_obj.content
            
            # Add helpful footer if user has policy
            if user_context.get("has_policy"):
                response_text += f"\n\n---\n📋 Your Policy: {user_context['policy_number']}\n📅 Valid: {user_context['effective_date']} to {user_context['expiry_date']}"
            
        except Exception as e:
            print(f"   ⚠️  LLM generation failed: {e}")
            # Fallback response
            if search_results:
                response_text = "Based on the policy documents:\n\n"
                for result in search_results[:2]:
                    response_text += f"**{result['heading']}** (Section {result['section_id']})\n{result['text'][:300]}...\n\n"
            else:
                response_text = "I couldn't find specific information in our policy documents. Please contact customer service for detailed assistance."
        
        # Update state
        messages.append(AIMessage(content=response_text))
        state["messages"] = messages
        state["policy_question"] = user_question
        
        print(f"   ✅ Generated {len(response_text)} character response")
        
        return state
    
    def process_document(state: ConversationState) -> ConversationState:
        """Process uploaded document using structured JSON data (OCR happens behind the scenes)."""
        
        print("\n📄 DOCUMENT PROCESSING NODE")
        
        messages = state.get("messages", [])
        if not messages:
            return state
        
        last_message = messages[-1]
        message_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        # Check if this is a document upload message
        if "[User uploaded a document" not in message_content:
            # Not a document upload, skip processing
            return state
        
        print(f"   Processing document upload...")
        
        # Get structured JSON from state (already extracted by OCR service)
        document_data = state.get("document_data", [])
        if not document_data:
            response = "I received your document, but couldn't process it. Please try uploading again."
            state["messages"].append(AIMessage(content=response))
            return state
        
        # Get the most recent document
        latest_doc = document_data[-1]
        extracted_json = latest_doc.get("extracted_json", {})
        document_type = extracted_json.get("document_type", "unknown")
        
        # Debug: Print extracted JSON structure (first level keys only)
        print(f"   📋 Extracted JSON keys: {list(extracted_json.keys()) if extracted_json else 'EMPTY'}")
        if extracted_json:
            print(f"   📋 Sample values:")
            for key in list(extracted_json.keys())[:5]:  # Show first 5 keys
                value = extracted_json.get(key)
                if isinstance(value, dict):
                    print(f"      {key}: {{...}} (dict with keys: {list(value.keys())[:3] if value else 'empty'})")
                elif isinstance(value, list):
                    print(f"      {key}: [...] (list with {len(value)} items)")
                else:
                    print(f"      {key}: {str(value)[:50]}")
        
        if document_type == "unknown":
            response = "I received your document, but couldn't determine its type. Could you please describe what information you'd like me to extract?"
            state["messages"].append(AIMessage(content=response))
            return state
        
        print(f"   ✅ Processing structured JSON: {document_type}")
        
        try:
            # Initialize policy recommender
            policy_recommender = PolicyRecommender()
            
            # CRITICAL: Get direct references to dictionaries, not copies
            # This ensures changes persist in state
            if "trip_details" not in state:
                state["trip_details"] = {}
            if "travelers_data" not in state:
                state["travelers_data"] = {}
            if "preferences" not in state:
                state["preferences"] = {}
            
            trip = state["trip_details"]  # Direct reference, not .get() copy
            travelers = state["travelers_data"]  # Direct reference
            prefs = state["preferences"]  # Direct reference
            
            extracted_items = []
            doc_type = extracted_json.get("document_type", "unknown")
            
            # Extract based on document type - use structured JSON first
            if doc_type == "flight_confirmation":
                # Handle None values from JSON (null in JSON becomes None in Python)
                flight_details = extracted_json.get("flight_details") or {}
                destination_info = extracted_json.get("destination") or {}
                
                if destination_info and destination_info.get("country"):
                    trip["destination"] = destination_info["country"]
                    extracted_items.append(f"destination: {destination_info['country']}")
                
                if flight_details:
                    departure = flight_details.get("departure") or {}
                    if departure and departure.get("date"):
                        dep_date_str = departure["date"]
                        parsed_date = parse_date_safe(dep_date_str)
                        if parsed_date:
                            trip["departure_date"] = parsed_date
                            extracted_items.append(f"departure date: {parsed_date}")
                            print(f"   ✅ Extracted and stored departure_date: {parsed_date} (from: {dep_date_str})")
                        else:
                            print(f"   ⚠️  Failed to parse departure_date: {dep_date_str}")
                    
                    return_flight = flight_details.get("return") or {}
                    if return_flight and return_flight.get("date"):
                        ret_date_str = return_flight["date"]
                        parsed_date = parse_date_safe(ret_date_str)
                        if parsed_date:
                            trip["return_date"] = parsed_date
                            extracted_items.append(f"return date: {parsed_date}")
                            print(f"   ✅ Extracted and stored return_date: {parsed_date} (from: {ret_date_str})")
                        else:
                            print(f"   ⚠️  Failed to parse return_date: {ret_date_str}")
                
                flight_travelers = extracted_json.get("travelers", [])
                if flight_travelers:
                    travelers["count"] = len(flight_travelers)
                    extracted_items.append(f"travelers: {len(flight_travelers)} person(s)")
            
            elif doc_type == "hotel_booking":
                # Handle None values from JSON
                location = extracted_json.get("location") or {}
                booking_dates = extracted_json.get("booking_dates") or {}
                
                if location:
                    address = location.get("address") or {}
                    if address and address.get("country"):
                        country = address["country"]
                        if not trip.get("destination"):
                            trip["destination"] = country
                            extracted_items.append(f"destination: {country}")
                
                if booking_dates:
                    check_in = booking_dates.get("check_in") or {}
                    if check_in and check_in.get("date"):
                        parsed_date = parse_date_safe(check_in["date"])
                        if parsed_date and not trip.get("departure_date"):
                            trip["departure_date"] = parsed_date
                            extracted_items.append(f"check-in date: {parsed_date}")
                    
                    check_out = booking_dates.get("check_out") or {}
                    if check_out and check_out.get("date"):
                        parsed_date = parse_date_safe(check_out["date"])
                        if parsed_date and not trip.get("return_date"):
                            trip["return_date"] = parsed_date
                            extracted_items.append(f"check-out date: {parsed_date}")
            
            elif doc_type == "itinerary":
                # Handle None values from JSON
                trip_overview = extracted_json.get("trip_overview") or {}
                destinations = extracted_json.get("destinations") or []
                adventure_sports = extracted_json.get("adventure_sports_detected") or {}
                
                if destinations:
                    first_dest = destinations[0]
                    if first_dest.get("country") and not trip.get("destination"):
                        trip["destination"] = first_dest["country"]
                        extracted_items.append(f"destination: {first_dest['country']}")
                
                if trip_overview.get("start_date"):
                    parsed_date = parse_date_safe(trip_overview["start_date"])
                    if parsed_date and not trip.get("departure_date"):
                        trip["departure_date"] = parsed_date
                        extracted_items.append(f"start date: {parsed_date}")
                
                if trip_overview.get("end_date"):
                    parsed_date = parse_date_safe(trip_overview["end_date"])
                    if parsed_date and not trip.get("return_date"):
                        trip["return_date"] = parsed_date
                        extracted_items.append(f"end date: {parsed_date}")
                
                if adventure_sports.get("has_adventure_sports"):
                    prefs["adventure_sports"] = True
                    extracted_items.append("adventure sports: Yes")
            
            elif doc_type == "visa_application":
                # Handle None values from JSON
                visa_details = extracted_json.get("visa_details") or {}
                planned_trip = extracted_json.get("planned_trip") or {}
                applicant = extracted_json.get("applicant") or {}
                
                if visa_details.get("destination_country") and not trip.get("destination"):
                    trip["destination"] = visa_details["destination_country"]
                    extracted_items.append(f"destination: {visa_details['destination_country']}")
                
                if planned_trip.get("intended_arrival_date"):
                    parsed_date = parse_date_safe(planned_trip["intended_arrival_date"])
                    if parsed_date and not trip.get("departure_date"):
                        trip["departure_date"] = parsed_date
                        extracted_items.append(f"intended arrival date: {parsed_date}")
                
                if planned_trip.get("intended_departure_date"):
                    parsed_date = parse_date_safe(planned_trip["intended_departure_date"])
                    if parsed_date and not trip.get("return_date"):
                        trip["return_date"] = parsed_date
                        extracted_items.append(f"intended departure date: {parsed_date}")
                
                if applicant.get("age") and not travelers.get("ages"):
                    age = applicant["age"]
                    if isinstance(age, int) and 0.08 <= age <= 110:
                        travelers["ages"] = [age]
                        travelers["count"] = 1
                        extracted_items.append(f"traveler age: {age}")
            
            # Note: We're using structured JSON from OCR service, so no need for LLM fallback
            # The JSON extractor already handles all document types with high accuracy
            
            # Extract Ancileo API required fields
            # Departure country: Default to Singapore (SG market)
            if not trip.get("departure_country"):
                trip["departure_country"] = "SG"
            
            # Arrival country: Extract from destination using GeoMapper
            if trip.get("destination") and not trip.get("arrival_country"):
                try:
                    arrival_country_iso = GeoMapper.get_country_iso_code(trip["destination"])
                    trip["arrival_country"] = arrival_country_iso
                    print(f"   ✅ Extracted arrival_country: {arrival_country_iso} from destination: {trip['destination']}")
                except ValueError as e:
                    print(f"   ⚠️  Could not convert destination '{trip['destination']}' to ISO code: {e}")
                    # Will need to ask user for clarification
            
            # Adults and children count: Calculate from travelers ages
            if travelers.get("ages"):
                ages = travelers["ages"]
                adults_count = sum(1 for age in ages if age >= 18)
                children_count = sum(1 for age in ages if age < 18)
                # Ensure at least 1 adult for Ancileo API
                if adults_count == 0 and children_count > 0:
                    adults_count = 1
                    children_count = max(0, children_count - 1)
                trip["adults_count"] = adults_count
                trip["children_count"] = children_count
                print(f"   ✅ Calculated adults_count: {adults_count}, children_count: {children_count}")
            elif travelers.get("count"):
                # If we have count but no ages, assume all adults (will need to ask for ages)
                trip["adults_count"] = travelers["count"]
                trip["children_count"] = 0
                print(f"   ⚠️  Using travelers count as adults_count: {travelers['count']} (ages needed)")
            
            # CRITICAL: Ensure state references are updated (trip, travelers, prefs are already references)
            # Since trip/travelers/prefs are direct references to state dicts, just ensure they're set
            state["trip_details"] = trip  # Already a reference, just ensure it's in state
            state["travelers_data"] = travelers
            state["preferences"] = prefs
            
            # Debug: Print what was extracted and stored
            print(f"   📊 After extraction - trip: destination={trip.get('destination')}, dep_date={trip.get('departure_date')}, ret_date={trip.get('return_date')}")
            print(f"   📊 After extraction - travelers: ages={travelers.get('ages')}, count={travelers.get('count')}")
            print(f"   📊 State trip_details after setting: destination={state['trip_details'].get('destination')}, dep_date={state['trip_details'].get('departure_date')}, ret_date={state['trip_details'].get('return_date')}")
            
            # Set flag to route to needs_assessment after document processing
            state["_document_processed"] = True
            
            # Store extracted JSON in state for reference
            if "ocr_results" not in state:
                state["ocr_results"] = []
            state["ocr_results"].append(extracted_json)
            
            # Update trip metadata_json with document reference
            if state.get("trip_id") and state.get("session_id"):
                try:
                    from app.services.json_builders import build_trip_metadata_json
                    from datetime import datetime
                    from app.models.trip import Trip
                    
                    trip = db.query(Trip).filter(Trip.id == uuid.UUID(state["trip_id"])).first()
                    if trip:
                        # Get existing metadata or create new
                        existing_metadata = trip.metadata_json or {}
                        
                        # Build document reference
                        doc_ref = {
                            "document_type": doc_type,
                            "filename": latest_doc.get("filename"),
                            "extracted_at": datetime.now().isoformat()
                        }
                        
                        # Add to document_references
                        if "document_references" not in existing_metadata:
                            existing_metadata["document_references"] = []
                        existing_metadata["document_references"].append(doc_ref)
                        
                        # Update conversation_flow
                        if "conversation_flow" not in existing_metadata:
                            existing_metadata["conversation_flow"] = {}
                        if "document_uploaded_at" not in existing_metadata["conversation_flow"]:
                            existing_metadata["conversation_flow"]["document_uploaded_at"] = datetime.now().isoformat()
                        
                        trip.metadata_json = existing_metadata
                        db.commit()
                        print(f"   ✅ Updated trip metadata_json with document reference")
                except Exception as e:
                    print(f"   ⚠️  Failed to update trip metadata_json: {e}")
            
            # Build confirmation response
            if extracted_items:
                response = f"Great! I've extracted the following information from your {doc_type.replace('_', ' ')}:\n\n"
                response += "\n".join([f"• {item}" for item in extracted_items])
                
                # Add confidence information if available
                high_conf_fields = extracted_json.get("high_confidence_fields", [])
                low_conf_fields = extracted_json.get("low_confidence_fields", [])
                if high_conf_fields or low_conf_fields:
                    response += f"\n\n**Confidence levels:**"
                    if high_conf_fields:
                        response += f"\n• High confidence ({len(high_conf_fields)} fields): Ready to use"
                    if low_conf_fields:
                        response += f"\n• Medium confidence ({len(low_conf_fields)} fields): Please verify"
                
                # Check for missing Ancileo API required fields
                missing_fields = []
                if not trip.get("departure_date"):
                    missing_fields.append("departure date")
                if not trip.get("return_date"):
                    missing_fields.append("return date")
                if not trip.get("departure_country"):
                    missing_fields.append("departure country")
                if not trip.get("arrival_country"):
                    missing_fields.append("destination country")
                if not trip.get("adults_count") and not travelers.get("ages"):
                    missing_fields.append("number of travelers (adults and children)")
                elif not trip.get("adults_count"):
                    missing_fields.append("number of adults")
                
                if missing_fields:
                    response += f"\n\nI still need a few more details to get you the best quote: {', '.join(missing_fields)}. Let me ask you about these now!"
                else:
                    response += "\n\n**Please confirm if these details are correct.** If everything looks good, I'll recommend the best insurance plan for your trip!"
                    # Set awaiting confirmation flag only if all fields are present
                    state["awaiting_confirmation"] = True
                    state["confirmation_type"] = "document_extraction"
            else:
                response = "I've processed your document. Could you clarify what specific information you'd like me to extract? For example, travel dates, destination, or traveler details?"
            
            state["messages"].append(AIMessage(content=response))
            
            # Update intent to quote after processing document (to prevent routing back to process_document)
            state["current_intent"] = "quote"
            
            # If we have enough info, mark as ready for pricing (but wait for confirmation)
            if trip.get("destination") and trip.get("departure_date") and trip.get("return_date") and travelers.get("ages"):
                print(f"   ✅ Document contains all required info - awaiting confirmation before pricing")
            
        except Exception as e:
            print(f"   ⚠️  Error extracting info from document: {e}")
            import traceback
            traceback.print_exc()
            response = "I had trouble extracting information from your document. Could you please provide the details manually, or try uploading a clearer image?"
            state["messages"].append(AIMessage(content=response))
            # Ensure state is properly initialized before returning
            if "trip_details" not in state:
                state["trip_details"] = {}
            if "travelers_data" not in state:
                state["travelers_data"] = {}
            if "preferences" not in state:
                state["preferences"] = {}
            # Update intent to quote to prevent routing back to process_document
            state["current_intent"] = "quote"
        
        # Always return state to prevent routing errors
        return state
    
    def claims_guidance(state: ConversationState) -> ConversationState:
        """Provide claims guidance."""
        
        last_message = state["messages"][-1]
        user_input = last_message.content.lower()
        
        # Check if this is a document upload for claims
        if "[User uploaded a document" in str(last_message.content) or "Extracted text:" in str(last_message.content):
            # Extract OCR text
            message_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
            ocr_text = ""
            if "Extracted text:" in message_content:
                parts = message_content.split("Extracted text:", 1)
                if len(parts) > 1:
                    ocr_text = parts[1].strip()
            
            # Try to identify claim document type from OCR text
            ocr_lower = ocr_text.lower()
            claim_type = None
            
            if any(word in ocr_lower for word in ["receipt", "invoice", "bill", "payment", "cost"]):
                claim_type = "medical"  # Likely medical receipt
            elif any(word in ocr_lower for word in ["delay", "late", "delayed"]):
                claim_type = "trip_delay"
            elif any(word in ocr_lower for word in ["lost", "stolen", "baggage", "luggage"]):
                claim_type = "baggage"
            
            if claim_type:
                requirements = tools.get_claim_requirements(claim_type)
                if requirements["success"]:
                    req_docs = requirements["requirements"].get("required_documents", [])
                    req_info = requirements["requirements"].get("required_info", [])
                    
                    response = f"I see you've uploaded a document related to a {claim_type} claim.\n\n"
                    response += f"For {claim_type} claims, you'll need:\n\n"
                    response += f"**Documents:** {', '.join(req_docs)}\n\n"
                    response += f"**Information:** {', '.join(req_info)}\n\n"
                    response += "I've extracted the text from your document. Would you like help filling out the claim form?"
                else:
                    response = "I've received your document. What type of claim are you looking to file?"
            else:
                response = "I've received your document. What type of claim are you looking to file?"
        else:
            # Regular claims guidance (no document)
            claim_type = None
            if "delay" in user_input:
                claim_type = "trip_delay"
            elif "medical" in user_input:
                claim_type = "medical"
            elif "baggage" in user_input:
                claim_type = "baggage"
            elif "theft" in user_input:
                claim_type = "theft"
            elif "cancellation" in user_input:
                claim_type = "cancellation"
            
            if claim_type:
                requirements = tools.get_claim_requirements(claim_type)
                
                if requirements["success"]:
                    req_docs = requirements["requirements"].get("required_documents", [])
                    req_info = requirements["requirements"].get("required_info", [])
                    
                    response = f"For {claim_type} claims, you'll need:\n\nDocuments: {', '.join(req_docs)}\n\nInformation: {', '.join(req_info)}"
                else:
                    response = "I can help you with claims guidance. What type of claim are you looking to file?"
            else:
                response = "I can help you with claims guidance. What type of claim are you looking to file?"
        
        state["messages"].append(AIMessage(content=response))
        
        return state
    
    def compliance(state: ConversationState) -> ConversationState:
        """Handle compliance and KYC requirements."""
        
        response = "Before we proceed, I need to confirm that you understand our terms and conditions. Do you consent to our data processing and privacy policy?"
        
        state["messages"].append(AIMessage(content=response))
        
        return state
    
    def customer_service(state: ConversationState) -> ConversationState:
        """Handle customer service requests and escalation."""
        
        # Check if we're in an active quote flow - if so, don't trigger handoff
        confirmation_received = state.get("confirmation_received", False)
        ready_for_pricing = state.get("_ready_for_pricing", False)
        has_destination = bool(state.get("trip_details", {}).get("destination"))
        in_active_quote_flow = confirmation_received or ready_for_pricing or has_destination
        
        if state.get("requires_human") and not in_active_quote_flow:
            # Create handoff request only if NOT in active quote flow
            handoff_result = tools.create_handoff_request(
                state["user_id"],
                "conversation_escalation",
                "User needs human assistance"
            )
            
            if handoff_result["success"]:
                response = "I'm connecting you with a human agent who can better assist you. They'll be with you shortly."
            else:
                response = "I'm having trouble connecting you with a human agent. Please try again or contact us directly."
        elif in_active_quote_flow:
            # If we're in quote flow but ended up here, redirect back to quote flow
            response = "Let me continue helping you with your travel insurance quote. What would you like to know?"
        else:
            response = "How else can I help you today?"
        
        state["messages"].append(AIMessage(content=response))
        
        return state
    
    def log_conversation_metrics(state: ConversationState):
        """Log metrics for analytics."""
        
        messages = state.get("messages", [])
        intent = state.get("current_intent", "")
        quote_data = state.get("quote_data")
        
        metrics = {
            "session_id": state.get("session_id", "unknown"),
            "message_count": len(messages),
            "intent": intent,
            "quote_generated": quote_data is not None,
            "loop_count": state.get("_loop_count", 0),
            "human_handoff": state.get("requires_human", False)
        }
        
        print(f"\n📊 CONVERSATION METRICS:")
        for key, value in metrics.items():
            print(f"   {key}: {value}")
        
        # TODO: Send to analytics service (Mixpanel, Segment, etc.)
        # For now, just log to console
        
        return metrics
    
    def should_continue(state: ConversationState) -> str:
        """Determine next step with loop protection and clear exit conditions."""
        
        # CRITICAL: Prevent infinite loops
        loop_count = state.get("_loop_count", 0)
        state["_loop_count"] = loop_count + 1
        
        if loop_count > 20:
            print(f"⚠️  LOOP LIMIT REACHED ({loop_count} iterations)")
            print(f"   Last intent: {state.get('current_intent')}")
            print(f"   Confirmation: {state.get('confirmation_received')}")
            print(f"   Ready for pricing: {state.get('_ready_for_pricing')}")
            print(f"   Pricing complete: {state.get('_pricing_complete')}")
            state["requires_human"] = True
            return "customer_service"
        
        # Log routing for debugging
        current_intent = state.get("current_intent", "unknown")
        print(f"🔀 Routing #{loop_count}: intent={current_intent}")
        
        # Priority 1: If policy created, END
        if state.get("_policy_created", False):
            print(f"   → END (policy created)")
            log_conversation_metrics(state)
            return END
        
        # Priority 2: Payment processing
        awaiting_payment = state.get("_awaiting_payment_confirmation", False)
        quote_data = state.get("quote_data")
        intent = state.get("current_intent", "")
        
        # Check for purchase intent (from LLM classification only - no hardcoded keyword matching)
        purchase_intent = (intent == "purchase")

        # Prevent recursion: don't route to payment_processor if payment already failed or checkout URL already sent
        payment_failed = state.get("_payment_failed", False)
        checkout_url_sent = state.get("_checkout_url_sent", False)

        # If we just sent the checkout URL, END to let user complete payment
        if checkout_url_sent and awaiting_payment:
            print(f"   → END (checkout URL sent, waiting for user to complete payment)")
            log_conversation_metrics(state)
            return END

        if awaiting_payment or (purchase_intent and quote_data and quote_data.get("quotes") and not payment_failed):
            print(f"   → payment_processor")
            return "payment_processor"
        
        # Priority 3: If pricing is complete (but no purchase intent), END
        # Only END if pricing complete AND no purchase intent detected
        if state.get("_pricing_complete", False) and not purchase_intent:
            print(f"   → END (pricing complete, no purchase intent)")
            log_conversation_metrics(state)
            return END

        # Priority 4: Human handoff (but skip if in active quote flow with confirmation)
        confirmation_received = state.get("confirmation_received", False)
        ready_for_pricing = state.get("_ready_for_pricing", False)
        in_active_quote_flow = confirmation_received or ready_for_pricing or state.get("trip_details", {}).get("destination")
        
        if state.get("requires_human") and not in_active_quote_flow:
            print(f"   → customer_service")
            return "customer_service"
        
        # Priority 5: Non-quote intents
        if intent == "policy_explanation":
            pass  # Handle policy explanation
        
        # Priority 2: Check if we're in an active quote flow first
        # (confirmation_received, ready_for_pricing, and in_active_quote_flow already set above)
        
        # Priority 4.5: After document processing, route to needs_assessment
        document_processed = state.get("_document_processed", False)
        if document_processed:
            # Check if we're coming from process_document node
            # Route to needs_assessment to collect missing Ancileo API fields
            print(f"   → needs_assessment (document processed, collecting missing fields)")
            # Clear the flag to prevent infinite loop
            state["_document_processed"] = False
            return "needs_assessment"
        
        # Priority 5: Non-quote intents
        if intent == "document_upload":
            print(f"   → process_document")
            return "process_document"
        elif intent == "policy_explanation":
            print(f"   → policy_explainer")
            return "policy_explainer"
        elif intent == "claims_guidance":
            print(f"   → claims_guidance")
            return "claims_guidance"
        elif intent == "human_handoff" and not in_active_quote_flow:
            # Only route to human handoff if NOT in active quote flow
            print(f"   → customer_service (human_handoff intent, not in quote flow)")
            return "customer_service"
        
        # Priority 6: Quote flow with clear progression
        if intent == "quote" or intent == "" or in_active_quote_flow:
            # Re-get these values (already checked above but being explicit)
            confirmation_received = state.get("confirmation_received", False)
            ready_for_pricing = state.get("_ready_for_pricing", False)
            pricing_complete = state.get("_pricing_complete", False)
            current_question = state.get("current_question", "")
            awaiting_confirmation = state.get("awaiting_confirmation", False)
            has_area = state.get("trip_details", {}).get("area") is not None
            # Check if quote_data actually has quotes (not just an empty dict)
            quote_data = state.get("quote_data", {})
            has_quote = bool(quote_data and quote_data.get("quotes"))
            
            print(f"   confirmed={confirmation_received}, ready={ready_for_pricing}")
            print(f"   area={has_area}, quote={has_quote}, complete={pricing_complete}")
            print(f"   current_question={current_question}, awaiting={awaiting_confirmation}")
            
            # If pricing already complete, we're done
            if pricing_complete or has_quote:
                print(f"   → END (quote exists)")
                log_conversation_metrics(state)
                return END
            
            # CRITICAL FIX: If we're waiting for user response, check if last message is from AI
            # If we asked a question AND the last message is from AI, END turn (waiting for user)
            # If we asked a question AND the last message is from user, process the answer (continue)
            # EXCEPTION: If we just confirmed but still have missing info, continue asking (don't END)
            messages = state.get("messages", [])
            if messages:
                last_msg_is_ai = isinstance(messages[-1], AIMessage)
                last_msg_content = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
                
                # Calculate all_required_present here (same logic as needs_assessment)
                trip = state.get("trip_details", {})
                travelers = state.get("travelers_data", {})
                
                # Handle dates - they might be date objects or strings
                has_dep_date = bool(trip.get("departure_date"))
                has_ret_date = bool(trip.get("return_date"))
                has_travelers_info = bool(travelers.get("ages") or travelers.get("count") or trip.get("adults_count") is not None)
                
                all_required_present = (
                    trip.get("destination") and
                    has_dep_date and
                    has_ret_date and
                    has_travelers_info and
                    trip.get("arrival_country") and
                    trip.get("adults_count") is not None
                )
                
                # Check if we just confirmed but still have missing info - continue asking
                just_confirmed_with_missing = (
                    confirmation_received and 
                    last_msg_is_ai and 
                    not all_required_present and
                    "few more details" in last_msg_content.lower()
                )
                
                # If we have a question pending and the last message is AI, we're done for this turn
                # BUT: if we just confirmed with missing info, continue to ask next question (don't END)
                if (current_question or awaiting_confirmation) and last_msg_is_ai and not just_confirmed_with_missing:
                    print(f"   → END (waiting for user response, AI message just added)")
                    return END
                # Also: if last message is AI and we're in quote flow but not actively processing, END
                # BUT: if we just confirmed with missing info, continue (don't END)
                if last_msg_is_ai and in_active_quote_flow and not awaiting_confirmation and not confirmation_received and not just_confirmed_with_missing:
                    # End if we don't have a current question (meaning we just asked one or finished processing)
                    if not current_question:
                        print(f"   → END (AI response added, turn complete)")
                        return END
                # If we just confirmed with missing info, continue (don't END) - let needs_assessment ask next question
                if just_confirmed_with_missing:
                    print(f"   → Continue (just confirmed but missing info, will ask next question)")
                    # Continue to needs_assessment to ask next missing question - don't return END, fall through
            
            # PRIORITY: If user just answered a question, process the answer first
            # Check if we have a current_question AND the last message is from user (not AI)
            if current_question and messages:
                last_msg_is_user = not isinstance(messages[-1], AIMessage)
                if last_msg_is_user:
                    print(f"   → needs_assessment (user answered question: {current_question})")
                    return "needs_assessment"
            
            # If confirmed and ready, proceed through pricing flow
            # BUT: If pricing is already complete, don't route to pricing again
            if confirmation_received and ready_for_pricing and not pricing_complete:
                if not has_area:
                    print(f"   → risk_assessment")
                    return "risk_assessment"
                elif has_area and not has_quote:
                    print(f"   → pricing")
                    return "pricing"
                else:
                    print(f"   → END")
                    log_conversation_metrics(state)
                    return END
            elif confirmation_received and ready_for_pricing and pricing_complete:
                # Pricing already done, just END
                print(f"   → END (pricing already complete)")
                log_conversation_metrics(state)
                return END
            
            # Otherwise, continue collecting info
            print(f"   → needs_assessment")
            return "needs_assessment"
        
        # Default fallback
        print(f"   → needs_assessment (default)")
        return "needs_assessment"
    
    # Create the graph
    graph = StateGraph(ConversationState)
    
    # Add nodes
    graph.add_node("orchestrator", orchestrator)
    graph.add_node("needs_assessment", needs_assessment)
    graph.add_node("risk_assessment", risk_assessment)
    graph.add_node("pricing", pricing)
    graph.add_node("payment_processor", payment_processor)
    graph.add_node("process_document", process_document)
    graph.add_node("policy_explainer", policy_explainer)
    graph.add_node("claims_guidance", claims_guidance)
    graph.add_node("compliance", compliance)
    graph.add_node("customer_service", customer_service)
    
    # Add conditional edges from orchestrator
    graph.add_conditional_edges(
        "orchestrator",
        should_continue,
        {
            "needs_assessment": "needs_assessment",
            "risk_assessment": "risk_assessment",
            "pricing": "pricing",
            "payment_processor": "payment_processor",
            "process_document": "process_document",
            "policy_explainer": "policy_explainer",
            "claims_guidance": "claims_guidance",
            "customer_service": "customer_service",
            END: END
        }
    )
    
    # Add conditional edges from process_document (can proceed to quote flow or other intents)
    graph.add_conditional_edges(
        "process_document",
        should_continue,
        {
            "needs_assessment": "needs_assessment",
            "risk_assessment": "risk_assessment",
            "pricing": "pricing",
            "claims_guidance": "claims_guidance",
            "customer_service": "customer_service",
            END: END
        }
    )
    
    # Add conditional edges from needs_assessment (can loop or proceed)
    graph.add_conditional_edges(
        "needs_assessment",
        should_continue,
        {
            "needs_assessment": "needs_assessment",  # Loop back for more questions
            "risk_assessment": "risk_assessment",     # Proceed to risk assessment
            "pricing": "pricing",                      # Skip to pricing if area already mapped
            "customer_service": "customer_service",   # Human handoff
            END: END                                   # End if needed
        }
    )
    
    # Fixed edge from risk_assessment to pricing
    graph.add_edge("risk_assessment", "pricing")
    
    # Conditional edge from pricing
    graph.add_conditional_edges(
        "pricing",
        should_continue,
        {
            "payment_processor": "payment_processor",
            "customer_service": "customer_service",
            END: END
        }
    )
    
    # Conditional edge from payment_processor (can loop for confirmation or END)
    graph.add_conditional_edges(
        "payment_processor",
        should_continue,
        {
            "payment_processor": "payment_processor",  # Loop for payment confirmation
            "customer_service": "customer_service",
            END: END
        }
    )
    
    # Fixed edges for other nodes
    graph.add_edge("policy_explainer", END)
    graph.add_edge("claims_guidance", END)
    graph.add_edge("compliance", END)
    graph.add_edge("customer_service", END)
    
    # Set entry point
    graph.set_entry_point("orchestrator")
    
    # Configure LangGraph checkpointing
    try:
        checkpointer = get_or_create_checkpointer()
        
        if checkpointer is not None:
            # Use context manager properly with the graph
            compiled_graph = graph.compile(checkpointer=checkpointer)
            print("✅ Graph compiled with persistent checkpointing (PostgreSQL)")
            return compiled_graph
        else:
            print("⚠️  Checkpointing not available, using non-persistent mode")
            return graph.compile()
            
    except Exception as e:
        print(f"⚠️  Checkpointing setup failed: {e}")
        import traceback
        traceback.print_exc()
        print("⚠️  Falling back to non-persistent mode")
        return graph.compile()


def create_simple_conversation_graph(db) -> StateGraph:
    """Create a simplified conversation graph as fallback when sophisticated features fail."""
    
    tools = ConversationTools(db)
    
    def simple_orchestrator(state: ConversationState) -> ConversationState:
        """Simple intent detection without LLM."""
        
        last_message = state["messages"][-1]
        user_input = last_message.content.lower()
        
        # Simple keyword-based intent detection
        if any(word in user_input for word in ["quote", "price", "cost", "insurance"]):
            state["current_intent"] = "quote"
            state["confidence_score"] = 0.8
        elif any(word in user_input for word in ["policy", "coverage", "what does"]):
            state["current_intent"] = "policy_explanation"
            state["confidence_score"] = 0.7
        elif any(word in user_input for word in ["claim", "file", "submit"]):
            state["current_intent"] = "claims_guidance"
            state["confidence_score"] = 0.8
        elif any(word in user_input for word in ["human", "agent", "help", "support"]):
            state["current_intent"] = "human_handoff"
            state["confidence_score"] = 0.9
        else:
            state["current_intent"] = "general_inquiry"
            state["confidence_score"] = 0.5
        
        # Check if human handoff is needed
        if state["confidence_score"] < 0.6:
            state["requires_human"] = True
        
        return state
    
    def simple_needs_assessment(state: ConversationState) -> ConversationState:
        """Simple trip information collection."""
        
        collected = state.get("collected_slots", {})
        last_message = state["messages"][-1]
        user_input = last_message.content.lower()
        
        # Simple keyword extraction
        if "trip" in user_input or "travel" in user_input:
            if "start" in user_input or "begin" in user_input:
                collected["trip_start"] = "extracted_date"
            if "end" in user_input or "finish" in user_input:
                collected["trip_end"] = "extracted_date"
            if "destination" in user_input or "going to" in user_input:
                collected["destinations"] = ["extracted_destination"]
        
        if "traveler" in user_input or "person" in user_input:
            collected["travelers"] = [{"name": "extracted_name", "age": 30}]
        
        if "activity" in user_input or "doing" in user_input:
            collected["activities"] = [{"type": "sightseeing"}]
        
        state["collected_slots"] = collected
        
        # Generate response based on missing information
        missing_info = []
        if not collected.get("trip_start"):
            missing_info.append("trip start date")
        if not collected.get("destinations"):
            missing_info.append("destinations")
        if not collected.get("travelers"):
            missing_info.append("traveler information")
        
        if missing_info:
            response = f"I need some more information to provide an accurate quote. Please provide: {', '.join(missing_info)}."
        else:
            response = "Great! I have enough information to provide a quote. Let me calculate that for you."
        
        state["messages"].append(AIMessage(content=response))
        return state
    
    def simple_pricing(state: ConversationState) -> ConversationState:
        """Simple pricing calculation."""
        
        quote_data = state.get("quote_data", {})
        
        if quote_data:
            # Calculate quote range using tools
            range_result = tools.get_quote_range(
                "basic_travel",  # Default product type
                quote_data.get("travelers", []),
                quote_data.get("activities", []),
                7,  # Default duration
                quote_data.get("destinations", [])
            )
            
            if range_result["success"]:
                price_min = range_result["price_min"]
                price_max = range_result["price_max"]
                
                response = f"Based on your trip details, I can provide a quote range of ${price_min:.2f} - ${price_max:.2f}. Would you like me to calculate a firm price?"
                
                state["quote_data"]["price_range"] = {
                    "min": price_min,
                    "max": price_max,
                    "breakdown": range_result["breakdown"]
                }
            else:
                response = "I'm having trouble calculating the quote. Let me connect you with a human agent."
                state["requires_human"] = True
        else:
            response = "I need more information to calculate your quote. Please provide your trip details."
        
        state["messages"].append(AIMessage(content=response))
        return state
    
    def simple_should_continue(state: ConversationState) -> str:
        """Simple routing logic."""
        
        intent = state.get("current_intent")
        
        if state.get("requires_human"):
            return "customer_service"
        
        if intent == "quote":
            if not state.get("collected_slots"):
                return "needs_assessment"
            elif not state.get("quote_data"):
                return "pricing"
            else:
                return END
        elif intent == "policy_explanation":
            return "policy_explainer"
        elif intent == "claims_guidance":
            return "claims_guidance"
        elif intent == "human_handoff":
            return "customer_service"
        else:
            return "customer_service"
    
    # Create the simple graph
    simple_graph = StateGraph(ConversationState)
    
    # Add nodes
    simple_graph.add_node("orchestrator", simple_orchestrator)
    simple_graph.add_node("needs_assessment", simple_needs_assessment)
    simple_graph.add_node("pricing", simple_pricing)
    simple_graph.add_node("policy_explainer", policy_explainer)
    simple_graph.add_node("claims_guidance", claims_guidance)
    simple_graph.add_node("customer_service", customer_service)
    
    # Add edges
    simple_graph.set_entry_point("orchestrator")
    
    simple_graph.add_conditional_edges(
        "orchestrator",
        simple_should_continue,
        {
            "needs_assessment": "needs_assessment",
            "pricing": "pricing",
            "policy_explainer": "policy_explainer",
            "claims_guidance": "claims_guidance",
            "customer_service": "customer_service",
            END: END
        }
    )
    
    simple_graph.add_edge("needs_assessment", "pricing")
    simple_graph.add_edge("pricing", END)
    simple_graph.add_edge("policy_explainer", END)
    simple_graph.add_edge("claims_guidance", END)
    simple_graph.add_edge("customer_service", END)
    
    return simple_graph.compile()


# def create_conversation_graph_no_checkpoint(db) -> StateGraph:
#     """Create conversation graph without checkpointing for fallback."""
#     # Reuse the same graph creation logic but without checkpointing
#     tools = ConversationTools(db)
#     llm_client = GroqLLMClient()
#     pricing_service = PricingService()
#     
#     def risk_assessment(state: ConversationState) -> ConversationState:
#         """Map destination to geographic area for pricing."""
#         trip = state.get("trip_details", {})
#         destination = trip.get("destination")
#         
#         if destination:
#             # Simple area mapping
#             if destination.lower() in ["japan", "tokyo", "osaka"]:
#                 trip["area"] = "asia_developed"
#             elif destination.lower() in ["thailand", "bangkok"]:
#                 trip["area"] = "asia_developing"
#             else:
#                 trip["area"] = "asia_developed"  # Default
#         
#         response = "Great! I've mapped your destination to the appropriate region for pricing."
#         state["messages"].append(AIMessage(content=response))
#         return state
#     
#     def pricing(state: ConversationState) -> ConversationState:
#         """Generate insurance quotes using pricing service."""
#         try:
#             trip = state.get("trip_details", {})
#             travelers = state.get("travelers_data", {})
#             preferences = state.get("preferences", {})
#             
#             # Generate quote
#             quote_result = pricing_service.generate_quote(
#                 destination=trip.get("destination", "Japan"),
#                 departure_date=trip.get("departure_date", date(2025, 12, 15)),
#                 return_date=trip.get("return_date", date(2025, 12, 22)),
#                 travelers=travelers.get("ages", [30]),
#                 adventure_sports=preferences.get("adventure_sports", False)
#             )
#             
#             if quote_result["success"]:
#                 state["quote_data"] = quote_result
#                 response = f"""Here are your travel insurance options:
# 
# 💰 **Standard Plan**: ${quote_result['quotes']['standard']['price']:.2f}
#    - Medical coverage: ${quote_result['quotes']['standard']['coverage']['medical']:,}
#    - Trip cancellation: ${quote_result['quotes']['standard']['coverage']['trip_cancellation']:,}
# 
# 💰 **Premium Plan**: ${quote_result['quotes']['premium']['price']:.2f}
#    - Medical coverage: ${quote_result['quotes']['premium']['coverage']['medical']:,}
#    - Trip cancellation: ${quote_result['quotes']['premium']['coverage']['trip_cancellation']:,}
# 
# Would you like to proceed with one of these options?"""
#             else:
#                 response = "I'm sorry, I couldn't generate quotes at this time. Please try again later."
#             
#             state["messages"].append(AIMessage(content=response))
#             return state
#             
#         except Exception as e:
#             response = "I'm having trouble generating quotes. Please try again."
#             state["messages"].append(AIMessage(content=response))
#             return state
#     
#     # Create the graph
#     graph = StateGraph(ConversationState)
#     
#     # Add nodes
#     graph.add_node("orchestrator", orchestrator)
#     graph.add_node("needs_assessment", needs_assessment)
#     graph.add_node("risk_assessment", risk_assessment)
#     graph.add_node("pricing", pricing)
#     
#     # Add edges
#     graph.set_entry_point("orchestrator")
#     
#     graph.add_conditional_edges(
#         "orchestrator",
#         should_continue,
#         {
#             "needs_assessment": "needs_assessment",
#             "risk_assessment": "risk_assessment",
#             "pricing": "pricing",
#             END: END
#         }
#     )
#     
#     graph.add_conditional_edges(
#         "needs_assessment",
#         should_continue,
#         {
#             "needs_assessment": "needs_assessment",
#             "risk_assessment": "risk_assessment",
#             "pricing": "pricing",
#             END: END
#         }
#     )
#     
#     graph.add_edge("risk_assessment", "pricing")
#     graph.add_edge("pricing", END)
#     
#     # Compile without checkpointing
#     return graph.compile()