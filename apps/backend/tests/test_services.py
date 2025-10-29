"""Tests for additional services."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from app.services.claims import ClaimsService
from app.services.handoff import HandoffService


class TestClaimsService:
    """Test cases for claims service."""
    
    def test_get_claim_requirements_medical(self):
        """Test get claim requirements for medical claims."""
        service = ClaimsService()
        
        result = service.get_claim_requirements("medical")
        
        assert "required_documents" in result
        assert "required_info" in result
        assert len(result["required_documents"]) > 0
        assert len(result["required_info"]) > 0
    
    def test_get_claim_requirements_trip_delay(self):
        """Test get claim requirements for trip delay."""
        service = ClaimsService()
        
        result = service.get_claim_requirements("trip_delay")
        
        assert "required_documents" in result
        assert "required_info" in result
    
    def test_get_claim_requirements_baggage(self):
        """Test get claim requirements for baggage claims."""
        service = ClaimsService()
        
        result = service.get_claim_requirements("baggage")
        
        assert "required_documents" in result
        assert "required_info" in result
    
    def test_get_claim_requirements_theft(self):
        """Test get claim requirements for theft claims."""
        service = ClaimsService()
        
        result = service.get_claim_requirements("theft")
        
        assert "required_documents" in result
        assert "Police report" in result["required_documents"]
    
    def test_get_claim_requirements_cancellation(self):
        """Test get claim requirements for cancellation."""
        service = ClaimsService()
        
        result = service.get_claim_requirements("cancellation")
        
        assert "required_documents" in result
        assert "required_info" in result
    
    def test_get_claim_requirements_unknown_type(self):
        """Test get claim requirements for unknown type."""
        service = ClaimsService()
        
        result = service.get_claim_requirements("unknown_type")
        
        # Should return generic requirements
        assert "required_documents" in result
        assert "required_info" in result


class TestHandoffService:
    """Test cases for handoff service."""
    
    def test_create_handoff_request(self):
        """Test create handoff request."""
        mock_db = Mock()
        service = HandoffService()
        
        result = service.create_handoff_request(
            mock_db,
            "user-123",
            "complex_query",
            "User needs help with policy details"
        )
        
        assert result is not None
        assert "id" in result
        assert result["user_id"] == "user-123"
        assert result["reason"] == "complex_query"
        assert result["status"] == "pending"
    
    def test_get_handoff_reasons(self):
        """Test get handoff reasons."""
        service = HandoffService()
        
        reasons = service.get_handoff_reasons()
        
        assert len(reasons) > 0
        assert all("code" in r for r in reasons)
        assert all("description" in r for r in reasons)
    
    def test_update_handoff_status(self):
        """Test update handoff status."""
        mock_db = Mock()
        service = HandoffService()
        
        # First create a handoff
        handoff = service.create_handoff_request(
            mock_db,
            "user-123",
            "complaint",
            "Customer complaint"
        )
        
        # Update status
        result = service.update_handoff_status(
            mock_db,
            handoff["id"],
            "in_progress",
            "agent-456"
        )
        
        assert result is not None
        assert result["status"] == "in_progress"
        assert result["assigned_to"] == "agent-456"
    
    def test_get_pending_handoffs(self):
        """Test get pending handoffs."""
        mock_db = Mock()
        service = HandoffService()
        
        # Create some handoffs
        service.create_handoff_request(
            mock_db, "user-1", "complex_query", "Query 1"
        )
        service.create_handoff_request(
            mock_db, "user-2", "complaint", "Query 2"
        )
        
        result = service.get_pending_handoffs(mock_db)
        
        assert isinstance(result, list)
        assert len(result) >= 2


class TestServicesIntegration:
    """Integration tests for services."""
    
    def test_claims_service_all_types(self):
        """Test claims service with all known types."""
        service = ClaimsService()
        
        claim_types = [
            "medical",
            "trip_delay",
            "baggage",
            "theft",
            "cancellation",
            "emergency_evacuation"
        ]
        
        for claim_type in claim_types:
            result = service.get_claim_requirements(claim_type)
            assert "required_documents" in result
            assert "required_info" in result
    
    def test_handoff_service_workflow(self):
        """Test complete handoff workflow."""
        mock_db = Mock()
        service = HandoffService()
        
        # Step 1: Create handoff
        handoff = service.create_handoff_request(
            mock_db,
            "user-123",
            "complex_query",
            "Customer needs detailed explanation"
        )
        
        assert handoff["status"] == "pending"
        
        # Step 2: Assign to agent
        updated = service.update_handoff_status(
            mock_db,
            handoff["id"],
            "in_progress",
            "agent-456"
        )
        
        assert updated["status"] == "in_progress"
        assert updated["assigned_to"] == "agent-456"
        
        # Step 3: Resolve
        resolved = service.update_handoff_status(
            mock_db,
            handoff["id"],
            "resolved",
            "agent-456"
        )
        
        assert resolved["status"] == "resolved"



