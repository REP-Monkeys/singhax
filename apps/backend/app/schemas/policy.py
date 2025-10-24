"""Policy schemas."""

from datetime import date, datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from uuid import UUID

from app.models.policy import PolicyStatus


class PolicyBase(BaseModel):
    """Base policy schema."""
    coverage: Dict[str, Any]
    named_insureds: List[Dict[str, Any]]
    effective_date: date
    expiry_date: date
    cooling_off_days: int = 14


class PolicyCreate(PolicyBase):
    """Schema for creating a policy."""
    quote_id: UUID


class PolicyUpdate(BaseModel):
    """Schema for updating a policy."""
    coverage: Optional[Dict[str, Any]] = None
    status: Optional[PolicyStatus] = None


class PolicyResponse(PolicyBase):
    """Schema for policy response."""
    id: UUID
    user_id: UUID
    quote_id: UUID
    policy_number: str
    insurer_ref: Optional[str] = None
    status: PolicyStatus
    created_at: datetime
    
    class Config:
        from_attributes = True
