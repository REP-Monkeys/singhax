"""
Simple unit tests for voice components (no API imports).
"""

import pytest
from pydantic import ValidationError
import uuid

from app.schemas.voice import (
    TranscribeRequest,
    TranscribeResponse,
    SynthesizeRequest,
    VoiceTranscriptCreate
)
from app.models.voice_transcript import VoiceTranscript


class TestVoiceSchemas:
    """Test voice request/response schemas."""
    
    def test_transcribe_response_valid(self):
        """Test TranscribeResponse with valid data."""
        response = TranscribeResponse(
            success=True,
            text="What is my medical coverage?",
            duration=3.5,
            language="en"
        )
        
        assert response.success is True
        assert response.text == "What is my medical coverage?"
        assert response.duration == 3.5
        assert response.language == "en"
    
    def test_transcribe_response_minimal(self):
        """Test TranscribeResponse with only required fields."""
        response = TranscribeResponse(
            success=True,
            text="Hello world"
        )
        
        assert response.success is True
        assert response.text == "Hello world"
        assert response.duration is None
        assert response.language is None
    
    def test_synthesize_request_valid(self):
        """Test SynthesizeRequest with valid text."""
        request = SynthesizeRequest(text="Hello world")
        
        assert request.text == "Hello world"
        assert request.voice_id is None
    
    def test_synthesize_request_with_voice(self):
        """Test SynthesizeRequest with custom voice ID."""
        request = SynthesizeRequest(
            text="Hello",
            voice_id="custom_voice_123"
        )
        
        assert request.text == "Hello"
        assert request.voice_id == "custom_voice_123"
    
    def test_synthesize_request_empty_text_fails(self):
        """Test SynthesizeRequest rejects empty text."""
        with pytest.raises(ValidationError):
            SynthesizeRequest(text="")
    
    def test_synthesize_request_text_too_long_fails(self):
        """Test SynthesizeRequest rejects text over 5000 chars."""
        long_text = "x" * 6000
        
        with pytest.raises(ValidationError) as exc_info:
            SynthesizeRequest(text=long_text)
        
        assert "5000" in str(exc_info.value) or "max_length" in str(exc_info.value)
    
    def test_voice_transcript_create_schema(self):
        """Test VoiceTranscriptCreate schema."""
        data = VoiceTranscriptCreate(
            session_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            user_audio_transcript="What's my coverage?",
            ai_response_text="Your coverage is...",
            duration_seconds=3.5
        )
        
        assert data.user_audio_transcript == "What's my coverage?"
        assert data.ai_response_text == "Your coverage is..."
        assert data.duration_seconds == 3.5


class TestVoiceTranscriptModel:
    """Test VoiceTranscript database model."""
    
    def test_model_creates_with_all_fields(self):
        """Test VoiceTranscript model can be created."""
        transcript_id = uuid.uuid4()
        session_id = str(uuid.uuid4())
        user_id = uuid.uuid4()
        
        transcript = VoiceTranscript(
            id=transcript_id,
            session_id=session_id,
            user_id=user_id,
            user_audio_transcript="What is my coverage?",
            ai_response_text="Your coverage is $500,000.",
            duration_seconds=3.5
        )
        
        assert transcript.id == transcript_id
        assert transcript.session_id == session_id
        assert transcript.user_id == user_id
        assert transcript.user_audio_transcript == "What is my coverage?"
        assert transcript.ai_response_text == "Your coverage is $500,000."
        assert transcript.duration_seconds == 3.5
    
    def test_model_creates_without_duration(self):
        """Test VoiceTranscript with optional duration."""
        transcript = VoiceTranscript(
            id=uuid.uuid4(),
            session_id=str(uuid.uuid4()),
            user_id=uuid.uuid4(),
            user_audio_transcript="Test",
            ai_response_text="Response"
        )
        
        assert transcript.duration_seconds is None
    
    def test_model_repr(self):
        """Test string representation."""
        session_id = str(uuid.uuid4())
        transcript = VoiceTranscript(
            id=uuid.uuid4(),
            session_id=session_id,
            user_id=uuid.uuid4(),
            user_audio_transcript="Test",
            ai_response_text="Response"
        )
        
        repr_str = repr(transcript)
        assert "VoiceTranscript" in repr_str
        assert session_id[:8] in repr_str
    
    def test_model_tablename(self):
        """Test table name is correct."""
        assert VoiceTranscript.__tablename__ == "voice_transcripts"


