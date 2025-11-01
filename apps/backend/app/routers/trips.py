"""Trips router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.core.security import get_current_user_supabase as get_current_user
from app.models.user import User
from app.models.trip import Trip
from app.models.quote import Quote
from app.models.payment import Payment
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
    status: str = None,  # Filter by status: draft, ongoing, completed, past (comma-separated)
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's trips, optionally filtered by status.

    Args:
        status: Comma-separated list of statuses (e.g., "draft,ongoing,completed")
    """

    query = db.query(Trip).filter(Trip.user_id == current_user.id)

    if status:
        # Handle comma-separated status values
        status_list = [s.strip() for s in status.split(',')]
        query = query.filter(Trip.status.in_(status_list))

    # Order by created_at desc (newest first)
    trips = query.order_by(Trip.created_at.desc()).all()

    # For completed trips, ensure total_cost shows actual price paid instead of range
    for trip in trips:
        if trip.status == "completed" and trip.total_cost and " - " in trip.total_cost:
            # Trip still shows a range, try to get actual price from completed payment
            # Get the quote for this trip
            quote = db.query(Quote).filter(
                Quote.trip_id == trip.id,
                Quote.user_id == current_user.id
            ).order_by(Quote.created_at.desc()).first()
            
            if quote:
                # Check for completed payment
                completed_payment = db.query(Payment).filter(
                    Payment.quote_id == quote.id,
                    Payment.payment_status == "completed"
                ).first()
                
                if completed_payment and quote.price_firm:
                    # Update trip total_cost to actual price
                    actual_price = float(quote.price_firm)
                    trip.total_cost = f"SGD {actual_price:.2f}"
                    db.commit()
                    db.refresh(trip)
                    print(f"💰 Updated trip {trip.id} total_cost to actual price: {trip.total_cost}")

    print(f"📋 Fetched {len(trips)} trips for user {current_user.id} (status filter: {status})")

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
