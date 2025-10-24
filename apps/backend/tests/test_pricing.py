"""Tests for pricing service."""

import pytest
from decimal import Decimal
from app.services.pricing import PricingService
from app.adapters.insurer.mock import MockInsurerAdapter


class TestPricingService:
    """Test cases for pricing service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pricing_service = PricingService()
        self.mock_adapter = MockInsurerAdapter()
        self.pricing_service.adapter = self.mock_adapter
    
    def test_calculate_quote_range_success(self):
        """Test successful quote range calculation."""
        travelers = [
            {"name": "John Doe", "age": 35, "is_primary": True},
            {"name": "Jane Doe", "age": 32, "is_primary": False}
        ]
        activities = [
            {"type": "sightseeing", "description": "City tours"},
            {"type": "hiking", "description": "Mountain hiking"}
        ]
        
        result = self.pricing_service.calculate_quote_range(
            "basic_travel",
            travelers,
            activities,
            7,
            ["France", "Italy"]
        )
        
        assert result["success"] is True
        assert result["price_min"] is not None
        assert result["price_max"] is not None
        assert result["price_min"] < result["price_max"]
        assert result["currency"] == "USD"
        assert "breakdown" in result
    
    def test_calculate_quote_range_error(self):
        """Test quote range calculation with error."""
        # Mock adapter to return error
        self.pricing_service.adapter = None
        
        result = self.pricing_service.calculate_quote_range(
            "invalid_product",
            [],
            [],
            0,
            []
        )
        
        assert result["success"] is False
        assert "error" in result
        assert result["price_min"] is None
        assert result["price_max"] is None
    
    def test_calculate_firm_price_success(self):
        """Test successful firm price calculation."""
        travelers = [
            {"name": "John Doe", "age": 35, "is_primary": True}
        ]
        activities = [
            {"type": "sightseeing", "description": "City tours"}
        ]
        risk_factors = {
            "total_risk_score": 0.1,
            "age_risk": 0.0,
            "activity_risk": 0.1,
            "destination_risk": 0.0
        }
        
        result = self.pricing_service.calculate_firm_price(
            "basic_travel",
            travelers,
            activities,
            7,
            ["France"],
            risk_factors
        )
        
        assert result["success"] is True
        assert result["price"] is not None
        assert result["price"] > 0
        assert result["currency"] == "USD"
        assert result["eligibility"] is True
        assert "breakdown" in result
    
    def test_calculate_trip_duration(self):
        """Test trip duration calculation."""
        from datetime import date
        
        start_date = date(2024, 3, 15)
        end_date = date(2024, 3, 22)
        
        duration = self.pricing_service.calculate_trip_duration(start_date, end_date)
        
        assert duration == 8  # 7 days + 1
    
    def test_assess_risk_factors(self):
        """Test risk factor assessment."""
        travelers = [
            {"name": "John Doe", "age": 35, "preexisting_conditions": []},
            {"name": "Jane Doe", "age": 70, "preexisting_conditions": ["diabetes"]}
        ]
        activities = [
            {"type": "skiing", "description": "Downhill skiing"},
            {"type": "sightseeing", "description": "City tours"}
        ]
        destinations = ["France", "war_zone"]
        
        risk_factors = self.pricing_service.assess_risk_factors(
            travelers, activities, destinations
        )
        
        assert "age_risk" in risk_factors
        assert "activity_risk" in risk_factors
        assert "destination_risk" in risk_factors
        assert "preexisting_conditions" in risk_factors
        assert "total_risk_score" in risk_factors
        
        # Should have some risk due to age and activities
        assert risk_factors["total_risk_score"] > 0
    
    def test_get_price_breakdown_explanation(self):
        """Test price breakdown explanation generation."""
        price = Decimal("125.50")
        breakdown = {
            "base_rate": 75.00,
            "age_loading": 0.0,
            "activity_loading": 0.2,
            "destination_loading": 0.1,
            "fees": 5.00,
            "tax": 10.05
        }
        risk_factors = {
            "age_risk": 0.0,
            "activity_risk": 0.2,
            "destination_risk": 0.1,
            "preexisting_conditions": 0.0
        }
        
        explanation = self.pricing_service.get_price_breakdown_explanation(
            price, breakdown, risk_factors
        )
        
        assert "Base rate" in explanation
        assert "Activity risk loading" in explanation
        assert "Destination risk loading" in explanation
        assert "Fees" in explanation
        assert "Tax" in explanation
