"""Pricing service for insurance quotes."""

from typing import Dict, Any, List
from decimal import Decimal
from datetime import date, timedelta

from app.core.config import settings
from app.adapters.insurer.base import InsurerAdapter
from app.adapters.insurer.mock import MockInsurerAdapter


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
