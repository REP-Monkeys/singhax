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
    is_onboarded: bool
    created_at: datetime

    class Config:
        from_attributes = True


class OnboardingData(BaseModel):
    """Schema for user onboarding data."""
    # Personal Information
    date_of_birth: datetime
    phone_number: str
    nationality: str
    passport_number: Optional[str] = None

    # Address Information
    country_of_residence: str
    state_province: Optional[str] = None
    city: str
    postal_code: str

    # Emergency Contact
    emergency_contact_name: str
    emergency_contact_phone: str
    emergency_contact_relationship: str

    # Travel & Insurance Preferences
    has_pre_existing_conditions: bool = False
    is_frequent_traveler: bool = False
    preferred_coverage_type: Optional[str] = None


class OnboardingStatusResponse(BaseModel):
    """Schema for onboarding status response."""
    is_onboarded: bool
    onboarded_at: Optional[datetime] = None


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
