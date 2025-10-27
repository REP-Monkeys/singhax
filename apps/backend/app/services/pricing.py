"""Pricing service for insurance quotes."""

from typing import Dict, Any, List, Literal
from decimal import Decimal
from datetime import date, timedelta

from app.core.config import settings
from app.adapters.insurer.base import InsurerAdapter
from app.adapters.insurer.mock import MockInsurerAdapter
from app.services.geo_mapping import GeoMapper, DestinationArea


# Type alias for coverage tiers
CoverageTier = Literal["standard", "elite", "premier"]

# Tier multipliers for pricing calculation
TIER_MULTIPLIERS = {
    "standard": 1.0,
    "elite": 1.8,
    "premier": 2.5,
}

# Coverage details for each tier
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


class PricingService:
    """Service for calculating insurance pricing."""
    
    def __init__(self):
        # TODO: Replace with real insurer adapter based on configuration
        self.adapter: InsurerAdapter = MockInsurerAdapter()
    
    def calculate_quote_range(
        self,
        product_type: str,
        travelers: List[Dict[str, Any]],
        activities: List[Dict[str, Any]],
        trip_duration: int,
        destinations: List[str]
    ) -> Dict[str, Any]:
        """Calculate price range for a quote."""
        
        # Prepare context for adapter
        context = {
            "product_type": product_type,
            "travelers": travelers,
            "activities": activities,
            "trip_duration": trip_duration,
            "destinations": destinations,
        }
        
        try:
            result = self.adapter.quote_range(context)
            return {
                "success": True,
                "price_min": Decimal(str(result["price_min"])),
                "price_max": Decimal(str(result["price_max"])),
                "breakdown": result["breakdown"],
                "currency": result.get("currency", "USD"),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "price_min": None,
                "price_max": None,
                "breakdown": None,
                "currency": "USD",
            }
    
    def calculate_firm_price(
        self,
        product_type: str,
        travelers: List[Dict[str, Any]],
        activities: List[Dict[str, Any]],
        trip_duration: int,
        destinations: List[str],
        risk_factors: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate firm price for a quote."""
        
        # Prepare context for adapter
        context = {
            "product_type": product_type,
            "travelers": travelers,
            "activities": activities,
            "trip_duration": trip_duration,
            "destinations": destinations,
            "risk_factors": risk_factors,
        }
        
        try:
            result = self.adapter.price_firm(context)
            return {
                "success": True,
                "price": Decimal(str(result["price"])),
                "breakdown": result["breakdown"],
                "currency": result.get("currency", "USD"),
                "eligibility": result.get("eligibility", True),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "price": None,
                "breakdown": None,
                "currency": "USD",
                "eligibility": False,
            }
    
    def calculate_trip_duration(self, start_date: date, end_date: date) -> int:
        """Calculate trip duration in days."""
        return (end_date - start_date).days + 1
    
    def assess_risk_factors(
        self,
        travelers: List[Dict[str, Any]],
        activities: List[Dict[str, Any]],
        destinations: List[str]
    ) -> Dict[str, Any]:
        """Assess risk factors for pricing."""
        
        risk_factors = {
            "age_risk": 0,
            "activity_risk": 0,
            "destination_risk": 0,
            "preexisting_conditions": 0,
            "total_risk_score": 0,
        }
        
        # Age-based risk assessment
        for traveler in travelers:
            age = traveler.get("age", 0)
            if age < 18 or age > 65:
                risk_factors["age_risk"] += 0.2
            elif age > 80:
                risk_factors["age_risk"] += 0.5
        
        # Activity-based risk assessment
        high_risk_activities = ["skiing", "diving", "rock_climbing", "extreme_sports"]
        for activity in activities:
            if activity.get("type") in high_risk_activities:
                risk_factors["activity_risk"] += 0.3
        
        # Destination-based risk assessment
        high_risk_destinations = ["war_zone", "high_crime", "remote_area"]
        for destination in destinations:
            # TODO: Implement real destination risk assessment
            if destination in high_risk_destinations:
                risk_factors["destination_risk"] += 0.2
        
        # Preexisting conditions
        for traveler in travelers:
            conditions = traveler.get("preexisting_conditions", [])
            if conditions:
                risk_factors["preexisting_conditions"] += len(conditions) * 0.1
        
        # Calculate total risk score
        risk_factors["total_risk_score"] = sum([
            risk_factors["age_risk"],
            risk_factors["activity_risk"], 
            risk_factors["destination_risk"],
            risk_factors["preexisting_conditions"],
        ])
        
        return risk_factors
    
    def get_price_breakdown_explanation(
        self,
        price: Decimal,
        breakdown: Dict[str, Any],
        risk_factors: Dict[str, Any]
    ) -> str:
        """Generate human-readable explanation of pricing."""
        
        explanations = []
        
        # Base rate explanation
        base_rate = breakdown.get("base_rate", 0)
        explanations.append(f"Base rate: ${base_rate:.2f}")
        
        # Risk factor explanations
        if risk_factors.get("age_risk", 0) > 0:
            explanations.append(f"Age risk loading: +{risk_factors['age_risk']:.1%}")
        
        if risk_factors.get("activity_risk", 0) > 0:
            explanations.append(f"Activity risk loading: +{risk_factors['activity_risk']:.1%}")
        
        if risk_factors.get("destination_risk", 0) > 0:
            explanations.append(f"Destination risk loading: +{risk_factors['destination_risk']:.1%}")
        
        if risk_factors.get("preexisting_conditions", 0) > 0:
            explanations.append(f"Medical conditions loading: +{risk_factors['preexisting_conditions']:.1%}")
        
        # Discounts
        if breakdown.get("discounts", 0) > 0:
            explanations.append(f"Discounts: -{breakdown['discounts']:.1%}")
        
        # Fees and taxes
        if breakdown.get("fees", 0) > 0:
            explanations.append(f"Fees: ${breakdown['fees']:.2f}")
        
        if breakdown.get("tax", 0) > 0:
            explanations.append(f"Tax: ${breakdown['tax']:.2f}")
        
        return " | ".join(explanations)
    
    def calculate_step1_quote(
        self,
        destination: str,
        departure_date: date,
        return_date: date,
        travelers_ages: List[int],
        adventure_sports: bool = False
    ) -> Dict[str, Any]:
        """Calculate Step 1 quote with tiered pricing.
        
        This method implements the MSIG pricing model with geographic areas
        and three coverage tiers (Standard, Elite, Premier).
        
        Pricing Formula:
        - Per-Traveler Base Price = Base Rate per Day × Duration × Age Multiplier
        - Total Base Price = Sum of all travelers' per-traveler base prices
        - Final Price for Tier = Total Base Price × Tier Multiplier
        
        Age Multipliers:
        - Children (<18): 0.7
        - Adults (18-64): 1.0
        - Seniors (65-69): 1.3
        - Seniors 70+: 1.5
        
        Tier Multipliers:
        - Standard: 1.0
        - Elite: 1.8
        - Premier: 2.5
        
        Args:
            destination: Country name (e.g., "Japan", "Thailand")
            departure_date: Trip start date
            return_date: Trip end date
            travelers_ages: List of traveler ages (can include decimals for infants)
            adventure_sports: Whether adventure sports coverage is required
            
        Returns:
            Dictionary with structure:
            {
                "success": True/False,
                "destination": str,
                "area": str,
                "departure_date": str (ISO format),
                "return_date": str (ISO format),
                "duration_days": int,
                "travelers_count": int,
                "adventure_sports": bool,
                "quotes": {
                    "standard": {...},
                    "elite": {...},
                    "premier": {...}
                },
                "recommended_tier": str
            }
            
            Or error dict: {"success": False, "error": str}
        """
        try:
            # Step 1: Calculate trip duration
            duration = (return_date - departure_date).days + 1
            
            # Step 2: Validate duration
            if duration > 182:
                return {
                    "success": False,
                    "error": "Trip duration exceeds maximum of 182 days"
                }
            
            # Step 3: Validate travelers list
            if not travelers_ages or len(travelers_ages) == 0:
                return {
                    "success": False,
                    "error": "At least one traveler is required"
                }
            
            if len(travelers_ages) > 9:
                return {
                    "success": False,
                    "error": "Maximum 9 travelers allowed per quote"
                }
            
            # Step 4: Validate traveler ages
            for age in travelers_ages:
                if age <= 0.08:
                    return {
                        "success": False,
                        "error": "Traveler age must be at least 1 month (0.08 years)"
                    }
                if age > 110:
                    return {
                        "success": False,
                        "error": "Traveler age cannot exceed 110 years"
                    }
            
            # Step 5: Get destination info
            dest_info = GeoMapper.validate_destination(destination)
            if not dest_info["valid"]:
                return {
                    "success": False,
                    "error": f"Invalid destination: {destination}"
                }
            
            area = dest_info["area"]
            base_rate = dest_info["base_rate"]
            
            # Step 6: Calculate per-traveler base prices
            travelers_breakdown = []
            for age in travelers_ages:
                # Determine age category and multiplier
                if age < 18:
                    category = "child"
                    age_multiplier = 0.7
                elif age < 65:
                    category = "adult"
                    age_multiplier = 1.0
                elif age < 70:
                    category = "senior"
                    age_multiplier = 1.3
                else:
                    category = "senior_plus"
                    age_multiplier = 1.5
                
                # Calculate per-traveler base price
                per_traveler_base_price = base_rate * duration * age_multiplier
                
                travelers_breakdown.append({
                    "age": age,
                    "category": category,
                    "age_multiplier": age_multiplier,
                    "base_price": round(per_traveler_base_price, 2)
                })
            
            # Step 7: Calculate total base price
            total_base_price = sum(t["base_price"] for t in travelers_breakdown)
            
            # Step 8: Calculate quotes for each tier
            quotes = {}
            for tier, tier_multiplier in TIER_MULTIPLIERS.items():
                # Skip tier if adventure sports required but tier doesn't support it
                if adventure_sports and not TIER_COVERAGE[tier]["adventure_sports"]:
                    continue
                
                # Calculate final price for tier
                final_price = total_base_price * tier_multiplier
                final_price = round(final_price, 2)
                
                # Build tier quote
                quotes[tier] = {
                    "tier": tier,
                    "price": final_price,
                    "currency": "SGD",
                    "coverage": TIER_COVERAGE[tier],
                    "breakdown": {
                        "base_rate_per_day": base_rate,
                        "duration_days": duration,
                        "travelers": travelers_breakdown,
                        "total_base_price": round(total_base_price, 2),
                        "tier_multiplier": tier_multiplier,
                        "area": area.value
                    }
                }
            
            # Step 9: Determine recommended tier
            if adventure_sports:
                # Recommend elite if available, otherwise premier
                recommended_tier = "elite" if "elite" in quotes else "premier"
            else:
                recommended_tier = "standard"
            
            # Step 10: Return success response
            return {
                "success": True,
                "destination": destination,
                "area": area.value,
                "departure_date": departure_date.isoformat(),
                "return_date": return_date.isoformat(),
                "duration_days": duration,
                "travelers_count": len(travelers_ages),
                "adventure_sports": adventure_sports,
                "quotes": quotes,
                "recommended_tier": recommended_tier
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
