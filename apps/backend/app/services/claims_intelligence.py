"""
Claims Intelligence Service

Provides statistical insights from MSIG claims database to enhance
risk assessment and tier recommendations.
"""

from typing import Dict, Any, List, Optional
from datetime import date, datetime
from decimal import Decimal
import logging

from app.core.claims_db import execute_claims_query, check_claims_db_health

logger = logging.getLogger(__name__)


class ClaimsIntelligenceService:
    """Service for querying MSIG claims database."""
    
    def __init__(self):
        """Initialize claims intelligence service."""
        self.is_available = check_claims_db_health()
        if not self.is_available:
            logger.warning("Claims intelligence unavailable - database not accessible")
    
    def get_destination_stats(self, destination: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a destination.
        
        Args:
            destination: Country name (e.g., "Japan", "Thailand")
        
        Returns:
            Dictionary with statistical data
        """
        if not self.is_available:
            return self._get_fallback_stats()
        
        query = """
        SELECT 
            COUNT(*) as total_claims,
            ROUND(AVG(net_incurred)::numeric, 2) as avg_claim,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY net_incurred)::numeric, 2) as median_claim,
            ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY net_incurred)::numeric, 2) as p90_claim,
            ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY net_incurred)::numeric, 2) as p95_claim,
            ROUND(MAX(net_incurred)::numeric, 2) as max_claim,
            COUNT(*) FILTER (WHERE claim_type = 'Medical Expenses') as medical_claims,
            COUNT(*) FILTER (WHERE cause_of_loss = 'Injury') as injury_claims,
            COUNT(*) FILTER (WHERE cause_of_loss = 'Adventurous Activities') as adventure_claims
        FROM hackathon.claims
        WHERE destination = :destination
            AND claim_status = 'Closed'
            AND net_incurred > 0
        """
        
        try:
            results = execute_claims_query(query, {"destination": destination})
            
            if not results or results[0]["total_claims"] == 0:
                logger.info(f"No claims data found for destination: {destination}")
                return self._get_fallback_stats()
            
            return results[0]
            
        except Exception as e:
            logger.error(f"Error querying destination stats: {e}")
            return self._get_fallback_stats()
    
    def get_claim_type_breakdown(self, destination: str) -> List[Dict[str, Any]]:
        """
        Get breakdown of claim types for a destination.
        
        Returns list of dicts with claim_type, count, avg_amount, max_amount
        """
        if not self.is_available:
            return []
        
        query = """
        SELECT 
            claim_type,
            COUNT(*) as count,
            ROUND(AVG(net_incurred)::numeric, 2) as avg_amount,
            ROUND(MAX(net_incurred)::numeric, 2) as max_amount
        FROM hackathon.claims
        WHERE destination = :destination
            AND claim_status = 'Closed'
            AND net_incurred > 0
        GROUP BY claim_type
        ORDER BY count DESC
        LIMIT 10
        """
        
        try:
            return execute_claims_query(query, {"destination": destination})
        except Exception as e:
            logger.error(f"Error querying claim types: {e}")
            return []
    
    def analyze_adventure_risk(
        self,
        destination: str,
        activity: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze risk for adventure sports activities.
        
        Args:
            destination: Country name
            activity: Optional activity type (e.g., "skiing", "diving")
        
        Returns:
            Dictionary with adventure sports statistics
        """
        if not self.is_available:
            return {"has_data": False}
        
        query = """
        SELECT 
            COUNT(*) as adventure_claims,
            ROUND(AVG(net_incurred)::numeric, 2) as avg_amount,
            ROUND(MAX(net_incurred)::numeric, 2) as max_amount,
            COUNT(*) FILTER (WHERE claim_type = 'Medical Expenses') as medical_count,
            COUNT(*) FILTER (WHERE cause_of_loss = 'Injury') as injury_count
        FROM hackathon.claims
        WHERE destination = :destination
            AND cause_of_loss = 'Adventurous Activities'
            AND claim_status = 'Closed'
        """
        
        try:
            results = execute_claims_query(query, {"destination": destination})
            
            if not results or results[0]["adventure_claims"] == 0:
                # Check for injury claims as proxy for adventure risk
                injury_query = """
                SELECT 
                    COUNT(*) as injury_claims,
                    ROUND(AVG(net_incurred)::numeric, 2) as avg_injury_amount
                FROM hackathon.claims
                WHERE destination = :destination
                    AND cause_of_loss = 'Injury'
                    AND claim_status = 'Closed'
                """
                injury_results = execute_claims_query(injury_query, {"destination": destination})
                
                return {
                    "has_data": True,
                    "explicit_adventure_claims": 0,
                    "injury_claims": injury_results[0]["injury_claims"] if injury_results else 0,
                    "avg_injury_amount": injury_results[0]["avg_injury_amount"] if injury_results else 0,
                    "risk_level": "medium" if injury_results and injury_results[0]["injury_claims"] > 20 else "low"
                }
            
            data = results[0]
            data["has_data"] = True
            data["risk_level"] = "high" if data["adventure_claims"] > 5 else "medium"
            
            return data
            
        except Exception as e:
            logger.error(f"Error analyzing adventure risk: {e}")
            return {"has_data": False}
    
    def get_seasonal_patterns(self, destination: str) -> List[Dict[str, Any]]:
        """Get seasonal claim patterns by month."""
        if not self.is_available:
            return []
        
        query = """
        SELECT 
            EXTRACT(MONTH FROM accident_date) as month,
            COUNT(*) as claim_count,
            ROUND(AVG(net_incurred)::numeric, 2) as avg_amount
        FROM hackathon.claims
        WHERE destination = :destination
            AND accident_date IS NOT NULL
            AND claim_status = 'Closed'
        GROUP BY month
        ORDER BY month
        """
        
        try:
            return execute_claims_query(query, {"destination": destination})
        except Exception as e:
            logger.error(f"Error querying seasonal patterns: {e}")
            return []
    
    def _get_fallback_stats(self) -> Dict[str, Any]:
        """Return fallback statistics when database unavailable."""
        return {
            "total_claims": 0,
            "avg_claim": 0,
            "median_claim": 0,
            "p90_claim": 0,
            "p95_claim": 0,
            "max_claim": 0,
            "medical_claims": 0,
            "injury_claims": 0,
            "adventure_claims": 0,
            "data_available": False
        }


