"""
Claims Database Connection Management.

Separate engine for MSIG claims database to avoid mixing
with main application database (Supabase).
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator, Optional, Dict, Any, List
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Claims database engine (separate from main app DB)
claims_engine = None
ClaimsSessionLocal = None


def init_claims_db():
    """Initialize claims database connection."""
    global claims_engine, ClaimsSessionLocal
    
    if not settings.claims_database_url:
        logger.warning("Claims database URL not configured - claims intelligence disabled")
        return
    
    try:
        # Create engine with connection pooling
        claims_engine = create_engine(
            settings.claims_database_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            echo=settings.debug
        )
        
        # Create session factory
        ClaimsSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=claims_engine
        )
        
        # Test connection
        with claims_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM hackathon.claims"))
            count = result.scalar()
            logger.info(f"✅ Connected to claims database: {count} claims available")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize claims database: {e}")
        claims_engine = None
        ClaimsSessionLocal = None


@contextmanager
def get_claims_db() -> Generator[Session, None, None]:
    """
    Get claims database session.
    
    Usage:
        with get_claims_db() as db:
            result = db.execute(text("SELECT * FROM hackathon.claims"))
    """
    if ClaimsSessionLocal is None:
        raise RuntimeError("Claims database not initialized")
    
    session = ClaimsSessionLocal()
    try:
        yield session
    finally:
        session.close()


def execute_claims_query(
    query: str,
    params: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Execute a query on claims database and return results as list of dicts.
    
    Args:
        query: SQL query string
        params: Query parameters (for parameterized queries)
    
    Returns:
        List of dictionaries with query results
    """
    if claims_engine is None:
        raise RuntimeError("Claims database not initialized")
    
    with claims_engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        
        # Convert to list of dicts
        columns = result.keys()
        rows = result.fetchall()
        
        return [dict(zip(columns, row)) for row in rows]


def check_claims_db_health() -> bool:
    """Check if claims database is accessible."""
    try:
        if claims_engine is None:
            return False
        
        with claims_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return True
    except Exception as e:
        logger.error(f"Claims database health check failed: {e}")
        return False


# Initialize on module import
init_claims_db()

