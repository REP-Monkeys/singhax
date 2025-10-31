"""User model."""

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.db import Base


class User(Base):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Onboarding fields - Personal Information
    date_of_birth = Column(DateTime, nullable=True)
    phone_number = Column(String, nullable=True)
    nationality = Column(String, nullable=True)
    passport_number = Column(String, nullable=True)

    # Address Information
    country_of_residence = Column(String, nullable=True)
    state_province = Column(String, nullable=True)
    city = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)

    # Emergency Contact
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    emergency_contact_relationship = Column(String, nullable=True)

    # Travel & Insurance Preferences
    has_pre_existing_conditions = Column(Boolean, default=False)
    is_frequent_traveler = Column(Boolean, default=False)
    preferred_coverage_type = Column(String, nullable=True)  # e.g., "basic", "comprehensive", "adventure"

    # Onboarding Status
    is_onboarded = Column(Boolean, default=False)
    onboarded_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    travelers = relationship("Traveler", back_populates="user")
    trips = relationship("Trip", back_populates="user")
    quotes = relationship("Quote", back_populates="user")
    policies = relationship("Policy", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    chat_history = relationship("ChatHistory", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"
