"""Quote model."""

from sqlalchemy import Column, String, ForeignKey, Enum, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.db import Base


class ProductType(str, enum.Enum):
    """Insurance product types."""
    SINGLE = "single"
    ANNUAL = "annual"


class QuoteStatus(str, enum.Enum):
    """Quote status enumeration."""
    DRAFT = "draft"
    RANGED = "ranged"
    FIRMED = "firmed"
    EXPIRED = "expired"


class Quote(Base):
    """Quote model for insurance quotes."""
    
    __tablename__ = "quotes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=False)
    product_type = Column(Enum(ProductType), nullable=False)
    
    # Traveler and activity data
    travelers = Column(JSONB, nullable=False)  # List of traveler data
    activities = Column(JSONB, nullable=False)  # List of planned activities
    risk_breakdown = Column(JSONB, nullable=True)  # Risk assessment details
    
    # Pricing
    price_min = Column(Numeric(10, 2), nullable=True)
    price_max = Column(Numeric(10, 2), nullable=True)
    price_firm = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), default="USD")
    
    # Status and metadata
    status = Column(Enum(QuoteStatus), default=QuoteStatus.DRAFT)
    breakdown = Column(JSONB, nullable=True)  # Price breakdown details
    insurer_ref = Column(String, nullable=True)  # External insurer reference
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="quotes")
    trip = relationship("Trip", back_populates="quotes")
    policies = relationship("Policy", back_populates="quote")
    payments = relationship("Payment", back_populates="quote")
    
    def __repr__(self):
        return f"<Quote(id={self.id}, status={self.status}, price_firm={self.price_firm})>"
