"""Claims router."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.core.security import get_current_user_supabase as get_current_user
from app.models.user import User
from app.models.claim import Claim
from app.schemas.claim import ClaimCreate, ClaimUpdate, ClaimResponse
from app.services.claims import ClaimsService

router = APIRouter(prefix="/claims", tags=["claims"])


@router.post("/", response_model=ClaimResponse)
async def create_claim(
    claim_data: ClaimCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new claim."""
    
    # TODO: Validate policy exists and belongs to user
    
    claims_service = ClaimsService()
    claim = claims_service.create_claim(db, claim_data)
    
    return claim


@router.get("/", response_model=List[ClaimResponse])
async def get_claims(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's claims."""
    
    # Get claims through policies
    claims = db.query(Claim).join(Claim.policy).filter(
        Claim.policy.has(user_id=current_user.id)
    ).all()
    
    return claims


@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific claim."""
    
    claim = db.query(Claim).join(Claim.policy).filter(
        Claim.id == claim_id,
        Claim.policy.has(user_id=current_user.id)
    ).first()
    
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found"
        )
    
    return claim


@router.put("/{claim_id}", response_model=ClaimResponse)
async def update_claim(
    claim_id: str,
    claim_data: ClaimUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a claim."""
    
    claim = db.query(Claim).join(Claim.policy).filter(
        Claim.id == claim_id,
        Claim.policy.has(user_id=current_user.id)
    ).first()
    
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found"
        )
    
    claims_service = ClaimsService()
    updated_claim = claims_service.update_claim(db, claim_id, claim_data)
    
    return updated_claim


@router.post("/{claim_id}/upload")
async def upload_document(
    claim_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a document to a claim."""
    
    claim = db.query(Claim).join(Claim.policy).filter(
        Claim.id == claim_id,
        Claim.policy.has(user_id=current_user.id)
    ).first()
    
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found"
        )
    
    # TODO: Process file upload and store metadata
    document_data = {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": file.size,
        "uploaded_at": "2024-01-01T00:00:00Z"  # Mock timestamp
    }
    
    claims_service = ClaimsService()
    updated_claim = claims_service.upload_document(db, claim_id, document_data)
    
    return {"message": "Document uploaded successfully", "claim": updated_claim}


@router.post("/{claim_id}/submit")
async def submit_claim(
    claim_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a claim for processing."""
    
    claim = db.query(Claim).join(Claim.policy).filter(
        Claim.id == claim_id,
        Claim.policy.has(user_id=current_user.id)
    ).first()
    
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found"
        )
    
    claims_service = ClaimsService()
    
    try:
        submitted_claim = claims_service.submit_claim(db, claim_id)
        return {"message": "Claim submitted successfully", "claim": submitted_claim}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
