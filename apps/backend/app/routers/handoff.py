"""Human handoff router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.handoff import HandoffService

router = APIRouter(prefix="/handoff", tags=["handoff"])


@router.post("/")
async def create_handoff_request(
    reason: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a human handoff request."""
    
    handoff_service = HandoffService()
    
    # Generate conversation summary
    conversation_summary = handoff_service.generate_conversation_summary(db, current_user.id)
    
    # Create handoff request
    handoff_request = handoff_service.create_handoff_request(
        db,
        current_user.id,
        reason,
        conversation_summary
    )
    
    return {
        "message": "Handoff request created successfully",
        "handoff_request": handoff_request
    }


@router.get("/reasons")
async def get_handoff_reasons(
    current_user: User = Depends(get_current_user)
):
    """Get available handoff reasons."""
    
    handoff_service = HandoffService()
    reasons = handoff_service.get_handoff_reasons()
    
    return {"reasons": reasons}
