"""Conversation tools for LangGraph agents."""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.services.pricing import PricingService
from app.services.rag import RagService
from app.services.claims import ClaimsService
from app.services.handoff import HandoffService


class ConversationTools:
    """Tools available to conversation agents."""
    
    def __init__(self, db: Session):
        self.db = db
        self.pricing_service = PricingService()
        self.rag_service = RagService()
        self.claims_service = ClaimsService()
        self.handoff_service = HandoffService()
    
    def get_quote_range(
        self,
        product_type: str,
        travelers: List[Dict[str, Any]],
        activities: List[Dict[str, Any]],
        trip_duration: int,
        destinations: List[str]
    ) -> Dict[str, Any]:
        """Get quote price range."""
        return self.pricing_service.calculate_quote_range(
            product_type, travelers, activities, trip_duration, destinations
        )
    
    def get_firm_price(
        self,
        product_type: str,
        travelers: List[Dict[str, Any]],
        activities: List[Dict[str, Any]],
        trip_duration: int,
        destinations: List[str],
        risk_factors: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get firm price for a quote."""
        return self.pricing_service.calculate_firm_price(
            product_type, travelers, activities, trip_duration, destinations, risk_factors
        )
    
    def search_policy_documents(
        self,
        query: str,
        product_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search policy documents for information."""
        from app.schemas.rag import RagSearchRequest
        
        search_request = RagSearchRequest(
            query=query,
            limit=5,
            product_type=product_type
        )
        
        search_response = self.rag_service.search_documents(self.db, search_request)
        
        return {
            "success": True,
            "results": [
                {
                    "title": doc.title,
                    "heading": doc.heading,
                    "text": doc.text,
                    "section_id": doc.section_id,
                    "citations": doc.citations
                }
                for doc in search_response.documents
            ]
        }
    
    def get_claim_requirements(
        self,
        claim_type: str
    ) -> Dict[str, Any]:
        """Get claim requirements for a claim type."""
        requirements = self.claims_service.get_claim_requirements(claim_type)
        
        return {
            "success": True,
            "requirements": requirements
        }
    
    def create_handoff_request(
        self,
        user_id: str,
        reason: str,
        conversation_summary: str
    ) -> Dict[str, Any]:
        """Create a human handoff request."""
        handoff_request = self.handoff_service.create_handoff_request(
            self.db, user_id, reason, conversation_summary
        )
        
        return {
            "success": True,
            "handoff_request": handoff_request
        }
    
    def assess_risk_factors(
        self,
        travelers: List[Dict[str, Any]],
        activities: List[Dict[str, Any]],
        destinations: List[str]
    ) -> Dict[str, Any]:
        """Assess risk factors for pricing."""
        return self.pricing_service.assess_risk_factors(travelers, activities, destinations)
    
    def get_price_breakdown_explanation(
        self,
        price: float,
        breakdown: Dict[str, Any],
        risk_factors: Dict[str, Any]
    ) -> str:
        """Get price breakdown explanation."""
        from decimal import Decimal
        return self.pricing_service.get_price_breakdown_explanation(
            Decimal(str(price)), breakdown, risk_factors
        )
    
    def get_available_products(self) -> List[Dict[str, Any]]:
        """Get available insurance products."""
        return self.pricing_service.adapter.get_products({})
    
    def get_handoff_reasons(self) -> List[Dict[str, str]]:
        """Get available handoff reasons."""
        return self.handoff_service.get_handoff_reasons()
