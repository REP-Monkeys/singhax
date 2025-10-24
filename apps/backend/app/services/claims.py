"""Claims service for processing insurance claims."""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.claim import Claim
from app.schemas.claim import ClaimCreate, ClaimUpdate


class ClaimsService:
    """Service for managing insurance claims."""
    
    def __init__(self):
        # Claim requirements templates
        self.claim_requirements = {
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
                    "Prescription receipts",
                    "Medical evacuation documents (if applicable)"
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
                    "Receipts for purchased replacement items",
                    "Police report (if theft)"
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
                    "Receipts for stolen items",
                    "Travel documents showing location"
                ],
                "required_info": [
                    "Date and location of theft",
                    "Description of stolen items",
                    "Police report number"
                ]
            },
            "cancellation": {
                "required_documents": [
                    "Trip booking confirmations",
                    "Cancellation receipts",
                    "Medical certificate (if medical cancellation)"
                ],
                "required_info": [
                    "Reason for cancellation",
                    "Date of cancellation",
                    "Total trip cost"
                ]
            }
        }
    
    def create_claim(
        self,
        db: Session,
        claim_data: ClaimCreate
    ) -> Claim:
        """Create a new claim."""
        
        # Get requirements for claim type
        requirements = self.claim_requirements.get(
            claim_data.claim_type,
            {"required_documents": [], "required_info": []}
        )
        
        # Create claim
        claim = Claim(
            policy_id=claim_data.policy_id,
            claim_type=claim_data.claim_type,
            amount=claim_data.amount,
            currency=claim_data.currency,
            requirements=requirements,
            documents=claim_data.documents or [],
            status="draft"
        )
        
        db.add(claim)
        db.commit()
        db.refresh(claim)
        
        return claim
    
    def update_claim(
        self,
        db: Session,
        claim_id: UUID,
        claim_data: ClaimUpdate
    ) -> Optional[Claim]:
        """Update an existing claim."""
        
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            return None
        
        # Update fields
        if claim_data.claim_type is not None:
            claim.claim_type = claim_data.claim_type
        if claim_data.amount is not None:
            claim.amount = claim_data.amount
        if claim_data.requirements is not None:
            claim.requirements = claim_data.requirements
        if claim_data.documents is not None:
            claim.documents = claim_data.documents
        if claim_data.status is not None:
            claim.status = claim_data.status
        
        db.commit()
        db.refresh(claim)
        
        return claim
    
    def get_claim_requirements(self, claim_type: str) -> Dict[str, Any]:
        """Get requirements for a specific claim type."""
        return self.claim_requirements.get(claim_type, {})
    
    def upload_document(
        self,
        db: Session,
        claim_id: UUID,
        document_data: Dict[str, Any]
    ) -> Optional[Claim]:
        """Upload a document to a claim."""
        
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            return None
        
        # Add document to claim
        if not claim.documents:
            claim.documents = []
        
        claim.documents.append(document_data)
        
        db.commit()
        db.refresh(claim)
        
        return claim
    
    def check_claim_completeness(
        self,
        claim: Claim
    ) -> Dict[str, Any]:
        """Check if a claim has all required documents and information."""
        
        requirements = claim.requirements or {}
        required_docs = requirements.get("required_documents", [])
        required_info = requirements.get("required_info", [])
        
        uploaded_docs = [doc.get("type") for doc in claim.documents or []]
        
        missing_documents = [
            doc for doc in required_docs 
            if doc not in uploaded_docs
        ]
        
        # TODO: Implement information completeness check
        missing_info = []
        
        completeness_score = len(uploaded_docs) / len(required_docs) if required_docs else 1.0
        
        return {
            "is_complete": len(missing_documents) == 0 and len(missing_info) == 0,
            "completeness_score": completeness_score,
            "missing_documents": missing_documents,
            "missing_info": missing_info,
            "uploaded_documents": uploaded_docs
        }
    
    def submit_claim(
        self,
        db: Session,
        claim_id: UUID
    ) -> Optional[Claim]:
        """Submit a claim for processing."""
        
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            return None
        
        # Check completeness
        completeness = self.check_claim_completeness(claim)
        
        if not completeness["is_complete"]:
            raise ValueError(f"Claim is not complete. Missing: {completeness['missing_documents']}")
        
        # Update status
        claim.status = "submitted"
        
        # TODO: Send to external insurer system
        # TODO: Generate claim packet
        
        db.commit()
        db.refresh(claim)
        
        return claim
    
    def generate_claim_packet(
        self,
        claim: Claim
    ) -> Dict[str, Any]:
        """Generate a pre-filled claim packet."""
        
        # TODO: Implement claim packet generation
        # This would typically generate a PDF or structured data
        
        packet = {
            "claim_id": str(claim.id),
            "claim_type": claim.claim_type,
            "policy_id": str(claim.policy_id),
            "amount": str(claim.amount) if claim.amount else None,
            "currency": claim.currency,
            "status": claim.status,
            "documents": claim.documents or [],
            "requirements": claim.requirements or {},
            "submission_date": claim.created_at.isoformat() if claim.created_at else None
        }
        
        return packet
