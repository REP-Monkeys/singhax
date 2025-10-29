"""Tests for conversation tools."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from app.agents.tools import ConversationTools
from app.schemas.rag import RagSearchRequest, RagSearchResponse, RagDocumentResponse


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return Mock()


@pytest.fixture
def mock_services():
    """Create mocked services."""
    with patch('app.agents.tools.PricingService') as mock_pricing, \
         patch('app.agents.tools.RagService') as mock_rag, \
         patch('app.agents.tools.ClaimsService') as mock_claims, \
         patch('app.agents.tools.HandoffService') as mock_handoff:
        
        yield {
            'pricing': mock_pricing.return_value,
            'rag': mock_rag.return_value,
            'claims': mock_claims.return_value,
            'handoff': mock_handoff.return_value
        }


class TestConversationTools:
    """Test cases for conversation tools."""
    
    def test_init(self, mock_db):
        """Test tools initialization."""
        tools = ConversationTools(mock_db)
        
        assert tools.db == mock_db
        assert tools.pricing_service is not None
        assert tools.rag_service is not None
        assert tools.claims_service is not None
        assert tools.handoff_service is not None
    
    def test_get_quote_range(self, mock_db, mock_services):
        """Test get quote range."""
        mock_services['pricing'].calculate_quote_range.return_value = {
            "success": True,
            "price_min": 100.0,
            "price_max": 150.0,
            "currency": "USD"
        }
        
        tools = ConversationTools(mock_db)
        tools.pricing_service = mock_services['pricing']
        
        result = tools.get_quote_range(
            "basic_travel",
            [{"name": "John", "age": 35}],
            [{"type": "sightseeing"}],
            7,
            ["France"]
        )
        
        assert result["success"] is True
        assert result["price_min"] == 100.0
        assert result["price_max"] == 150.0
        mock_services['pricing'].calculate_quote_range.assert_called_once()
    
    def test_get_firm_price(self, mock_db, mock_services):
        """Test get firm price."""
        mock_services['pricing'].calculate_firm_price.return_value = {
            "success": True,
            "price": 125.0,
            "currency": "USD"
        }
        
        tools = ConversationTools(mock_db)
        tools.pricing_service = mock_services['pricing']
        
        result = tools.get_firm_price(
            "basic_travel",
            [{"name": "John", "age": 35}],
            [{"type": "sightseeing"}],
            7,
            ["France"],
            {"total_risk_score": 0.1}
        )
        
        assert result["success"] is True
        assert result["price"] == 125.0
        mock_services['pricing'].calculate_firm_price.assert_called_once()
    
    def test_search_policy_documents(self, mock_db, mock_services):
        """Test search policy documents."""
        from uuid import uuid4
        mock_doc = RagDocumentResponse(
            id=uuid4(),
            title="Test Policy",
            insurer_name="Test Insurer",
            product_code="TEST",
            section_id="1.1",
            heading="Test Section",
            text="Test content",
            citations={"section": "1.1"}
        )
        
        mock_response = RagSearchResponse(
            query="test query",
            documents=[mock_doc],
            total_results=1,
            search_method="text"
        )
        
        mock_services['rag'].search_documents.return_value = mock_response
        
        tools = ConversationTools(mock_db)
        tools.rag_service = mock_services['rag']
        
        result = tools.search_policy_documents("test query")
        
        assert result["success"] is True
        assert len(result["results"]) == 1
        assert result["results"][0]["title"] == "Test Policy"
        assert result["results"][0]["text"] == "Test content"
    
    def test_get_claim_requirements(self, mock_db, mock_services):
        """Test get claim requirements."""
        mock_services['claims'].get_claim_requirements.return_value = {
            "required_documents": ["Police report", "Receipt"],
            "required_info": ["Date", "Location"]
        }
        
        tools = ConversationTools(mock_db)
        tools.claims_service = mock_services['claims']
        
        result = tools.get_claim_requirements("theft")
        
        assert result["success"] is True
        assert "required_documents" in result["requirements"]
        assert "required_info" in result["requirements"]
        mock_services['claims'].get_claim_requirements.assert_called_once_with("theft")
    
    def test_create_handoff_request(self, mock_db, mock_services):
        """Test create handoff request."""
        mock_handoff = {
            "id": "handoff-123",
            "user_id": "user-123",
            "reason": "complex_query",
            "status": "pending"
        }
        
        mock_services['handoff'].create_handoff_request.return_value = mock_handoff
        
        tools = ConversationTools(mock_db)
        tools.handoff_service = mock_services['handoff']
        
        result = tools.create_handoff_request(
            "user-123",
            "complex_query",
            "User needs help with complex policy question"
        )
        
        assert result["success"] is True
        assert result["handoff_request"]["id"] == "handoff-123"
        mock_services['handoff'].create_handoff_request.assert_called_once()
    
    def test_assess_risk_factors(self, mock_db, mock_services):
        """Test assess risk factors."""
        mock_services['pricing'].assess_risk_factors.return_value = {
            "age_risk": 0.1,
            "activity_risk": 0.2,
            "destination_risk": 0.0,
            "total_risk_score": 0.3
        }
        
        tools = ConversationTools(mock_db)
        tools.pricing_service = mock_services['pricing']
        
        result = tools.assess_risk_factors(
            [{"age": 65}],
            [{"type": "skiing"}],
            ["France"]
        )
        
        assert result["age_risk"] == 0.1
        assert result["activity_risk"] == 0.2
        assert result["total_risk_score"] == 0.3
    
    def test_get_price_breakdown_explanation(self, mock_db, mock_services):
        """Test get price breakdown explanation."""
        mock_services['pricing'].get_price_breakdown_explanation.return_value = (
            "Base rate: $75.00\nActivity loading: $15.00\nTotal: $90.00"
        )
        
        tools = ConversationTools(mock_db)
        tools.pricing_service = mock_services['pricing']
        
        result = tools.get_price_breakdown_explanation(
            90.0,
            {"base_rate": 75.0, "activity_loading": 15.0},
            {"activity_risk": 0.2}
        )
        
        assert "Base rate" in result
        assert "$75.00" in result
        mock_services['pricing'].get_price_breakdown_explanation.assert_called_once()
    
    def test_get_available_products(self, mock_db, mock_services):
        """Test get available products."""
        mock_adapter = Mock()
        mock_adapter.get_products.return_value = [
            {"code": "basic_travel", "name": "Basic Travel Insurance"},
            {"code": "premium_travel", "name": "Premium Travel Insurance"}
        ]
        
        mock_services['pricing'].adapter = mock_adapter
        
        tools = ConversationTools(mock_db)
        tools.pricing_service = mock_services['pricing']
        
        result = tools.get_available_products()
        
        assert len(result) == 2
        assert result[0]["code"] == "basic_travel"
        assert result[1]["code"] == "premium_travel"
    
    def test_get_handoff_reasons(self, mock_db, mock_services):
        """Test get handoff reasons."""
        mock_services['handoff'].get_handoff_reasons.return_value = [
            {"code": "complex_query", "description": "Complex question"},
            {"code": "complaint", "description": "Customer complaint"}
        ]
        
        tools = ConversationTools(mock_db)
        tools.handoff_service = mock_services['handoff']
        
        result = tools.get_handoff_reasons()
        
        assert len(result) == 2
        assert result[0]["code"] == "complex_query"
        assert result[1]["code"] == "complaint"


class TestToolsIntegration:
    """Integration tests for tools with real services."""
    
    def test_tools_with_real_pricing_service(self, mock_db):
        """Test tools with real pricing service."""
        tools = ConversationTools(mock_db)
        
        result = tools.assess_risk_factors(
            [{"age": 35}],
            [{"type": "sightseeing"}],
            ["France"]
        )
        
        assert "age_risk" in result
        assert "activity_risk" in result
        assert "destination_risk" in result
        assert "total_risk_score" in result
    
    def test_tools_with_real_claims_service(self, mock_db):
        """Test tools with real claims service."""
        tools = ConversationTools(mock_db)
        
        result = tools.get_claim_requirements("medical")
        
        assert result["success"] is True
        assert "required_documents" in result["requirements"]
        assert "required_info" in result["requirements"]