class TestVoiceConfiguration:
    """Test voice configuration settings."""
    
    def test_config_has_elevenlabs_settings(self):
        """Test configuration includes all voice settings."""
        from app.core.config import settings
        
        # Check ElevenLabs settings exist
        assert hasattr(settings, 'elevenlabs_api_key')
        assert hasattr(settings, 'elevenlabs_voice_id')
        assert hasattr(settings, 'elevenlabs_model')
        assert hasattr(settings, 'max_audio_size_mb')
        assert hasattr(settings, 'audio_timeout_seconds')
    
    def test_config_defaults(self):
        """Test voice configuration has correct defaults."""
        from app.core.config import settings
        
        # Bella voice ID
        assert settings.elevenlabs_voice_id == "EXAVITQu4vr4xnSDxMaL"
        
        # Turbo V2 model
        assert settings.elevenlabs_model == "eleven_turbo_v2"
        
        # 5MB limit
        assert settings.max_audio_size_mb == 5
        
        # 10 second timeout
        assert settings.audio_timeout_seconds == 10
    
    def test_config_api_key_loaded(self):
        """Test ElevenLabs API key is loaded from environment."""
        from app.core.config import settings
        
        # Should have API key (may be None in test environment)
        # Just check the attribute exists
        api_key = settings.elevenlabs_api_key
        assert api_key is None or isinstance(api_key, str)
        
        if api_key:
            # If set, should start with sk_
            assert api_key.startswith("sk_")


# Note: Router tests skipped - require running server to test properly
# See scripts/test_voice_endpoints.py for manual testing


class TestVoiceUtilities:
    """Test voice utility functions."""
    
    def test_audio_chunk_concatenation(self):
        """Test audio chunks join correctly."""
        chunks = [b"chunk1", b"chunk2", b"chunk3"]
        result = b"".join(chunks)
        
        assert result == b"chunk1chunk2chunk3"
        assert len(result) == 18
    
    def test_file_size_calculation(self):
        """Test file size calculation to MB."""
        bytes_data = b"x" * (2 * 1024 * 1024)  # 2MB
        size_mb = len(bytes_data) / (1024 * 1024)
        
        assert size_mb == 2.0
    
    def test_session_id_truncation(self):
        """Test session ID truncation for logging."""
        session_id = str(uuid.uuid4())
        truncated = session_id[:8]
        
        assert len(truncated) == 8
        assert session_id.startswith(truncated)


class TestDatabaseTable:
    """Test voice_transcripts table exists."""
    
    def test_table_exists_in_database(self):
        """Test voice_transcripts table was created."""
        from sqlalchemy import create_engine, text
        from app.core.config import settings
        
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_name = 'voice_transcripts'"
            )).fetchone()
            
            assert result is not None
            assert result[0] == "voice_transcripts"
    
    def test_table_has_required_columns(self):
        """Test voice_transcripts has all required columns."""
        from sqlalchemy import create_engine, text
        from app.core.config import settings
        
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'voice_transcripts' "
                "ORDER BY ordinal_position"
            )).fetchall()
            
            columns = [row[0] for row in result]
            
            assert 'id' in columns
            assert 'session_id' in columns
            assert 'user_id' in columns
            assert 'user_audio_transcript' in columns
            assert 'ai_response_text' in columns
            assert 'duration_seconds' in columns
            assert 'created_at' in columns
    
    def test_table_has_indexes(self):
        """Test voice_transcripts has proper indexes."""
        from sqlalchemy import create_engine, text
        from app.core.config import settings
        
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT indexname FROM pg_indexes "
                "WHERE tablename = 'voice_transcripts'"
            )).fetchall()
            
            indexes = [row[0] for row in result]
            
            # Should have indexes on key columns
            assert any('session_id' in idx for idx in indexes)
            assert any('user_id' in idx for idx in indexes)
            assert any('created_at' in idx for idx in indexes)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  VOICE FEATURE - SIMPLE UNIT TESTS")
    print("="*70 + "\n")
    pytest.main([__file__, "-v", "-s"])

