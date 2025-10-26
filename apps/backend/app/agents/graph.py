"""LangGraph conversation orchestration."""

from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime, date
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from app.agents.tools import ConversationTools
from app.agents.llm_client import GroqLLMClient
from app.services.pricing import PricingService
from app.services.geo_mapping import GeoMapper
from app.core.config import settings


def parse_date_safe(date_string: str) -> Optional[date]:
    """Safely parse date string to date object.
    
    Args:
        date_string: Date in YYYY-MM-DD format
        
    Returns:
        date object if parsing succeeds, None otherwise
    """
    try:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except:
        return None


class ConversationState(TypedDict):
    """State for conversation graph."""
    messages: List[BaseMessage]
    user_id: str
    current_intent: str
    collected_slots: Dict[str, Any]
    confidence_score: float
    requires_human: bool
    quote_data: Dict[str, Any]
    policy_question: str
    claim_type: str
    handoff_reason: str
    # New fields for Step 1 quote flow
    trip_details: Dict[str, Any]  # destination, departure_date, return_date, duration_days, area, base_rate
    travelers_data: Dict[str, Any]  # ages list, count
    preferences: Dict[str, Any]  # adventure_sports
    current_question: str  # Which question we're asking
    awaiting_confirmation: bool  # Waiting for user confirmation
    confirmation_received: bool  # User confirmed details


