"""Quote schemas."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal

from app.models.quote import ProductType, QuoteStatus, TierType


class QuoteBase(BaseModel):
    """Base quote schema."""
    product_type: ProductType
    travelers: List[Dict[str, Any]]
    activities: List[Dict[str, Any]]


class QuoteCreate(QuoteBase):
    """Schema for creating a quote."""
    trip_id: UUID
    selected_tier: TierType = TierType.STANDARD  # Default to standard tier


class QuoteUpdate(BaseModel):
    """Schema for updating a quote."""
    travelers: Optional[List[Dict[str, Any]]] = None
    activities: Optional[List[Dict[str, Any]]] = None
    risk_breakdown: Optional[Dict[str, Any]] = None


class QuotePriceRequest(BaseModel):
    """Schema for price calculation request."""
    quote_id: UUID


class QuoteResponse(QuoteBase):
    """Schema for quote response."""
    id: UUID
    user_id: UUID
    trip_id: UUID
    selected_tier: TierType
    risk_breakdown: Optional[Dict[str, Any]] = None
    price_min: Optional[Decimal] = None
    price_max: Optional[Decimal] = None
    price_firm: Optional[Decimal] = None
    currency: str = "USD"
    status: QuoteStatus
    breakdown: Optional[Dict[str, Any]] = None
    insurer_ref: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
