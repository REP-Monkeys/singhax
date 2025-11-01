"""Chat conversation schemas for request/response validation."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
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


# New schemas for Phase 4 Chat API

class ChatMessageRequest(BaseModel):
    """Request schema for sending a chat message."""
    session_id: str  # UUID as string
    message: str = Field(..., min_length=1, max_length=5000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "I need travel insurance for Japan"
            }
        }


class ChatMessageResponse(BaseModel):
    """Response schema for chat message."""
    session_id: str
    message: str  # Agent's response text
    state: Dict[str, Any]  # Current conversation state
    quote: Optional[Dict[str, Any]] = None  # Quote data if available
    requires_human: bool = False  # Whether human handoff needed
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Where are you traveling to?",
                "state": {
                    "current_intent": "quote",
                    "trip_details": {},
                    "travelers_data": {},
                    "preferences": {}
                },
                "quote": None,
                "requires_human": False
            }
        }


class ChatSessionCreate(BaseModel):
    """Request schema for creating a new chat session."""
    user_id: Optional[str] = None  # Optional user association
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class ChatSessionResponse(BaseModel):
    """Response schema for chat session."""
    session_id: str
    created_at: str  # ISO format datetime
    user_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "created_at": "2025-10-26T12:00:00Z",
                "user_id": None
            }
        }


class ChatSessionState(BaseModel):
    """Response schema for session state."""
    session_id: str
    state: Dict[str, Any]
    messages: List[Dict[str, str]]  # List of {"role": "user/assistant", "content": "text"}
    policy: Optional[Dict[str, Any]] = None  # Policy details if confirmed
    policy_confirmed: bool = False  # Whether policy has been confirmed
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "state": {"current_intent": "quote"},
                "messages": [
                    {"role": "user", "content": "I need insurance"},
                    {"role": "assistant", "content": "Where are you traveling?"}
                ],
                "policy": None,
                "policy_confirmed": False
            }
        }


class ImageUploadResponse(BaseModel):
    """Response schema for image upload with OCR."""
    session_id: str
    image_id: str
    filename: str
    ocr_result: Dict[str, Any]
    message: Optional[str] = None  # Suggested message to send with extracted text
    document_id: Optional[str] = None  # Document ID from database for editing
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "image_id": "img_123456",
                "filename": "booking_confirmation.pdf",
                "ocr_result": {
                    "text": "Extracted text from document...",
                    "confidence": 85.5,
                    "word_count": 150,
                    "file_type": "pdf"
                },
                "message": "I've uploaded a booking confirmation. Extracted text: ..."
            }
        }
