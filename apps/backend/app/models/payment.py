"""Payment model."""

from sqlalchemy import Column, String, ForeignKey, Enum, Numeric, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.db import Base


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class Payment(Base):
    """Payment model for insurance payment records."""
    
    __tablename__ = "payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    quote_id = Column(UUID(as_uuid=True), ForeignKey("quotes.id"), nullable=False, index=True)
    
    # Stripe payment identifiers
    payment_intent_id = Column(String, unique=True, nullable=False, index=True)  # Primary lookup key
    stripe_session_id = Column(String, nullable=True, index=True)  # Stripe checkout session ID
    stripe_payment_intent = Column(String, nullable=True)  # Stripe payment intent ID
    
    # Payment details
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)  # Amount in cents (e.g., 5000 = $50.00)
    currency = Column(String(3), default="SGD", nullable=False)
    product_name = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    webhook_processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="payments")
    quote = relationship("Quote", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, payment_intent_id={self.payment_intent_id}, status={self.payment_status})>"

