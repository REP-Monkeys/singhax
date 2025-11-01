"""Payments router for Stripe webhook handling."""

import logging
import json
from typing import Dict, Any
from datetime import datetime, date

import stripe
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.config import settings
from app.core.db import get_db
from app.core.security import get_current_user_supabase
from app.models.payment import Payment, PaymentStatus
from app.models.quote import Quote, TierType
from app.models.user import User
from app.services.payment import PaymentService

logger = logging.getLogger("payment-webhook")

router = APIRouter(prefix="/payments", tags=["payments"])


class CreateCheckoutRequest(BaseModel):
    """Request to create a Stripe checkout session."""
    session_id: str  # Chat session ID
    selected_tier: str  # 'standard', 'elite', or 'premier'


class CreateCheckoutResponse(BaseModel):
    """Response from creating a Stripe checkout session."""
    checkout_url: str
    payment_intent_id: str


@router.get("/health")
async def health():
    """Health check endpoint for payments service."""
    return {"status": "ok", "service": "payments-router"}


@router.post("/create-checkout", response_model=CreateCheckoutResponse)
async def create_checkout_session(
    request: CreateCheckoutRequest,
    current_user: User = Depends(get_current_user_supabase),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe checkout session for a selected insurance tier.

    This endpoint:
    1. Retrieves the quote data from the chat session
    2. Creates a Quote record if not exists
    3. Creates a Payment record
    4. Creates a Stripe checkout session
    5. Returns the checkout URL for the frontend to redirect to
    """
    try:
        # Get the conversation state from the chat session
        from app.agents.graph import create_conversation_graph
        from app.models.trip import Trip

        graph = create_conversation_graph(db)
        config = {"configurable": {"thread_id": request.session_id}}
        state = graph.get_state(config)

        if not state or not state.values:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found"
            )

        # Extract quote data
        quote_data = state.values.get("quote_data")
        if not quote_data or "quotes" not in quote_data:
            raise HTTPException(
                status_code=400,
                detail="No quote found in this session. Please complete the quote process first."
            )

        # Get selected tier price
        selected_tier = request.selected_tier.lower()
        if selected_tier not in quote_data["quotes"]:
            raise HTTPException(
                status_code=400,
                detail=f"Tier '{selected_tier}' not available in quote"
            )

        tier_quote = quote_data["quotes"][selected_tier]
        price = tier_quote["price"]  # In SGD

        # Create or get Quote record
        trip_id = state.values.get("trip_id")
        if not trip_id:
            raise HTTPException(
                status_code=400,
                detail="No trip associated with this session"
            )

        # Check if quote already exists for this trip with same price and tier
        from decimal import Decimal
        from app.models.quote import QuoteStatus, ProductType

        # selected_tier is already lowercase string from request, use directly
        existing_quote = db.query(Quote).filter(
            Quote.trip_id == trip_id,
            Quote.price_firm == Decimal(str(price)),
            Quote.selected_tier == selected_tier,  # Use lowercase string directly
            Quote.status == QuoteStatus.FIRMED
        ).first()

        if existing_quote:
            quote = existing_quote
        else:
            # Create new quote record
            # Get travelers and trip data
            travelers_data = state.values.get("travelers_data", {})
            trip_details = state.values.get("trip_details", {})
            preferences = state.values.get("preferences", {})
            
            # Build Ancileo JSON structures
            from app.services.json_builders import build_ancileo_quotation_json, build_ancileo_purchase_json

            # Parse name field (User model has single 'name' field, not first_name/last_name)
            if current_user.name:
                name_parts = current_user.name.split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ""
            else:
                first_name = ""
                last_name = ""

            user_data = {
                "first_name": first_name,
                "last_name": last_name,
                "email": current_user.email or ""
            }
            
            # Build quotation JSON
            ancileo_quotation_json = build_ancileo_quotation_json(
                trip_details=trip_details,
                travelers_data=travelers_data,
                preferences=preferences
            )
            
            # Build purchase JSON
            ancileo_purchase_json = build_ancileo_purchase_json(
                user_data=user_data,
                travelers_data=travelers_data
            )

            # Convert dates to strings for JSONB storage
            departure_date = trip_details.get("departure_date")
            return_date = trip_details.get("return_date")
            
            if isinstance(departure_date, date):
                departure_date_str = departure_date.strftime("%Y-%m-%d")
            else:
                departure_date_str = str(departure_date) if departure_date else None
            
            if isinstance(return_date, date):
                return_date_str = return_date.strftime("%Y-%m-%d")
            else:
                return_date_str = str(return_date) if return_date else None

            quote = Quote(
                user_id=current_user.id,
                trip_id=trip_id,
                price_firm=Decimal(str(price)),
                currency="SGD",
                status=QuoteStatus.FIRMED,
                product_type=ProductType.SINGLE,  # Use SINGLE for single-trip insurance
                selected_tier=selected_tier,  # Use lowercase string directly (database has enum, we use String column)
                travelers=travelers_data,
                activities=[{"adventure_sports": preferences.get("adventure_sports", False)}],
                breakdown={
                    "selected_tier": selected_tier,
                    "tier_details": tier_quote,
                    "destination": trip_details.get("destination"),
                    "departure_date": departure_date_str,
                    "return_date": return_date_str
                },
                ancileo_quotation_json=ancileo_quotation_json,
                ancileo_purchase_json=ancileo_purchase_json
            )
            db.add(quote)
            db.commit()
            db.refresh(quote)

        # Create payment using PaymentService
        payment_service = PaymentService()
        payment_result = payment_service.create_payment_intent(
            quote=quote,
            user=current_user,
            db=db,
            product_name=f"Travel Insurance - {selected_tier.title()} Plan"
        )

        # Create Stripe checkout session
        amount_cents = int(float(price) * 100)
        checkout_session = payment_service.create_stripe_checkout(
            payment_intent_id=payment_result["payment_intent_id"],
            amount=amount_cents,
            product_name=f"Travel Insurance - {selected_tier.title()} Plan",
            user_email=current_user.email,
            db=db
        )

        logger.info(f"Created checkout session for user {current_user.id}, tier {selected_tier}")

        return CreateCheckoutResponse(
            checkout_url=checkout_session.url,
            payment_intent_id=payment_result["payment_intent_id"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events.
    
    Processes:
    - checkout.session.completed -> Update payment status to 'completed'
    - checkout.session.expired -> Update payment status to 'expired'
    - payment_intent.payment_failed -> Update payment status to 'failed'
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    webhook_secret = settings.stripe_webhook_secret
    
    # Log webhook receipt (without exposing secret)
    if webhook_secret:
        logger.info(f"Webhook secret configured (length: {len(webhook_secret)})")
    else:
        logger.warning("STRIPE_WEBHOOK_SECRET not configured - signature verification disabled")
    
    # Verify webhook signature
    try:
        if webhook_secret and len(webhook_secret) >= 20 and sig_header:
            # Full signature verification
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        else:
            # Local testing mode - parse without signature verification
            logger.warning("Using webhook without signature verification (local testing)")
            event = json.loads(payload.decode('utf-8'))
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception as e:
        if 'signature' in str(e).lower():
            logger.error(f"Invalid signature: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    event_type = event["type"]
    event_data = event["data"]["object"]
    
    logger.info(f"Received Stripe event: {event_type}")
    
    # Handle different event types
    if event_type == "checkout.session.completed":
        await handle_payment_success(event_data, db)
    elif event_type == "checkout.session.expired":
        await handle_payment_expired(event_data, db)
    elif event_type == "payment_intent.payment_failed":
        await handle_payment_failed(event_data, db)
    else:
        logger.info(f"Unhandled event type: {event_type}")
    
    return JSONResponse({"status": "success"})


async def handle_payment_success(session_data: Dict[str, Any], db: Session):
    """Handle successful payment checkout session."""
    session_id = session_data.get("id")
    client_reference_id = session_data.get("client_reference_id")  # Our payment_intent_id
    stripe_payment_intent = session_data.get("payment_intent")
    
    logger.info(f"Payment successful for session: {session_id}")
    
    if not client_reference_id:
        logger.warning(f"No client_reference_id found for session {session_id}")
        return
    
    try:
        # Find payment record by payment_intent_id
        payment = db.query(Payment).filter(
            Payment.payment_intent_id == client_reference_id
        ).first()
        
        if not payment:
            logger.warning(f"Payment record not found for payment_intent_id: {client_reference_id}")
            return
        
        # Update payment status
        payment.payment_status = "completed"
        payment.stripe_payment_intent = stripe_payment_intent
        payment.webhook_processed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(payment)
        
        logger.info(f"Updated payment status to completed for {client_reference_id}")
        
    except Exception as e:
        logger.error(f"Failed to update payment record: {e}")
        db.rollback()
        raise


async def handle_payment_expired(session_data: Dict[str, Any], db: Session):
    """Handle expired checkout session."""
    session_id = session_data.get("id")
    client_reference_id = session_data.get("client_reference_id")
    
    logger.info(f"Payment session expired: {session_id}")
    
    if not client_reference_id:
        logger.warning(f"No client_reference_id found for expired session {session_id}")
        return
    
    try:
        # Find payment record
        payment = db.query(Payment).filter(
            Payment.payment_intent_id == client_reference_id
        ).first()
        
        if not payment:
            logger.warning(f"Payment record not found for payment_intent_id: {client_reference_id}")
            return
        
        # Update payment status
        payment.payment_status = "expired"
        payment.webhook_processed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(payment)
        
        logger.info(f"Updated payment status to expired for {client_reference_id}")
        
    except Exception as e:
        logger.error(f"Failed to update expired payment record: {e}")
        db.rollback()
        raise


async def handle_payment_failed(payment_intent_data: Dict[str, Any], db: Session):
    """Handle failed payment intent."""
    stripe_payment_intent_id = payment_intent_data.get("id")
    
    logger.info(f"Payment failed for intent: {stripe_payment_intent_id}")
    
    try:
        # Find payment record by stripe_payment_intent
        payment = db.query(Payment).filter(
            Payment.stripe_payment_intent == stripe_payment_intent_id
        ).first()
        
        if not payment:
            logger.warning(f"Payment record not found for stripe_payment_intent: {stripe_payment_intent_id}")
            return
        
        # Update payment status
        payment.payment_status = "failed"
        payment.webhook_processed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(payment)
        
        logger.info(f"Updated payment status to failed for {payment.payment_intent_id}")
        
    except Exception as e:
        logger.error(f"Failed to update failed payment record: {e}")
        db.rollback()
        raise

