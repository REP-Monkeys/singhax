"""Tests for LangGraph conversation graph."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage

from app.agents.graph import create_conversation_graph, ConversationState
from app.agents.tools import ConversationTools


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return Mock()


@pytest.fixture
def mock_tools():
    """Create mock conversation tools."""
    tools = Mock(spec=ConversationTools)
    
    # Mock tool methods
    tools.assess_risk_factors.return_value = {
        "age_risk": 0.1,
        "activity_risk": 0.2,
        "destination_risk": 0.0,
        "preexisting_conditions": 0.0,
        "total_risk_score": 0.3
    }
    
    tools.get_quote_range.return_value = {
        "success": True,
        "price_min": 100.0,
        "price_max": 150.0,
        "breakdown": {"base_rate": 75.0},
        "currency": "USD"
    }
    
    tools.search_policy_documents.return_value = {
        "success": True,
        "results": [
            {
                "text": "Coverage includes medical expenses up to $100,000",
                "section_id": "2.1"
            }
        ]
    }
    
    tools.get_claim_requirements.return_value = {
        "success": True,
        "requirements": {
            "required_documents": ["Police report", "Receipt"],
            "required_info": ["Date of incident", "Location"]
        }
    }
    
    tools.create_handoff_request.return_value = {
        "success": True,
        "handoff_id": "test-handoff-123"
    }
    
    return tools


class TestConversationGraph:
    """Test cases for conversation graph."""
    
    def test_create_graph(self, mock_db):
        """Test graph creation."""
        graph = create_conversation_graph(mock_db)
        
        assert graph is not None
    
    @patch('app.agents.graph.ConversationTools')
    def test_orchestrator_quote_intent(self, mock_tools_class, mock_db):
        """Test orchestrator detects quote intent."""
        mock_tools_class.return_value = Mock()
        
        graph = create_conversation_graph(mock_db)
        
        initial_state = {
            "messages": [HumanMessage(content="I need a travel insurance quote")],
            "user_id": "test-user",
            "current_intent": "",
            "collected_slots": {},
            "confidence_score": 0.0,
            "requires_human": False,
            "quote_data": {},
            "policy_question": "",
            "claim_type": "",
            "handoff_reason": "",
            "trip_details": {},
            "travelers_data": {},
            "preferences": {},
            "awaiting_confirmation": False,
            "confirmation_received": False,
            "awaiting_field": ""
        }
        
        result = graph.invoke(initial_state)
        
        assert result["current_intent"] == "quote"
        assert result["confidence_score"] > 0.5
    
    @patch('app.agents.graph.ConversationTools')
    def test_orchestrator_policy_intent(self, mock_tools_class, mock_db):
        """Test orchestrator detects policy explanation intent."""
        mock_tools_class.return_value = Mock()
        
        graph = create_conversation_graph(mock_db)
        
        initial_state = {
            "messages": [HumanMessage(content="What does the policy cover?")],
            "user_id": "test-user",
            "current_intent": "",
            "collected_slots": {},
            "confidence_score": 0.0,
            "requires_human": False,
            "quote_data": {},
            "policy_question": "",
            "claim_type": "",
            "handoff_reason": "",
            "trip_details": {},
            "travelers_data": {},
            "preferences": {},
            "awaiting_confirmation": False,
            "confirmation_received": False,
            "awaiting_field": ""
        }
        
        result = graph.invoke(initial_state)
        
        assert result["current_intent"] == "policy_explanation"
    
    @patch('app.agents.graph.ConversationTools')
    def test_orchestrator_claims_intent(self, mock_tools_class, mock_db):
        """Test orchestrator detects claims intent."""
        mock_tools_class.return_value = Mock()
        
        graph = create_conversation_graph(mock_db)
        
        initial_state = {
            "messages": [HumanMessage(content="I need to file a claim")],
            "user_id": "test-user",
            "current_intent": "",
            "collected_slots": {},
            "confidence_score": 0.0,
            "requires_human": False,
            "quote_data": {},
            "policy_question": "",
            "claim_type": "",
            "handoff_reason": "",
            "trip_details": {},
            "travelers_data": {},
            "preferences": {},
            "awaiting_confirmation": False,
            "confirmation_received": False,
            "awaiting_field": ""
        }
        
        result = graph.invoke(initial_state)
        
        assert result["current_intent"] == "claims_guidance"
    
    @patch('app.agents.graph.ConversationTools')
    def test_orchestrator_human_handoff_intent(self, mock_tools_class, mock_db):
        """Test orchestrator detects human handoff intent."""
        mock_tools_class.return_value = Mock()
        
        graph = create_conversation_graph(mock_db)
        
        initial_state = {
            "messages": [HumanMessage(content="I need to speak to a human agent")],
            "user_id": "test-user",
            "current_intent": "",
            "collected_slots": {},
            "confidence_score": 0.0,
            "requires_human": False,
            "quote_data": {},
            "policy_question": "",
            "claim_type": "",
            "handoff_reason": "",
            "trip_details": {},
            "travelers_data": {},
            "preferences": {},
            "awaiting_confirmation": False,
            "confirmation_received": False,
            "awaiting_field": ""
        }
        
        result = graph.invoke(initial_state)
        
        assert result["current_intent"] == "human_handoff"
    
    @patch('app.agents.graph.ConversationTools')
    def test_needs_assessment_node(self, mock_tools_class, mock_db):
        """Test needs assessment collects trip information."""
        mock_tools_class.return_value = Mock()
        
        graph = create_conversation_graph(mock_db)
        
        initial_state = {
            "messages": [HumanMessage(content="I need insurance for my trip to France")],
            "user_id": "test-user",
            "current_intent": "quote",
            "collected_slots": {},
            "confidence_score": 0.8,
            "requires_human": False,
            "quote_data": {},
            "policy_question": "",
            "claim_type": "",
            "handoff_reason": "",
            "trip_details": {},
            "travelers_data": {},
            "preferences": {},
            "awaiting_confirmation": False,
            "confirmation_received": False,
            "awaiting_field": ""
        }
        
        result = graph.invoke(initial_state)
        
        # Should have AI response in messages
        ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
        assert len(ai_messages) > 0
    
    @patch('app.agents.graph.ConversationTools')
    def test_policy_explainer_with_results(self, mock_tools_class, mock_db):
        """Test policy explainer returns search results."""
        mock_tools = Mock()
        mock_tools.search_policy_documents.return_value = {
            "success": True,
            "results": [
                {
                    "text": "Medical coverage includes emergency services",
                    "section_id": "3.1"
                }
            ]
        }
        mock_tools_class.return_value = mock_tools
        
        graph = create_conversation_graph(mock_db)
        
        initial_state = {
            "messages": [HumanMessage(content="What medical coverage is included?")],
            "user_id": "test-user",
            "current_intent": "policy_explanation",
            "collected_slots": {},
            "confidence_score": 0.8,
            "requires_human": False,
            "quote_data": {},
            "policy_question": "",
            "claim_type": "",
            "handoff_reason": "",
            "trip_details": {},
            "travelers_data": {},
            "preferences": {},
            "awaiting_confirmation": False,
            "confirmation_received": False,
            "awaiting_field": ""
        }
        
        result = graph.invoke(initial_state)
        
        # Should have policy information in response
        ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
        assert len(ai_messages) > 0
        assert "medical" in ai_messages[-1].content.lower() or "3.1" in ai_messages[-1].content
    
    @patch('app.agents.graph.ConversationTools')
    def test_claims_guidance_with_type(self, mock_tools_class, mock_db):
        """Test claims guidance provides requirements."""
        mock_tools = Mock()
        mock_tools.get_claim_requirements.return_value = {
            "success": True,
            "requirements": {
                "required_documents": ["Medical report", "Receipts"],
                "required_info": ["Date", "Location"]
            }
        }
        mock_tools_class.return_value = mock_tools
        
        graph = create_conversation_graph(mock_db)
        
        initial_state = {
            "messages": [HumanMessage(content="I need to file a medical claim")],
            "user_id": "test-user",
            "current_intent": "claims_guidance",
            "collected_slots": {},
            "confidence_score": 0.8,
            "requires_human": False,
            "quote_data": {},
            "policy_question": "",
            "claim_type": "",
            "handoff_reason": "",
            "trip_details": {},
            "travelers_data": {},
            "preferences": {},
            "awaiting_confirmation": False,
            "confirmation_received": False,
            "awaiting_field": ""
        }
        
        result = graph.invoke(initial_state)
        
        # Should provide claim requirements
        ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
        assert len(ai_messages) > 0
        response = ai_messages[-1].content.lower()
        assert "medical" in response or "documents" in response or "requirements" in response
    
    @patch('app.agents.graph.ConversationTools')
    def test_low_confidence_triggers_handoff(self, mock_tools_class, mock_db):
        """Test low confidence score triggers human handoff."""
        mock_tools_class.return_value = Mock()
        
        graph = create_conversation_graph(mock_db)
        
        initial_state = {
            "messages": [HumanMessage(content="xyz random unclear message")],
            "user_id": "test-user",
            "current_intent": "",
            "collected_slots": {},
            "confidence_score": 0.0,
            "requires_human": False,
            "quote_data": {},
            "policy_question": "",
            "claim_type": "",
            "handoff_reason": "",
            "trip_details": {},
            "travelers_data": {},
            "preferences": {},
            "awaiting_confirmation": False,
            "confirmation_received": False,
            "awaiting_field": ""
        }
        
        result = graph.invoke(initial_state)
        
        # Low confidence should trigger human requirement
        assert result["confidence_score"] < 0.6



