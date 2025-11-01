"""Ancileo MSIG insurance adapter with 3-tier pricing system."""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import date

from .base import InsurerAdapter
from .ancileo_client import AncileoClient, AncileoAPIError

logger = logging.getLogger(__name__)


# Tier multipliers relative to Elite tier
# Elite is the base (1.0), Standard is cheaper, Premier is more expensive
TIER_MULTIPLIERS = {
    "standard": 1.0 / 1.8,   # Standard = Elite ÷ 1.8 = 0.556
    "elite": 1.0,             # Elite is the baseline from Ancileo
    "premier": 1.39          # Premier = Elite × 1.39
}


# Coverage details for each tier (matching current system)
TIER_COVERAGE = {
    "standard": {
        "medical_coverage": 250000,
        "trip_cancellation": 5000,
        "baggage_loss": 3000,
        "personal_accident": 100000,
        "adventure_sports": False,
    },
    "elite": {
        "medical_coverage": 500000,
        "trip_cancellation": 12500,
        "baggage_loss": 5000,
        "personal_accident": 250000,
        "adventure_sports": True,
    },
    "premier": {
        "medical_coverage": 1000000,
        "trip_cancellation": 15000,
        "baggage_loss": 7500,
        "personal_accident": 500000,
        "adventure_sports": True,
        "emergency_evacuation": 1000000,
    },
}


