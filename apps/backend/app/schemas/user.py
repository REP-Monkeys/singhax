"""User schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from uuid import UUID


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    name: str


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
