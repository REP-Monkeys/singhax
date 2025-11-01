"""Integration tests for Ancileo MSIG API integration."""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from app.services.pricing import PricingService
from app.services.geo_mapping import GeoMapper
from app.adapters.insurer.ancileo_adapter import AncileoAdapter
from app.adapters.insurer.ancileo_client import AncileoClient, AncileoAPIError


class TestPricingServiceIntegration:
    """Integration tests for PricingService with Ancileo adapter."""
    
    @patch.object(AncileoClient, 'get_quotation')
    def test_calculate_step1_quote_with_ancileo(self, mock_quotation):
        """Test calculate_step1_quote integrates with Ancileo API."""
        # Mock Ancileo API response
        mock_quotation.return_value = {
            "quoteId": "integration-test-quote-123",
            "offers": [{
                "offerId": "integration-test-offer-456",
                "productCode": "SG_AXA_SCOOT_COMP",
                "unitPrice": 378.0,
                "currency": "SGD",
                "coverageDetails": {
                    "medical": 500000,
                    "cancellation": 12500
                }
            }]
        }
        
        service = PricingService()
        
        departure = date.today() + timedelta(days=30)
        return_date = departure + timedelta(days=10)
        
        result = service.calculate_step1_quote(
            destination="Japan",
            departure_date=departure,
            return_date=return_date,
            travelers_ages=[30, 8],
            adventure_sports=False
        )
        
        # Verify success
        assert result["success"] is True
        assert result["destination"] == "Japan"
        
        # Verify quotes returned
        assert "quotes" in result
        assert len(result["quotes"]) == 3  # Standard, Elite, Premier
        
        # Verify Elite price matches Ancileo
        assert result["quotes"]["elite"]["price"] == 378.0
        
        # Verify Standard calculation
        expected_standard = round(378.0 / 1.8, 2)
        assert result["quotes"]["standard"]["price"] == expected_standard
        
        # Verify Premier calculation
        expected_premier = round(378.0 * 1.39, 2)
        assert result["quotes"]["premier"]["price"] == expected_premier
        
        # Verify Ancileo reference is stored
        assert "ancileo_reference" in result
        assert result["ancileo_reference"]["quote_id"] == "integration-test-quote-123"
        assert result["ancileo_reference"]["offer_id"] == "integration-test-offer-456"
        
        # Verify API was called with correct params
        mock_quotation.assert_called_once()
        call_args = mock_quotation.call_args
        assert call_args[1]["trip_type"] == "RT"
        assert call_args[1]["departure_country"] == "SG"
        assert call_args[1]["arrival_country"] == "JP"
        assert call_args[1]["adults_count"] == 1  # 1 adult
        assert call_args[1]["children_count"] == 1  # 1 child
    
    @patch.object(AncileoClient, 'get_quotation')
    def test_adventure_sports_filters_standard_tier(self, mock_quotation):
        """Test adventure sports requirement filters out standard tier."""
        mock_quotation.return_value = {
            "quoteId": "test-quote",
            "offers": [{"offerId": "test-offer", "productCode": "TEST", "unitPrice": 200.0}]
        }
        
        service = PricingService()
        departure = date.today() + timedelta(days=30)
        return_date = departure + timedelta(days=10)
        
        result = service.calculate_step1_quote(
            destination="Thailand",
            departure_date=departure,
            return_date=return_date,
            travelers_ages=[25],
            adventure_sports=True  # Requires adventure coverage
        )
        
        assert result["success"] is True
        
        # Standard should be filtered out (doesn't support adventure sports)
        assert "standard" not in result["quotes"]
        
        # Elite and Premier should remain
        assert "elite" in result["quotes"]
        assert "premier" in result["quotes"]
        
        # Recommended should be elite
        assert result["recommended_tier"] == "elite"
    
    @patch.object(AncileoClient, 'get_quotation')
    def test_multiple_destinations_use_correct_iso_codes(self, mock_quotation):
        """Test different destinations use correct ISO codes."""
        mock_quotation.return_value = {
            "quoteId": "test",
            "offers": [{"offerId": "test", "productCode": "TEST", "unitPrice": 100.0}]
        }
        
        service = PricingService()
        departure = date.today() + timedelta(days=30)
        return_date = departure + timedelta(days=10)
        
        # Test various destinations
        destinations_iso = [
            ("Japan", "JP"),
            ("Thailand", "TH"),
            ("United States", "US"),
            ("Australia", "AU"),
            ("United Kingdom", "GB")
        ]
        
        for destination, expected_iso in destinations_iso:
            result = service.calculate_step1_quote(
                destination=destination,
                departure_date=departure,
                return_date=return_date,
                travelers_ages=[30],
                adventure_sports=False
            )
            
            assert result["success"] is True
            
            # Verify correct ISO code was used in API call
            call_args = mock_quotation.call_args
            assert call_args[1]["arrival_country"] == expected_iso
    
    @patch.object(AncileoClient, 'get_quotation')
    def test_api_error_returns_error_response(self, mock_quotation):
        """Test API error is handled gracefully."""
        mock_quotation.side_effect = AncileoAPIError("API temporarily unavailable")
        
        service = PricingService()
        departure = date.today() + timedelta(days=30)
        return_date = departure + timedelta(days=10)
        
        result = service.calculate_step1_quote(
            destination="Singapore",
            departure_date=departure,
            return_date=return_date,
            travelers_ages=[30],
            adventure_sports=False
        )
        
        # Should return error
        assert result["success"] is False
        assert "error" in result


