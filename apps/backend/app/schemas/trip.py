"""Trip schemas."""

from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID


class TripBase(BaseModel):
    """Base trip schema."""
    start_date: date
    end_date: date
    destinations: List[str]
    flight_refs: Optional[List[dict]] = []
    accommodation_refs: Optional[List[dict]] = []
    total_cost: Optional[str] = None


class TripCreate(TripBase):
    """Schema for creating a trip."""
    pass


class TripUpdate(BaseModel):
    """Schema for updating a trip."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    destinations: Optional[List[str]] = None
    flight_refs: Optional[List[dict]] = None
    accommodation_refs: Optional[List[dict]] = None
    total_cost: Optional[str] = None


class TripResponse(TripBase):
    """Schema for trip response."""
    id: UUID
    user_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True
