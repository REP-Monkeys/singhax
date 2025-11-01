"""
Database model for storing voice conversation transcripts.
"""

from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.core.db import Base


class VoiceTranscript(Base):
    """
    Store voice conversation transcripts for analytics and history.
    
    Note: We store TEXT only, not audio files (to save storage costs).
    """
    __tablename__ = "voice_transcripts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Conversation content
    user_audio_transcript = Column(Text, nullable=False)  # What user said
    ai_response_text = Column(Text, nullable=False)       # What AI responded
    
    # Metadata
    duration_seconds = Column(Float, nullable=True)  # Audio duration
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<VoiceTranscript {self.id} session={self.session_id[:8]}>"