class TestGeoMappingIntegration:
    """Integration tests for geographic mapping."""
    
    def test_get_country_iso_code_for_all_areas(self):
        """Test ISO code mapping for countries in all areas."""
        # Area A - ASEAN
        assert GeoMapper.get_country_iso_code("Thailand") == "TH"
        assert GeoMapper.get_country_iso_code("Vietnam") == "VN"
        assert GeoMapper.get_country_iso_code("Malaysia") == "MY"
        
        # Area B - Asia-Pacific
        assert GeoMapper.get_country_iso_code("Japan") == "JP"
        assert GeoMapper.get_country_iso_code("China") == "CN"
        assert GeoMapper.get_country_iso_code("Australia") == "AU"
        
        # Area C - Worldwide
        assert GeoMapper.get_country_iso_code("United States") == "US"
        assert GeoMapper.get_country_iso_code("France") == "FR"
        assert GeoMapper.get_country_iso_code("United Kingdom") == "GB"
    
    def test_iso_code_case_insensitive(self):
        """Test ISO code lookup is case-insensitive."""
        assert GeoMapper.get_country_iso_code("japan") == "JP"
        assert GeoMapper.get_country_iso_code("JAPAN") == "JP"
        assert GeoMapper.get_country_iso_code("JaPaN") == "JP"
    
    def test_iso_code_handles_variations(self):
        """Test ISO code handles country name variations."""
        # USA variations
        assert GeoMapper.get_country_iso_code("United States") == "US"
        assert GeoMapper.get_country_iso_code("USA") == "US"
        
        # UK variations
        assert GeoMapper.get_country_iso_code("United Kingdom") == "GB"
        assert GeoMapper.get_country_iso_code("UK") == "GB"
        
        # UAE variations
        assert GeoMapper.get_country_iso_code("United Arab Emirates") == "AE"
        assert GeoMapper.get_country_iso_code("UAE") == "AE"
        assert GeoMapper.get_country_iso_code("Dubai") == "AE"
    
    def test_iso_code_unknown_country_raises_error(self):
        """Test unknown country raises clear error."""
        with pytest.raises(ValueError, match="not found in ISO code mapping"):
            GeoMapper.get_country_iso_code("Atlantis")


