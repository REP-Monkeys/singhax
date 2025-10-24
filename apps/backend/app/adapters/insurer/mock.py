"""Mock insurer adapter for testing and development."""

from typing import Dict, Any, List
from decimal import Decimal
import random

from .base import InsurerAdapter


class MockInsurerAdapter(InsurerAdapter):
    """Mock insurer adapter with deterministic pricing."""
    
    def __init__(self):
        # Mock product data
        self.products = [
            {
                "id": "basic_travel",
                "name": "Basic Travel Insurance",
                "description": "Essential coverage for basic travel needs",
                "base_rate": 25.00,
                "coverage_limits": {
                    "medical": 50000,
                    "trip_cancellation": 2500,
                    "baggage": 1000
                }
            },
            {
                "id": "comprehensive_travel",
                "name": "Comprehensive Travel Insurance",
                "description": "Full coverage for comprehensive travel protection",
                "base_rate": 45.00,
                "coverage_limits": {
                    "medical": 100000,
                    "trip_cancellation": 5000,
                    "baggage": 2500
                }
            },
            {
                "id": "premium_travel",
                "name": "Premium Travel Insurance",
                "description": "Premium coverage with maximum protection",
                "base_rate": 75.00,
                "coverage_limits": {
                    "medical": 250000,
                    "trip_cancellation": 10000,
                    "baggage": 5000
                }
            }
        ]
        
        # Mock pricing data
        self.base_rates = {
            "basic_travel": 25.00,
            "comprehensive_travel": 45.00,
            "premium_travel": 75.00
        }
        
        # Activity loadings
        self.activity_loadings = {
            "skiing": 0.3,
            "diving": 0.4,
            "rock_climbing": 0.5,
            "extreme_sports": 0.6,
            "hiking": 0.1,
            "sightseeing": 0.0,
            "business": 0.0
        }
        
        # Age loadings
        self.age_loadings = {
            (0, 17): 0.2,    # Children
            (18, 30): 0.0,   # Young adults
            (31, 50): 0.0,   # Adults
            (51, 65): 0.1,   # Mature adults
            (66, 75): 0.3,   # Seniors
            (76, 100): 0.5   # Elderly
        }
        
        # Destination loadings
        self.destination_loadings = {
            "US": 0.0,
            "Canada": 0.0,
            "UK": 0.0,
            "France": 0.0,
            "Germany": 0.0,
            "Japan": 0.0,
            "Australia": 0.0,
            "Thailand": 0.1,
            "India": 0.2,
            "Brazil": 0.2,
            "Mexico": 0.15,
            "Egypt": 0.25,
            "Russia": 0.3
        }
    
    def get_products(self, ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get available insurance products."""
        return self.products
    
    def quote_range(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Get quote price range."""
        
        product_type = input.get("product_type", "basic_travel")
        travelers = input.get("travelers", [])
        activities = input.get("activities", [])
        trip_duration = input.get("trip_duration", 7)
        destinations = input.get("destinations", [])
        
        # Get base rate
        base_rate = self.base_rates.get(product_type, 25.00)
        
        # Calculate loadings
        total_loading = 0.0
        
        # Age loading
        for traveler in travelers:
            age = traveler.get("age", 30)
            for age_range, loading in self.age_loadings.items():
                if age_range[0] <= age <= age_range[1]:
                    total_loading += loading
                    break
        
        # Activity loading
        for activity in activities:
            activity_type = activity.get("type", "sightseeing")
            loading = self.activity_loadings.get(activity_type, 0.0)
            total_loading += loading
        
        # Destination loading
        for destination in destinations:
            loading = self.destination_loadings.get(destination, 0.1)
            total_loading += loading
        
        # Calculate price range
        min_price = base_rate * (1 + total_loading * 0.8) * trip_duration
        max_price = base_rate * (1 + total_loading * 1.2) * trip_duration
        
        # Add some variance for realistic range
        min_price *= 0.9
        max_price *= 1.1
        
        return {
            "price_min": round(min_price, 2),
            "price_max": round(max_price, 2),
            "breakdown": {
                "base_rate": base_rate,
                "trip_duration": trip_duration,
                "total_loading": total_loading,
                "age_loading": total_loading * 0.3,
                "activity_loading": total_loading * 0.4,
                "destination_loading": total_loading * 0.3
            },
            "currency": "USD"
        }
    
    def price_firm(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Get firm price for a quote."""
        
        product_type = input.get("product_type", "basic_travel")
        travelers = input.get("travelers", [])
        activities = input.get("activities", [])
        trip_duration = input.get("trip_duration", 7)
        destinations = input.get("destinations", [])
        risk_factors = input.get("risk_factors", {})
        
        # Get base rate
        base_rate = self.base_rates.get(product_type, 25.00)
        
        # Calculate loadings
        total_loading = 0.0
        
        # Age loading
        for traveler in travelers:
            age = traveler.get("age", 30)
            for age_range, loading in self.age_loadings.items():
                if age_range[0] <= age <= age_range[1]:
                    total_loading += loading
                    break
        
        # Activity loading
        for activity in activities:
            activity_type = activity.get("type", "sightseeing")
            loading = self.activity_loadings.get(activity_type, 0.0)
            total_loading += loading
        
        # Destination loading
        for destination in destinations:
            loading = self.destination_loadings.get(destination, 0.1)
            total_loading += loading
        
        # Risk factor loading
        risk_score = risk_factors.get("total_risk_score", 0.0)
        total_loading += risk_score * 0.2
        
        # Calculate firm price
        firm_price = base_rate * (1 + total_loading) * trip_duration
        
        # Add fees and taxes
        fees = 5.00
        tax_rate = 0.08  # 8% tax
        tax = firm_price * tax_rate
        
        total_price = firm_price + fees + tax
        
        return {
            "price": round(total_price, 2),
            "breakdown": {
                "base_rate": base_rate,
                "trip_duration": trip_duration,
                "total_loading": total_loading,
                "age_loading": total_loading * 0.3,
                "activity_loading": total_loading * 0.4,
                "destination_loading": total_loading * 0.3,
                "risk_loading": risk_score * 0.2,
                "fees": fees,
                "tax": round(tax, 2),
                "subtotal": round(firm_price, 2)
            },
            "currency": "USD",
            "eligibility": True
        }
    
    def bind_policy(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Bind a policy from a quote."""
        
        quote_id = input.get("quote_id")
        payment_id = input.get("payment_id")
        
        # Generate mock policy number
        policy_number = f"POL-{random.randint(100000, 999999)}"
        
        # Mock policy details
        policy_details = {
            "policy_number": policy_number,
            "coverage": {
                "medical": 100000,
                "trip_cancellation": 5000,
                "baggage": 2500
            },
            "named_insureds": input.get("travelers", []),
            "effective_date": input.get("effective_date"),
            "expiry_date": input.get("expiry_date"),
            "premium": input.get("premium", 0)
        }
        
        return {
            "policy_number": policy_number,
            "coverage": policy_details["coverage"],
            "named_insureds": policy_details["named_insureds"],
            "insurer_ref": f"INS-{random.randint(10000, 99999)}"
        }
    
    def claim_requirements(self, claim_type: str) -> Dict[str, Any]:
        """Get claim requirements for a claim type."""
        
        requirements = {
            "trip_delay": {
                "required_documents": [
                    "Flight confirmation",
                    "Delay certificate from airline",
                    "Receipts for additional expenses"
                ],
                "required_info": [
                    "Delay duration",
                    "Reason for delay",
                    "Additional expenses incurred"
                ]
            },
            "medical": {
                "required_documents": [
                    "Medical report from treating physician",
                    "Hospital bills and receipts",
                    "Prescription receipts"
                ],
                "required_info": [
                    "Date of illness/injury",
                    "Treatment received",
                    "Total medical expenses"
                ]
            },
            "baggage": {
                "required_documents": [
                    "Baggage claim report from airline",
                    "Receipts for purchased replacement items"
                ],
                "required_info": [
                    "Date of loss",
                    "Description of lost items",
                    "Estimated value of lost items"
                ]
            }
        }
        
        return requirements.get(claim_type, {})
