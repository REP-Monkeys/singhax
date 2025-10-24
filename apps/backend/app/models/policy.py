"""Policy model."""

from sqlalchemy import Column, String, Date, ForeignKey, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.db import Base


class PolicyStatus(str, enum.Enum):
    """Policy status enumeration."""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Policy(Base):
    """Policy model for active insurance policies."""
    
    __tablename__ = "policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    quote_id = Column(UUID(as_uuid=True), ForeignKey("quotes.id"), nullable=False)
    
    # Policy details
    policy_number = Column(String, unique=True, nullable=False)
    insurer_ref = Column(String, nullable=True)  # External insurer reference
    coverage = Column(JSONB, nullable=False)  # Coverage details and limits
    named_insureds = Column(JSONB, nullable=False)  # List of covered travelers
    
    # Dates
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    cooling_off_days = Column(Integer, default=14)  # Cancellation period
    
    # Status
    status = Column(Enum(PolicyStatus), default=PolicyStatus.ACTIVE)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="policies")
    quote = relationship("Quote", back_populates="policies")
    claims = relationship("Claim", back_populates="policy")
    
    def __repr__(self):
        return f"<Policy(id={self.id}, policy_number={self.policy_number}, status={self.status})>"
