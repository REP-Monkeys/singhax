"""Trips router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.trip import Trip
from app.schemas.trip import TripCreate, TripResponse

router = APIRouter(prefix="/trips", tags=["trips"])


@router.post("/", response_model=TripResponse)
async def create_trip(
    trip_data: TripCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new trip."""
    
    trip = Trip(
        user_id=current_user.id,
        start_date=trip_data.start_date,
        end_date=trip_data.end_date,
        destinations=trip_data.destinations,
        flight_refs=trip_data.flight_refs,
        accommodation_refs=trip_data.accommodation_refs,
        total_cost=trip_data.total_cost
    )
    
    db.add(trip)
    db.commit()
    db.refresh(trip)
    
    return trip


@router.get("/", response_model=List[TripResponse])
async def get_trips(
    status: str = None,  # Filter by status: draft, ongoing, completed, past
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's trips, optionally filtered by status."""

    query = db.query(Trip).filter(Trip.user_id == current_user.id)

    if status:
        query = query.filter(Trip.status == status)

    # Order by created_at desc (newest first)
    trips = query.order_by(Trip.created_at.desc()).all()
    return trips


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific trip."""
    
    trip = db.query(Trip).filter(
        Trip.id == trip_id,
        Trip.user_id == current_user.id
    ).first()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    return trip


@router.post("/{trip_id}/events")
async def create_trip_event(
    trip_id: str,
    event_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a trip event (delay, baggage issue, etc.)."""
    
    trip = db.query(Trip).filter(
        Trip.id == trip_id,
        Trip.user_id == current_user.id
    ).first()
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    # TODO: Process trip event and suggest claims if applicable
    
    return {
        "message": "Trip event recorded successfully",
        "event_type": event_data.get("type"),
        "suggested_actions": ["file_claim", "contact_airline"]
    }
