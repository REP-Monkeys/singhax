"""Chat schemas."""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel
from uuid import UUID


class ChatMessage(BaseModel):
    """Schema for chat message."""
    role: str  # user, assistant, system
    message: str
    rationale: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Schema for chat response."""
    id: UUID
    user_id: UUID
    role: str
    message: str
    rationale: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class VoiceRequest(BaseModel):
    """Schema for voice input request."""
    audio_data: Optional[str] = None  # Base64 encoded audio
    transcript: Optional[str] = None  # Pre-transcribed text


class VoiceResponse(BaseModel):
    """Schema for voice response."""
    transcript: Optional[str] = None
    response: str
    success: bool = True
