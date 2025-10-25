"""Audit log model."""

from sqlalchemy import Column, String, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.db import Base


class AuditLog(Base):
    """Audit log model for tracking user actions."""
    
    __tablename__ = "audit_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Nullable for system actions
    
    # Action details
    action = Column(String, nullable=False)  # create, update, delete, login, etc.
    entity = Column(String, nullable=False)  # quote, policy, claim, etc.
    entity_id = Column(UUID(as_uuid=True), nullable=True)  # ID of affected entity
    payload = Column(JSONB, nullable=True)  # Additional context and data
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, entity={self.entity})>"
