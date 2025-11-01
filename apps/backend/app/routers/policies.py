"""Policies router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.core.security import get_current_user_supabase as get_current_user
from app.models.user import User
from app.models.policy import Policy
from app.schemas.policy import PolicyCreate, PolicyResponse

router = APIRouter(prefix="/policies", tags=["policies"])


@router.post("/", response_model=PolicyResponse)
async def create_policy(
    policy_data: PolicyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new policy from a quote."""
    
    # TODO: Validate quote exists and belongs to user
    # TODO: Process payment
    # TODO: Generate policy number
    
    policy = Policy(
        user_id=current_user.id,
        quote_id=policy_data.quote_id,
        policy_number=f"POL-{current_user.id.hex[:8].upper()}",
        coverage=policy_data.coverage,
        named_insureds=policy_data.named_insureds,
        effective_date=policy_data.effective_date,
        expiry_date=policy_data.expiry_date,
        cooling_off_days=policy_data.cooling_off_days
    )
    
    db.add(policy)
    db.commit()
    db.refresh(policy)
    
    return policy


@router.get("/", response_model=List[PolicyResponse])
async def get_policies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's policies."""
    
    policies = db.query(Policy).filter(Policy.user_id == current_user.id).all()
    return policies


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific policy."""
    
    policy = db.query(Policy).filter(
        Policy.id == policy_id,
        Policy.user_id == current_user.id
    ).first()
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    return policy


@router.post("/{policy_id}/send-email")
async def send_policy_email(
    policy_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send policy copy via email."""
    
    # Get policy and verify ownership
    policy = db.query(Policy).filter(
        Policy.id == policy_id,
        Policy.user_id == current_user.id
    ).first()
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    # Get user email
    if not current_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User email not found"
        )
    
    # Get quote and trip for additional details
    quote = policy.quote
    trip = quote.trip if quote else None
    
    # Prepare policy details for email
    policy_details = {
        "effective_date": policy.effective_date.isoformat() if policy.effective_date else "N/A",
        "expiry_date": policy.expiry_date.isoformat() if policy.expiry_date else "N/A",
        "selected_tier": quote.selected_tier if quote else "N/A",
        "destination": ", ".join(trip.destinations) if trip and trip.destinations else "N/A",
        "coverage": policy.coverage
    }
    
    # Send email
    try:
        from app.services.email import EmailService
        
        email_service = EmailService()
        success = email_service.send_policy_copy(
            to_email=current_user.email,
            policy_number=policy.policy_number,
            policy_details=policy_details
        )
        
        if success:
            return {
                "success": True,
                "message": f"Policy copy sent to {current_user.email}",
                "policy_number": policy.policy_number
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email"
            )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send policy email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )
