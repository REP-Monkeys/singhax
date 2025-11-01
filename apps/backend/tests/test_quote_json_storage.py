"""Tests for quote creation with JSON storage in pricing node."""

import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, MagicMock

from app.models.quote import Quote, QuoteStatus, ProductType
from app.models.trip import Trip
from app.models.user import User
from app.services.json_builders import build_ancileo_quotation_json, build_ancileo_purchase_json


class TestQuoteCreationWithJSONStorage:
    """Test quote creation with JSON structures in pricing node."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock(spec=Session)
        db.query = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        return db
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = Mock(spec=User)
        user.id = "user-123"
        user.first_name = "John"
        user.last_name = "Doe"
        user.email = "john.doe@example.com"
        return user
    
    @pytest.fixture
    def mock_trip(self):
        """Create mock trip."""
        trip = Mock(spec=Trip)
        trip.id = "trip-456"
        trip.user_id = "user-123"
        trip.session_id = "session-789"
        trip.destinations = ["Japan"]
        trip.total_cost = None
        return trip
    
    @pytest.fixture
    def mock_quote_result(self):
        """Create mock quote result from pricing service."""
        return {
            "success": True,
            "destination": "Japan",
            "quotes": {
                "standard": {
                    "tier": "standard",
                    "price": 50.00,
                    "currency": "SGD",
                    "coverage": {}
                },
                "elite": {
                    "tier": "elite",
                    "price": 90.00,
                    "currency": "SGD",
                    "coverage": {}
                },
                "premier": {
                    "tier": "premier",
                    "price": 125.00,
                    "currency": "SGD",
                    "coverage": {}
                }
            }
        }
    
    def test_create_quote_with_json_structures_new_quote(self, mock_db, mock_user, mock_trip, mock_quote_result):
        """Test creating a new quote with JSON structures."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_trip,  # Trip query
            None,  # Quote query (no existing quote)
            mock_user  # User query
        ]
        
        # Mock UUID conversion
        with patch('uuid.UUID') as mock_uuid:
            mock_uuid.side_effect = lambda x: x
            
            # Prepare state
            state = {
                "trip_id": "trip-456",
                "user_id": "user-123",
                "trip_details": {
                    "destination": "Japan",
                    "departure_date": date(2025, 12, 15),
                    "return_date": date(2025, 12, 22),
                    "departure_country": "SG",
                    "arrival_country": "JP",
                    "adults_count": 2,
                    "children_count": 0
                },
                "travelers_data": {
                    "ages": [30, 35],
                    "count": 2
                },
                "preferences": {
                    "adventure_sports": False
                },
                "quote_data": mock_quote_result
            }
            
            # Build JSON structures
            ancileo_quotation_json = build_ancileo_quotation_json(
                trip_details=state["trip_details"],
                travelers_data=state["travelers_data"],
                preferences=state["preferences"]
            )
            
            ancileo_purchase_json = build_ancileo_purchase_json(
                user_data={
                    "first_name": mock_user.first_name,
                    "last_name": mock_user.last_name,
                    "email": mock_user.email
                },
                travelers_data=state["travelers_data"]
            )
            
            # Create quote
            travelers_list = [{"age": age} for age in state["travelers_data"]["ages"]]
            activities_list = [{"type": "general"}]
            
            new_quote = Quote(
                user_id=mock_uuid(state["user_id"]),
                trip_id=mock_uuid(state["trip_id"]),
                product_type=ProductType.SINGLE,
                selected_tier="standard",
                travelers=travelers_list,
                activities=activities_list,
                price_min=Decimal("50.00"),
                price_max=Decimal("125.00"),
                currency="SGD",
                status=QuoteStatus.RANGED,
                ancileo_quotation_json=ancileo_quotation_json,
                ancileo_purchase_json=ancileo_purchase_json
            )
            
            # Verify JSON structures
            assert new_quote.ancileo_quotation_json is not None
            assert new_quote.ancileo_quotation_json["market"] == "SG"
            assert new_quote.ancileo_quotation_json["context"]["tripType"] == "RT"
            assert new_quote.ancileo_quotation_json["adventure_sports_activities"] is False
            
            assert new_quote.ancileo_purchase_json is not None
            assert len(new_quote.ancileo_purchase_json["insureds"]) == 1
            assert new_quote.ancileo_purchase_json["insureds"][0]["firstName"] == "John"
            
            assert new_quote.price_min == Decimal("50.00")
            assert new_quote.price_max == Decimal("125.00")
            assert new_quote.status == QuoteStatus.RANGED
    
    def test_update_existing_quote_with_json_structures(self, mock_db, mock_user, mock_trip, mock_quote_result):
        """Test updating an existing quote with JSON structures."""
        # Create existing quote
        existing_quote = Mock(spec=Quote)
        existing_quote.id = "quote-789"
        existing_quote.trip_id = "trip-456"
        existing_quote.user_id = "user-123"
        
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_trip,  # Trip query
            existing_quote,  # Quote query (existing quote found)
            mock_user  # User query
        ]
        
        with patch('uuid.UUID') as mock_uuid:
            mock_uuid.side_effect = lambda x: x
            
            # Prepare state
            state = {
                "trip_id": "trip-456",
                "user_id": "user-123",
                "trip_details": {
                    "destination": "Japan",
                    "departure_date": date(2025, 12, 15),
                    "return_date": date(2025, 12, 22),
                    "departure_country": "SG",
                    "arrival_country": "JP",
                    "adults_count": 2,
                    "children_count": 0
                },
                "travelers_data": {
                    "ages": [30, 35],
                    "count": 2
                },
                "preferences": {
                    "adventure_sports": True  # Changed to True
                },
                "quote_data": mock_quote_result
            }
            
            # Build JSON structures
            ancileo_quotation_json = build_ancileo_quotation_json(
                trip_details=state["trip_details"],
                travelers_data=state["travelers_data"],
                preferences=state["preferences"]
            )
            
            ancileo_purchase_json = build_ancileo_purchase_json(
                user_data={
                    "first_name": mock_user.first_name,
                    "last_name": mock_user.last_name,
                    "email": mock_user.email
                },
                travelers_data=state["travelers_data"]
            )
            
            # Update existing quote
            existing_quote.ancileo_quotation_json = ancileo_quotation_json
            existing_quote.ancileo_purchase_json = ancileo_purchase_json
            existing_quote.price_min = Decimal("50.00")
            existing_quote.price_max = Decimal("125.00")
            existing_quote.status = QuoteStatus.RANGED
            existing_quote.currency = "SGD"
            
            # Verify updates
            assert existing_quote.ancileo_quotation_json["adventure_sports_activities"] is True
            assert existing_quote.price_min == Decimal("50.00")
            assert existing_quote.price_max == Decimal("125.00")
            assert existing_quote.status == QuoteStatus.RANGED
    
    def test_json_structures_include_adventure_sports(self):
        """Test that JSON structures correctly include adventure_sports flag."""
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
        preferences = {"adventure_sports": True}
        
        quotation_json = build_ancileo_quotation_json(trip_details, travelers_data, preferences)
        
        assert quotation_json["adventure_sports_activities"] is True
        
        # Verify it's NOT in the context (should be separate field)
        assert "adventure_sports_activities" not in quotation_json["context"]
    
    def test_purchase_json_with_multiple_travelers(self):
        """Test purchase JSON with multiple travelers."""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com"
        }
        travelers_data = {"ages": [30, 35, 8], "count": 3}
        additional_travelers = [
            {"firstName": "Jane", "lastName": "Doe", "email": "jane@example.com"},
            {"firstName": "Bob", "lastName": "Doe"}
        ]
        
        purchase_json = build_ancileo_purchase_json(
            user_data,
            travelers_data=travelers_data,
            additional_travelers=additional_travelers
        )
        
        assert len(purchase_json["insureds"]) == 3
        assert purchase_json["insureds"][0]["id"] == "1"  # Primary
        assert purchase_json["insureds"][1]["id"] == "2"  # First additional
        assert purchase_json["insureds"][2]["id"] == "3"  # Second additional


