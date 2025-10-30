"""Core configuration settings for the ConvoTravelInsure backend."""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings


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
    
    # Supabase Configuration
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None
    supabase_jwt_secret: Optional[str] = None  # JWT secret for verifying Supabase tokens
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # External APIs
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    
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
    
    class Config:
        env_file = "../../.env"  # Look in project root
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
settings = Settings()
