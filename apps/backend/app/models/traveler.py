"""Traveler model."""

from sqlalchemy import Column, String, Date, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.db import Base


class Traveler(Base):
    """Traveler model for trip participants."""
    
    __tablename__ = "travelers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    full_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    passport_no = Column(String, nullable=True)  # TODO: Encrypt in production
    is_primary = Column(Boolean, default=False)
    preexisting_conditions = Column(JSONB, default=list)  # List of condition descriptions
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="travelers")
    
    def __repr__(self):
        return f"<Traveler(id={self.id}, name={self.full_name}, is_primary={self.is_primary})>"
