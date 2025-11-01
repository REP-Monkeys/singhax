"""Tests for JSON builders service."""

import pytest
from datetime import date, datetime
from app.services.json_builders import (
    build_ancileo_quotation_json,
    build_ancileo_purchase_json,
    build_trip_metadata_json
)


class TestAncileoQuotationJSONBuilder:
    """Test build_ancileo_quotation_json function."""
    
    def test_build_round_trip_quotation(self):
        """Test building quotation JSON for round trip."""
        trip_details = {
            "destination": "Japan",
            "departure_date": date(2025, 12, 15),
            "return_date": date(2025, 12, 22),
            "departure_country": "SG",
            "arrival_country": "JP",
            "adults_count": 2,
            "children_count": 0
        }
        travelers_data = {"ages": [30, 35], "count": 2}
        preferences = {"adventure_sports": False}
        
        result = build_ancileo_quotation_json(trip_details, travelers_data, preferences)
        
        assert result["market"] == "SG"
        assert result["languageCode"] == "en"
        assert result["channel"] == "white-label"
        assert result["deviceType"] == "DESKTOP"
        assert result["context"]["tripType"] == "RT"
        assert result["context"]["departureDate"] == "2025-12-15"
        assert result["context"]["returnDate"] == "2025-12-22"
        assert result["context"]["departureCountry"] == "SG"
        assert result["context"]["arrivalCountry"] == "JP"
        assert result["context"]["adultsCount"] == 2
        assert result["context"]["childrenCount"] == 0
        assert result["adventure_sports_activities"] is False
    
    def test_build_single_trip_quotation(self):
        """Test building quotation JSON for single trip."""
        trip_details = {
            "destination": "Thailand",
            "departure_date": date(2025, 6, 1),
            "departure_country": "SG",
            "arrival_country": "TH",
            "adults_count": 1,
            "children_count": 1
        }
        travelers_data = {"ages": [35, 8], "count": 2}
        preferences = {"adventure_sports": True}
        
        result = build_ancileo_quotation_json(trip_details, travelers_data, preferences)
        
        assert result["context"]["tripType"] == "ST"
        assert "returnDate" not in result["context"]
        assert result["context"]["adultsCount"] == 1
        assert result["context"]["childrenCount"] == 1
        assert result["adventure_sports_activities"] is True
    
    def test_calculate_adults_children_from_ages(self):
        """Test that adults/children are calculated from ages if not provided."""
        trip_details = {
            "destination": "Japan",
            "departure_date": date(2025, 12, 15),
            "return_date": date(2025, 12, 22),
            "departure_country": "SG",
            "arrival_country": "JP",
            "adults_count": 0,  # Not set
            "children_count": 0  # Not set
        }
        travelers_data = {"ages": [30, 35, 8, 5], "count": 4}
        preferences = {"adventure_sports": False}
        
        result = build_ancileo_quotation_json(trip_details, travelers_data, preferences)
        
        assert result["context"]["adultsCount"] == 2
        assert result["context"]["childrenCount"] == 2
    
    def test_ensure_at_least_one_adult(self):
        """Test that at least one adult is ensured even if all travelers are children."""
        trip_details = {
            "destination": "Japan",
            "departure_date": date(2025, 12, 15),
            "return_date": date(2025, 12, 22),
            "departure_country": "SG",
            "arrival_country": "JP"
        }
        travelers_data = {"ages": [8, 5], "count": 2}  # All children
        preferences = {"adventure_sports": False}
        
        result = build_ancileo_quotation_json(trip_details, travelers_data, preferences)
        
        assert result["context"]["adultsCount"] == 1
        assert result["context"]["childrenCount"] == 1  # One child converted to adult
    
    def test_default_departure_country(self):
        """Test that departure_country defaults to SG."""
        trip_details = {
            "destination": "Japan",
            "departure_date": date(2025, 12, 15),
            "return_date": date(2025, 12, 22),
            "arrival_country": "JP"
        }
        travelers_data = {"ages": [30], "count": 1}
        preferences = {"adventure_sports": False}
        
        result = build_ancileo_quotation_json(trip_details, travelers_data, preferences)
        
        assert result["context"]["departureCountry"] == "SG"
    
    def test_string_date_formatting(self):
        """Test that string dates are handled correctly."""
        trip_details = {
            "destination": "Japan",
            "departure_date": "2025-12-15",
            "return_date": "2025-12-22",
            "departure_country": "SG",
            "arrival_country": "JP",
            "adults_count": 2,
            "children_count": 0
        }
        travelers_data = {"ages": [30, 35], "count": 2}
        preferences = {"adventure_sports": False}
        
        result = build_ancileo_quotation_json(trip_details, travelers_data, preferences)
        
        assert result["context"]["departureDate"] == "2025-12-15"
        assert result["context"]["returnDate"] == "2025-12-22"


