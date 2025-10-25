"""Chat history model."""

from sqlalchemy import Column, String, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.db import Base


class ChatHistory(Base):
    """Chat history model for conversation tracking."""
    
    __tablename__ = "chat_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Message details
    role = Column(String, nullable=False)  # user, assistant, system
    message = Column(Text, nullable=False)
    rationale = Column(JSONB, nullable=True)  # AI reasoning and context
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_history")
    
    def __repr__(self):
        return f"<ChatHistory(id={self.id}, role={self.role}, created_at={self.created_at})>"
