"""Traveler schemas."""

from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID


class TravelerBase(BaseModel):
    """Base traveler schema."""
    full_name: str
    date_of_birth: date
    passport_no: Optional[str] = None
    is_primary: bool = False
    preexisting_conditions: List[str] = []


class TravelerCreate(TravelerBase):
    """Schema for creating a traveler."""
    pass


class TravelerUpdate(BaseModel):
    """Schema for updating a traveler."""
    full_name: Optional[str] = None
    passport_no: Optional[str] = None
    is_primary: Optional[bool] = None
    preexisting_conditions: Optional[List[str]] = None


class TravelerResponse(TravelerBase):
    """Schema for traveler response."""
    id: UUID
    user_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True