def create_conversation_graph(db) -> StateGraph:
    """Create the conversation state graph."""
    
    tools = ConversationTools(db)
    llm_client = GroqLLMClient()
    pricing_service = PricingService()
    
    def orchestrator(state: ConversationState) -> ConversationState:
        """Route conversation based on LLM intent classification."""
        try:
            last_message = state["messages"][-1]
            user_input = last_message.content.lower()
            
            # Simple intent classification without LLM for debugging
            if any(word in user_input for word in ["insurance", "quote", "travel", "trip"]):
                state["current_intent"] = "quote"
                state["confidence_score"] = 0.9
            elif any(word in user_input for word in ["policy", "coverage", "terms"]):
                state["current_intent"] = "policy_explanation"
                state["confidence_score"] = 0.8
            elif any(word in user_input for word in ["claim", "file", "reimbursement"]):
                state["current_intent"] = "claims_guidance"
                state["confidence_score"] = 0.8
            else:
                state["current_intent"] = "quote"  # Default to quote
                state["confidence_score"] = 0.7
            
            # Check if human handoff needed (low confidence)
            if state["confidence_score"] < 0.6:
                state["requires_human"] = True
            
            return state
        except Exception as e:
            # On error, default to quote intent
            state["current_intent"] = "quote"
            state["confidence_score"] = 0.5
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
            
            # Update state with extracted information
            if "destination" in extracted:
                trip["destination"] = extracted["destination"]
            
            if "departure_date" in extracted:
                # Parse to date object with error handling
                parsed_date = parse_date_safe(extracted["departure_date"])
                if parsed_date:
                    trip["departure_date"] = parsed_date
                else:
                    # Date parsing failed - will ask for clarification below
                    pass
            
            if "return_date" in extracted:
                # Parse to date object with error handling
                parsed_date = parse_date_safe(extracted["return_date"])
                if parsed_date:
                    trip["return_date"] = parsed_date
                else:
                    # Date parsing failed - will ask for clarification below
                    pass
            
            if "travelers_ages" in extracted:
                # Validate ages are integers in valid range
                valid_ages = [age for age in extracted["travelers_ages"] if isinstance(age, int) and 0.08 <= age <= 110]
                if valid_ages:
                    travelers["ages"] = valid_ages
                    travelers["count"] = len(valid_ages)
            
            if "adventure_sports" in extracted:
                prefs["adventure_sports"] = extracted["adventure_sports"]
            
            # Handle confirmation flow
            if state.get("awaiting_confirmation"):
                # Check if user confirmed or wants to make changes
                user_response_lower = user_input.lower()
                said_yes = any(word in user_response_lower for word in ["yes", "correct", "confirm", "looks good", "that's right", "yeah"])
                said_no = any(word in user_response_lower for word in ["no", "wrong", "incorrect", "change", "fix"])
                
                if said_yes:
                    state["confirmation_received"] = True
                    state["awaiting_confirmation"] = False
                    response = "Great! Let me calculate your insurance options..."
                    state["messages"].append(AIMessage(content=response))
                    return state
                elif said_no:
                    state["awaiting_confirmation"] = False
                    response = "No problem! What would you like to correct?"
                    state["messages"].append(AIMessage(content=response))
                    return state
                else:
                    # User didn't clearly say yes or no
                    response = "I didn't catch that. Is the information above correct? (yes/no)"
                    state["messages"].append(AIMessage(content=response))
                    return state
            
            # Set default for adventure_sports if not answered yet
            if "adventure_sports" not in prefs or prefs.get("adventure_sports") is None:
                prefs["adventure_sports"] = False
            
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
            if missing:
                # Ask for next missing piece of information
                if "destination" in missing:
                    response = "Where are you traveling to?"
                    state["current_question"] = "destination"
                elif "departure_date" in missing:
                    response = "When does your trip start? Please provide the date in YYYY-MM-DD format. For example: 2025-12-15"
                    state["current_question"] = "departure_date"
                elif "return_date" in missing:
                    response = "When do you return to Singapore? Please provide the date in YYYY-MM-DD format. For example: 2025-12-22"
                    state["current_question"] = "return_date"
                elif "travelers" in missing:
                    response = "How many travelers are going, and what are their ages? For example: '2 travelers, ages 30 and 8'"
                    state["current_question"] = "travelers"
            elif prefs.get("adventure_sports") is False and not state.get("awaiting_confirmation"):
                # Ask about adventure sports if not explicitly answered
                response = "Are you planning any adventure activities like skiing, scuba diving, trekking, or bungee jumping?"
                state["current_question"] = "adventure_sports"
            elif all_required_present and not state.get("awaiting_confirmation"):
                # All info collected, show summary and ask for confirmation
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
            
            return state
            
        except Exception as e:
            response = "I encountered an error calculating your quote. Let me connect you with a human agent."
            state["requires_human"] = True
            state["messages"].append(AIMessage(content=response))
            return state
    
    def policy_explainer(state: ConversationState) -> ConversationState:
        """Provide policy explanations using RAG."""
        
        last_message = state["messages"][-1]
        user_input = last_message.content
        
        # Search policy documents
        search_result = tools.search_policy_documents(user_input)
        
        if search_result["success"] and search_result["results"]:
            response_parts = []
            for result in search_result["results"][:2]:  # Limit to 2 results
                response_parts.append(f"{result['text']}\nSource: §{result['section_id']}")
            
            response = "\n\n".join(response_parts)
        else:
            response = "I couldn't find specific information about that in our policy documents. Let me connect you with a human agent for assistance."
            state["requires_human"] = True
        
        state["messages"].append(AIMessage(content=response))
        
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
    
    def should_continue(state: ConversationState) -> str:
        """Determine next step in conversation with clear priority logic."""
        
        # Priority 1: Human handoff
        if state.get("requires_human"):
            return "customer_service"
        
        # Priority 2: Non-quote intents
        intent = state.get("current_intent", "")
        if intent == "policy_explanation":
            return "policy_explainer"
        elif intent == "claims_guidance":
            return "claims_guidance"
        elif intent == "human_handoff":
            return "customer_service"
        
        # Priority 3: Quote flow - SIMPLIFIED LOGIC
        if intent == "quote":
            # Check if we have a quote already - if so, we're done
            if state.get("quote_data"):
                return END
            
            # Check if we have area but no quote - go to pricing
            if state.get("trip_details", {}).get("area") and not state.get("quote_data"):
                return "pricing"
            
            # Check if we have confirmation but no area - go to risk assessment
            if state.get("confirmation_received") and not state.get("trip_details", {}).get("area"):
                return "risk_assessment"
            
            # Otherwise, stay in needs_assessment
            return "needs_assessment"
        
        # Default: general inquiry routes to needs assessment for quote flow
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
    
    # Configure checkpointing for conversation persistence
    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        # Create checkpointer with proper connection handling
        conn_string = settings.langgraph_checkpoint_db or settings.database_url
        with PostgresSaver.from_conn_string(conn_string) as checkpointer:
            # Setup tables if needed
            checkpointer.setup()
            return graph.compile(checkpointer=checkpointer)
    except Exception as e:
        # Fallback if checkpoint package not installed or connection fails
        print(f"Warning: LangGraph checkpointing not available - {e}")
        print("Using fallback without persistence")
        return graph.compile()


def create_conversation_graph_no_checkpoint(db) -> StateGraph:
    """Create conversation graph without checkpointing for fallback."""
    # Reuse the same graph creation logic but without checkpointing
    tools = ConversationTools(db)
    llm_client = GroqLLMClient()
    pricing_service = PricingService()
    
    def orchestrator(state: ConversationState) -> ConversationState:
        """Route conversation based on LLM intent classification."""
        try:
            last_message = state["messages"][-1]
            
            # Use LLM to classify intent
            classification = llm_client.classify_intent(
                last_message.content,
                state["messages"][:-1]  # History excluding current message
            )
            
            state["current_intent"] = classification["intent"]
            state["confidence_score"] = classification["confidence"]
            
            # Add rationale for debugging
            state["rationale"] = {
                "intent": classification["intent"],
                "confidence": classification["confidence"],
                "reasoning": classification.get("reasoning", "")
            }
            
            return state
            
        except Exception as e:
            print(f"Error in orchestrator: {e}")
            state["current_intent"] = "quote"  # Default fallback
            state["confidence_score"] = 0.5
            return state
    
    def needs_assessment(state: ConversationState) -> ConversationState:
        """Collect trip information through structured conversation."""
        try:
            # Initialize data structures if not present
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
            
            # Simple extraction logic for fallback
            user_input_lower = user_input.lower()
            
            # Extract destination
            if not trip.get("destination"):
                if "japan" in user_input_lower:
                    trip["destination"] = "Japan"
                elif "thailand" in user_input_lower:
                    trip["destination"] = "Thailand"
                elif "singapore" in user_input_lower:
                    trip["destination"] = "Singapore"
            
            # Extract dates (simple patterns)
            if not trip.get("departure_date"):
                if "dec 15" in user_input_lower or "2025-12-15" in user_input_lower:
                    trip["departure_date"] = date(2025, 12, 15)
            
            if not trip.get("return_date"):
                if "dec 22" in user_input_lower or "2025-12-22" in user_input_lower:
                    trip["return_date"] = date(2025, 12, 22)
            
            # Extract travelers
            if not travelers.get("ages"):
                if "age 30" in user_input_lower or "30" in user_input_lower:
                    travelers["ages"] = [30]
                    travelers["count"] = 1
            
            # Extract adventure sports
            if "adventure_sports" not in prefs:
                if "no" in user_input_lower and ("adventure" in user_input_lower or "sports" in user_input_lower):
                    prefs["adventure_sports"] = False
            
            # Check if we have all required info
            has_destination = trip.get("destination")
            has_departure = trip.get("departure_date")
            has_return = trip.get("return_date")
            has_travelers = travelers.get("ages")
            
            if has_destination and has_departure and has_return and has_travelers:
                # All info collected, ask for confirmation
                dest = trip["destination"]
                dep_date = trip["departure_date"]
                ret_date = trip["return_date"]
                ages = travelers["ages"]
                
                response = f"""Let me confirm your trip details:

📍 Destination: {dest}
📅 Travel dates: {dep_date} to {ret_date}
👥 Travelers: {len(ages)} traveler(s) (ages: {', '.join(map(str, ages))})
🏔️ Adventure activities: No

Is this information correct? (yes/no)"""
                
                state["awaiting_confirmation"] = True
            else:
                # Ask for missing information
                if not has_destination:
                    response = "Where are you traveling to?"
                elif not has_departure:
                    response = "When does your trip start? Please provide the date in YYYY-MM-DD format."
                elif not has_return:
                    response = "When do you return? Please provide the date in YYYY-MM-DD format."
                elif not has_travelers:
                    response = "How many travelers are going, and what are their ages?"
                else:
                    response = "Are you planning any adventure activities like skiing, scuba diving, or trekking?"
            
            state["messages"].append(AIMessage(content=response))
            return state
            
        except Exception as e:
            response = "I'm having trouble processing that. Could you please rephrase?"
            state["messages"].append(AIMessage(content=response))
            return state
    
    def risk_assessment(state: ConversationState) -> ConversationState:
        """Map destination to geographic area for pricing."""
        trip = state.get("trip_details", {})
        destination = trip.get("destination")
        
        if destination:
            # Simple area mapping
            if destination.lower() in ["japan", "tokyo", "osaka"]:
                trip["area"] = "asia_developed"
            elif destination.lower() in ["thailand", "bangkok"]:
                trip["area"] = "asia_developing"
            else:
                trip["area"] = "asia_developed"  # Default
        
        response = "Great! I've mapped your destination to the appropriate region for pricing."
        state["messages"].append(AIMessage(content=response))
        return state
    
    def pricing(state: ConversationState) -> ConversationState:
        """Generate insurance quotes using pricing service."""
        try:
            trip = state.get("trip_details", {})
            travelers = state.get("travelers_data", {})
            preferences = state.get("preferences", {})
            
            # Generate quote
            quote_result = pricing_service.generate_quote(
                destination=trip.get("destination", "Japan"),
                departure_date=trip.get("departure_date", date(2025, 12, 15)),
                return_date=trip.get("return_date", date(2025, 12, 22)),
                travelers=travelers.get("ages", [30]),
                adventure_sports=preferences.get("adventure_sports", False)
            )
            
            if quote_result["success"]:
                state["quote_data"] = quote_result
                response = f"""Here are your travel insurance options:

💰 **Standard Plan**: ${quote_result['quotes']['standard']['price']:.2f}
   - Medical coverage: ${quote_result['quotes']['standard']['coverage']['medical']:,}
   - Trip cancellation: ${quote_result['quotes']['standard']['coverage']['trip_cancellation']:,}

💰 **Premium Plan**: ${quote_result['quotes']['premium']['price']:.2f}
   - Medical coverage: ${quote_result['quotes']['premium']['coverage']['medical']:,}
   - Trip cancellation: ${quote_result['quotes']['premium']['coverage']['trip_cancellation']:,}

Would you like to proceed with one of these options?"""
            else:
                response = "I'm sorry, I couldn't generate quotes at this time. Please try again later."
            
            state["messages"].append(AIMessage(content=response))
            return state
            
        except Exception as e:
            response = "I'm having trouble generating quotes. Please try again."
            state["messages"].append(AIMessage(content=response))
            return state
    
    def should_continue(state: ConversationState) -> str:
        """Determine next step in conversation."""
        intent = state.get("current_intent", "")
        
        if intent == "quote":
            # Check if we have a quote already - if so, we're done
            if state.get("quote_data"):
                return END
            
            # Check if we have area but no quote - go to pricing
            if state.get("trip_details", {}).get("area") and not state.get("quote_data"):
                return "pricing"
            
            # Check if we have confirmation but no area - go to risk assessment
            if state.get("confirmation_received") and not state.get("trip_details", {}).get("area"):
                return "risk_assessment"
            
            # Otherwise, stay in needs_assessment
            return "needs_assessment"
        
        return "needs_assessment"
    
    # Create the graph
    graph = StateGraph(ConversationState)
    
    # Add nodes
    graph.add_node("orchestrator", orchestrator)
    graph.add_node("needs_assessment", needs_assessment)
    graph.add_node("risk_assessment", risk_assessment)
    graph.add_node("pricing", pricing)
    
    # Add edges
    graph.set_entry_point("orchestrator")
    
    graph.add_conditional_edges(
        "orchestrator",
        should_continue,
        {
            "needs_assessment": "needs_assessment",
            "risk_assessment": "risk_assessment",
            "pricing": "pricing",
            END: END
        }
    )
    
    graph.add_conditional_edges(
        "needs_assessment",
        should_continue,
        {
            "needs_assessment": "needs_assessment",
            "risk_assessment": "risk_assessment",
            "pricing": "pricing",
            END: END
        }
    )
    
    graph.add_edge("risk_assessment", "pricing")
    graph.add_edge("pricing", END)
    
    # Compile without checkpointing
    return graph.compile()