"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.config import settings

# Create database engine with SSL support for Supabase
# For Supabase pooler connections, the SSL mode should be in the connection string
# Don't override it in connect_args to avoid conflicts
import re

# Check if connection string already has sslmode parameter
has_sslmode_in_url = "sslmode=" in settings.database_url
is_supabase = "supabase.co" in settings.database_url or "pooler.supabase.com" in settings.database_url

# Build connect_args - only add SSL if not already in URL
connect_args = {
    "connect_timeout": 10,  # 10 second connection timeout
}

# Only add sslmode to connect_args if it's not already in the connection string
if not has_sslmode_in_url:
    if is_supabase:
        # Force SSL for Supabase if not specified in URL
        connect_args["sslmode"] = "require"
    else:
        # No SSL for local connections
        connect_args["sslmode"] = "disable"

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,  # Number of connections to maintain
    max_overflow=10,  # Max connections beyond pool_size
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=settings.debug,
    connect_args=connect_args
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


def get_uuid():
    """Generate a new UUID."""
    return uuid.uuid4()


# Import all models to ensure they are registered with Base
# This needs to be done after Base is created
from app.models import *  # noqa: F401, F403