class ClaimsAnalyzer:
    """Analyze claims data to generate risk insights."""
    
    def __init__(self, claims_service: ClaimsIntelligenceService):
        """Initialize analyzer with claims intelligence service."""
        self.claims_service = claims_service
    
    def calculate_risk_score(
        self,
        destination: str,
        travelers_ages: List[int],
        adventure_sports: bool
    ) -> Dict[str, Any]:
        """
        Calculate risk score (0-10) based on claims data.
        
        Args:
            destination: Destination country
            travelers_ages: List of traveler ages
            adventure_sports: Whether adventure sports are planned
        
        Returns:
            Dictionary with risk analysis
        """
        stats = self.claims_service.get_destination_stats(destination)
        
        if not stats.get("data_available", True):
            return {
                "risk_score": 5.0,
                "risk_level": "medium",
                "risk_factors": ["No historical data available"],
                "confidence": "low"
            }
        
        # Base risk from destination claim frequency and amounts
        base_score = 3.0
        risk_factors = []
        
        # Factor 1: Average claim amount
        avg_claim = float(stats.get("avg_claim", 0))
        if avg_claim > 2000:
            base_score += 2.0
            risk_factors.append(f"High average claims (${avg_claim:.0f})")
        elif avg_claim > 1000:
            base_score += 1.5
            risk_factors.append(f"Elevated average claims (${avg_claim:.0f})")
        elif avg_claim > 500:
            base_score += 0.5
            risk_factors.append(f"Moderate average claims (${avg_claim:.0f})")
        
        # Factor 2: Medical claim frequency
        total = stats.get("total_claims", 1)
        medical_rate = stats.get("medical_claims", 0) / total if total > 0 else 0
        if medical_rate > 0.15:
            base_score += 1.0
            risk_factors.append(f"High medical claim rate ({medical_rate*100:.0f}%)")
        elif medical_rate > 0.08:
            base_score += 0.5
            risk_factors.append(f"Elevated medical claim rate ({medical_rate*100:.0f}%)")
        
        # Factor 3: Adventure sports
        if adventure_sports:
            adventure_data = self.claims_service.analyze_adventure_risk(destination)
            if adventure_data.get("has_data"):
                base_score += 2.5
                risk_factors.append("Adventure sports (high-risk activity)")
            else:
                base_score += 1.5
                risk_factors.append("Adventure sports (limited historical data)")
        
        # Factor 4: Age
        avg_age = sum(travelers_ages) / len(travelers_ages) if travelers_ages else 30
        if avg_age >= 70:
            base_score += 1.5
            risk_factors.append(f"Senior travelers (avg age {avg_age:.0f})")
        elif avg_age >= 65:
            base_score += 1.0
            risk_factors.append(f"Mature travelers (avg age {avg_age:.0f})")
        elif avg_age < 18:
            base_score += 0.5
            risk_factors.append(f"Minor travelers (avg age {avg_age:.0f})")
        
        # Cap at 10
        risk_score = min(base_score, 10.0)
        
        # Determine risk level
        if risk_score >= 8.0:
            risk_level = "very_high"
        elif risk_score >= 6.0:
            risk_level = "high"
        elif risk_score >= 4.0:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Confidence based on data availability
        confidence = "high" if total > 100 else "medium" if total > 10 else "low"
        
        return {
            "risk_score": round(risk_score, 1),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "confidence": confidence,
            "based_on_claims": total
        }
    
    def recommend_tier(
        self,
        destination: str,
        risk_score: float,
        adventure_sports: bool
    ) -> Dict[str, Any]:
        """
        Recommend coverage tier based on claims analysis.
        
        Returns:
            Dictionary with tier recommendation and reasoning
        """
        stats = self.claims_service.get_destination_stats(destination)
        
        reasoning = []
        coverage_gaps = []
        
        # Default to Standard
        recommended_tier = "standard"
        
        # Check if adventure sports require higher tier
        if adventure_sports:
            recommended_tier = "elite"
            reasoning.append("Adventure sports require Elite or Premier coverage")
            coverage_gaps.append("Standard excludes adventure sports activities")
        
        # Check if claim amounts exceed Standard limits
        p95_claim = float(stats.get("p95_claim", 0))
        max_claim = float(stats.get("max_claim", 0))
        
        if max_claim > 500000:
            recommended_tier = "premier"
            reasoning.append(f"Rare extreme claims up to ${max_claim:,.0f} seen")
            coverage_gaps.append(f"Max claim ${max_claim:,.0f} exceeds Elite limit")
        elif p95_claim > 250000 or max_claim > 250000:
            if recommended_tier != "premier":
                recommended_tier = "elite"
            reasoning.append(f"95th percentile claims (${p95_claim:,.0f}) exceed Standard")
            coverage_gaps.append(f"Top 5% of claims exceed Standard limit")
        
        # Check if risk score is very high
        if risk_score >= 8.0 and recommended_tier == "standard":
            recommended_tier = "elite"
            reasoning.append(f"Very high risk score ({risk_score}/10) warrants premium coverage")
        
        # Add data-based reasoning
        total_claims = stats.get("total_claims", 0)
        if total_claims > 1000:
            reasoning.append(f"Based on analysis of {total_claims:,} historical claims")
        
        return {
            "recommended_tier": recommended_tier,
            "reasoning": reasoning,
            "coverage_gaps": coverage_gaps if recommended_tier != "standard" else []
        }