class TestEndToEndQuoteFlow:
    """End-to-end integration tests for quote flow."""
    
    @patch.object(AncileoClient, 'get_quotation')
    def test_full_quote_flow_japan_trip(self, mock_quotation):
        """Test complete quote flow for Japan trip."""
        # Mock realistic Ancileo response
        mock_quotation.return_value = {
            "quoteId": "e2e-quote-japan-001",
            "offers": [{
                "offerId": "e2e-offer-japan-001",
                "productCode": "SG_AXA_SCOOT_COMP",
                "unitPrice": 378.0,
                "currency": "SGD",
                "productType": "travel-insurance",
                "coverageDetails": {
                    "medicalCoverage": 500000,
                    "tripCancellation": 12500,
                    "baggageLoss": 5000
                }
            }]
        }
        
        # Initialize service
        service = PricingService()
        
        # User inputs
        destination = "Japan"
        departure = date(2025, 12, 15)
        return_date = date(2026, 1, 3)
        travelers = [30, 8]  # Adult and child
        adventure = True  # Skiing trip
        
        # Call pricing service
        result = service.calculate_step1_quote(
            destination=destination,
            departure_date=departure,
            return_date=return_date,
            travelers_ages=travelers,
            adventure_sports=adventure
        )
        
        # Assertions
        assert result["success"] is True
        assert result["destination"] == "Japan"
        assert result["area"] == "area_b"  # Japan is in Area B
        assert result["duration_days"] == 20
        assert result["travelers_count"] == 2
        assert result["adventure_sports"] is True
        
        # Verify quotes
        quotes = result["quotes"]
        
        # Standard should be filtered out (adventure sports)
        assert "standard" not in quotes
        
        # Elite tier (from Ancileo)
        assert "elite" in quotes
        assert quotes["elite"]["price"] == 378.0
        assert quotes["elite"]["currency"] == "SGD"
        assert quotes["elite"]["coverage"]["adventure_sports"] is True
        
        # Premier tier (calculated)
        assert "premier" in quotes
        assert quotes["premier"]["price"] == 525.42  # 378 * 1.39
        
        # Verify Ancileo reference
        ref = result["ancileo_reference"]
        assert ref["quote_id"] == "e2e-quote-japan-001"
        assert ref["offer_id"] == "e2e-offer-japan-001"
        assert ref["product_code"] == "SG_AXA_SCOOT_COMP"
        assert ref["base_price"] == 378.0
        
        # Verify API was called correctly
        call_kwargs = mock_quotation.call_args[1]
        assert call_kwargs["trip_type"] == "RT"
        assert call_kwargs["departure_date"] == departure
        assert call_kwargs["return_date"] == return_date
        assert call_kwargs["departure_country"] == "SG"
        assert call_kwargs["arrival_country"] == "JP"
        assert call_kwargs["adults_count"] == 1
        assert call_kwargs["children_count"] == 1
    
    @patch.object(AncileoClient, 'get_quotation')
    def test_quote_expiration_scenario(self, mock_quotation):
        """Test handling of quote that may expire."""
        # First call - successful
        mock_quotation.return_value = {
            "quoteId": "expiring-quote-001",
            "offers": [{
                "offerId": "expiring-offer-001",
                "productCode": "SG_AXA_SCOOT_COMP",
                "unitPrice": 150.0
            }]
        }
        
        service = PricingService()
        departure = date.today() + timedelta(days=30)
        return_date = departure + timedelta(days=7)
        
        # Get first quote
        result1 = service.calculate_step1_quote(
            destination="Thailand",
            departure_date=departure,
            return_date=return_date,
            travelers_ages=[25],
            adventure_sports=False
        )
        
        assert result1["success"] is True
        quote_id_1 = result1["ancileo_reference"]["quote_id"]
        
        # Simulate getting a fresh quote (would happen in real flow)
        # Second call - new quote
        mock_quotation.return_value = {
            "quoteId": "fresh-quote-002",  # Different quote ID
            "offers": [{
                "offerId": "fresh-offer-002",
                "productCode": "SG_AXA_SCOOT_COMP",
                "unitPrice": 152.0  # Slightly different price
            }]
        }
        
        result2 = service.calculate_step1_quote(
            destination="Thailand",
            departure_date=departure,
            return_date=return_date,
            travelers_ages=[25],
            adventure_sports=False
        )
        
        assert result2["success"] is True
        quote_id_2 = result2["ancileo_reference"]["quote_id"]
        
        # Verify fresh quote was generated
        assert quote_id_2 != quote_id_1
        assert quote_id_2 == "fresh-quote-002"
    
    @patch.object(AncileoClient, 'get_quotation')
    def test_price_consistency_across_tiers(self, mock_quotation):
        """Test price relationships are always consistent."""
        test_prices = [50.0, 100.0, 200.0, 378.0, 500.0]
        
        service = PricingService()
        departure = date.today() + timedelta(days=30)
        return_date = departure + timedelta(days=10)
        
        for elite_price in test_prices:
            mock_quotation.return_value = {
                "quoteId": f"test-{elite_price}",
                "offers": [{
                    "offerId": f"offer-{elite_price}",
                    "productCode": "TEST",
                    "unitPrice": elite_price
                }]
            }
            
            result = service.calculate_step1_quote(
                destination="Singapore",
                departure_date=departure,
                return_date=return_date,
                travelers_ages=[30],
                adventure_sports=False
            )
            
            quotes = result["quotes"]
            
            # Verify price ordering
            assert quotes["standard"]["price"] < quotes["elite"]["price"] < quotes["premier"]["price"]
            
            # Verify Elite matches Ancileo
            assert quotes["elite"]["price"] == elite_price
            
            # Verify Standard is approximately 56% of Elite
            standard_ratio = quotes["standard"]["price"] / elite_price
            assert 0.55 < standard_ratio < 0.56
            
            # Verify Premier is approximately 139% of Elite
            premier_ratio = quotes["premier"]["price"] / elite_price
            assert 1.38 < premier_ratio < 1.40


