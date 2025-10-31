"""Security utilities for authentication and authorization."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from cryptography.fernet import Fernet
import base64
import hashlib

from app.core.config import settings
from app.core.db import get_db
from app.models.user import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Data encryption for sensitive information (e.g., passport numbers)
# We use Fernet (symmetric encryption) with a key derived from the SECRET_KEY
def _get_encryption_key() -> bytes:
    """Generate a Fernet-compatible encryption key from the SECRET_KEY."""
    # Derive a 32-byte key from the SECRET_KEY using SHA-256
    key = hashlib.sha256(settings.secret_key.encode()).digest()
    # Fernet requires a base64-encoded 32-byte key
    return base64.urlsafe_b64encode(key)

_cipher = Fernet(_get_encryption_key())

# JWT token scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


def verify_supabase_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a Supabase JWT token.

    Supabase uses a JWT secret to sign tokens.
    The token contains user information in the 'sub' claim (user ID).
    """
    try:
        # Get JWT secret - try dedicated JWT secret first, fallback to service role key
        jwt_secret = settings.supabase_jwt_secret or settings.supabase_service_role_key

        if not jwt_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Supabase JWT secret not configured"
            )

        print(f"[DEBUG] Using JWT secret: {jwt_secret[:20]}... (length: {len(jwt_secret)})")
        print(f"[DEBUG] Token first 50 chars: {token[:50]}...")

        # Decode and verify the Supabase JWT
        # Supabase uses HS256 algorithm
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False}  # Supabase doesn't always include audience
        )
        print(f"[DEBUG] JWT verification successful! User ID: {payload.get('sub')}")
        return payload
    except JWTError as e:
        print(f"Supabase JWT verification failed: {e}")
        print(f"[DEBUG] Token: {token[:100]}...")
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user (legacy - uses custom JWT)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(credentials.credentials)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_user_supabase(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from Supabase JWT.

    This function:
    1. Validates the Supabase JWT token
    2. Extracts the user ID from the token
    3. Sets the RLS context for the database session
    4. Returns the user from the database
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Verify Supabase JWT token
    payload = verify_supabase_token(credentials.credentials)
    if payload is None:
        raise credentials_exception

    # Extract user ID from Supabase JWT (stored in 'sub' claim)
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Set RLS context for this database session
    # This tells Supabase/PostgreSQL which user is making the query
    # SET LOCAL is transaction-scoped, so it applies to subsequent queries in the same transaction
    try:
        import json
        # Use text() wrapper for SQLAlchemy 2.0+ compatibility
        # Escape single quotes in JSON to prevent SQL injection
        payload_json = json.dumps(payload).replace("'", "''")
        db.execute(text(f"SET LOCAL request.jwt.claims = '{payload_json}'"))
        db.execute(text(f"SET LOCAL request.jwt.claim.sub = '{user_id}'"))
        # Flush to ensure SET LOCAL is executed before query
        db.flush()
    except Exception as e:
        print(f"Warning: Failed to set RLS context: {e}")
        # Don't fail the request if RLS context setting fails
        # RLS policies will still work based on explicit user_id checks
        # Rollback the SET LOCAL statements if they failed
        try:
            db.rollback()
        except:
            pass

    # Get user from database
    # The user.id in our database should match the Supabase auth.users.id
    try:
        user = db.query(User).filter(User.id == user_id).first()
    except Exception as db_error:
        # Database connection error - provide helpful error message
        error_msg = str(db_error)
        if "Connection refused" in error_msg or "OperationalError" in str(type(db_error).__name__):
            print(f"[ERROR] Database connection failed: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection failed. Please check your Supabase configuration and ensure the project is active."
            )
        # Re-raise other database errors
        raise

    if user is None:
        # User exists in Supabase but not in our database
        email = payload.get("email")

        # Check if user exists with same email but different ID (old auth system)
        existing_user = db.query(User).filter(User.email == email).first()

        if existing_user:
            # Update the existing user's ID to match Supabase
            print(f"[DEBUG] Migrating user {existing_user.id} -> {user_id} for email {email}")
            existing_user.id = user_id
            db.commit()
            db.refresh(existing_user)
            user = existing_user
        else:
            # Create new user
            print(f"[DEBUG] User {user_id} not found in database, creating...")
            user_metadata = payload.get("user_metadata", {})
            name = user_metadata.get("name") or email.split("@")[0] if email else "Unknown"

            user = User(
                id=user_id,
                email=email,
                name=name,
                hashed_password="",  # Supabase handles auth
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"[DEBUG] User {user_id} created successfully")

    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user with email and password."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def encrypt_sensitive_data(data: str) -> str:
    """
    Encrypt sensitive data (e.g., passport numbers) using Fernet symmetric encryption.

    Args:
        data: Plain text string to encrypt

    Returns:
        Base64-encoded encrypted string
    """
    if not data:
        return data
    encrypted_bytes = _cipher.encrypt(data.encode('utf-8'))
    return encrypted_bytes.decode('utf-8')


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """
    Decrypt sensitive data that was encrypted with encrypt_sensitive_data.

    Args:
        encrypted_data: Base64-encoded encrypted string

    Returns:
        Decrypted plain text string
    """
    if not encrypted_data:
        return encrypted_data
    try:
        decrypted_bytes = _cipher.decrypt(encrypted_data.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception:
        # If decryption fails, return empty string (corrupted or invalid data)
        return ""


# TODO: Implement proper session management for production
# TODO: Add password reset functionality
# TODO: Add email verification
# TODO: Implement role-based access control
