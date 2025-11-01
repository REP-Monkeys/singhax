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
    
    @patch('app.routers.chat.OCRService')
    @patch('app.routers.chat.JSONExtractor')
    @patch('app.routers.chat.get_conversation_graph')
    @patch('app.routers.chat.get_current_user_supabase')
    @patch('app.routers.chat.get_db')
    def test_upload_image_success(
        self, 
        mock_get_db, 
        mock_get_user, 
        mock_get_graph,
        mock_json_extractor_class,
        mock_ocr_service_class,
        client, 
        valid_session_id
    ):
        """Test successful image upload with OCR."""
        # Mock authentication
        mock_user = Mock()
        mock_user.id = "user123"
        mock_get_user.return_value = mock_user
        mock_get_db.return_value = Mock()
        
        # Mock OCR service
        mock_ocr_service = Mock()
        mock_ocr_service.extract_text.return_value = {
            "text": "Flight TR892 from SIN to NRT on March 15, 2025",
            "confidence": 91.5,
            "word_count": 10,
            "file_type": "image",
            "error": None
        }
        mock_ocr_service_class.return_value = mock_ocr_service
        
        # Mock JSON extractor
        mock_json_extractor = Mock()
        mock_json_extractor.extract.return_value = {
            "document_type": "flight_confirmation",
            "session_id": valid_session_id,
            "source_filename": "flight.png",
            "high_confidence_fields": ["airline", "destination"],
            "low_confidence_fields": [],
            "json_file_path": "/path/to/json"
        }
        mock_json_extractor_class.return_value = mock_json_extractor
        
        # Mock graph
        mock_graph = Mock()
        mock_graph.get_state.return_value = Mock(values={"messages": []})
        mock_graph.invoke.return_value = {
            "messages": [
                AIMessage(content="I've processed your flight confirmation")
            ]
        }
        mock_get_graph.return_value = mock_graph
        
        # Create test file
        files = {
            "file": ("flight.png", b"fake image data", "image/png")
        }
        data = {
            "session_id": valid_session_id
        }
        
        response = client.post(
            "/api/v1/chat/upload-image",
            files=files,
            data=data
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["session_id"] == valid_session_id
        assert "image_id" in response_data
        assert "ocr_result" in response_data
        assert response_data["ocr_result"]["document_type"] == "flight_confirmation"
        assert "message" in response_data
    
    @patch('app.routers.chat.get_current_user_supabase')
    def test_upload_image_invalid_session_id(self, mock_get_user, client):
        """Test image upload with invalid session ID."""
        mock_user = Mock()
        mock_get_user.return_value = mock_user
        
        files = {
            "file": ("test.png", b"fake data", "image/png")
        }
        data = {
            "session_id": "invalid-session-id"
        }
        
        response = client.post(
            "/api/v1/chat/upload-image",
            files=files,
            data=data
        )
        
        assert response.status_code == 400
        assert "Invalid session_id format" in response.json()["detail"]
    
    @patch('app.routers.chat.get_current_user_supabase')
    def test_upload_image_unsupported_format(self, mock_get_user, client, valid_session_id):
        """Test image upload with unsupported file format."""
        mock_user = Mock()
        mock_get_user.return_value = mock_user
        
        files = {
            "file": ("test.txt", b"fake data", "text/plain")
        }
        data = {
            "session_id": valid_session_id
        }
        
        response = client.post(
            "/api/v1/chat/upload-image",
            files=files,
            data=data
        )
        
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]
    
    @patch('app.routers.chat.get_current_user_supabase')
    def test_upload_image_file_too_large(self, mock_get_user, client, valid_session_id):
        """Test image upload with file exceeding size limit."""
        mock_user = Mock()
        mock_get_user.return_value = mock_user
        
        # Create file larger than 10MB
        large_file_data = b"x" * (11 * 1024 * 1024)  # 11MB
        
        files = {
            "file": ("large.png", large_file_data, "image/png")
        }
        data = {
            "session_id": valid_session_id
        }
        
        response = client.post(
            "/api/v1/chat/upload-image",
            files=files,
            data=data
        )
        
        assert response.status_code == 400
        assert "File too large" in response.json()["detail"]
    
    @patch('app.routers.chat.OCRService')
    @patch('app.routers.chat.get_current_user_supabase')
    @patch('app.routers.chat.get_db')
    def test_upload_image_ocr_error(
        self, 
        mock_get_db, 
        mock_get_user, 
        mock_ocr_service_class,
        client, 
        valid_session_id
    ):
        """Test image upload when OCR processing fails."""
        mock_user = Mock()
        mock_get_user.return_value = mock_user
        mock_get_db.return_value = Mock()
        
        # Mock OCR service to return error
        mock_ocr_service = Mock()
        mock_ocr_service.extract_text.return_value = {
            "text": "",
            "confidence": 0.0,
            "word_count": 0,
            "file_type": "image",
            "error": "OCR processing failed"
        }
        mock_ocr_service_class.return_value = mock_ocr_service
        
        files = {
            "file": ("test.png", b"fake image data", "image/png")
        }
        data = {
            "session_id": valid_session_id
        }
        
        response = client.post(
            "/api/v1/chat/upload-image",
            files=files,
            data=data
        )
        
        assert response.status_code == 500
        assert "OCR processing failed" in response.json()["detail"]
    
    @patch('app.routers.chat.OCRService')
    @patch('app.routers.chat.JSONExtractor')
    @patch('app.routers.chat.get_current_user_supabase')
    @patch('app.routers.chat.get_db')
    def test_upload_pdf_success(
        self, 
        mock_get_db, 
        mock_get_user, 
        mock_json_extractor_class,
        mock_ocr_service_class,
        client, 
        valid_session_id
    ):
        """Test successful PDF upload with OCR."""
        mock_user = Mock()
        mock_get_user.return_value = mock_user
        mock_get_db.return_value = Mock()
        
        # Mock OCR service for PDF
        mock_ocr_service = Mock()
        mock_ocr_service.extract_text.return_value = {
            "text": "Hotel Booking: Grand Tokyo Hotel. Check-in: March 15, 2025",
            "confidence": 89.2,
            "word_count": 8,
            "file_type": "pdf",
            "pages": 1,
            "error": None
        }
        mock_ocr_service_class.return_value = mock_ocr_service
        
        # Mock JSON extractor
        mock_json_extractor = Mock()
        mock_json_extractor.extract.return_value = {
            "document_type": "hotel_booking",
            "session_id": valid_session_id,
            "source_filename": "hotel.pdf",
            "high_confidence_fields": ["hotel_details", "booking_dates"],
            "low_confidence_fields": [],
            "json_file_path": "/path/to/json"
        }
        mock_json_extractor_class.return_value = mock_json_extractor
        
        files = {
            "file": ("hotel.pdf", b"fake pdf data", "application/pdf")
        }
        data = {
            "session_id": valid_session_id
        }
        
        response = client.post(
            "/api/v1/chat/upload-image",
            files=files,
            data=data
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["ocr_result"]["document_type"] == "hotel_booking"
        assert response_data["ocr_result"]["file_type"] == "pdf"



