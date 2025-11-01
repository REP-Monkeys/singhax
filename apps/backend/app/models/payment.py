"""Payment model."""

from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime, Index, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID, ENUM
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


class PaymentStatusEnum(TypeDecorator):
    """Type decorator to ensure enum values (lowercase) are used, not member names."""
    impl = ENUM
    cache_ok = True
    
    def __init__(self):
        # Use the existing PostgreSQL enum type, but don't let SQLAlchemy serialize it
        super().__init__(
            PaymentStatus,
            name='paymentstatus',
            create_type=False,
            native_enum=False  # Don't use native enum serialization - we'll handle it
        )
    
    def process_bind_param(self, value, dialect):
        """Convert enum to its value (lowercase string) when binding to database."""
        if value is None:
            return None
        # Handle PaymentStatus enum - always return lowercase value
        if isinstance(value, PaymentStatus):
            return value.value  # Return 'pending', 'completed', etc. (lowercase)
        # Handle string values - ensure lowercase
        if isinstance(value, str):
            value_lower = value.lower()
            # Validate it's a valid enum value
            if value_lower in ['pending', 'completed', 'failed', 'expired']:
                return value_lower
            return value_lower
        return value
    
    def process_result_value(self, value, dialect):
        """Convert database value back to enum when reading from database."""
        if value is None:
            return None
        if isinstance(value, str):
            return PaymentStatus(value.lower())  # Convert 'pending' -> PaymentStatus.PENDING
        return value


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
    # Use String type and explicitly convert enum to lowercase string
    # Database has paymentstatus enum, but we handle conversion in application code
    payment_status = Column(String, default="pending", nullable=False)
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

