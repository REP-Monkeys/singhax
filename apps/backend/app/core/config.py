"""Core configuration settings for the ConvoTravelInsure backend."""

import os
from pathlib import Path
from typing import List, Optional, Union
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field

# Load .env file from project root
from dotenv import load_dotenv

# Get the project root (3 levels up from this file)
project_root = Path(__file__).parent.parent.parent.parent
env_file = project_root / ".env"

# Load environment variables from .env file
if env_file.exists():
    load_dotenv(env_file)
    print(f"[CONFIG] Loaded .env from: {env_file}")
else:
    print(f"[CONFIG] No .env file found at: {env_file}")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_v1_prefix: str = "/api/v1"
    project_name: str = "ConvoTravelInsure"
    version: str = "1.0.0"
    description: str = "Conversational travel insurance quoting and claims platform"
    
    # Database - Supabase
    database_url: str = "postgresql://postgres:password@localhost:5432/convo_travel_insure"
    database_test_url: str = "postgresql://postgres:password@localhost:5432/convo_travel_insure_test"
    
    # Claims Database Configuration
    claims_database_url: Optional[str] = Field(
        default=None,
        description="PostgreSQL URL for MSIG claims database"
    )
    enable_claims_intelligence: bool = Field(
        default=True,
        description="Enable claims intelligence features"
    )
    claims_cache_ttl: int = Field(
        default=3600,
        description="Claims data cache TTL in seconds"
    )
    
    # Supabase Configuration
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None
    supabase_jwt_secret: Optional[str] = None  # JWT secret for verifying Supabase tokens
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # External APIs
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None  # For webhook signature verification
    
    # Voice Configuration (ElevenLabs + Whisper)
    enable_tts: bool = Field(
        default=False,
        description="Enable text-to-speech with ElevenLabs (set to False to save credits)"
    )
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: str = Field(
        default="EXAVITQu4vr4xnSDxMaL",  # Bella voice
        description="ElevenLabs voice ID for TTS"
    )
    elevenlabs_model: str = Field(
        default="eleven_turbo_v2",
        description="ElevenLabs TTS model"
    )
    
    # Audio processing limits
    max_audio_size_mb: int = Field(default=5, description="Max audio file size in MB")
    audio_timeout_seconds: int = Field(default=10, description="Audio processing timeout")
    
    # Ancileo MSIG API Configuration
    ancileo_msig_api_key: Optional[str] = None
    ancileo_api_base_url: str = "https://dev.api.ancileo.com"
    
    # Payment Configuration
    payment_success_url: str = "http://localhost:8085/success?session_id={CHECKOUT_SESSION_ID}"
    payment_cancel_url: str = "http://localhost:8085/cancel"
    
    # Email Configuration
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_use_tls: bool = True
    
    # LLM Configuration
    model_name: str = "llama3-8b-8192"  # Default Groq model
    embedding_model: str = "text-embedding-3-small"
    
    # Groq Configuration
    groq_model: Optional[str] = None  # Alternative Groq model specification
    groq_temperature: Optional[float] = None
    groq_max_tokens: Optional[int] = None
    groq_timeout: Optional[int] = None
    
    # Vector Store
    vector_dimension: int = 1536  # OpenAI embedding dimension
    
    # LangGraph Configuration
    # LangGraph checkpoint DB - falls back to database_url if not set
    langgraph_checkpoint_db: Optional[str] = None
    
    # Application Settings
    debug: bool = False
    environment: str = "development"
    
    # Frontend Configuration (optional)
    next_public_api_url: Optional[str] = None
    
    # CORS - stored as string internally, accessed as list via property
    allowed_origins_raw: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        validation_alias="allowed_origins",
        description="CORS allowed origins as comma-separated string"
    )
    
    model_config = ConfigDict(
        env_file="../../.env",  # Look in project root
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from .env
        env_parse_none_str=None  # Parse 'None' strings as None
    )
    
    @property
    def allowed_origins(self) -> List[str]:
        """Parse comma-separated string to list."""
        return [origin.strip() for origin in self.allowed_origins_raw.split(',') if origin.strip()]


# Global settings instance
settings = Settings()