class TestAncileoPurchaseJSONBuilder:
    """Test build_ancileo_purchase_json function."""
    
    def test_build_purchase_json_with_user_data(self):
        """Test building purchase JSON with user data."""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com"
        }
        
        result = build_ancileo_purchase_json(user_data)
        
        assert len(result["insureds"]) == 1
        assert result["insureds"][0]["id"] == "1"
        assert result["insureds"][0]["firstName"] == "John"
        assert result["insureds"][0]["lastName"] == "Doe"
        assert result["insureds"][0]["email"] == "john.doe@example.com"
        assert result["mainContact"]["id"] == "1"
        assert result["mainContact"]["firstName"] == "John"
        assert result["mainContact"]["lastName"] == "Doe"
        assert result["mainContact"]["email"] == "john.doe@example.com"
    
    def test_build_purchase_json_with_additional_travelers(self):
        """Test building purchase JSON with additional travelers."""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com"
        }
        additional_travelers = [
            {
                "firstName": "Jane",
                "lastName": "Doe",
                "email": "jane.doe@example.com"
            },
            {
                "first_name": "Bob",  # Test both naming conventions
                "last_name": "Smith"
            }
        ]
        
        result = build_ancileo_purchase_json(user_data, additional_travelers=additional_travelers)
        
        assert len(result["insureds"]) == 3
        assert result["insureds"][0]["id"] == "1"  # Primary
        assert result["insureds"][1]["id"] == "2"  # First additional
        assert result["insureds"][1]["firstName"] == "Jane"
        assert result["insureds"][2]["id"] == "3"  # Second additional
        assert result["insureds"][2]["firstName"] == "Bob"
        assert result["insureds"][2]["email"] == "john.doe@example.com"  # Defaults to primary's email
    
    def test_empty_user_data(self):
        """Test building purchase JSON with empty user data."""
        user_data = {
            "first_name": "",
            "last_name": "",
            "email": ""
        }
        
        result = build_ancileo_purchase_json(user_data)
        
        assert result["insureds"][0]["firstName"] == ""
        assert result["insureds"][0]["lastName"] == ""
        assert result["insureds"][0]["email"] == ""


class TestTripMetadataJSONBuilder:
    """Test build_trip_metadata_json function."""
    
    def test_build_basic_metadata(self):
        """Test building basic metadata JSON."""
        session_id = "test-session-123"
        user_id = "test-user-456"
        
        result = build_trip_metadata_json(session_id, user_id)
        
        assert result["session_id"] == session_id
        assert result["user_id"] == user_id
        assert "document_references" not in result
        assert "chat_history_references" not in result
        assert "conversation_flow" not in result
    
    def test_build_metadata_with_documents(self):
        """Test building metadata JSON with document references."""
        session_id = "test-session-123"
        user_id = "test-user-456"
        document_data = [
            {
                "document_id": "doc-1",
                "filename": "flight_confirmation.pdf",
                "file_path": "/uploads/flight_confirmation.pdf",
                "extracted_at": "2025-01-20T10:00:00",
                "extracted_json": {
                    "document_type": "flight_confirmation"
                }
            },
            {
                "document_id": "doc-2",
                "filename": "hotel_booking.pdf",
                "file_path": "/uploads/hotel_booking.pdf",
                "uploaded_at": "2025-01-20T11:00:00",
                "extracted_json": {
                    "document_type": "hotel_booking"
                }
            }
        ]
        
        result = build_trip_metadata_json(session_id, user_id, document_data=document_data)
        
        assert len(result["document_references"]) == 2
        assert result["document_references"][0]["document_id"] == "doc-1"
        assert result["document_references"][0]["document_type"] == "flight_confirmation"
        assert result["document_references"][0]["filename"] == "flight_confirmation.pdf"
        assert result["document_references"][1]["document_type"] == "hotel_booking"
    
    def test_build_metadata_with_conversation_flow(self):
        """Test building metadata JSON with conversation flow timestamps."""
        session_id = "test-session-123"
        user_id = "test-user-456"
        conversation_flow = {
            "started_at": "2025-01-20T09:00:00",
            "document_uploaded_at": "2025-01-20T10:00:00",
            "quote_generated_at": "2025-01-20T11:00:00"
        }
        
        result = build_trip_metadata_json(session_id, user_id, conversation_flow=conversation_flow)
        
        assert result["conversation_flow"]["started_at"] == "2025-01-20T09:00:00"
        assert result["conversation_flow"]["document_uploaded_at"] == "2025-01-20T10:00:00"
        assert result["conversation_flow"]["quote_generated_at"] == "2025-01-20T11:00:00"
    
    def test_build_metadata_complete(self):
        """Test building complete metadata JSON with all fields."""
        session_id = "test-session-123"
        user_id = "test-user-456"
        document_data = [
            {
                "document_id": "doc-1",
                "filename": "flight_confirmation.pdf",
                "file_path": "/uploads/flight_confirmation.pdf",
                "extracted_at": "2025-01-20T10:00:00",
                "extracted_json": {
                    "document_type": "flight_confirmation"
                }
            }
        ]
        chat_history_references = [
            {"message_id": "msg-1", "timestamp": "2025-01-20T09:00:00"},
            {"message_id": "msg-2", "timestamp": "2025-01-20T09:05:00"}
        ]
        conversation_flow = {
            "started_at": "2025-01-20T09:00:00"
        }
        
        result = build_trip_metadata_json(
            session_id,
            user_id,
            document_data=document_data,
            chat_history_references=chat_history_references,
            conversation_flow=conversation_flow
        )
        
        assert result["session_id"] == session_id
        assert result["user_id"] == user_id
        assert len(result["document_references"]) == 1
        assert len(result["chat_history_references"]) == 2
        assert "conversation_flow" in result
    
    def test_remove_none_values_from_document_references(self):
        """Test that None values are removed from document references."""
        session_id = "test-session-123"
        user_id = "test-user-456"
        document_data = [
            {
                "document_id": "doc-1",
                "filename": "flight_confirmation.pdf",
                "file_path": None,  # None value
                "extracted_at": None,  # None value
                "extracted_json": {
                    "document_type": "flight_confirmation"
                }
            }
        ]
        
        result = build_trip_metadata_json(session_id, user_id, document_data=document_data)
        
        doc_ref = result["document_references"][0]
        assert "file_path" not in doc_ref
        assert "extracted_at" not in doc_ref
        assert "document_id" in doc_ref
        assert "document_type" in doc_ref


