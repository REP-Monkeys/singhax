"""Tests for chat router and conversation endpoints."""

import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from langchain_core.messages import HumanMessage, AIMessage

from app.main import app
from app.core.db import get_db


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return Mock()


@pytest.fixture
def valid_session_id():
    """Generate valid session ID."""
    return str(uuid.uuid4())


class TestChatRouter:
    """Test cases for chat router endpoints."""
    
    def test_chat_health_endpoint(self, client):
        """Test chat health check endpoint."""
        response = client.get("/api/v1/chat/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "chat"
    
    @patch('app.routers.chat.create_conversation_graph')
    def test_send_message_success(self, mock_create_graph, client, valid_session_id):
        """Test successful message sending."""
        # Mock graph
        mock_graph = Mock()
        mock_graph.invoke.return_value = {
            "messages": [
                HumanMessage(content="I need travel insurance"),
                AIMessage(content="I can help you with that!")
            ],
            "current_intent": "quote",
            "trip_details": {},
            "travelers_data": {},
            "preferences": {},
            "awaiting_confirmation": False,
            "confirmation_received": False,
            "awaiting_field": "",
            "quote_data": None,
            "requires_human": False
        }
        mock_create_graph.return_value = mock_graph
        
        payload = {
            "session_id": valid_session_id,
            "message": "I need travel insurance"
        }
        
        response = client.post("/api/v1/chat/message", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == valid_session_id
        assert "message" in data
        assert data["message"] == "I can help you with that!"
        assert "state" in data
        assert data["requires_human"] is False
    
    def test_send_message_invalid_session_id(self, client):
        """Test message sending with invalid session ID."""
        payload = {
            "session_id": "invalid-session-id",
            "message": "Hello"
        }
        
        response = client.post("/api/v1/chat/message", json=payload)
        
        assert response.status_code == 400
        assert "Invalid session_id format" in response.json()["detail"]
    
    @patch('app.routers.chat.create_conversation_graph')
    def test_send_message_with_quote_data(self, mock_create_graph, client, valid_session_id):
        """Test message sending that includes quote data."""
        mock_graph = Mock()
        mock_graph.invoke.return_value = {
            "messages": [
                HumanMessage(content="Quote for France trip"),
                AIMessage(content="Here's your quote for France")
            ],
            "current_intent": "quote",
            "trip_details": {"destination": "France"},
            "travelers_data": {},
            "preferences": {},
            "awaiting_confirmation": False,
            "confirmation_received": False,
            "awaiting_field": "",
            "quote_data": {
                "destination": "France",
                "price_range": {"min": 100.0, "max": 150.0}
            },
            "requires_human": False
        }
        mock_create_graph.return_value = mock_graph
        
        payload = {
            "session_id": valid_session_id,
            "message": "Quote for France trip"
        }
        
        response = client.post("/api/v1/chat/message", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["quote"] is not None
        assert data["quote"]["destination"] == "France"
    
    @patch('app.routers.chat.create_conversation_graph')
    def test_send_message_requires_human(self, mock_create_graph, client, valid_session_id):
        """Test message that requires human handoff."""
        mock_graph = Mock()
        mock_graph.invoke.return_value = {
            "messages": [
                HumanMessage(content="I need to speak to someone"),
                AIMessage(content="Let me connect you with an agent")
            ],
            "current_intent": "human_handoff",
            "trip_details": {},
            "travelers_data": {},
            "preferences": {},
            "awaiting_confirmation": False,
            "confirmation_received": False,
            "awaiting_field": "",
            "quote_data": None,
            "requires_human": True
        }
        mock_create_graph.return_value = mock_graph
        
        payload = {
            "session_id": valid_session_id,
            "message": "I need to speak to someone"
        }
        
        response = client.post("/api/v1/chat/message", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["requires_human"] is True
    
    @patch('app.routers.chat.create_conversation_graph')
    def test_send_message_graph_error(self, mock_create_graph, client, valid_session_id):
        """Test handling of graph execution errors."""
        mock_graph = Mock()
        mock_graph.invoke.side_effect = Exception("Graph execution failed")
        mock_create_graph.return_value = mock_graph
        
        payload = {
            "session_id": valid_session_id,
            "message": "Test message"
        }
        
        response = client.post("/api/v1/chat/message", json=payload)
        
        assert response.status_code == 500
        assert "Processing failed" in response.json()["detail"]
    
    @patch('app.routers.chat.create_conversation_graph')
    def test_conversation_with_multiple_messages(self, mock_create_graph, client, valid_session_id):
        """Test conversation flow with multiple messages."""
        mock_graph = Mock()
        
        # First message
        mock_graph.invoke.return_value = {
            "messages": [
                HumanMessage(content="I need insurance"),
                AIMessage(content="What's your destination?")
            ],
            "current_intent": "quote",
            "trip_details": {},
            "travelers_data": {},
            "preferences": {},
            "awaiting_confirmation": False,
            "confirmation_received": False,
            "awaiting_field": "destination",
            "quote_data": None,
            "requires_human": False
        }
        mock_create_graph.return_value = mock_graph
        
        response1 = client.post("/api/v1/chat/message", json={
            "session_id": valid_session_id,
            "message": "I need insurance"
        })
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert "destination" in data1["message"].lower()
        
        # Second message
        mock_graph.invoke.return_value = {
            "messages": [
                HumanMessage(content="France"),
                AIMessage(content="Great! How many travelers?")
            ],
            "current_intent": "quote",
            "trip_details": {"destination": "France"},
            "travelers_data": {},
            "preferences": {},
            "awaiting_confirmation": False,
            "confirmation_received": False,
            "awaiting_field": "travelers",
            "quote_data": None,
            "requires_human": False
        }
        
        response2 = client.post("/api/v1/chat/message", json={
            "session_id": valid_session_id,
            "message": "France"
        })
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert "travelers" in data2["message"].lower() or "many" in data2["message"].lower()
    
    def test_missing_required_fields(self, client):
        """Test request with missing required fields."""
        # Missing message
        response = client.post("/api/v1/chat/message", json={
            "session_id": str(uuid.uuid4())
        })
        assert response.status_code == 422
        
        # Missing session_id
        response = client.post("/api/v1/chat/message", json={
            "message": "Test"
        })
        assert response.status_code == 422



