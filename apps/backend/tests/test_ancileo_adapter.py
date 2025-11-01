"""Tests for Ancileo MSIG adapter and client."""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from app.adapters.insurer.ancileo_adapter import AncileoAdapter, TIER_MULTIPLIERS
from app.adapters.insurer.ancileo_client import (
    AncileoClient,
    AncileoAPIError,
    AncileoQuoteExpiredError
)


class TestAncileoClient:
    """Tests for AncileoClient HTTP client."""
    
    def test_client_initialization(self):
        """Test client initializes with default settings."""
        client = AncileoClient()
        assert client.api_key is not None  # From settings
        assert client.base_url == "https://dev.api.ancileo.com"
        assert client.timeout == 30
        assert client.session is not None
    
    def test_client_initialization_with_custom_params(self):
        """Test client accepts custom parameters."""
        client = AncileoClient(
            api_key="test-key",
            base_url="https://test.api.com",
            timeout=60
        )
        assert client.api_key == "test-key"
        assert client.base_url == "https://test.api.com"
        assert client.timeout == 60
    
    @patch('app.adapters.insurer.ancileo_client.requests.Session')
    def test_quotation_round_trip_success(self, mock_session):
        """Test successful quotation API call for round trip."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"quoteId": "test-quote-123"}'  # Add text attribute
        mock_response.json.return_value = {
            "quoteId": "test-quote-123",
            "offers": [{
                "offerId": "test-offer-456",
                "productCode": "SG_AXA_SCOOT_COMP",
                "unitPrice": 100.50,
                "currency": "SGD"
            }]
        }
        mock_session_instance = Mock()
        mock_session_instance.request.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        client = AncileoClient(api_key="test-key")
        client.session = mock_session_instance
        
        # Call quotation
        departure = date.today() + timedelta(days=30)
        return_date = departure + timedelta(days=10)
        
        result = client.get_quotation(
            trip_type="RT",
            departure_date=departure,
            return_date=return_date,
            departure_country="SG",
            arrival_country="JP",
            adults_count=1,
            children_count=0
        )
        
        assert result["quoteId"] == "test-quote-123"
        assert len(result["offers"]) == 1
        assert result["offers"][0]["unitPrice"] == 100.50
        
        # Verify API call was made
        mock_session_instance.request.assert_called_once()
        call_args = mock_session_instance.request.call_args
        assert call_args[1]["method"] == "POST"
        assert "/v1/travel/front/pricing" in call_args[1]["url"]
        
        # Verify payload structure
        payload = call_args[1]["json"]
        assert payload["market"] == "SG"
        assert payload["context"]["tripType"] == "RT"
        assert payload["context"]["returnDate"] == return_date.strftime("%Y-%m-%d")
    
    @patch('app.adapters.insurer.ancileo_client.requests.Session')
    def test_quotation_single_trip_omits_return_date(self, mock_session):
        """Test single trip request does not include returnDate."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"quoteId": "test-quote-789"}'  # Add text attribute
        mock_response.json.return_value = {
            "quoteId": "test-quote-789",
            "offers": [{"offerId": "test-offer-789", "unitPrice": 50.0}]
        }
        mock_session_instance = Mock()
        mock_session_instance.request.return_value = mock_response
        
        client = AncileoClient(api_key="test-key")
        client.session = mock_session_instance
        
        departure = date.today() + timedelta(days=30)
        
        result = client.get_quotation(
            trip_type="ST",
            departure_date=departure,
            return_date=None,  # Should be omitted from payload
            departure_country="SG",
            arrival_country="TH",
            adults_count=1,
            children_count=0
        )
        
        # Verify payload does NOT contain returnDate
        call_args = mock_session_instance.request.call_args
        payload = call_args[1]["json"]
        assert "returnDate" not in payload["context"]
        assert payload["context"]["tripType"] == "ST"
    
    def test_quotation_validates_trip_type(self):
        """Test quotation rejects invalid trip type."""
        client = AncileoClient(api_key="test-key")
        departure = date.today() + timedelta(days=30)
        
        with pytest.raises(ValueError, match="Invalid trip_type"):
            client.get_quotation(
                trip_type="INVALID",
                departure_date=departure,
                return_date=None,
                departure_country="SG",
                arrival_country="JP",
                adults_count=1,
                children_count=0
            )
    
    def test_quotation_validates_round_trip_requires_return_date(self):
        """Test round trip requires return date."""
        client = AncileoClient(api_key="test-key")
        departure = date.today() + timedelta(days=30)
        
        with pytest.raises(ValueError, match="return_date is required"):
            client.get_quotation(
                trip_type="RT",
                departure_date=departure,
                return_date=None,
                departure_country="SG",
                arrival_country="JP",
                adults_count=1,
                children_count=0
            )
    
    def test_quotation_validates_future_dates(self):
        """Test quotation rejects past dates."""
        client = AncileoClient(api_key="test-key")
        past_date = date.today() - timedelta(days=1)
        
        with pytest.raises(ValueError, match="must be in the future"):
            client.get_quotation(
                trip_type="ST",
                departure_date=past_date,
                return_date=None,
                departure_country="SG",
                arrival_country="JP",
                adults_count=1,
                children_count=0
            )
    
    def test_quotation_validates_return_after_departure(self):
        """Test return date must be after departure."""
        client = AncileoClient(api_key="test-key")
        departure = date.today() + timedelta(days=30)
        bad_return = departure - timedelta(days=1)
        
        with pytest.raises(ValueError, match="must be after departure"):
            client.get_quotation(
                trip_type="RT",
                departure_date=departure,
                return_date=bad_return,
                departure_country="SG",
                arrival_country="JP",
                adults_count=1,
                children_count=0
            )
    
    def test_quotation_validates_adults_count(self):
        """Test at least 1 adult required."""
        client = AncileoClient(api_key="test-key")
        departure = date.today() + timedelta(days=30)
        
        with pytest.raises(ValueError, match="adults_count must be at least 1"):
            client.get_quotation(
                trip_type="ST",
                departure_date=departure,
                return_date=None,
                departure_country="SG",
                arrival_country="JP",
                adults_count=0,
                children_count=2
            )
    
    @patch('app.adapters.insurer.ancileo_client.requests.Session')
    def test_quotation_handles_401_error(self, mock_session):
        """Test quotation handles 401 authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"
        mock_session_instance = Mock()
        mock_session_instance.request.return_value = mock_response
        
        client = AncileoClient(api_key="invalid-key")
        client.session = mock_session_instance
        
        departure = date.today() + timedelta(days=30)
        
        with pytest.raises(AncileoAPIError, match="Authentication failed"):
            client.get_quotation(
                trip_type="ST",
                departure_date=departure,
                return_date=None,
                departure_country="SG",
                arrival_country="JP",
                adults_count=1,
                children_count=0
            )
    
    @patch('app.adapters.insurer.ancileo_client.requests.Session')
    def test_quotation_handles_404_expired_quote(self, mock_session):
        """Test quotation handles 404 as quote expired."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Quote not found"
        mock_session_instance = Mock()
        mock_session_instance.request.return_value = mock_response
        
        client = AncileoClient(api_key="test-key")
        client.session = mock_session_instance
        
        departure = date.today() + timedelta(days=30)
        
        with pytest.raises(AncileoQuoteExpiredError, match="Quote not found or expired"):
            client.get_quotation(
                trip_type="ST",
                departure_date=departure,
                return_date=None,
                departure_country="SG",
                arrival_country="JP",
                adults_count=1,
                children_count=0
            )
    
    @patch('app.adapters.insurer.ancileo_client.requests.Session')
    def test_purchase_api_success(self, mock_session):
        """Test successful purchase API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"policyNumber": "POL-ABC123"}'  # Add text attribute
        mock_response.json.return_value = {
            "policyNumber": "POL-ABC123",
            "status": "active"
        }
        mock_session_instance = Mock()
        mock_session_instance.request.return_value = mock_response
        
        client = AncileoClient(api_key="test-key")
        client.session = mock_session_instance
        
        insureds = [{
            "id": "1",
            "title": "Mr",
            "firstName": "John",
            "lastName": "Doe",
            "nationality": "SG",
            "dateOfBirth": "1990-01-01",
            "passport": "E1234567",
            "email": "john@example.com",
            "phoneType": "mobile",
            "phoneNumber": "6581234567",
            "relationship": "main"
        }]
        
        main_contact = {
            **insureds[0],
            "address": "123 Test St",
            "city": "Singapore",
            "zipCode": "123456",
            "countryCode": "SG"
        }
        
        result = client.create_purchase(
            quote_id="quote-123",
            offer_id="offer-456",
            product_code="SG_AXA_SCOOT_COMP",
            unit_price=100.50,
            insureds=insureds,
            main_contact=main_contact
        )
        
        assert result["policyNumber"] == "POL-ABC123"
        
        # Verify API call
        call_args = mock_session_instance.request.call_args
        payload = call_args[1]["json"]
        assert payload["quoteId"] == "quote-123"
        assert payload["purchaseOffers"][0]["offerId"] == "offer-456"
        assert payload["purchaseOffers"][0]["isSendEmail"] is True
        assert len(payload["insureds"]) == 1
        assert payload["mainContact"]["address"] == "123 Test St"


class TestAncileoAdapter:
    """Tests for AncileoAdapter."""
    
    def test_adapter_initialization(self):
        """Test adapter initializes with client."""
        adapter = AncileoAdapter()
        assert adapter.client is not None
        assert isinstance(adapter.client, AncileoClient)
    
    def test_get_products_returns_three_tiers(self):
        """Test get_products returns 3 tier definitions."""
        adapter = AncileoAdapter()
        products = adapter.get_products({})
        
        assert len(products) == 3
        tiers = [p["tier"] for p in products]
        assert "standard" in tiers
        assert "elite" in tiers
        assert "premier" in tiers
        
        # Verify each has coverage details
        for product in products:
            assert "coverage" in product
            assert "medical_coverage" in product["coverage"]
    
    @patch.object(AncileoClient, 'get_quotation')
    def test_price_firm_calculates_tiers_correctly(self, mock_quotation):
        """Test price_firm calculates all 3 tiers from Ancileo price."""
        # Mock Ancileo response
        mock_quotation.return_value = {
            "quoteId": "test-quote-123",
            "offers": [{
                "offerId": "test-offer-456",
                "productCode": "SG_AXA_SCOOT_COMP",
                "unitPrice": 180.0,  # Elite price
                "currency": "SGD"
            }]
        }
        
        adapter = AncileoAdapter()
        departure = date.today() + timedelta(days=30)
        return_date = departure + timedelta(days=10)
        
        result = adapter.price_firm({
            "trip_type": "RT",
            "departure_date": departure,
            "return_date": return_date,
            "departure_country": "SG",
            "arrival_country": "JP",
            "adults_count": 1,
            "children_count": 0
        })
        
        # Verify result structure
        assert result["eligibility"] is True
        assert result["currency"] == "SGD"
        assert "tiers" in result
        assert "ancileo_reference" in result
        
        # Verify tier calculations
        tiers = result["tiers"]
        assert len(tiers) == 3
        
        # Elite = 180.0 (from Ancileo)
        assert tiers["elite"]["price"] == 180.0
        assert tiers["elite"]["multiplier"] == 1.0
        
        # Standard = 180.0 / 1.8 = 100.0
        assert tiers["standard"]["price"] == 100.0
        assert abs(tiers["standard"]["multiplier"] - (1.0 / 1.8)) < 0.001
        
        # Premier = 180.0 * 1.39 = 250.2
        assert tiers["premier"]["price"] == 250.2
        assert tiers["premier"]["multiplier"] == 1.39
        
        # Verify Ancileo reference
        ref = result["ancileo_reference"]
        assert ref["quote_id"] == "test-quote-123"
        assert ref["offer_id"] == "test-offer-456"
        assert ref["product_code"] == "SG_AXA_SCOOT_COMP"
        assert ref["base_price"] == 180.0
    
    @patch.object(AncileoClient, 'get_quotation')
    def test_tier_multipliers_are_correct(self, mock_quotation):
        """Test tier multiplier math is exact."""
        mock_quotation.return_value = {
            "quoteId": "test-quote",
            "offers": [{"offerId": "test-offer", "productCode": "TEST", "unitPrice": 100.0}]
        }
        
        adapter = AncileoAdapter()
        departure = date.today() + timedelta(days=30)
        
        result = adapter.price_firm({
            "trip_type": "ST",
            "departure_date": departure,
            "return_date": None,
            "departure_country": "SG",
            "arrival_country": "TH",
            "adults_count": 1,
            "children_count": 0
        })
        
        tiers = result["tiers"]
        
        # Elite = 100.0
        elite_price = tiers["elite"]["price"]
        assert elite_price == 100.0
        
        # Standard should be exactly Elite / 1.8
        standard_price = tiers["standard"]["price"]
        expected_standard = round(100.0 / 1.8, 2)
        assert standard_price == expected_standard
        
        # Premier should be exactly Elite * 1.39
        premier_price = tiers["premier"]["price"]
        expected_premier = round(100.0 * 1.39, 2)
        assert premier_price == expected_premier
    
    @patch.object(AncileoClient, 'get_quotation')
    def test_price_firm_handles_api_error(self, mock_quotation):
        """Test price_firm handles API errors gracefully."""
        mock_quotation.side_effect = AncileoAPIError("API down")
        
        adapter = AncileoAdapter()
        departure = date.today() + timedelta(days=30)
        
        result = adapter.price_firm({
            "trip_type": "ST",
            "departure_date": departure,
            "return_date": None,
            "departure_country": "SG",
            "arrival_country": "JP",
            "adults_count": 1,
            "children_count": 0
        })
        
        # Should return error response
        assert result["eligibility"] is False
        assert "error" in result["breakdown"]
        assert result["tiers"] == {}
    
    @patch.object(AncileoClient, 'create_purchase')
    def test_bind_policy_calls_purchase_api(self, mock_purchase):
        """Test bind_policy calls Ancileo Purchase API."""
        mock_purchase.return_value = {
            "policyNumber": "POL-TEST123"
        }
        
        adapter = AncileoAdapter()
        
        ancileo_ref = {
            "quote_id": "test-quote",
            "offer_id": "test-offer",
            "product_code": "SG_AXA_SCOOT_COMP",
            "base_price": 180.0
        }
        
        insureds = [{
            "id": "1",
            "title": "Mr",
            "firstName": "John",
            "lastName": "Doe",
            "nationality": "SG",
            "dateOfBirth": "1990-01-01",
            "passport": "E1234567",
            "email": "john@example.com",
            "phoneType": "mobile",
            "phoneNumber": "6581234567",
            "relationship": "main"
        }]
        
        main_contact = {**insureds[0], "address": "123 St", "city": "Singapore", "zipCode": "12345", "countryCode": "SG"}
        
        result = adapter.bind_policy({
            "ancileo_reference": ancileo_ref,
            "selected_tier": "elite",
            "insureds": insureds,
            "main_contact": main_contact
        })
        
        assert result["policy_number"] == "POL-TEST123"
        assert result["selected_tier"] == "elite"
        
        # Verify purchase API was called
        mock_purchase.assert_called_once_with(
            quote_id="test-quote",
            offer_id="test-offer",
            product_code="SG_AXA_SCOOT_COMP",
            unit_price=180.0,
            insureds=insureds,
            main_contact=main_contact
        )
    
    @patch.object(AncileoClient, 'create_purchase')
    def test_bind_policy_calculates_tier_price(self, mock_purchase):
        """Test bind_policy calculates actual price for selected tier."""
        mock_purchase.return_value = {"policyNumber": "POL-TEST"}
        
        adapter = AncileoAdapter()
        
        ancileo_ref = {
            "quote_id": "test-quote",
            "offer_id": "test-offer",
            "product_code": "TEST",
            "base_price": 100.0  # Elite price
        }
        
        insureds = [{"id": "1", "title": "Mr", "firstName": "Test", "lastName": "User", 
                     "nationality": "SG", "dateOfBirth": "1990-01-01", "passport": "E123",
                     "email": "test@test.com", "phoneType": "mobile", "phoneNumber": "123",
                     "relationship": "main"}]
        main_contact = {**insureds[0], "address": "123", "city": "SG", "zipCode": "12345", "countryCode": "SG"}
        
        # Test standard tier
        result = adapter.bind_policy({
            "ancileo_reference": ancileo_ref,
            "selected_tier": "standard",
            "insureds": insureds,
            "main_contact": main_contact
        })
        
        # Standard = 100 / 1.8 = 55.56
        expected_standard = round(100.0 / 1.8, 2)
        assert result["actual_price"] == expected_standard
    
    def test_claim_requirements_returns_valid_data(self):
        """Test claim_requirements returns expected structure."""
        adapter = AncileoAdapter()
        
        # Test each claim type
        claim_types = ["trip_delay", "medical", "baggage", "theft", "cancellation"]
        
        for claim_type in claim_types:
            result = adapter.claim_requirements(claim_type)
            assert "required_documents" in result
            assert "required_info" in result
            assert isinstance(result["required_documents"], list)
            assert isinstance(result["required_info"], list)
            assert len(result["required_documents"]) > 0


class TestTierCalculationMath:
    """Specific tests for tier calculation accuracy."""
    
    def test_tier_multipliers_values(self):
        """Test tier multiplier constants are correct."""
        assert TIER_MULTIPLIERS["standard"] == 1.0 / 1.8
        assert TIER_MULTIPLIERS["elite"] == 1.0
        assert TIER_MULTIPLIERS["premier"] == 1.39
        
        # Verify math
        assert abs(TIER_MULTIPLIERS["standard"] - 0.5555555) < 0.0001
    
    def test_tier_price_calculations_with_real_examples(self):
        """Test tier calculations with realistic prices."""
        test_cases = [
            # (elite_price, expected_standard, expected_premier)
            (100.0, 55.56, 139.0),
            (180.0, 100.0, 250.2),
            (378.0, 210.0, 525.42),
            (50.0, 27.78, 69.5),
        ]
        
        for elite, expected_std, expected_prem in test_cases:
            # Calculate
            standard = round(elite * TIER_MULTIPLIERS["standard"], 2)
            premier = round(elite * TIER_MULTIPLIERS["premier"], 2)
            
            # Verify
            assert standard == expected_std, f"Standard calculation failed for elite={elite}"
            assert premier == expected_prem, f"Premier calculation failed for elite={elite}"
    
    def test_tier_ordering_is_correct(self):
        """Test Standard < Elite < Premier."""
        elite_price = 100.0
        standard = elite_price * TIER_MULTIPLIERS["standard"]
        premier = elite_price * TIER_MULTIPLIERS["premier"]
        
        assert standard < elite_price < premier

