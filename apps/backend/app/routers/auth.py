"""Authentication router."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
    encrypt_sensitive_data,
    decrypt_sensitive_data
)
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, OnboardingData, OnboardingStatusResponse
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """Authenticate user and return access token."""
    
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return current_user


@router.post("/onboarding", response_model=UserResponse)
async def submit_onboarding(
    onboarding_data: OnboardingData,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit user onboarding information."""

    # Check if user is already onboarded
    if current_user.is_onboarded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has already completed onboarding"
        )

    # Update user with onboarding data
    current_user.date_of_birth = onboarding_data.date_of_birth
    current_user.phone_number = onboarding_data.phone_number
    current_user.nationality = onboarding_data.nationality
    # Encrypt passport number for security
    if onboarding_data.passport_number:
        current_user.passport_number = encrypt_sensitive_data(onboarding_data.passport_number)
    else:
        current_user.passport_number = None

    current_user.country_of_residence = onboarding_data.country_of_residence
    current_user.state_province = onboarding_data.state_province
    current_user.city = onboarding_data.city
    current_user.postal_code = onboarding_data.postal_code

    current_user.emergency_contact_name = onboarding_data.emergency_contact_name
    current_user.emergency_contact_phone = onboarding_data.emergency_contact_phone
    current_user.emergency_contact_relationship = onboarding_data.emergency_contact_relationship

    current_user.has_pre_existing_conditions = onboarding_data.has_pre_existing_conditions
    current_user.is_frequent_traveler = onboarding_data.is_frequent_traveler
    current_user.preferred_coverage_type = onboarding_data.preferred_coverage_type

    # Mark user as onboarded
    current_user.is_onboarded = True
    from datetime import datetime as dt
    current_user.onboarded_at = dt.now()

    db.commit()
    db.refresh(current_user)

    return current_user


@router.get("/onboarding-status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    current_user: User = Depends(get_current_user)
):
    """Check if current user has completed onboarding."""
    return {
        "is_onboarded": current_user.is_onboarded,
        "onboarded_at": current_user.onboarded_at
    }
