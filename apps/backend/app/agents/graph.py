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


def parse_date_safe(date_string: str) -> Optional[date]:
    """Safely parse date string to date object with flexible format support.
    
    Accepts multiple formats:
    - YYYY-MM-DD (2025-12-15)
    - MM/DD/YYYY (12/15/2025)
    - DD/MM/YYYY (15/12/2025)
    - Natural language (December 15, 2025, Dec 15, 2025)
    - Relative dates (tomorrow, next week, in 3 days)
    
    Args:
        date_string: Date in any common format
        
    Returns:
        date object if parsing succeeds, None otherwise
    """
    try:
        # First try standard YYYY-MM-DD for efficiency
        if isinstance(date_string, str) and len(date_string) == 10 and date_string.count('-') == 2:
            try:
                return datetime.strptime(date_string, "%Y-%m-%d").date()
            except:
                pass
        
        # Use dateparser for flexible parsing
        settings = {
            'PREFER_DATES_FROM': 'future',  # Prefer future dates for travel
            'RELATIVE_BASE': datetime.now(),
            'RETURN_AS_TIMEZONE_AWARE': False,
        }
        
        parsed = dateparser.parse(date_string, settings=settings)
        
        if parsed:
            return parsed.date()
        
        return None
        
    except Exception as e:
        print(f"   ⚠️ Date parsing error: {e}")
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


