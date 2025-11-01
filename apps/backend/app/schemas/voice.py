"""
Voice conversation schemas for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TranscribeRequest(BaseModel):
    """Request schema for audio transcription."""
    # Note: audio file will be in form data, not JSON body
    language: Optional[str] = Field(default="en", description="Language code for transcription")
    
    class Config:
        json_schema_extra = {
            "example": {
                "language": "en"
            }
        }


class TranscribeResponse(BaseModel):
    """Response schema for audio transcription."""
    success: bool
    text: str = Field(..., description="Transcribed text from audio")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    language: Optional[str] = Field(None, description="Detected language")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "text": "What is my medical coverage for skiing in Japan?",
                "duration": 3.5,
                "language": "en"
            }
        }


class SynthesizeRequest(BaseModel):
    """Request schema for speech synthesis."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize")
    voice_id: Optional[str] = Field(None, description="ElevenLabs voice ID (defaults to Bella)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Your Elite plan includes five hundred thousand dollars in medical coverage.",
                "voice_id": "EXAVITQu4vr4xnSDxMaL"
            }
        }


class VoiceTranscriptCreate(BaseModel):
    """Schema for creating voice transcript record."""
    session_id: str
    user_id: str
    user_audio_transcript: str
    ai_response_text: str
    duration_seconds: Optional[float] = None
    

class VoiceTranscriptResponse(BaseModel):
    """Schema for voice transcript response."""
    id: str
    session_id: str
    user_audio_transcript: str
    ai_response_text: str
    created_at: datetime
    
    class Config:
        from_attributes = True

