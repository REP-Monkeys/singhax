"""Policies router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.core.security import get_current_user
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
