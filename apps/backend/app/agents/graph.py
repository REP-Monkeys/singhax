"""LangGraph conversation orchestration."""

from typing import Dict, Any, List, Optional, TypedDict
from langgraph import StateGraph, END
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from app.agents.tools import ConversationTools


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


def create_conversation_graph(db) -> StateGraph:
    """Create the conversation state graph."""
    
    tools = ConversationTools(db)
    
    def orchestrator(state: ConversationState) -> ConversationState:
        """Route conversation based on intent and confidence."""
        
        last_message = state["messages"][-1]
        user_input = last_message.content.lower()
        
        # Simple intent detection (TODO: Replace with proper NLP)
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
    
    def needs_assessment(state: ConversationState) -> ConversationState:
        """Collect trip information for quotes."""
        
        collected = state.get("collected_slots", {})
        last_message = state["messages"][-1]
        user_input = last_message.content.lower()
        
        # Extract trip information (TODO: Use proper NLP)
        if "trip" in user_input or "travel" in user_input:
            if "start" in user_input or "begin" in user_input:
                collected["trip_start"] = "extracted_date"
            if "end" in user_input or "finish" in user_input:
                collected["trip_end"] = "extracted_date"
            if "destination" in user_input or "going to" in user_input:
                collected["destinations"] = ["extracted_destination"]
        
        # Extract traveler information
        if "traveler" in user_input or "person" in user_input:
            collected["travelers"] = [{"name": "extracted_name", "age": 30}]
        
        # Extract activities
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
    
    def risk_assessment(state: ConversationState) -> ConversationState:
        """Assess risk factors for pricing."""
        
        collected = state.get("collected_slots", {})
        
        if collected.get("travelers") and collected.get("activities") and collected.get("destinations"):
            risk_factors = tools.assess_risk_factors(
                collected["travelers"],
                collected["activities"],
                collected["destinations"]
            )
            
            state["quote_data"] = {
                **collected,
                "risk_factors": risk_factors
            }
        
        return state
    
    def pricing(state: ConversationState) -> ConversationState:
        """Calculate pricing for quotes."""
        
        quote_data = state.get("quote_data", {})
        
        if quote_data:
            # Calculate quote range
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
        """Determine next step in conversation."""
        
        intent = state.get("current_intent")
        
        if state.get("requires_human"):
            return "customer_service"
        
        if intent == "quote":
            if not state.get("collected_slots"):
                return "needs_assessment"
            elif not state.get("quote_data"):
                return "risk_assessment"
            else:
                return "pricing"
        elif intent == "policy_explanation":
            return "policy_explainer"
        elif intent == "claims_guidance":
            return "claims_guidance"
        elif intent == "human_handoff":
            return "customer_service"
        else:
            return "customer_service"
    
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
    
    # Add edges
    graph.add_edge("orchestrator", "needs_assessment")
    graph.add_edge("needs_assessment", "risk_assessment")
    graph.add_edge("risk_assessment", "pricing")
    graph.add_edge("pricing", "compliance")
    graph.add_edge("policy_explainer", END)
    graph.add_edge("claims_guidance", END)
    graph.add_edge("compliance", END)
    graph.add_edge("customer_service", END)
    
    # Set entry point
    graph.set_entry_point("orchestrator")
    
    return graph.compile()