class AncileoAdapter(InsurerAdapter):
    """Ancileo MSIG insurance adapter implementing 3-tier pricing.
    
    Strategy:
    1. Call Ancileo API to get real market quote
    2. Use Ancileo price as Elite tier baseline
    3. Calculate Standard = Elite ÷ 1.8
    4. Calculate Premier = Elite × 1.39
    5. Store Ancileo quoteId/offerId for later purchase
    """
    
    def __init__(self):
        """Initialize Ancileo adapter with API client."""
        self.client = AncileoClient()
        logger.info("Initialized AncileoAdapter with real API integration")
    
    def get_products(self, ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get available insurance products (3 tiers).
        
        Returns:
            List of product definitions for Standard, Elite, Premier
        """
        return [
            {
                "id": "standard_travel",
                "name": "Standard Travel Insurance",
                "tier": "standard",
                "description": "Essential coverage for basic travel needs",
                "coverage": TIER_COVERAGE["standard"]
            },
            {
                "id": "elite_travel",
                "name": "Elite Travel Insurance",
                "tier": "elite",
                "description": "Comprehensive coverage with adventure sports",
                "coverage": TIER_COVERAGE["elite"]
            },
            {
                "id": "premium_travel",
                "name": "Premier Travel Insurance",
                "tier": "premier",
                "description": "Premium coverage with maximum protection",
                "coverage": TIER_COVERAGE["premier"]
            }
        ]
    
    def quote_range(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Get quote price range by calling Ancileo API.
        
        Args:
            input: Dictionary containing:
                - trip_type: "RT" or "ST"
                - departure_date: date object
                - return_date: date object (for RT)
                - departure_country: ISO code (e.g., "SG")
                - arrival_country: ISO code (e.g., "JP")
                - adults_count: int
                - children_count: int
        
        Returns:
            Dictionary with price_min, price_max, breakdown, currency
        """
        try:
            # Extract parameters
            trip_type = input.get("trip_type", "RT")
            departure_date = input.get("departure_date")
            return_date = input.get("return_date")
            departure_country = input.get("departure_country", "SG")
            arrival_country = input.get("arrival_country")
            adults_count = input.get("adults_count", 1)
            children_count = input.get("children_count", 0)
            
            # Call Ancileo Quotation API
            response = self.client.get_quotation(
                trip_type=trip_type,
                departure_date=departure_date,
                return_date=return_date,
                departure_country=departure_country,
                arrival_country=arrival_country,
                adults_count=adults_count,
                children_count=children_count
            )
            
            # Extract price from first offer
            offers = response.get("offers", [])
            if not offers:
                raise AncileoAPIError("No offers returned from Ancileo API")
            
            elite_price = offers[0].get("unitPrice", 0)
            
            # Calculate tier prices
            standard_price = elite_price * TIER_MULTIPLIERS["standard"]
            premier_price = elite_price * TIER_MULTIPLIERS["premier"]
            
            # Return price range (min = standard, max = premier)
            return {
                "price_min": round(standard_price, 2),
                "price_max": round(premier_price, 2),
                "breakdown": {
                    "base_price_elite": elite_price,
                    "standard_multiplier": TIER_MULTIPLIERS["standard"],
                    "premier_multiplier": TIER_MULTIPLIERS["premier"],
                    "quote_id": response.get("quoteId"),
                    "offer_id": offers[0].get("offerId"),
                    "product_code": offers[0].get("productCode")
                },
                "currency": "SGD"
            }
            
        except AncileoAPIError as e:
            logger.error(f"Ancileo API error in quote_range: {e}")
            # Return error response
            return {
                "price_min": 0,
                "price_max": 0,
                "breakdown": {"error": str(e)},
                "currency": "SGD"
            }
        except Exception as e:
            logger.error(f"Unexpected error in quote_range: {e}")
            return {
                "price_min": 0,
                "price_max": 0,
                "breakdown": {"error": str(e)},
                "currency": "SGD"
            }
    
    def price_firm(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Get firm pricing for all 3 tiers using Ancileo API.
        
        This is the key method that:
        1. Calls Ancileo to get real market price (Elite tier)
        2. Calculates Standard and Premier tiers using multipliers
        3. Returns all 3 tier prices with Ancileo reference data
        
        Args:
            input: Dictionary containing trip details
        
        Returns:
            Dictionary with:
            {
                "price": float,  # Not used in 3-tier system
                "tiers": {
                    "standard": {"price": float, "coverage": dict},
                    "elite": {"price": float, "coverage": dict},
                    "premier": {"price": float, "coverage": dict}
                },
                "ancileo_reference": {
                    "quote_id": str,
                    "offer_id": str,
                    "product_code": str,
                    "base_price": float  # Elite tier price from Ancileo
                },
                "breakdown": {...},
                "currency": "SGD",
                "eligibility": bool
            }
        """
        try:
            # Extract parameters
            trip_type = input.get("trip_type", "RT")
            departure_date = input.get("departure_date")
            return_date = input.get("return_date")
            departure_country = input.get("departure_country", "SG")
            arrival_country = input.get("arrival_country")
            adults_count = input.get("adults_count", 1)
            children_count = input.get("children_count", 0)
            
            logger.info(f"Calling Ancileo API for firm pricing: {arrival_country}, {adults_count} adults, {children_count} children")
            
            # Call Ancileo Quotation API for fresh quote
            response = self.client.get_quotation(
                trip_type=trip_type,
                departure_date=departure_date,
                return_date=return_date,
                departure_country=departure_country,
                arrival_country=arrival_country,
                adults_count=adults_count,
                children_count=children_count
            )
            
            # Extract data from response
            quote_id = response.get("quoteId")
            offers = response.get("offers", [])
            
            if not offers:
                raise AncileoAPIError("No offers returned from Ancileo API")
            
            # Get first offer (Ancileo returns 1 offer)
            offer = offers[0]
            elite_price = offer.get("unitPrice", 0)
            offer_id = offer.get("offerId")
            product_code = offer.get("productCode")
            coverage_details = offer.get("coverageDetails", {})
            
            logger.info(f"Ancileo quote received: Elite price = ${elite_price} SGD")
            
            # Calculate tier prices using multipliers
            standard_price = round(elite_price * TIER_MULTIPLIERS["standard"], 2)
            premier_price = round(elite_price * TIER_MULTIPLIERS["premier"], 2)
            
            # Build tier structure
            tiers = {
                "standard": {
                    "tier": "standard",
                    "price": standard_price,
                    "currency": "SGD",
                    "coverage": TIER_COVERAGE["standard"],
                    "multiplier": TIER_MULTIPLIERS["standard"]
                },
                "elite": {
                    "tier": "elite",
                    "price": elite_price,
                    "currency": "SGD",
                    "coverage": TIER_COVERAGE["elite"],
                    "multiplier": TIER_MULTIPLIERS["elite"],
                    "ancileo_coverage": coverage_details  # Real coverage from Ancileo
                },
                "premier": {
                    "tier": "premier",
                    "price": premier_price,
                    "currency": "SGD",
                    "coverage": TIER_COVERAGE["premier"],
                    "multiplier": TIER_MULTIPLIERS["premier"]
                }
            }
            
            # Store Ancileo reference data (CRITICAL for purchase)
            ancileo_reference = {
                "quote_id": quote_id,
                "offer_id": offer_id,
                "product_code": product_code,
                "base_price": elite_price,
                "created_at": date.today().isoformat()
            }
            
            return {
                "price": elite_price,  # Default to elite price
                "tiers": tiers,
                "ancileo_reference": ancileo_reference,
                "breakdown": {
                    "standard_price": standard_price,
                    "elite_price": elite_price,
                    "premier_price": premier_price,
                    "tier_multipliers": TIER_MULTIPLIERS,
                    "source": "ancileo_api"
                },
                "currency": "SGD",
                "eligibility": True
            }
            
        except AncileoAPIError as e:
            logger.error(f"Ancileo API error in price_firm: {e}")
            return {
                "price": 0,
                "tiers": {},
                "ancileo_reference": None,
                "breakdown": {"error": str(e)},
                "currency": "SGD",
                "eligibility": False
            }
        except Exception as e:
            logger.error(f"Unexpected error in price_firm: {e}", exc_info=True)
            return {
                "price": 0,
                "tiers": {},
                "ancileo_reference": None,
                "breakdown": {"error": str(e)},
                "currency": "SGD",
                "eligibility": False
            }
    
    def bind_policy(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Bind a policy via Ancileo Purchase API.
        
        CRITICAL: Only call this AFTER payment is confirmed.
        
        Args:
            input: Dictionary containing:
                - ancileo_reference: {quote_id, offer_id, product_code, base_price}
                - selected_tier: "standard" | "elite" | "premier"
                - insureds: List of traveler details
                - main_contact: Main contact information
        
        Returns:
            Dictionary with policy_number and insurer_ref
        """
        try:
            # Extract Ancileo reference data
            ancileo_ref = input.get("ancileo_reference")
            if not ancileo_ref:
                raise ValueError("Missing ancileo_reference in bind_policy input")
            
            quote_id = ancileo_ref.get("quote_id")
            offer_id = ancileo_ref.get("offer_id")
            product_code = ancileo_ref.get("product_code")
            base_price = ancileo_ref.get("base_price")
            
            # Get selected tier and calculate actual price
            selected_tier = input.get("selected_tier", "elite")
            tier_multiplier = TIER_MULTIPLIERS.get(selected_tier, 1.0)
            actual_price = round(base_price * tier_multiplier, 2)
            
            # Extract traveler data
            insureds = input.get("insureds", [])
            main_contact = input.get("main_contact")
            
            if not insureds:
                raise ValueError("No insureds provided for policy binding")
            if not main_contact:
                raise ValueError("No main_contact provided for policy binding")
            
            logger.info(f"Binding policy via Ancileo Purchase API: quote={quote_id}, tier={selected_tier}")
            
            # Call Ancileo Purchase API
            # Note: We always use the Elite tier's offerId/productCode from Ancileo
            # The tier selection is reflected in our pricing, but Ancileo issues the policy
            response = self.client.create_purchase(
                quote_id=quote_id,
                offer_id=offer_id,
                product_code=product_code,
                unit_price=base_price,  # Use original Ancileo price
                insureds=insureds,
                main_contact=main_contact
            )
            
            # Extract policy details from response
            # Ancileo response structure may vary - adapt as needed
            policy_number = response.get("policyNumber") or response.get("policy_number") or f"ANCILEO-{quote_id[:8]}"
            
            logger.info(f"Successfully bound policy: {policy_number}")
            
            return {
                "policy_number": policy_number,
                "coverage": TIER_COVERAGE[selected_tier],
                "named_insureds": insureds,
                "insurer_ref": f"ANCILEO-{offer_id}",
                "ancileo_response": response,
                "selected_tier": selected_tier,
                "actual_price": actual_price
            }
            
        except AncileoAPIError as e:
            logger.error(f"Ancileo API error in bind_policy: {e}")
            raise
        except Exception as e:
            logger.error(f"Error binding policy: {e}", exc_info=True)
            raise
    
    def claim_requirements(self, claim_type: str) -> Dict[str, Any]:
        """Get claim requirements for a claim type.
        
        Uses the same logic as MockInsurerAdapter.
        """
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
            },
            "theft": {
                "required_documents": [
                    "Police report",
                    "Proof of ownership",
                    "Receipts for stolen items"
                ],
                "required_info": [
                    "Date and location of theft",
                    "Description of stolen items",
                    "Estimated value"
                ]
            },
            "cancellation": {
                "required_documents": [
                    "Booking cancellation confirmation",
                    "Receipts for non-refundable expenses",
                    "Proof of cancellation reason"
                ],
                "required_info": [
                    "Date of cancellation",
                    "Reason for cancellation",
                    "Total cancellation costs"
                ]
            }
        }
        
        return requirements.get(claim_type, {})

