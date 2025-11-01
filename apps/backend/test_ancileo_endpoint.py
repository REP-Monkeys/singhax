"""Test script for Ancileo API endpoint.

Tests the Ancileo MSIG API integration:
1. Direct client test (get_quotation)
2. Test through pricing service
3. Test error handling
"""

import os
import sys
from datetime import date, timedelta
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.adapters.insurer.ancileo_client import AncileoClient, AncileoAPIError, AncileoQuoteExpiredError
from app.services.pricing import PricingService


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def test_1_environment_check():
    """Test 1: Check environment configuration."""
    print_section("TEST 1: ENVIRONMENT CONFIGURATION")
    
    from app.core.config import settings
    
    api_key = settings.ancileo_msig_api_key
    base_url = settings.ancileo_api_base_url
    
    print(f"✓ API Key: {'Present' if api_key else 'MISSING'}")
    if api_key:
        print(f"  Key preview: {api_key[:8]}...{api_key[-4:]}")
    print(f"✓ Base URL: {base_url}")
    
    if not api_key:
        print("\n❌ ERROR: ANCILEO_MSIG_API_KEY not configured!")
        return False
    
    return True


def test_2_direct_quotation():
    """Test 2: Direct Ancileo quotation API call."""
    print_section("TEST 2: DIRECT ANCILEO QUOTATION API")
    
    client = AncileoClient()
    
    # Test parameters
    test_cases = [
        {
            "name": "Round Trip - Japan",
            "trip_type": "RT",
            "departure_date": date.today() + timedelta(days=15),
            "return_date": date.today() + timedelta(days=22),
            "departure_country": "SG",
            "arrival_country": "JP",
            "adults_count": 1,
            "children_count": 0
        },
        {
            "name": "Round Trip - Thailand",
            "trip_type": "RT",
            "departure_date": date.today() + timedelta(days=20),
            "return_date": date.today() + timedelta(days=27),
            "departure_country": "SG",
            "arrival_country": "TH",
            "adults_count": 2,
            "children_count": 0
        },
        {
            "name": "Single Trip - Australia",
            "trip_type": "ST",
            "departure_date": date.today() + timedelta(days=30),
            "return_date": None,
            "departure_country": "SG",
            "arrival_country": "AU",
            "adults_count": 1,
            "children_count": 1
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        print(f"   Trip Type: {test_case['trip_type']}")
        print(f"   Departure: {test_case['departure_date']}")
        if test_case['return_date']:
            print(f"   Return: {test_case['return_date']}")
        print(f"   Route: {test_case['departure_country']} → {test_case['arrival_country']}")
        print(f"   Travelers: {test_case['adults_count']} adult(s), {test_case['children_count']} child(ren)")
        
        try:
            response = client.get_quotation(
                trip_type=test_case['trip_type'],
                departure_date=test_case['departure_date'],
                return_date=test_case['return_date'],
                departure_country=test_case['departure_country'],
                arrival_country=test_case['arrival_country'],
                adults_count=test_case['adults_count'],
                children_count=test_case['children_count']
            )
            
            # Validate response structure
            quote_id = response.get('quoteId')
            offers = response.get('offers', [])
            
            print(f"\n   ✅ SUCCESS")
            print(f"   Quote ID: {quote_id}")
            print(f"   Offers: {len(offers)}")
            
            if offers:
                for i, offer in enumerate(offers, 1):
                    print(f"\n   Offer {i}:")
                    print(f"     Offer ID: {offer.get('offerId')}")
                    print(f"     Product Code: {offer.get('productCode')}")
                    print(f"     Unit Price: ${offer.get('unitPrice', 0):.2f} {offer.get('currency', 'SGD')}")
                    print(f"     Product Type: {offer.get('productType')}")
            
            # Check required fields
            if not quote_id:
                print("   ⚠️  WARNING: Missing quoteId")
                all_passed = False
            
            if not offers:
                print("   ⚠️  WARNING: No offers returned")
                all_passed = False
            
        except AncileoAPIError as e:
            print(f"\n   ❌ API ERROR: {e}")
            all_passed = False
        except ValueError as e:
            print(f"\n   ❌ VALIDATION ERROR: {e}")
            all_passed = False
        except Exception as e:
            print(f"\n   ❌ UNEXPECTED ERROR: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    return all_passed


def test_3_pricing_service():
    """Test 3: Ancileo through pricing service."""
    print_section("TEST 3: PRICING SERVICE (ANCILEO MODE)")
    
    pricing_service = PricingService()
    
    # Test case: Round trip to Japan
    departure_date = date.today() + timedelta(days=15)
    return_date = date.today() + timedelta(days=22)
    destination = "Japan"
    travelers_ages = [30]  # Single 30-year-old traveler
    
    print(f"\n📋 Test Parameters:")
    print(f"   Destination: {destination}")
    print(f"   Departure: {departure_date}")
    print(f"   Return: {return_date}")
    print(f"   Travelers Ages: {travelers_ages}")
    
    try:
        result = pricing_service.calculate_step1_quote(
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            travelers_ages=travelers_ages,
            adventure_sports=False,
            pricing_mode="ancileo"
        )
        
        print(f"\n   ✅ SUCCESS")
        print(f"   Pricing Source: {result.get('pricing_source')}")
        print(f"   Success: {result.get('success')}")
        
        if result.get('success'):
            quotes = result.get('quotes', {})
            print(f"\n   Quotes by Tier:")
            for tier in ['standard', 'elite', 'premier']:
                if tier in quotes:
                    quote = quotes[tier]
                    print(f"     {tier.capitalize()}: ${quote.get('price', 0):.2f}")
            
            ancileo_ref = result.get('ancileo_reference')
            if ancileo_ref:
                print(f"\n   Ancileo Reference:")
                print(f"     Quote ID: {ancileo_ref.get('quote_id')}")
                print(f"     Offer ID: {ancileo_ref.get('offer_id')}")
                print(f"     Product Code: {ancileo_ref.get('product_code')}")
            else:
                print(f"\n   ⚠️  WARNING: No Ancileo reference found")
        else:
            print(f"\n   ❌ FAILED: {result.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_4_error_handling():
    """Test 4: Error handling."""
    print_section("TEST 4: ERROR HANDLING")
    
    client = AncileoClient()
    
    error_tests = [
        {
            "name": "Invalid trip type",
            "expected_error": ValueError,
            "func": lambda: client.get_quotation(
                trip_type="INVALID",
                departure_date=date.today() + timedelta(days=15),
                return_date=date.today() + timedelta(days=22),
                departure_country="SG",
                arrival_country="JP",
                adults_count=1
            )
        },
        {
            "name": "Past departure date",
            "expected_error": ValueError,
            "func": lambda: client.get_quotation(
                trip_type="RT",
                departure_date=date.today() - timedelta(days=1),
                return_date=date.today() + timedelta(days=7),
                departure_country="SG",
                arrival_country="JP",
                adults_count=1
            )
        },
        {
            "name": "Return date before departure",
            "expected_error": ValueError,
            "func": lambda: client.get_quotation(
                trip_type="RT",
                departure_date=date.today() + timedelta(days=15),
                return_date=date.today() + timedelta(days=10),
                departure_country="SG",
                arrival_country="JP",
                adults_count=1
            )
        },
        {
            "name": "Zero adults",
            "expected_error": ValueError,
            "func": lambda: client.get_quotation(
                trip_type="RT",
                departure_date=date.today() + timedelta(days=15),
                return_date=date.today() + timedelta(days=22),
                departure_country="SG",
                arrival_country="JP",
                adults_count=0
            )
        }
    ]
    
    all_passed = True
    
    for test in error_tests:
        print(f"\n📋 Testing: {test['name']}")
        try:
            test['func']()
            print(f"   ❌ FAILED: Expected {test['expected_error'].__name__} but no exception raised")
            all_passed = False
        except test['expected_error']:
            print(f"   ✅ PASSED: Correctly raised {test['expected_error'].__name__}")
        except Exception as e:
            print(f"   ⚠️  Unexpected error: {type(e).__name__}: {e}")
            all_passed = False
    
    return all_passed


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("  ANCILEO API ENDPOINT TEST SUITE")
    print("="*80)
    
    results = {}
    
    # Run tests
    results['environment'] = test_1_environment_check()
    
    if results['environment']:
        results['direct_quotation'] = test_2_direct_quotation()
        results['pricing_service'] = test_3_pricing_service()
        results['error_handling'] = test_4_error_handling()
    else:
        print("\n⚠️  Skipping API tests due to environment configuration issues")
        results['direct_quotation'] = False
        results['pricing_service'] = False
        results['error_handling'] = False
    
    # Summary
    print_section("TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n  Total: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n  🎉 All tests passed!")
        return 0
    else:
        print("\n  ⚠️  Some tests failed. Check output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

