"""Conversation tools for LangGraph agents."""

import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from pathlib import Path

from app.services.pricing import PricingService
from app.services.rag import RagService
from app.services.claims import ClaimsService
from app.services.handoff import HandoffService
from app.services.payment import PaymentService
from app.services.claims_intelligence import ClaimsIntelligenceService, ClaimsAnalyzer, NarrativeGenerator
from app.services.ocr import OCRService


class ConversationTools:
    """Tools available to conversation agents."""
    
    def __init__(self, db: Session, llm_client=None):
        self.db = db
        self.pricing_service = PricingService()
        self.rag_service = RagService()
        self.claims_service = ClaimsService()
        self.handoff_service = HandoffService()
        self.payment_service = PaymentService()
        
        # Initialize claims intelligence services if llm_client provided
        if llm_client:
            self.claims_intelligence_service = ClaimsIntelligenceService()
            self.claims_analyzer = ClaimsAnalyzer(self.claims_intelligence_service)
            self.narrative_generator = NarrativeGenerator(llm_client)
        else:
            self.claims_intelligence_service = None
            self.claims_analyzer = None
            self.narrative_generator = None
        self.ocr_service = OCRService()
    
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
    
    def create_payment_checkout(self, quote_id: str, user_id: str) -> Dict[str, Any]:
        """
        Create a payment checkout session for a quote.
        
        Args:
            quote_id: Quote UUID string
            user_id: User UUID string
            
        Returns:
            Dict with payment_intent_id, checkout_url, and message
        """
        from app.models.quote import Quote
        from app.models.user import User
        
        # Load Quote and User from database
        quote = self.db.query(Quote).filter(Quote.id == uuid.UUID(quote_id)).first()
        if not quote:
            return {
                "success": False,
                "error": "Quote not found"
            }
        
        user = self.db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            return {
                "success": False,
                "error": "User not found"
            }
        
        # Validate quote has firm price
        if not quote.price_firm:
            return {
                "success": False,
                "error": "Quote does not have a firm price set"
            }
        
        try:
            # Create payment intent
            payment_result = self.payment_service.create_payment_intent(
                quote=quote,
                user=user,
                db=self.db
            )
            
            payment_intent_id = payment_result["payment_intent_id"]
            amount_cents = int(float(quote.price_firm) * 100)
            product_name = f"Travel Insurance - {quote.product_type.value.title()}"
            
            # Create Stripe checkout session
            checkout_session = self.payment_service.create_stripe_checkout(
                payment_intent_id=payment_intent_id,
                amount=amount_cents,
                product_name=product_name,
                user_email=user.email,
                db=self.db
            )
            
            return {
                "success": True,
                "payment_intent_id": payment_intent_id,
                "checkout_url": checkout_session.url,
                "message": "Please complete payment at the provided URL"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_payment_completion(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Check if a payment has been completed.
        
        Args:
            payment_intent_id: Payment intent ID
            
        Returns:
            Dict with payment_intent_id, status, and is_completed flag
        """
        status = self.payment_service.check_payment_status(payment_intent_id, self.db)
        
        if status is None:
            return {
                "success": False,
                "error": "Payment not found"
            }
        
        return {
            "success": True,
            "payment_intent_id": payment_intent_id,
            "status": status,
            "is_completed": status == "completed"
        }
    
    def create_policy_from_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Create a Policy record after successful payment.
        
        Args:
            payment_intent_id: Payment intent ID
            
        Returns:
            Dict with success, policy_number, and policy_id
        """
        from app.models.payment import Payment, PaymentStatus
        from app.models.quote import Quote, QuoteStatus
        from app.models.policy import Policy, PolicyStatus
        
        # Query Payment record
        payment = self.db.query(Payment).filter(
            Payment.payment_intent_id == payment_intent_id
        ).first()
        
        if not payment:
            return {
                "success": False,
                "error": "Payment not found"
            }
        
        # Verify payment is completed
        if payment.payment_status != PaymentStatus.COMPLETED:
            return {
                "success": False,
                "error": f"Payment status is {payment.payment_status.value}, not completed"
            }
        
        # Query Quote
        quote = self.db.query(Quote).filter(Quote.id == payment.quote_id).first()
        if not quote:
            return {
                "success": False,
                "error": "Quote not found"
            }
        
        # Check if policy already exists for this quote
        existing_policy = self.db.query(Policy).filter(
            Policy.quote_id == quote.id
        ).first()
        
        if existing_policy:
            return {
                "success": True,
                "policy_number": existing_policy.policy_number,
                "policy_id": str(existing_policy.id),
                "message": "Policy already exists for this quote"
            }
        
        # Get Trip for dates
        trip = quote.trip
        if not trip or not trip.start_date or not trip.end_date:
            return {
                "success": False,
                "error": "Trip dates not available"
            }
        
        # Extract coverage from quote breakdown
        # quote.breakdown should contain coverage details
        coverage = quote.breakdown or {}
        
        # If breakdown doesn't have coverage, extract from quote data structure
        # This might need adjustment based on actual quote structure
        if "coverage" not in coverage and isinstance(quote.breakdown, dict):
            # Try to extract from breakdown structure
            coverage = {
                "medical_coverage": coverage.get("medical_coverage", 50000),
                "trip_cancellation": coverage.get("trip_cancellation", 5000),
                "baggage_loss": coverage.get("baggage_loss", 3000),
                "personal_accident": coverage.get("personal_accident", 100000),
            }
        elif not coverage:
            # Default coverage if breakdown is missing
            coverage = {
                "medical_coverage": 50000,
                "trip_cancellation": 5000,
                "baggage_loss": 3000,
                "personal_accident": 100000,
            }
        
        # Extract travelers for named_insureds
        # quote.travelers is JSONB field
        named_insureds = quote.travelers if quote.travelers else []
        
        # Generate policy number (format: POL-{8 hex chars})
        policy_number = f"POL-{uuid.uuid4().hex[:8].upper()}"
        
        # Update Quote status to ACCEPTED (or equivalent)
        # Note: QuoteStatus doesn't have ACCEPTED, we'll use a different approach
        # For now, we'll just create the policy
        
        # Create Policy record
        policy = Policy(
            user_id=payment.user_id,
            quote_id=quote.id,
            policy_number=policy_number,
            coverage=coverage,
            named_insureds=named_insureds,
            effective_date=trip.start_date,
            expiry_date=trip.end_date,
            status=PolicyStatus.ACTIVE,
            cooling_off_days=14
        )
        
        self.db.add(policy)
        
        # Update quote status if we want to mark it as accepted
        # Since QuoteStatus doesn't have ACCEPTED, we could add it or use another approach
        # For now, we'll commit the policy and let the quote status remain as is
        
        self.db.commit()
        self.db.refresh(policy)
        
        return {
            "success": True,
            "policy_number": policy_number,
            "policy_id": str(policy.id)
        }
    
    def analyze_destination_risk(
        self,
        destination: str,
        travelers_ages: List[int],
        adventure_sports: bool
    ) -> Dict[str, Any]:
        """
        Analyze risk for a destination using historical claims data.
        
        This tool queries the MSIG claims database to provide data-backed
        risk assessment and coverage recommendations.
        
        Args:
            destination: Destination country (e.g., "Japan", "Thailand")
            travelers_ages: List of traveler ages
            adventure_sports: Whether adventure sports are planned
        
        Returns:
            Dictionary with risk analysis, tier recommendation, and narrative
        """
        if not self.claims_intelligence_service or not self.claims_analyzer:
            return {
                "success": False,
                "error": "Claims intelligence not initialized",
                "destination": destination
            }
        
        try:
            # Get destination statistics
            stats = self.claims_intelligence_service.get_destination_stats(destination)
            
            # Calculate risk score
            risk_analysis = self.claims_analyzer.calculate_risk_score(
                destination=destination,
                travelers_ages=travelers_ages,
                adventure_sports=adventure_sports
            )
            
            # Get tier recommendation
            tier_recommendation = self.claims_analyzer.recommend_tier(
                destination=destination,
                risk_score=risk_analysis["risk_score"],
                adventure_sports=adventure_sports
            )
            
            # Generate narrative
            user_profile = {
                "ages": travelers_ages,
                "adventure_sports": adventure_sports,
                "duration_days": "unknown"  # Can be added if available
            }
            
            narrative = self.narrative_generator.generate_risk_narrative(
                destination=destination,
                stats=stats,
                risk_analysis=risk_analysis,
                tier_recommendation=tier_recommendation,
                user_profile=user_profile
            )
            
            return {
                "success": True,
                "destination": destination,
                "stats": stats,
                "risk_analysis": risk_analysis,
                "tier_recommendation": tier_recommendation,
                "narrative": narrative,
                "data_available": stats.get("data_available", True)
            }
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error analyzing destination risk: {e}")
            return {
                "success": False,
                "error": str(e),
                "destination": destination,
                "data_available": False
            }
    
    def check_adventure_coverage(
        self,
        destination: str,
        activity: str
    ) -> Dict[str, Any]:
        """
        Check if adventure sports are covered and analyze specific risks.
        
        Args:
            destination: Destination country
            activity: Activity type (e.g., "skiing", "diving", "hiking")
        
        Returns:
            Dictionary with adventure risk analysis
        """
        if not self.claims_intelligence_service:
            return {
                "success": False,
                "error": "Claims intelligence not initialized",
                "activity": activity
            }
        
        try:
            adventure_data = self.claims_intelligence_service.analyze_adventure_risk(
                destination=destination,
                activity=activity
            )
            
            # Determine if activity requires premium coverage
            requires_premium = activity.lower() in [
                "skiing", "snowboarding", "scuba diving", "diving", "skydiving",
                "bungee jumping", "rock climbing", "paragliding", "parasailing"
            ]
            
            return {
                "success": True,
                "activity": activity,
                "destination": destination,
                "requires_premium_coverage": requires_premium,
                "adventure_data": adventure_data,
                "minimum_tier": "elite" if requires_premium else "standard",
                "reasoning": f"{activity.title()} is classified as an adventurous activity" if requires_premium else f"{activity.title()} is covered under all tiers"
            }
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error checking adventure coverage: {e}")
            return {
                "success": False,
                "error": str(e),
                "activity": activity
            }
    
    def extract_text_from_image(
        self,
        image_path: str,
        language: str = 'eng'
    ) -> Dict[str, Any]:
        """
        Extract text from an image file using OCR.
        
        Args:
            image_path: Path to the image file (relative to uploads directory or absolute)
            language: Tesseract language code (default: 'eng')
            
        Returns:
            Dictionary with:
            - success: bool
            - text: Extracted text
            - confidence: Average confidence score
            - word_count: Number of words
            - error: Error message if processing failed
        """
        try:
            # Resolve path - check if it's relative to uploads or absolute
            path = Path(image_path)
            if not path.is_absolute():
                # Try relative to uploads directory
                uploads_path = Path("apps/backend/uploads/temp") / path
                if uploads_path.exists():
                    path = uploads_path
                else:
                    uploads_path = Path("apps/backend/uploads/documents") / path
                    if uploads_path.exists():
                        path = uploads_path
            
            if not path.exists():
                return {
                    "success": False,
                    "text": "",
                    "confidence": 0.0,
                    "word_count": 0,
                    "error": f"Image file not found: {image_path}"
                }
            
            # Read file and extract text
            with open(path, 'rb') as f:
                file_bytes = f.read()
            
            result = self.ocr_service.extract_text(
                file_bytes,
                path.name,
                language=language
            )
            
            # Add success flag
            result["success"] = result.get("error") is None
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "word_count": 0,
                "error": f"OCR processing failed: {str(e)}"
            }
