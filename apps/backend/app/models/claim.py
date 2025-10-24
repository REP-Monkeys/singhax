"""Claim model."""

from sqlalchemy import Column, String, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.db import Base


class Claim(Base):
    """Claim model for insurance claims."""
    
    __tablename__ = "claims"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), nullable=False)
    
    # Claim details
    claim_type = Column(String, nullable=False)  # trip_delay, medical, baggage, theft, cancellation
    amount = Column(Numeric(10, 2), nullable=True)  # Claim amount
    currency = Column(String(3), default="USD")
    
    # Requirements and documents
    requirements = Column(JSONB, nullable=True)  # Required documents and info
    documents = Column(JSONB, default=list)  # Uploaded documents metadata
    
    # Status and processing
    status = Column(String, default="draft")  # draft, submitted, processing, approved, rejected
    insurer_ref = Column(String, nullable=True)  # External insurer reference
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    policy = relationship("Policy", back_populates="claims")
    
    def __repr__(self):
        return f"<Claim(id={self.id}, type={self.claim_type}, status={self.status})>"
