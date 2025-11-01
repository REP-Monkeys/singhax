"""
Voice conversation endpoints for STT (Whisper) and TTS (ElevenLabs).
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import openai
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
import logging
import tempfile
import os
from typing import Optional
import uuid as uuid_pkg

from app.core.config import settings
from app.core.db import get_db
from app.core.security import get_current_user_supabase
from app.models.user import User
from app.models.voice_transcript import VoiceTranscript
from app.schemas.voice import (
    TranscribeResponse,
    SynthesizeRequest
)

router = APIRouter(prefix="/voice", tags=["voice"])
logger = logging.getLogger(__name__)

# Initialize clients
openai_client = openai.OpenAI(api_key=settings.openai_api_key)
elevenlabs_client = ElevenLabs(api_key=settings.elevenlabs_api_key)


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    audio: UploadFile = File(..., description="Audio file (webm, wav, mp3)"),
    language: str = "en",
    current_user: User = Depends(get_current_user_supabase),
    db: Session = Depends(get_db)
):
    """
    Transcribe user's voice to text using OpenAI Whisper.
    
    Supported formats: webm, wav, mp3, m4a
    Max size: 5MB (configurable)
    Timeout: 10 seconds
    
    Returns:
        TranscribeResponse with transcribed text
    """
    logger.info(f"🎤 Transcription request from user {current_user.id}")
    
    # Validate file size
    file_size = 0
    temp_file = None
    
    try:
        # Read file content
        content = await audio.read()
        file_size = len(content) / (1024 * 1024)  # Convert to MB
        
        if file_size > settings.max_audio_size_mb:
            raise HTTPException(
                status_code=413,
                detail=f"Audio file too large: {file_size:.2f}MB (max: {settings.max_audio_size_mb}MB)"
            )
        
        logger.info(f"   File size: {file_size:.2f}MB")
        
        # Save to temporary file (Whisper API requires file, not bytes)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp:
            temp.write(content)
            temp_file = temp.name
        
        # Transcribe using Whisper
        logger.info(f"   Calling Whisper API...")
        
        with open(temp_file, "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format="verbose_json"  # Get additional metadata
            )
        
        transcribed_text = transcript.text.strip()
        duration = getattr(transcript, 'duration', None)
        
        if not transcribed_text:
            raise HTTPException(
                status_code=400,
                detail="Could not transcribe audio. Please speak clearly and try again."
            )
        
        logger.info(f"   ✅ Transcribed ({duration}s): {transcribed_text[:50]}...")
        
        return TranscribeResponse(
            success=True,
            text=transcribed_text,
            duration=duration,
            language=language
        )
        
    except openai.APIError as e:
        logger.error(f"   ❌ Whisper API error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Speech recognition service unavailable. Please try again."
        )
        
    except Exception as e:
        logger.error(f"   ❌ Transcription error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process audio. Please try again."
        )
        
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
            logger.info(f"   🧹 Cleaned up temp file")


@router.post("/synthesize")
async def synthesize_speech(
    request: SynthesizeRequest,
    current_user: User = Depends(get_current_user_supabase)
):
    """
    Convert AI response text to speech using ElevenLabs.

    Uses Bella voice (warm, professional) with turbo_v2 model.
    Returns streaming MP3 audio.

    Args:
        request: Text to synthesize (max 5000 chars)

    Returns:
        Audio stream (audio/mpeg)
    """
    logger.info(f"🔊 TTS request from user {current_user.id}")
    logger.info(f"   Text length: {len(request.text)} chars")

    # Check if TTS is enabled
    if not settings.enable_tts:
        logger.info("   ⏸️  TTS is disabled (to enable, set ENABLE_TTS=true in .env)")
        raise HTTPException(
            status_code=503,
            detail="Text-to-speech is currently disabled. TTS credits are being conserved."
        )

    try:
        # Use Bella voice by default, or custom voice from request
        voice_id = request.voice_id or settings.elevenlabs_voice_id
        
        # Generate speech using ElevenLabs SDK
        audio_stream = elevenlabs_client.text_to_speech.convert(
            voice_id=voice_id,
            text=request.text,
            model_id=settings.elevenlabs_model,
            voice_settings=VoiceSettings(
                stability=0.5,        # More dynamic/emotional
                similarity_boost=0.75,
                style=0.0,            # Neutral delivery
                use_speaker_boost=True
            )
        )
        
        # Convert generator to bytes
        audio_bytes = b"".join(audio_stream)
        
        logger.info(f"   ✅ Generated {len(audio_bytes)} bytes of audio")
        
        # Stream audio back to client
        def generate():
            yield audio_bytes
        
        return StreamingResponse(
            generate(),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=response.mp3",
                "X-Text-Length": str(len(request.text)),
                "Access-Control-Expose-Headers": "X-Text-Length"
            }
        )
        
    except Exception as e:
        logger.error(f"   ❌ TTS error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate speech. Please try typing your message instead."
        )


@router.post("/save-transcript")
async def save_voice_transcript(
    session_id: str,
    user_audio_transcript: str,
    ai_response_text: str,
    duration_seconds: Optional[float] = None,
    current_user: User = Depends(get_current_user_supabase),
    db: Session = Depends(get_db)
):
    """
    Save voice conversation transcript to database.
    
    This is called after a complete voice exchange (user spoke, AI responded).
    We store TEXT only, not audio files.
    """
    try:
        transcript = VoiceTranscript(
            id=uuid_pkg.uuid4(),
            session_id=session_id,
            user_id=current_user.id,
            user_audio_transcript=user_audio_transcript,
            ai_response_text=ai_response_text,
            duration_seconds=duration_seconds
        )
        
        db.add(transcript)
        db.commit()
        
        logger.info(f"💾 Saved voice transcript for session {session_id[:8]}")
        
        return {"success": True, "transcript_id": str(transcript.id)}
        
    except Exception as e:
        logger.error(f"Failed to save transcript: {e}")
        db.rollback()
        # Don't fail the request if saving transcript fails
        return {"success": False, "error": str(e)}
