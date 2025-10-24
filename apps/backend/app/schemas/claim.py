"""Claim schemas."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal


class ClaimBase(BaseModel):
    """Base claim schema."""
    claim_type: str
    amount: Optional[Decimal] = None
    currency: str = "USD"
    requirements: Optional[Dict[str, Any]] = None
    documents: Optional[List[Dict[str, Any]]] = []


class ClaimCreate(ClaimBase):
    """Schema for creating a claim."""
    policy_id: UUID


class ClaimUpdate(BaseModel):
    """Schema for updating a claim."""
    claim_type: Optional[str] = None
    amount: Optional[Decimal] = None
    requirements: Optional[Dict[str, Any]] = None
    documents: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None


class ClaimResponse(ClaimBase):
    """Schema for claim response."""
    id: UUID
    policy_id: UUID
    status: str
    insurer_ref: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
