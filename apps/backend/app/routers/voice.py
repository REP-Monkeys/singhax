"""Voice router for speech-to-text and text-to-speech."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.chat import VoiceRequest, VoiceResponse

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/", response_model=VoiceResponse)
async def process_voice_input(
    voice_data: VoiceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process voice input and return response."""
    
    # TODO: Implement real speech-to-text processing
    # For now, return mock response
    
    if voice_data.transcript:
        transcript = voice_data.transcript
    else:
        transcript = "Mock transcript from voice input"
    
    # TODO: Process transcript through conversation system
    response = f"I heard you say: '{transcript}'. This is a mock response from the voice system."
    
    return VoiceResponse(
        transcript=transcript,
        response=response,
        success=True
    )
