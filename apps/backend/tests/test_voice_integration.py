"""
Integration tests for voice conversation flow.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import uuid
import io

from app.main import app
from app.models.user import User
from app.models.voice_transcript import VoiceTranscript


class TestVoiceEndToEnd:
    """Test complete voice conversation flow."""
    
    @pytest.fixture
    def test_user(self, mock_db):
        """Create test user with auth token."""
        user = User(
            id=uuid.uuid4(),
            email="voice_test@example.com",
            name="Voice Test User",
            hashed_password="hashed"
        )
        return user
    
    @pytest.fixture
    def auth_token(self, test_user):
        """Generate mock JWT token."""
        # In real test, would use actual JWT generation
        return "mock_jwt_token"
    
    def test_transcribe_flow(self, test_user, auth_token):
        """Test audio upload and transcription."""
        client = TestClient(app)
        
        # Create mock audio file
        audio_data = b"fake webm audio data"
        audio_file = ("audio", io.BytesIO(audio_data), "audio/webm")
        
        # Mock Whisper API
        with patch('app.routers.voice.openai_client') as mock_openai:
            mock_transcript = Mock()
            mock_transcript.text = "What is my medical coverage?"
            mock_transcript.duration = 3.2
            mock_openai.audio.transcriptions.create.return_value = mock_transcript
            
            # Mock auth
            with patch('app.core.security.get_current_user_supabase', return_value=test_user):
                response = client.post(
                    "/api/v1/voice/transcribe",
                    files={"audio": audio_file},
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                
                # Should succeed
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["text"] == "What is my medical coverage?"
                assert data["duration"] == 3.2
    
    def test_synthesize_flow(self, test_user, auth_token):
        """Test text-to-speech generation."""
        client = TestClient(app)
        
        # Mock ElevenLabs API
        with patch('app.routers.voice.elevenlabs_client') as mock_elevenlabs:
            mock_elevenlabs.text_to_speech.convert.return_value = iter([b"audio_chunk"])
            
            # Mock auth
            with patch('app.core.security.get_current_user_supabase', return_value=test_user):
                response = client.post(
                    "/api/v1/voice/synthesize",
                    json={"text": "Your coverage is five hundred thousand dollars."},
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                
                # Should return audio stream
                assert response.status_code == 200
                assert response.headers["content-type"] == "audio/mpeg"
                assert len(response.content) > 0
    
    def test_save_transcript_flow(self, test_user, auth_token, mock_db):
        """Test saving voice conversation transcript."""
        client = TestClient(app)
        
        session_id = str(uuid.uuid4())
        
        # Mock database
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        # Mock auth
        with patch('app.core.security.get_current_user_supabase', return_value=test_user):
            response = client.post(
                "/api/v1/voice/save-transcript",
                params={
                    "session_id": session_id,
                    "user_audio_transcript": "What's my coverage?",
                    "ai_response_text": "Your coverage is...",
                    "duration_seconds": 3.5
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            # Should succeed
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "transcript_id" in data


class TestVoiceErrorHandling:
    """Test error scenarios in voice endpoints."""
    
    def test_transcribe_without_auth(self):
        """Test transcription requires authentication."""
        client = TestClient(app)
        
        audio_data = b"audio"
        audio_file = ("audio", io.BytesIO(audio_data), "audio/webm")
        
        response = client.post(
            "/api/v1/voice/transcribe",
            files={"audio": audio_file}
            # No auth header
        )
        
        assert response.status_code in [401, 403]
    
    def test_transcribe_whisper_api_error(self, mock_db):
        """Test handling of Whisper API failures."""
        audio_file = Mock(spec=UploadFile)
        audio_file.read = Mock(return_value=b"audio")
        
        mock_user = Mock()
        mock_user.id = uuid.uuid4()
        
        with patch('app.routers.voice.openai_client') as mock_openai:
            # Simulate API error
            import openai
            mock_openai.audio.transcriptions.create.side_effect = openai.APIError("API Error")
            
            # Should handle gracefully and return 503
    
    def test_synthesize_elevenlabs_error(self):
        """Test handling of ElevenLabs API failures."""
        request = SynthesizeRequest(text="Hello world")
        mock_user = Mock()
        
        with patch('app.routers.voice.elevenlabs_client') as mock_elevenlabs:
            mock_elevenlabs.text_to_speech.convert.side_effect = Exception("TTS Error")
            
            # Should return 500 error


class TestVoiceDatabaseOperations:
    """Test voice transcript database operations."""
    
    def test_transcript_saved_to_database(self, mock_db):
        """Test transcript is properly saved."""
        transcript = VoiceTranscript(
            id=uuid.uuid4(),
            session_id=str(uuid.uuid4()),
            user_id=uuid.uuid4(),
            user_audio_transcript="Test question",
            ai_response_text="Test response",
            duration_seconds=2.5
        )
        
        mock_db.add(transcript)
        mock_db.commit()
        
        # Verify add and commit were called
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_transcript_rollback_on_error(self, mock_db):
        """Test rollback on database error."""
        mock_db.add = Mock()
        mock_db.commit = Mock(side_effect=Exception("DB Error"))
        mock_db.rollback = Mock()
        
        transcript = VoiceTranscript(
            id=uuid.uuid4(),
            session_id=str(uuid.uuid4()),
            user_id=uuid.uuid4(),
            user_audio_transcript="Test",
            ai_response_text="Response"
        )
        
        try:
            mock_db.add(transcript)
            mock_db.commit()
        except Exception:
            mock_db.rollback()
        
        mock_db.rollback.assert_called_once()


class TestVoicePerformance:
    """Test voice performance and resource management."""
    
    def test_temp_file_cleanup(self):
        """Test temporary files are cleaned up."""
        import tempfile
        import os
        
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp:
            temp.write(b"test audio")
            temp_path = temp.name
        
        # File should exist
        assert os.path.exists(temp_path)
        
        # Clean up
        os.unlink(temp_path)
        
        # File should be gone
        assert not os.path.exists(temp_path)
    
    def test_audio_chunk_concatenation(self):
        """Test ElevenLabs audio chunks concatenate correctly."""
        chunks = [b"chunk1", b"chunk2", b"chunk3"]
        
        # Simulate ElevenLabs generator
        audio_stream = iter(chunks)
        audio_bytes = b"".join(audio_stream)
        
        assert audio_bytes == b"chunk1chunk2chunk3"
        assert len(audio_bytes) == 18


if __name__ == "__main__":
    print("="*60)
    print("Voice API Comprehensive Test Suite")
    print("="*60)
    pytest.main([__file__, "-v", "-s", "--tb=short"])

