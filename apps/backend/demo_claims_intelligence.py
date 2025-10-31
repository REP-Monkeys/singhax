"""
Demo script for Claims Intelligence System

Usage: python demo_claims_intelligence.py
"""

from app.services.claims_intelligence import ClaimsIntelligenceService, ClaimsAnalyzer
from app.agents.llm_client import GroqLLMClient


def demo_japan_skiing():
    """Demo scenario: Skiing trip to Japan."""
    print("\n" + "="*70)
    print("DEMO: Skiing Trip to Japan")
    print("="*70 + "\n")
    
    # Initialize services
    claims_service = ClaimsIntelligenceService()
    analyzer = ClaimsAnalyzer(claims_service)
    
    # Scenario
    destination = "Japan"
    travelers_ages = [32, 8]
    adventure_sports = True
    
    print(f"📍 Destination: {destination}")
    print(f"👥 Travelers: {travelers_ages}")
    print(f"🎿 Adventure Sports: {adventure_sports}\n")
    
    # Get statistics
    print("📊 Querying claims database...")
    stats = claims_service.get_destination_stats(destination)
    
    print(f"\n✅ Found {stats['total_claims']:,} historical claims")
    print(f"💰 Average claim: ${stats['avg_claim']:,.2f}")
    print(f"📈 95th percentile: ${stats['p95_claim']:,.2f}")
    print(f"🏥 Medical claims: {stats['medical_claims']}")
    print(f"🤕 Injury claims: {stats['injury_claims']}")
    print(f"🎿 Adventure claims: {stats['adventure_claims']}")
    
    # Calculate risk
    print("\n🔍 Calculating risk score...")
    risk = analyzer.calculate_risk_score(destination, travelers_ages, adventure_sports)
    
    print(f"\n⚠️ Risk Score: {risk['risk_score']}/10")
    print(f"📊 Risk Level: {risk['risk_level'].upper()}")
    print(f"🎯 Confidence: {risk['confidence']}")
    print("\n📋 Risk Factors:")
    for factor in risk['risk_factors']:
        print(f"   • {factor}")
    
    # Get recommendation
    print("\n💡 Generating recommendation...")
    recommendation = analyzer.recommend_tier(
        destination, risk['risk_score'], adventure_sports
    )
    
    print(f"\n✅ Recommended Tier: {recommendation['recommended_tier'].upper()}")
    print("\n📝 Reasoning:")
    for reason in recommendation['reasoning']:
        print(f"   • {reason}")
    
    if recommendation['coverage_gaps']:
        print("\n⚠️ Coverage Gaps with Standard:")
        for gap in recommendation['coverage_gaps']:
            print(f"   • {gap}")
    
    print("\n" + "="*70 + "\n")


def demo_thailand_diving():
    """Demo scenario: Diving trip to Thailand."""
    print("\n" + "="*70)
    print("DEMO: Diving Trip to Thailand")
    print("="*70 + "\n")
    
    claims_service = ClaimsIntelligenceService()
    
    destination = "Thailand"
    
    print(f"📍 Destination: {destination}")
    print(f"🤿 Activity: Scuba Diving\n")
    
    # Get adventure analysis
    print("🔍 Analyzing adventure sports risk...")
    adventure_risk = claims_service.analyze_adventure_risk(destination, "diving")
    
    print(f"\n📊 Adventure Risk Analysis:")
    print(f"   • Has historical data: {adventure_risk.get('has_data', False)}")
    print(f"   • Explicit adventure claims: {adventure_risk.get('explicit_adventure_claims', adventure_risk.get('adventure_claims', 0))}")
    print(f"   • Risk level: {adventure_risk.get('risk_level', 'unknown')}")
    
    if adventure_risk.get('injury_claims'):
        print(f"   • Related injury claims: {adventure_risk['injury_claims']}")
        print(f"   • Avg injury amount: ${adventure_risk.get('avg_injury_amount', 0):,.2f}")
    
    print("\n" + "="*70 + "\n")


def demo_with_llm_narrative():
    """Demo scenario with full LLM narrative generation."""
    print("\n" + "="*70)
    print("DEMO: Full LLM Narrative Generation")
    print("="*70 + "\n")
    
    # Initialize services
    llm_client = GroqLLMClient()
    claims_service = ClaimsIntelligenceService()
    analyzer = ClaimsAnalyzer(claims_service)
    from app.services.claims_intelligence import NarrativeGenerator
    narrative_gen = NarrativeGenerator(llm_client)
    
    # Scenario
    destination = "Japan"
    travelers_ages = [32, 8]
    adventure_sports = True
    
    print(f"📍 Destination: {destination}")
    print(f"👥 Travelers: {travelers_ages}")
    print(f"🎿 Adventure Sports: {adventure_sports}\n")
    
    # Get complete analysis
    stats = claims_service.get_destination_stats(destination)
    risk_analysis = analyzer.calculate_risk_score(destination, travelers_ages, adventure_sports)
    tier_recommendation = analyzer.recommend_tier(destination, risk_analysis['risk_score'], adventure_sports)
    
    # Generate narrative
    print("🤖 Generating LLM narrative...")
    user_profile = {
        "ages": travelers_ages,
        "adventure_sports": adventure_sports,
        "duration_days": "7"
    }
    
    narrative = narrative_gen.generate_risk_narrative(
        destination=destination,
        stats=stats,
        risk_analysis=risk_analysis,
        tier_recommendation=tier_recommendation,
        user_profile=user_profile
    )
    
    print("\n📝 Generated Narrative:")
    print("-" * 70)
    print(narrative)
    print("-" * 70 + "\n")


if __name__ == "__main__":
    print("\n🚀 Claims Intelligence System - Demo\n")
    
    # Run demos
    demo_japan_skiing()
    demo_thailand_diving()
    
    # Run LLM narrative demo (takes longer)
    try:
        demo_with_llm_narrative()
    except Exception as e:
        print(f"\n⚠️ LLM narrative demo failed (this is okay if API key issues): {e}\n")
    
    print("✅ Demo complete!\n")