def create_conversation_graph(db) -> StateGraph:
    """Create the conversation state graph."""
    
    tools = ConversationTools(db)
    llm_client = GroqLLMClient()
    pricing_service = PricingService()
    
    def orchestrator(state: ConversationState) -> ConversationState:
        """Route conversation based on LLM intent classification."""
        
        # Initialize loop protection
        if "_loop_count" not in state:
            state["_loop_count"] = 0
        if "_ready_for_pricing" not in state:
            state["_ready_for_pricing"] = False
        if "_pricing_complete" not in state:
            state["_pricing_complete"] = False
        
        state["_loop_count"] += 1
        print(f"\n{'='*60}")
        print(f"🔀 ORCHESTRATOR (iteration {state['_loop_count']})")
        print(f"{'='*60}")
        
        messages = state.get("messages", [])
        if not messages:
            state["current_intent"] = "quote"
            return state
        
        last_message = messages[-1]
        user_message = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        # Get conversation history for context
        history = []
        for msg in messages[-5:]:  # Last 5 messages
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
        if confidence < 0.6:
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
            
            trip = state["trip_details"]
            travelers = state["travelers_data"]
            prefs = state["preferences"]
            
            last_message = state["messages"][-1]
            user_input = last_message.content
            
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
                            new_trip = Trip(
                                user_id=uuid.UUID(state["user_id"]),
                                session_id=state["session_id"],
                                status="draft",
                                destinations=[extracted["destination"]],
                                travelers_count=1  # Default, will update later
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
                            db.commit()
                            print(f"   ✅ Updated existing trip: {existing_trip.id}")
                    except Exception as e:
                        print(f"   ⚠️  Failed to create/update trip: {e}")

            if "departure_date" in extracted:
                # Parse to date object with error handling
                parsed_date = parse_date_safe(extracted["departure_date"])
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
                    pass
            
            if "return_date" in extracted:
                # Parse to date object with error handling
                parsed_date = parse_date_safe(extracted["return_date"])
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
                    pass
            
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
                    
                    # If user clearly said yes/no, validate extraction
                    if said_yes and extracted["adventure_sports"] == False:
                        print(f"   ⚠️  LLM extracted False but user said yes - ignoring extraction, will use special handling")
                        # Don't set extracted_info, let special handling below catch it
                    elif said_no and extracted["adventure_sports"] == True:
                        print(f"   ⚠️  LLM extracted True but user said no - ignoring extraction, will use special handling")
                        # Don't set extracted_info, let special handling below catch it
                    else:
                        # Extraction matches user intent (or no clear yes/no), accept it
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
            
            # Handle confirmation flow
            if state.get("awaiting_confirmation"):
                # Check if user confirmed or wants to make changes
                user_response_lower = user_input.lower()
                said_yes = any(word in user_response_lower for word in ["yes", "correct", "confirm", "looks good", "that's right", "yeah"])
                said_no = any(word in user_response_lower for word in ["no", "wrong", "incorrect", "change", "fix"])
                
                if said_yes:
                    state["confirmation_received"] = True
                    state["_ready_for_pricing"] = True  # ADD THIS LINE
                    state["awaiting_confirmation"] = False
                    state["current_question"] = ""  # Clear the question
                    print(f"   ✅ User confirmed - ready for pricing")
                    response = "Great! Let me calculate your insurance options..."
                    state["messages"].append(AIMessage(content=response))
                    return state
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
            
            # Determine what information is still missing
            missing = []
            if not trip.get("destination"):
                missing.append("destination")
            if not trip.get("departure_date"):
                missing.append("departure_date")
            if not trip.get("return_date"):
                missing.append("return_date")
            if not travelers.get("ages"):
                missing.append("travelers")
            
            # Check if user provided everything at once
            all_required_present = (
                trip.get("destination") and
                trip.get("departure_date") and
                trip.get("return_date") and
                travelers.get("ages")
            )
            
            # Generate appropriate response based on conversation state
            print(f"   🔍 Debug: missing={missing}, adventure_sports={prefs.get('adventure_sports')}, all_present={all_required_present}")
            print(f"   🔍 Conditions: awaiting_confirmation={state.get('awaiting_confirmation')}, adventure_is_none={prefs.get('adventure_sports') is None}")
            
            # Priority: If we just answered adventure question and all required info is present, go to confirmation
            # (This prevents asking for destination again after successfully answering adventure)
            adventure_answered = prefs.get("adventure_sports") is not None
            if not state.get("awaiting_confirmation") and all_required_present and adventure_answered:
                print(f"   🔍 Branch: All info collected including adventure - going to confirmation")
                # Set default for adventure_sports before showing confirmation if not answered yet (shouldn't happen here)
                if "adventure_sports" not in prefs or prefs.get("adventure_sports") is None:
                    prefs["adventure_sports"] = False
                
                dest = trip["destination"]
                dep_date = trip["departure_date"]
                ret_date = trip["return_date"]
                duration_days = (ret_date - dep_date).days + 1
                
                dep_formatted = dep_date.strftime("%B %d, %Y")
                ret_formatted = ret_date.strftime("%B %d, %Y")
                ages = ", ".join(map(str, travelers["ages"]))
                adv = "Yes" if prefs.get("adventure_sports") else "No"
                
                response = f"""Let me confirm your trip details:

📍 Destination: {dest}
📅 Travel dates: {dep_formatted} to {ret_formatted} ({duration_days} days)
👥 Travelers: {len(travelers['ages'])} traveler(s) (ages: {ages})
🏔️ Adventure activities: {adv}

Is this information correct? (yes/no)"""
                
                state["awaiting_confirmation"] = True
                state["current_question"] = "confirmation"
                print(f"   💬 Asking for confirmation")
            # Check adventure_sports BEFORE checking all_required_present (but only if not already answered)
            elif not state.get("awaiting_confirmation") and all_required_present and prefs.get("adventure_sports") is None:
                print(f"   🔍 Branch: Going to ask adventure question")
                # Ask about adventure sports if all required info is present but adventure sports not answered
                response = "Are you planning any adventure activities like skiing, scuba diving, trekking, or bungee jumping?"
                state["current_question"] = "adventure_sports"
                print(f"   💬 Asking adventure question: {response}")
            elif missing:
                print(f"   🔍 Branch: Asking missing questions")
                # Ask for next missing piece of information
                if "destination" in missing:
                    response = "Where are you traveling to?"
                    state["current_question"] = "destination"
                    print(f"   💬 Asking: {response}")
                elif "departure_date" in missing:
                    response = "When does your trip start? Please provide the date in YYYY-MM-DD format. For example: 2025-12-15"
                    state["current_question"] = "departure_date"
                    print(f"   💬 Asking: {response}")
                elif "return_date" in missing:
                    response = "When do you return to Singapore? Please provide the date in YYYY-MM-DD format. For example: 2025-12-22"
                    state["current_question"] = "return_date"
                    print(f"   💬 Asking: {response}")
                elif "travelers" in missing:
                    response = "How many travelers are going, and what are their ages? For example: '2 travelers, ages 30 and 8'"
                    state["current_question"] = "travelers"
                    print(f"   💬 Asking: {response}")
            elif all_required_present and not state.get("awaiting_confirmation"):
                print(f"   🔍 Branch: Going to confirmation")
                # All info collected, show summary and ask for confirmation
                # Set default for adventure_sports before showing confirmation if not answered yet
                if "adventure_sports" not in prefs or prefs.get("adventure_sports") is None:
                    prefs["adventure_sports"] = False
                
                dest = trip["destination"]
                dep_date = trip["departure_date"]
                ret_date = trip["return_date"]
                duration_days = (ret_date - dep_date).days + 1
                
                dep_formatted = dep_date.strftime("%B %d, %Y")
                ret_formatted = ret_date.strftime("%B %d, %Y")
                ages = ", ".join(map(str, travelers["ages"]))
                adv = "Yes" if prefs.get("adventure_sports") else "No"
                
                response = f"""Let me confirm your trip details:

📍 Destination: {dest}
📅 Travel dates: {dep_formatted} to {ret_formatted} ({duration_days} days)
👥 Travelers: {len(travelers['ages'])} traveler(s) (ages: {ages})
🏔️ Adventure activities: {adv}

Is this information correct? (yes/no)"""
                
                state["awaiting_confirmation"] = True
                state["current_question"] = "confirmation"
                print(f"   💬 Asking for confirmation")
            else:
                # Shouldn't reach here, but handle gracefully
                response = "I have all the information I need. Let me calculate your quote..."
                state["confirmation_received"] = True
            
            state["messages"].append(AIMessage(content=response))
            return state
            
        except Exception as e:
            # Error handling with friendly message
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
            trip = state["trip_details"]
            travelers = state["travelers_data"]
            prefs = state["preferences"]
            
            # Extract required data
            destination = trip["destination"]
            departure_date = trip["departure_date"]
            return_date = trip["return_date"]
            travelers_ages = travelers["ages"]
            
            # Default to False if user never answered or is None
            adventure_sports = prefs.get("adventure_sports", False)
            if adventure_sports is None:
                adventure_sports = False
            
            # Call pricing service
            quote_result = pricing_service.calculate_step1_quote(
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                travelers_ages=travelers_ages,
                adventure_sports=adventure_sports
            )
            
            if not quote_result["success"]:
                # Error in quote calculation - provide friendly error message
                error_msg = quote_result.get("error", "Unknown error")
                if "182 days" in error_msg:
                    response = "Your trip is a bit too long for our standard coverage (maximum 182 days). Let me connect you with a specialist who can help with extended coverage."
                elif "age" in error_msg.lower():
                    response = "I noticed one of the ages might not be quite right. Travelers should be between 1 month and 110 years old. Could you double-check the ages?"
                else:
                    response = f"I'm sorry, but I encountered an issue: {error_msg}. Let me connect you with a human agent who can help."
                
                state["requires_human"] = True
                state["messages"].append(AIMessage(content=response))
                return state
            
            # Store full quote result
            state["quote_data"] = quote_result
            
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
            
            response = "\n".join(response_parts)
            state["messages"].append(AIMessage(content=response))
            
            # CRITICAL: Mark pricing as complete to prevent re-entry
            state["_pricing_complete"] = True
            state["_ready_for_pricing"] = False
            
            print(f"   ✅ Pricing complete, will route to END")
            
            return state
            
        except Exception as e:
            response = "I encountered an error calculating your quote. Let me connect you with a human agent."
            state["requires_human"] = True
            state["messages"].append(AIMessage(content=response))
            return state
    
    def policy_explainer(state: ConversationState) -> ConversationState:
        """
        Answer policy questions using mock policy knowledge base.
        """
        
        print("\n📚 POLICY EXPLAINER NODE")
        
        messages = state.get("messages", [])
        last_message = messages[-1]
        user_question = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        print(f"   Question: {user_question[:100]}...")
        
        # Mock policy knowledge base (replace with real RAG later)
        policy_kb = {
            "medical": {
                "coverage": "Medical coverage includes emergency medical treatment, hospitalization, and medical evacuation up to policy limits.",
                "limits": "Standard: $50,000 | Elite: $100,000 | Premier: $200,000",
                "exclusions": "Pre-existing conditions (unless declared), cosmetic procedures, routine checkups"
            },
            "cancellation": {
                "coverage": "Trip cancellation covers non-refundable expenses if you must cancel due to covered reasons.",
                "reasons": "Serious illness, injury, death of traveler/family, natural disasters, travel warnings",
                "limits": "Standard: $5,000 | Elite: $10,000 | Premier: $15,000"
            },
            "baggage": {
                "coverage": "Baggage coverage includes loss, theft, or damage to personal belongings.",
                "limits": "Standard: $3,000 | Elite: $5,000 | Premier: $10,000",
                "exclusions": "Cash, jewelry over $500, electronics over $1,000 (unless declared)"
            },
            "adventure": {
                "coverage": "Adventure sports coverage available in Elite and Premier plans.",
                "included": "Skiing, scuba diving (certified), hiking, zip-lining",
                "excluded": "Base jumping, solo climbing, motor sports",
                "requirement": "Must select Elite or Premier plan and declare activities"
            },
            "pre-existing": {
                "coverage": "Pre-existing conditions can be covered if declared and accepted.",
                "process": "Declare conditions during application, underwriting review, additional premium may apply",
                "exclusions": "Conditions not declared, terminal illnesses, ongoing treatment required"
            }
        }
        
        # Simple keyword matching to find relevant policy section
        question_lower = user_question.lower()
        
        relevant_sections = []
        
        if any(word in question_lower for word in ["medical", "hospital", "doctor", "treatment", "sick", "injured"]):
            relevant_sections.append(("Medical Coverage", policy_kb["medical"]))
        
        if any(word in question_lower for word in ["cancel", "cancellation", "refund", "can't go"]):
            relevant_sections.append(("Trip Cancellation", policy_kb["cancellation"]))
        
        if any(word in question_lower for word in ["bag", "luggage", "lost", "stolen", "damage"]):
            relevant_sections.append(("Baggage Coverage", policy_kb["baggage"]))
        
        if any(word in question_lower for word in ["adventure", "sport", "ski", "dive", "scuba", "hiking"]):
            relevant_sections.append(("Adventure Sports", policy_kb["adventure"]))
        
        if any(word in question_lower for word in ["pre-existing", "condition", "medical history"]):
            relevant_sections.append(("Pre-existing Conditions", policy_kb["pre-existing"]))
        
        # Build response
        if relevant_sections:
            response = "Based on our policy:\n\n"
            for section_name, section_data in relevant_sections:
                response += f"**{section_name}:**\n"
                for key, value in section_data.items():
                    response += f"• {key.title()}: {value}\n"
                response += "\n"
            response += "Do you have any other questions about coverage?"
        else:
            response = """I can help explain our travel insurance policy. Here are common topics:

- **Medical Coverage** - Emergency treatment and hospitalization
- **Trip Cancellation** - Non-refundable expenses if you must cancel
- **Baggage** - Lost, stolen, or damaged belongings
- **Adventure Sports** - Coverage for activities (Elite/Premier plans)
- **Pre-existing Conditions** - How we handle medical history

What would you like to know more about?"""
        
        state["messages"].append(AIMessage(content=response))
        state["policy_question"] = user_question
        
        print(f"   ✅ Answered with {len(relevant_sections)} relevant sections")
        
        return state
    
    def claims_guidance(state: ConversationState) -> ConversationState:
        """Provide claims guidance."""
        
        last_message = state["messages"][-1]
        user_input = last_message.content.lower()
        
        # Extract claim type
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
        
        if state.get("requires_human"):
            # Create handoff request
            handoff_result = tools.create_handoff_request(
                state["user_id"],
                "conversation_escalation",
                "User needs human assistance"
            )
            
            if handoff_result["success"]:
                response = "I'm connecting you with a human agent who can better assist you. They'll be with you shortly."
            else:
                response = "I'm having trouble connecting you with a human agent. Please try again or contact us directly."
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
        
        # Priority 1: If pricing is complete, END
        if state.get("_pricing_complete", False):
            print(f"   → END (pricing complete)")
            log_conversation_metrics(state)
            return END

        # Priority 2: Human handoff
        if state.get("requires_human"):
            print(f"   → customer_service")
            return "customer_service"
        
        # Priority 3: Non-quote intents
        intent = state.get("current_intent", "")
        if intent == "policy_explanation":
            print(f"   → policy_explainer")
            return "policy_explainer"
        elif intent == "claims_guidance":
            print(f"   → claims_guidance")
            return "claims_guidance"
        elif intent == "human_handoff":
            print(f"   → customer_service")
            return "customer_service"
        
        # Priority 4: Quote flow with clear progression
        if intent == "quote" or intent == "":
            confirmation_received = state.get("confirmation_received", False)
            ready_for_pricing = state.get("_ready_for_pricing", False)
            pricing_complete = state.get("_pricing_complete", False)
            current_question = state.get("current_question", "")
            awaiting_confirmation = state.get("awaiting_confirmation", False)
            has_area = state.get("trip_details", {}).get("area") is not None
            has_quote = state.get("quote_data") is not None
            
            print(f"   confirmed={confirmation_received}, ready={ready_for_pricing}")
            print(f"   area={has_area}, quote={has_quote}, complete={pricing_complete}")
            print(f"   current_question={current_question}, awaiting={awaiting_confirmation}")
            
            # If pricing already complete, we're done
            if pricing_complete or has_quote:
                print(f"   → END (quote exists)")
                log_conversation_metrics(state)
                return END
            
            # CRITICAL FIX: If we're waiting for user response, check if last message is from user
            # If we asked a question AND the last message is from AI, END turn
            # If we asked a question AND the last message is from user, process the answer
            messages = state.get("messages", [])
            if messages:
                last_msg_is_ai = isinstance(messages[-1], AIMessage)
                if (current_question or awaiting_confirmation) and last_msg_is_ai:
                    print(f"   → END (waiting for user response)")
                    return END
            
            # If confirmed and ready, proceed through pricing flow
            if confirmation_received and ready_for_pricing:
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
            "policy_explainer": "policy_explainer",
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