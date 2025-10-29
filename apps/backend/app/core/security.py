"""Security utilities for authentication and authorization."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
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


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user."""
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
