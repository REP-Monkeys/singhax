"""Policy recommendation service based on extracted document data."""

from typing import Dict, Any, List, Optional


class PolicyRecommender:
    """Recommend insurance policy based on extracted document data."""
    
    def __init__(self):
        pass
    
    def recommend_policy(
        self,
        extracted_data: Dict[str, Any],
        normalized_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Recommend insurance policy based on extracted data.
        
        Args:
            extracted_data: Single document's extracted JSON
            normalized_data: Merged data from multiple documents (if available)
            
        Returns:
            Dictionary with recommendation and reasoning
        """
        # Use normalized data if available, otherwise use extracted data
        data = normalized_data if normalized_data else extracted_data
        
        # Extract key information
        travelers = data.get("travelers", [])
        trip_details = data.get("trip_details", {})
        activities = data.get("activities", {})
        airline_info = data.get("airline_info", {})
        
        # Get ages (if available)
        ages = []
        for traveler in travelers:
            if isinstance(traveler, dict):
                age = traveler.get("age")
                if age and isinstance(age, (int, float)):
                    ages.append(int(age))
        
        max_age = max(ages) if ages else None
        
        # Check for pre-existing conditions
        has_pre_existing = False
        for traveler in travelers:
            if isinstance(traveler, dict):
                pre_ex = traveler.get("pre_existing_conditions", {})
                if pre_ex and pre_ex.get("has_conditions", False):
                    has_pre_existing = True
                    break
        
        # Get trip details
        destination = trip_details.get("destination", {}).get("country") if isinstance(trip_details, dict) else None
        trip_type = trip_details.get("trip_type", {}).get("value") if isinstance(trip_details, dict) else None
        duration = trip_details.get("duration_days", {}).get("value") if isinstance(trip_details, dict) else None
        
        # Check adventure sports
        has_adventure_sports = activities.get("adventure_sports", {}).get("value", False) if isinstance(activities, dict) else False
        
        # Check airline
        is_scoot = airline_info.get("is_scoot", False) if isinstance(airline_info, dict) else False
        
        # Decision logic based on POLICY_DECISION_CRITERIA_ANALYSIS.md
        recommendation = self._determine_policy(
            has_pre_existing=has_pre_existing,
            max_age=max_age,
            trip_type=trip_type,
            duration=duration,
            is_scoot=is_scoot,
            has_adventure_sports=has_adventure_sports
        )
        
        return recommendation
    
    def _determine_policy(
        self,
        has_pre_existing: bool,
        max_age: Optional[int],
        trip_type: Optional[str],
        duration: Optional[int],
        is_scoot: bool,
        has_adventure_sports: bool
    ) -> Dict[str, Any]:
        """Determine policy recommendation based on criteria."""
        
        reasoning_parts = []
        
        # Primary decision: Pre-existing conditions
        if has_pre_existing:
            # Check Pre-Ex eligibility (simplified - would need more details)
            if duration and duration <= 30 and trip_type == "single_return":
                return {
                    "recommended_policy": "TravelEasy Pre-Ex",
                    "recommended_tier": "Standard",  # Default, could be Elite/Premier based on needs
                    "reasoning": "You have pre-existing conditions. TravelEasy Pre-Ex provides coverage for stable pre-existing conditions for trips up to 30 days.",
                    "eligibility_check": {
                        "age_eligible": True,
                        "pre_ex_eligible": True,
                        "trip_type_eligible": True,
                        "duration_eligible": True
                    },
                    "confidence": 0.85
                }
            else:
                reasoning_parts.append("Pre-existing conditions detected")
                return {
                    "recommended_policy": "TravelEasy Standard",
                    "recommended_tier": "Standard",
                    "reasoning": "You have pre-existing conditions. TravelEasy Standard provides coverage with exclusions for pre-existing conditions. For coverage of pre-existing conditions, consider TravelEasy Pre-Ex (requires trip ≤30 days, single return trip).",
                    "eligibility_check": {
                        "age_eligible": True,
                        "pre_ex_eligible": False,
                        "trip_type_eligible": True,
                        "duration_eligible": duration is None or duration <= 90
                    },
                    "confidence": 0.80
                }
        
        # Age-based decisions
        if max_age and max_age >= 70:
            return {
                "recommended_policy": "TravelEasy Standard",
                "recommended_tier": "Standard",
                "reasoning": "For travelers aged 70+, TravelEasy Standard offers single return trip coverage with appropriate limits.",
                "eligibility_check": {
                    "age_eligible": True,
                    "pre_ex_eligible": None,
                    "trip_type_eligible": trip_type == "single_return",
                    "duration_eligible": True
                },
                "confidence": 0.90
            }
        
        # Scoot airline preference
        if is_scoot:
            reasoning_parts.append("Traveling on Scoot airline")
            return {
                "recommended_policy": "Scootsurance",
                "recommended_tier": "Elite" if has_adventure_sports else "Standard",
                "reasoning": "Since you're traveling on Scoot, Scootsurance is designed specifically for Scoot passengers. " + 
                           ("Elite tier recommended for adventure sports coverage." if has_adventure_sports else "Standard tier provides comprehensive coverage."),
                "eligibility_check": {
                    "age_eligible": True,
                    "pre_ex_eligible": None,
                    "trip_type_eligible": True,
                    "duration_eligible": True,
                    "scoot_airline": True
                },
                "confidence": 0.88
            }
        
        # Annual coverage
        if trip_type == "annual":
            return {
                "recommended_policy": "TravelEasy Standard",
                "recommended_tier": "Elite" if has_adventure_sports else "Standard",
                "reasoning": "For annual coverage, TravelEasy Standard offers flexible multi-trip protection. " +
                           ("Elite tier recommended for adventure sports coverage." if has_adventure_sports else ""),
                "eligibility_check": {
                    "age_eligible": True,
                    "pre_ex_eligible": None,
                    "trip_type_eligible": True,
                    "duration_eligible": True
                },
                "confidence": 0.85
            }
        
        # Default: Compare options
        tier = "Elite" if has_adventure_sports else "Standard"
        return {
            "recommended_policy": "Compare Scootsurance vs TravelEasy Standard",
            "recommended_tier": tier,
            "reasoning": f"Both Scootsurance and TravelEasy Standard are suitable. " +
                        f"Consider: Scootsurance for Scoot-specific benefits, TravelEasy for flexible options. " +
                        (f"{tier} tier recommended for adventure sports coverage." if has_adventure_sports else ""),
            "eligibility_check": {
                "age_eligible": True,
                "pre_ex_eligible": None,
                "trip_type_eligible": True,
                "duration_eligible": True
            },
            "confidence": 0.75
        }

