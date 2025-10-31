"""
Tests for Claims Intelligence System

"""

import pytest
from unittest.mock import Mock, patch

from app.services.claims_intelligence import ClaimsIntelligenceService, ClaimsAnalyzer, NarrativeGenerator


class TestClaimsIntelligenceService:
    """Test ClaimsIntelligenceService database queries."""
    
    def test_get_destination_stats_japan(self):
        """Test getting stats for Japan."""
        service = ClaimsIntelligenceService()
        
        if not service.is_available:
            pytest.skip("Claims database not available")
        
        stats = service.get_destination_stats("Japan")
        
        assert stats["total_claims"] > 0
        assert stats["avg_claim"] > 0
        assert "medical_claims" in stats
    
    def test_get_destination_stats_unknown(self):
        """Test fallback for unknown destination."""
        service = ClaimsIntelligenceService()
        stats = service.get_destination_stats("Atlantis")
        
        assert stats["total_claims"] == 0
        assert stats.get("data_available") == False
    
    def test_analyze_adventure_risk(self):
        """Test adventure sports risk analysis."""
        service = ClaimsIntelligenceService()
        
        if not service.is_available:
            pytest.skip("Claims database not available")
        
        risk = service.analyze_adventure_risk("Japan", "skiing")
        
        assert "has_data" in risk
        assert "risk_level" in risk or "injury_claims" in risk


class TestClaimsAnalyzer:
    """Test ClaimsAnalyzer risk calculations."""
    
    def test_calculate_risk_score_high_risk(self):
        """Test risk score for high-risk scenario."""
        mock_service = Mock()
        mock_service.get_destination_stats.return_value = {
            "total_claims": 5000,
            "avg_claim": 1500,
            "medical_claims": 800,
            "data_available": True
        }
        mock_service.analyze_adventure_risk.return_value = {
            "has_data": True,
            "adventure_claims": 10,
            "avg_amount": 5000
        }
        
        analyzer = ClaimsAnalyzer(mock_service)
        
        risk = analyzer.calculate_risk_score(
            destination="Japan",
            travelers_ages=[70, 68],
            adventure_sports=True
        )
        
        assert risk["risk_score"] >= 7.0
        assert risk["risk_level"] in ["high", "very_high"]
        assert len(risk["risk_factors"]) > 0
    
    def test_recommend_tier_adventure_sports(self):
        """Test tier recommendation with adventure sports."""
        mock_service = Mock()
        mock_service.get_destination_stats.return_value = {
            "total_claims": 1000,
            "p95_claim": 2000,
            "max_claim": 50000
        }
        
        analyzer = ClaimsAnalyzer(mock_service)
        
        recommendation = analyzer.recommend_tier(
            destination="Thailand",
            risk_score=6.5,
            adventure_sports=True
        )
        
        assert recommendation["recommended_tier"] in ["elite", "premier"]
        assert len(recommendation["reasoning"]) > 0


class TestNarrativeGenerator:
    """Test NarrativeGenerator LLM integration."""
    
    def test_generate_risk_narrative(self):
        """Test narrative generation."""
        mock_llm = Mock()
        mock_llm.generate.return_value = "Test narrative about Japan risks..."
        
        generator = NarrativeGenerator(mock_llm)
        
        narrative = generator.generate_risk_narrative(
            destination="Japan",
            stats={"total_claims": 5000, "avg_claim": 1000},
            risk_analysis={"risk_score": 7.0, "risk_level": "high", "risk_factors": []},
            tier_recommendation={"recommended_tier": "elite", "reasoning": []},
            user_profile={"ages": [30], "adventure_sports": True}
        )
        
        assert len(narrative) > 0
        assert mock_llm.generate.called
    
    def test_fallback_narrative(self):
        """Test fallback when LLM fails."""
        mock_llm = Mock()
        mock_llm.generate.side_effect = Exception("LLM error")
        
        generator = NarrativeGenerator(mock_llm)
        
        narrative = generator._fallback_narrative(
            destination="Japan",
            stats={"total_claims": 5000, "avg_claim": 1000},
            tier_recommendation={"recommended_tier": "elite"}
        )
        
        assert len(narrative) > 0
        assert "5,000" in narrative or "5000" in narrative