class TestQuoteModelIntegration:
    """Integration tests for Quote model Ancileo reference methods."""
    
    def test_set_and_get_ancileo_ref(self):
        """Test storing and retrieving Ancileo reference."""
        from app.models.quote import Quote
        
        quote = Quote()
        
        # Set reference
        quote.set_ancileo_ref(
            quote_id="test-quote-123",
            offer_id="test-offer-456",
            product_code="SG_AXA_SCOOT_COMP",
            base_price=378.0
        )
        
        # Verify stored as JSON string
        assert quote.insurer_ref is not None
        assert isinstance(quote.insurer_ref, str)
        
        # Get reference
        ref = quote.get_ancileo_ref()
        
        assert ref is not None
        assert ref["quote_id"] == "test-quote-123"
        assert ref["offer_id"] == "test-offer-456"
        assert ref["product_code"] == "SG_AXA_SCOOT_COMP"
        assert ref["base_price"] == 378.0
    
    def test_get_ancileo_ref_returns_none_when_empty(self):
        """Test get returns None when no reference set."""
        from app.models.quote import Quote
        
        quote = Quote()
        ref = quote.get_ancileo_ref()
        
        assert ref is None
    
    def test_get_ancileo_ref_handles_invalid_json(self):
        """Test get handles invalid JSON gracefully."""
        from app.models.quote import Quote
        
        quote = Quote()
        quote.insurer_ref = "not valid json"
        
        ref = quote.get_ancileo_ref()
        
        # Should return None instead of raising exception
        assert ref is None


class TestAdapterFallbackBehavior:
    """Test graceful degradation when API unavailable."""
    
    @patch.object(AncileoClient, 'get_quotation')
    def test_network_error_returns_error_response(self, mock_quotation):
        """Test network errors are handled gracefully."""
        mock_quotation.side_effect = Exception("Connection timeout")
        
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
        
        # Should not raise exception
        assert result["eligibility"] is False
        assert "error" in result["breakdown"]
        assert result["tiers"] == {}

