"""Pricing service for insurance quotes."""

from typing import Dict, Any, List, Literal
from decimal import Decimal
from datetime import date, timedelta

from app.core.config import settings
from app.adapters.insurer.base import InsurerAdapter
from app.adapters.insurer.mock import MockInsurerAdapter
from app.adapters.insurer.ancileo_adapter import AncileoAdapter
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
        import logging
        logger = logging.getLogger(__name__)
        
        # Use Ancileo adapter for real API integration
        self.adapter: InsurerAdapter = AncileoAdapter()
        
        # ALWAYS initialize these attributes (even if to None) before trying to set them
        self.claims_intelligence = None
        self.claims_analyzer = None
        
        # Initialize claims intelligence services with error handling
        try:
            from app.services.claims_intelligence import (
                ClaimsIntelligenceService,
                ClaimsAnalyzer
            )
            self.claims_intelligence = ClaimsIntelligenceService()
            self.claims_analyzer = ClaimsAnalyzer(self.claims_intelligence)
            logger.info("✓ Claims intelligence initialized successfully")
        except Exception as e:
            logger.warning(f"⚠ Failed to initialize claims intelligence: {e}")
            logger.warning(f"  Pricing service will use Ancileo-only mode")
            # Attributes already set to None above
    
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
        adventure_sports: bool = False,
        pricing_mode: str = "ancileo"
    ) -> Dict[str, Any]:
        """Calculate Step 1 quote using Ancileo API.
        
        Pricing strategy:
        - Ancileo mode (default): Direct pricing from Ancileo MSIG API for all trips
        - Claims-based mode (deprecated): Available but not recommended due to data quality issues
        
        Args:
            destination: Country name (e.g., "Japan", "Thailand")
            departure_date: Trip start date
            return_date: Trip end date
            travelers_ages: List of traveler ages (can include decimals for infants)
            adventure_sports: Whether adventure sports coverage is required
            pricing_mode: "ancileo" for Ancileo pricing, "claims_based" for data-driven pricing
            
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
                "ancileo_reference": {...},  # For purchase API
                "recommended_tier": str,
                "pricing_source": "ancileo" | "claims_based"
            }
            
            Or error dict: {"success": False, "error": str}
        """
        try:
            # Common validation for all pricing modes
            
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
            
            # Step 5: Get destination info and ISO code
            dest_info = GeoMapper.validate_destination(destination)
            if not dest_info["valid"]:
                return {
                    "success": False,
                    "error": f"Invalid destination: {destination}"
                }
            
            # Route to appropriate pricing method
            if pricing_mode == "ancileo":
                return self._calculate_ancileo_quote(
                    destination, departure_date, return_date,
                    travelers_ages, adventure_sports, dest_info
                )
            else:
                return self._calculate_claims_based_quote(
                    destination, departure_date, return_date,
                    travelers_ages, adventure_sports, dest_info
                )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in calculate_step1_quote: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def _calculate_ancileo_quote(
        self,
        destination: str,
        departure_date: date,
        return_date: date,
        travelers_ages: List[int],
        adventure_sports: bool,
        dest_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate quote using Ancileo API pricing.
        
        This is the original pricing logic extracted for mode switching.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        area = dest_info["area"]
        duration = (return_date - departure_date).days + 1
        
        # Get ISO country codes for Ancileo API
        try:
            arrival_country_iso = GeoMapper.get_country_iso_code(destination)
        except ValueError as e:
            return {
                "success": False,
                "error": str(e)
            }
        
        # Count adults and children for Ancileo API
        adults_count = sum(1 for age in travelers_ages if age >= 18)
        children_count = sum(1 for age in travelers_ages if age < 18)
        
        # Ensure at least 1 adult for Ancileo API
        if adults_count == 0:
            adults_count = 1
            children_count = max(0, children_count - 1)
        
        # Call Ancileo API via adapter
        adapter_input = {
            "trip_type": "RT",  # Round trip
            "departure_date": departure_date,
            "return_date": return_date,
            "departure_country": "SG",  # Singapore market
            "arrival_country": arrival_country_iso,
            "adults_count": adults_count,
            "children_count": children_count
        }
        
        pricing_result = self.adapter.price_firm(adapter_input)
        
        # Check if pricing was successful
        if not pricing_result.get("eligibility", False):
            return {
                "success": False,
                "error": pricing_result.get("breakdown", {}).get("error", "Failed to get pricing from Ancileo API")
            }
        
        # Extract tier prices from adapter response
        tiers = pricing_result.get("tiers", {})
        ancileo_reference = pricing_result.get("ancileo_reference")
        
        # Build quotes structure
        quotes = {}
        for tier_name, tier_data in tiers.items():
            # Include ALL tiers - users can see what coverage they're getting
            # Don't skip standard even if adventure sports is required - let users choose
            
            quotes[tier_name] = {
                "tier": tier_name,
                "price": tier_data.get("price"),
                "currency": tier_data.get("currency", "SGD"),
                "coverage": tier_data.get("coverage"),
                "breakdown": {
                    "duration_days": duration,
                    "travelers_count": len(travelers_ages),
                    "area": area.value,
                    "source": "ancileo_api",
                    "multiplier": tier_data.get("multiplier")
                }
            }
        
        # Ensure ALL three tiers are always present
        # Ancileo adapter should provide all three, but add safeguard
        for tier in ["standard", "elite", "premier"]:
            if tier not in quotes and tier in tiers:
                # This shouldn't happen, but include it just in case
                tier_data = tiers[tier]
                quotes[tier] = {
                    "tier": tier,
                    "price": tier_data.get("price"),
                    "currency": tier_data.get("currency", "SGD"),
                    "coverage": tier_data.get("coverage"),
                    "breakdown": {
                        "duration_days": duration,
                        "travelers_count": len(travelers_ages),
                        "area": area.value,
                        "source": "ancileo_api",
                        "multiplier": tier_data.get("multiplier")
                    }
                }
        
        # Determine recommended tier
        if adventure_sports:
            # Recommend elite if available, otherwise premier
            recommended_tier = "elite" if "elite" in quotes else "premier"
        else:
            recommended_tier = "standard"
        
        # Return success response with Ancileo reference
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
            "ancileo_reference": ancileo_reference,  # CRITICAL: Store for purchase
            "recommended_tier": recommended_tier,
            "pricing_source": "ancileo"
        }
    
    def _calculate_base_premium(
        self,
        stats: Dict[str, Any],
        duration_days: int
    ) -> Dict[str, float]:
        """
        Calculate base premium using percentile-based approach.
        
        Formula: (Percentile × Claim_Frequency × Risk_Buffer) × Overhead × Duration_Factor
        
        Tiers mapped to percentiles:
        - Standard: P50 (median) - covers 50% of claims
        - Elite: P90 - covers 90% of claims
        - Premier: P95 - covers 95%+ of claims
        
        Args:
            stats: Claims statistics from ClaimsIntelligenceService
            duration_days: Trip duration in days
            
        Returns:
            Dictionary with base premiums for each tier
        """
        # Extract claims percentiles
        p50_claim = float(stats.get("median_claim", 500))
        p90_claim = float(stats.get("p90_claim", 2500))
        p95_claim = float(stats.get("p95_claim", 5000))
        total_claims = stats.get("total_claims", 100)
        avg_claim = float(stats.get("avg_claim", 800))
        
        # Calculate claim frequency (assuming 100K trip population over 5 years)
        trip_population = 100000
        claim_frequency = total_claims / trip_population
        
        # Calculate base premiums with risk buffers and overhead
        # Standard: P50 × frequency × 1.5 buffer × 2.0 overhead
        standard_base = (p50_claim * claim_frequency * 1.5) * 2.0
        
        # Elite: P90 × frequency × 1.3 buffer × 1.8 overhead
        elite_base = (p90_claim * claim_frequency * 1.3) * 1.8
        
        # Premier: P95 × frequency × 1.2 buffer × 1.5 overhead
        premier_base = (p95_claim * claim_frequency * 1.2) * 1.5
        
        # Apply duration factor (non-linear)
        weeks = duration_days / 7.0
        if weeks <= 1:
            duration_factor = 1.0
        elif weeks <= 2:
            duration_factor = 1.0 + (weeks - 1) * 0.6
        else:
            duration_factor = 1.6 + (weeks - 2) * 0.4
        
        return {
            "standard": round(standard_base * duration_factor, 2),
            "elite": round(elite_base * duration_factor, 2),
            "premier": round(premier_base * duration_factor, 2)
        }
    
    def _apply_adventure_sports_multiplier(
        self,
        base_prices: Dict[str, float],
        stats: Dict[str, Any],
        destination: str
    ) -> Dict[str, Any]:
        """
        Apply adventure sports risk multiplier based on actual claims data.
        
        Logic:
        1. Query adventure-specific claims for destination
        2. Calculate risk increase from adventure vs regular claims
        3. Cap multiplier at 2.5x maximum
        4. Exclude Standard tier (business rule)
        
        Args:
            base_prices: Base premiums from _calculate_base_premium
            stats: General claims statistics
            destination: Destination country
            
        Returns:
            Modified prices with Standard=None, Elite/Premier adjusted
        """
        adventure_data = self.claims_intelligence.analyze_adventure_risk(destination)
        
        if adventure_data.get("adventure_claims", 0) > 0:
            # Calculate actual risk from data
            adventure_avg = float(adventure_data.get("avg_amount", 0))
            regular_avg = float(stats.get("avg_claim", 1))
            
            if regular_avg > 0:
                risk_multiplier = min(adventure_avg / regular_avg, 2.5)
            else:
                risk_multiplier = 1.5
        else:
            # Conservative default if no adventure data
            risk_multiplier = 1.4
        
        return {
            "standard": None,  # Excluded for adventure sports
            "elite": round(base_prices["elite"] * risk_multiplier, 2),
            "premier": round(base_prices["premier"] * risk_multiplier, 2)
        }
    
    def _apply_age_multiplier(
        self,
        base_prices: Dict[str, Any],
        travelers_ages: List[int]
    ) -> Dict[str, Any]:
        """
        Apply age-based risk multiplier.
        
        Risk factors from claims analysis:
        - Age >= 70: +30% (higher claim severity, longer recovery)
        - Age >= 65: +20% (elevated risk)
        - Age < 18: +10% (minors)
        - Age 18-64: No adjustment
        
        Args:
            base_prices: Premiums to adjust
            travelers_ages: List of traveler ages
            
        Returns:
            Adjusted premiums
        """
        avg_age = sum(travelers_ages) / len(travelers_ages)
        
        if avg_age >= 70:
            multiplier = 1.30
        elif avg_age >= 65:
            multiplier = 1.20
        elif avg_age < 18:
            multiplier = 1.10
        else:
            multiplier = 1.0
        
        return {
            tier: round(price * multiplier, 2) if price is not None else None
            for tier, price in base_prices.items()
        }
    
    def _apply_seasonal_multiplier(
        self,
        base_prices: Dict[str, Any],
        departure_date: date,
        destination: str
    ) -> Dict[str, Any]:
        """
        Apply seasonal risk multiplier based on monthly claim patterns.
        
        Uses get_seasonal_patterns() to detect high-risk months.
        Example: January in Japan = ski season = higher risk
        
        Capped at ±20% (0.8x to 1.2x).
        
        Args:
            base_prices: Premiums to adjust
            departure_date: Trip departure date
            destination: Destination country
            
        Returns:
            Seasonally adjusted premiums
        """
        seasonal_data = self.claims_intelligence.get_seasonal_patterns(destination)
        
        if not seasonal_data or len(seasonal_data) == 0:
            return base_prices
        
        month = departure_date.month
        month_stats = next((s for s in seasonal_data if int(s["month"]) == month), None)
        
        if month_stats:
            month_avg = float(month_stats["avg_amount"])
            annual_avg = sum(float(s["avg_amount"]) for s in seasonal_data) / len(seasonal_data)
            
            if annual_avg > 0:
                multiplier = max(0.8, min(month_avg / annual_avg, 1.2))
            else:
                multiplier = 1.0
        else:
            multiplier = 1.0
        
        return {
            tier: round(price * multiplier, 2) if price is not None else None
            for tier, price in base_prices.items()
        }
    
    def _normalize_tier_ratios(
        self,
        claims_prices: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize tier pricing to maintain consistent ratios.
        
        Ensures business logic consistency:
        - Elite: 1.0x (baseline)
        - Standard: Elite ÷ 1.8 (0.556x)
        - Premier: Elite × 1.39 (1.39x)
        
        Uses Elite as anchor since it's most reliable from claims data.
        
        Args:
            claims_prices: Unadjusted prices from claims calculation
            
        Returns:
            Normalized prices maintaining tier ratios
        """
        # Tier multipliers from ancileo_adapter
        TIER_RATIO_MULTIPLIERS = {
            "standard": 1.0 / 1.8,  # 0.556
            "elite": 1.0,
            "premier": 1.39
        }
        
        elite_price = claims_prices.get("elite")
        
        if not elite_price:
            return claims_prices
        
        normalized = {
            "standard": round(elite_price * TIER_RATIO_MULTIPLIERS["standard"], 2),
            "elite": elite_price,
            "premier": round(elite_price * TIER_RATIO_MULTIPLIERS["premier"], 2)
        }
        
        # Preserve adventure sports exclusion
        if claims_prices.get("standard") is None:
            normalized["standard"] = None
        
        return normalized
    
    def _validate_pricing_sanity_check(
        self,
        claims_prices: Dict[str, Any],
        ancileo_prices: Dict[str, Any],
        stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare claims-based vs Ancileo pricing to detect anomalies.
        
        Variance thresholds:
        - > 50%: WARNING - large variance
        - 30-50%: REVIEW - moderate variance
        - < 30%: OK - acceptable range
        
        Recommendation logic:
        - If 2+ warnings → use_ancileo
        - If total_claims < 50 → use_ancileo (insufficient data)
        - Else → use_claims (trust the data)
        
        Args:
            claims_prices: Prices from claims-based calculation
            ancileo_prices: Prices from Ancileo API (from quotes dict)
            stats: Claims statistics for confidence assessment
            
        Returns:
            Validation report with recommendation
        """
        import logging
        logger = logging.getLogger(__name__)
        
        validations = {}
        
        for tier in ["standard", "elite", "premier"]:
            claims_price = claims_prices.get(tier)
            
            # Extract price from ancileo quote structure
            ancileo_quote = ancileo_prices.get(tier)
            if ancileo_quote:
                ancileo_price = ancileo_quote.get("price")
            else:
                ancileo_price = None
            
            if claims_price is None or ancileo_price is None:
                continue
            
            variance = (claims_price - ancileo_price) / ancileo_price
            variance_pct = variance * 100
            
            if abs(variance) > 0.50:  # More than 50% difference
                status = "warning"
                message = f"Large variance: claims=${claims_price:.2f}, ancileo=${ancileo_price:.2f}"
                logger.warning(f"{tier.upper()}: {message}")
            elif abs(variance) > 0.30:  # 30-50% difference
                status = "review"
                message = f"Moderate variance: {variance_pct:.1f}%"
            else:
                status = "ok"
                message = f"Within expected range: {variance_pct:.1f}%"
            
            validations[tier] = {
                "status": status,
                "variance_pct": round(variance_pct, 1),
                "claims_price": claims_price,
                "ancileo_price": ancileo_price,
                "message": message
            }
        
        # Decide recommendation
        warnings = sum(1 for v in validations.values() if v["status"] == "warning")
        total_claims = stats.get("total_claims", 0)
        
        if warnings >= 2:
            recommendation = "use_ancileo"
            logger.warning(f"Too many pricing warnings ({warnings}), recommending Ancileo pricing")
        elif total_claims < 50:
            recommendation = "use_ancileo"
            logger.warning(f"Insufficient claims data ({total_claims}), recommending Ancileo pricing")
        else:
            recommendation = "use_claims"
        
        # Determine confidence level
        if total_claims > 500:
            confidence = "high"
        elif total_claims > 100:
            confidence = "medium"
        else:
            confidence = "low"
        
        return {
            "validations": validations,
            "recommendation": recommendation,
            "data_confidence": confidence
        }
    
    def _build_risk_factors(
        self,
        stats: Dict[str, Any],
        travelers_ages: List[int],
        adventure_sports: bool
    ) -> List[str]:
        """
        Build human-readable list of risk factors.
        
        Args:
            stats: Claims statistics
            travelers_ages: List of traveler ages
            adventure_sports: Whether adventure sports included
            
        Returns:
            List of risk factor descriptions
        """
        factors = []
        
        # Average claim amount
        avg_claim = float(stats.get("avg_claim", 0))
        if avg_claim > 2000:
            factors.append(f"High average claims (${avg_claim:,.0f})")
        elif avg_claim > 1000:
            factors.append(f"Elevated average claims (${avg_claim:,.0f})")
        
        # Medical claim rate
        total = stats.get("total_claims", 1)
        medical_rate = stats.get("medical_claims", 0) / total if total > 0 else 0
        if medical_rate > 0.15:
            factors.append(f"High medical claim rate ({medical_rate*100:.0f}%)")
        
        # Adventure sports
        if adventure_sports:
            factors.append("Adventure sports (high-risk activity)")
        
        # Age
        avg_age = sum(travelers_ages) / len(travelers_ages)
        if avg_age >= 70:
            factors.append(f"Senior travelers (avg age {avg_age:.0f})")
        elif avg_age >= 65:
            factors.append(f"Mature travelers (avg age {avg_age:.0f})")
        elif avg_age < 18:
            factors.append(f"Minor travelers (avg age {avg_age:.0f})")
        
        return factors
    
    def _calculate_claims_based_quote(
        self,
        destination: str,
        departure_date: date,
        return_date: date,
        travelers_ages: List[int],
        adventure_sports: bool,
        dest_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate quote using claims-based pricing with Ancileo sanity check.
        
        Algorithm:
        1. Query claims statistics from database
        2. Calculate base premium using percentile approach
        3. Apply risk multipliers (adventure, age, seasonal)
        4. Normalize to tier ratios
        5. Sanity check against Ancileo pricing
        6. Return quote with data insights
        
        Args:
            destination: Destination country
            departure_date: Trip start date
            return_date: Trip end date
            travelers_ages: List of traveler ages
            adventure_sports: Whether adventure sports included
            dest_info: Destination validation info
            
        Returns:
            Quote with claims-based pricing and data insights
        """
        import logging
        logger = logging.getLogger(__name__)
        
        area = dest_info["area"]
        duration = (return_date - departure_date).days + 1
        
        # Step 1: Get claims statistics
        stats = self.claims_intelligence.get_destination_stats(destination)
        
        # Check if we have sufficient data
        if not stats.get("total_claims") or stats.get("total_claims", 0) == 0:
            logger.warning(f"No claims data for {destination}, falling back to Ancileo")
            result = self._calculate_ancileo_quote(
                destination, departure_date, return_date,
                travelers_ages, adventure_sports, dest_info
            )
            if result.get("success"):
                result["pricing_source"] = "ancileo_fallback"
                result["fallback_reason"] = "No claims data available"
            return result
        
        logger.info(f"Calculating claims-based pricing for {destination} using {stats['total_claims']} claims")
        
        # Step 2: Calculate base premium from percentiles
        base_prices = self._calculate_base_premium(stats, duration)
        
        # Step 3: Apply adventure sports multiplier
        if adventure_sports:
            base_prices = self._apply_adventure_sports_multiplier(base_prices, stats, destination)
        
        # Step 4: Apply age multiplier
        base_prices = self._apply_age_multiplier(base_prices, travelers_ages)
        
        # Step 5: Apply seasonal multiplier
        base_prices = self._apply_seasonal_multiplier(base_prices, departure_date, destination)
        
        # Step 6: Normalize to tier ratios
        final_prices = self._normalize_tier_ratios(base_prices)
        
        # Step 7: Get Ancileo pricing for sanity check
        ancileo_quote = self._calculate_ancileo_quote(
            destination, departure_date, return_date,
            travelers_ages, adventure_sports, dest_info
        )
        
        if not ancileo_quote.get("success"):
            logger.error("Failed to get Ancileo pricing for sanity check")
            return ancileo_quote
        
        # Step 8: Validate pricing reasonableness
        sanity_check = self._validate_pricing_sanity_check(
            final_prices,
            ancileo_quote.get("quotes", {}),
            stats
        )
        
        # Step 9: Decide which pricing to use based on validation
        if sanity_check["recommendation"] == "use_ancileo":
            logger.warning(f"Falling back to Ancileo pricing: {sanity_check}")
            result = ancileo_quote
            result["pricing_source"] = "ancileo"
            result["fallback_reason"] = "Sanity check failed"
            result["sanity_check"] = sanity_check
            return result
        
        # Step 10: Build response with claims-based pricing
        quotes = {}
        for tier, price in final_prices.items():
            if price is None:
                continue
            
            quotes[tier] = {
                "tier": tier,
                "price": price,
                "currency": "SGD",
                "coverage": TIER_COVERAGE[tier],
                "data_backed": True,
                "breakdown": {
                    "duration_days": duration,
                    "travelers_count": len(travelers_ages),
                    "area": area.value,
                    "source": "claims_data",
                    "base_claims": stats["total_claims"]
                }
            }
        
        # Ensure ALL three tiers are always present - fill missing ones from Ancileo
        ancileo_quotes = ancileo_quote.get("quotes", {})
        for tier in ["standard", "elite", "premier"]:
            if tier not in quotes:
                # Try to get from Ancileo quotes
                if tier in ancileo_quotes:
                    quotes[tier] = ancileo_quotes[tier].copy()
                    quotes[tier]["breakdown"] = {
                        "duration_days": duration,
                        "travelers_count": len(travelers_ages),
                        "area": area.value,
                        "source": "ancileo_fallback",
                        "base_claims": stats["total_claims"]
                    }
                else:
                    # Calculate using tier multipliers from an existing tier
                    # Use elite as baseline if available, otherwise standard
                    baseline_tier = "elite" if "elite" in quotes else ("standard" if "standard" in quotes else "premier")
                    if baseline_tier in quotes:
                        baseline_price = quotes[baseline_tier]["price"]
                        multiplier = TIER_MULTIPLIERS[tier] / TIER_MULTIPLIERS[baseline_tier]
                        calculated_price = round(baseline_price * multiplier, 2)
                        quotes[tier] = {
                            "tier": tier,
                            "price": calculated_price,
                            "currency": "SGD",
                            "coverage": TIER_COVERAGE[tier],
                            "data_backed": False,
                            "breakdown": {
                                "duration_days": duration,
                                "travelers_count": len(travelers_ages),
                                "area": area.value,
                                "source": "calculated_fallback",
                                "base_claims": stats["total_claims"]
                            }
                        }
        
        # Determine recommended tier
        if adventure_sports:
            recommended_tier = "elite" if "elite" in quotes else "premier"
        else:
            recommended_tier = "standard" if "standard" in quotes else "elite"
        
        # Calculate claim frequency for insights
        claim_frequency_pct = round((stats['total_claims'] / 100000) * 100, 2)
        
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
            "ancileo_reference": ancileo_quote.get("ancileo_reference"),  # Keep for purchase
            "recommended_tier": recommended_tier,
            "pricing_source": "claims_based",
            "data_insights": {
                "based_on_claims": stats["total_claims"],
                "destination": destination,
                "avg_claim_amount": stats.get("avg_claim", 0),
                "claim_frequency_pct": claim_frequency_pct,
                "risk_factors": self._build_risk_factors(stats, travelers_ages, adventure_sports),
                "sanity_check": sanity_check,
                "confidence": sanity_check["data_confidence"]
            }
        }