class NarrativeGenerator:
    """Generate compelling risk narratives using LLM reasoning."""
    
    def __init__(self, llm_client):
        """
        Initialize narrative generator.
        
        Args:
            llm_client: LLMClient instance for generating narratives
        """
        self.llm_client = llm_client
    
    def generate_risk_narrative(
        self,
        destination: str,
        stats: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        tier_recommendation: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> str:
        """
        Generate a compelling, data-backed risk narrative.
        
        Args:
            destination: Destination country
            stats: Destination statistics from ClaimsService
            risk_analysis: Risk score and factors from ClaimsAnalyzer
            tier_recommendation: Tier recommendation from ClaimsAnalyzer
            user_profile: Dict with age, adventure_sports, etc.
        
        Returns:
            Formatted narrative string for user
        """
        # Build prompt for LLM
        prompt = f"""You are an insurance risk advisor analyzing historical claims data.

**Destination:** {destination}

**Historical Claims Data:**
- Total claims analyzed: {stats.get('total_claims', 0):,}
- Average claim amount: ${stats.get('avg_claim', 0):,.2f}
- 95th percentile claim: ${stats.get('p95_claim', 0):,.2f}
- Maximum claim seen: ${stats.get('max_claim', 0):,.2f}
- Medical claims: {stats.get('medical_claims', 0)}
- Injury claims: {stats.get('injury_claims', 0)}

**User Profile:**
- Ages: {user_profile.get('ages', [])}
- Adventure sports planned: {user_profile.get('adventure_sports', False)}
- Trip duration: {user_profile.get('duration_days', 'unknown')} days

**Risk Analysis:**
- Risk score: {risk_analysis.get('risk_score', 0)}/10
- Risk level: {risk_analysis.get('risk_level', 'medium')}
- Risk factors: {', '.join(risk_analysis.get('risk_factors', []))}

**Recommendation:** {tier_recommendation.get('recommended_tier', 'standard').title()} plan

Generate a compelling 2-3 paragraph narrative that:
1. Starts with the key finding (e.g., "Based on analysis of X claims to {destination}...")
2. Highlights specific risk factors relevant to this traveler
3. Explains why the recommended tier is appropriate
4. Uses specific data points but keeps language natural and empathetic
5. Ends with clear recommendation

Keep it concise, data-driven, and actionable. Avoid fear-mongering but be honest about risks."""

        try:
            narrative = self.llm_client.generate(
                prompt=prompt,
                max_tokens=400,
                temperature=0.7
            )
            
            return narrative.strip()
            
        except Exception as e:
            logger.error(f"Error generating narrative: {e}")
            return self._fallback_narrative(destination, stats, tier_recommendation)
    
    def _fallback_narrative(
        self,
        destination: str,
        stats: Dict[str, Any],
        tier_recommendation: Dict[str, Any]
    ) -> str:
        """Generate fallback narrative if LLM fails."""
        total = stats.get('total_claims', 0)
        avg = stats.get('avg_claim', 0)
        recommended = tier_recommendation.get('recommended_tier', 'standard')
        
        return f"""Based on analysis of {total:,} historical claims to {destination}, I've identified some important considerations for your trip.

The average claim amount for this destination is ${avg:,.2f}, with some claims reaching significantly higher amounts. This data, combined with your travel profile, suggests that {recommended.title()} coverage would provide the most appropriate protection.

I recommend reviewing the {recommended.title()} plan details to ensure you have adequate coverage for your specific needs."""

