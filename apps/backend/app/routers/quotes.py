"""Quotes router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.core.security import get_current_user_supabase as get_current_user
from app.models.user import User
from app.models.quote import Quote
from app.schemas.quote import QuoteCreate, QuoteUpdate, QuoteResponse, QuotePriceRequest
from app.services.pricing import PricingService

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.post("/", response_model=QuoteResponse)
async def create_quote(
    quote_data: QuoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new quote."""
    
    # Create quote
    quote = Quote(
        user_id=current_user.id,
        trip_id=quote_data.trip_id,
        product_type=quote_data.product_type,
        selected_tier=quote_data.selected_tier,
        travelers=quote_data.travelers,
        activities=quote_data.activities
    )
    
    db.add(quote)
    db.commit()
    db.refresh(quote)
    
    return quote


@router.get("/", response_model=List[QuoteResponse])
async def get_quotes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's quotes."""
    
    quotes = db.query(Quote).filter(Quote.user_id == current_user.id).all()
    return quotes


@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific quote."""
    
    quote = db.query(Quote).filter(
        Quote.id == quote_id,
        Quote.user_id == current_user.id
    ).first()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    return quote


@router.put("/{quote_id}", response_model=QuoteResponse)
async def update_quote(
    quote_id: str,
    quote_data: QuoteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a quote."""
    
    quote = db.query(Quote).filter(
        Quote.id == quote_id,
        Quote.user_id == current_user.id
    ).first()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Update fields
    if quote_data.travelers is not None:
        quote.travelers = quote_data.travelers
    if quote_data.activities is not None:
        quote.activities = quote_data.activities
    if quote_data.risk_breakdown is not None:
        quote.risk_breakdown = quote_data.risk_breakdown
    
    db.commit()
    db.refresh(quote)
    
    return quote


@router.post("/{quote_id}/price")
async def calculate_price(
    quote_id: str,
    price_request: QuotePriceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate firm price for a quote."""
    
    quote = db.query(Quote).filter(
        Quote.id == quote_id,
        Quote.user_id == current_user.id
    ).first()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Get trip information
    trip = quote.trip
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trip not found for quote"
        )
    
    # Calculate trip duration
    pricing_service = PricingService()
    trip_duration = pricing_service.calculate_trip_duration(
        trip.start_date, trip.end_date
    )
    
    # Assess risk factors
    risk_factors = pricing_service.assess_risk_factors(
        quote.travelers,
        quote.activities,
        trip.destinations
    )
    
    # Calculate firm price
    price_result = pricing_service.calculate_firm_price(
        quote.product_type.value,
        quote.travelers,
        quote.activities,
        trip_duration,
        trip.destinations,
        risk_factors
    )
    
    if price_result["success"]:
        # Update quote with firm price
        quote.price_firm = price_result["price"]
        quote.breakdown = price_result["breakdown"]
        quote.status = "firmed"
        
        db.commit()
        db.refresh(quote)
        
        return {
            "quote_id": quote.id,
            "price": price_result["price"],
            "breakdown": price_result["breakdown"],
            "currency": price_result["currency"],
            "explanation": pricing_service.get_price_breakdown_explanation(
                price_result["price"],
                price_result["breakdown"],
                risk_factors
            )
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Price calculation failed: {price_result['error']}"
        )
