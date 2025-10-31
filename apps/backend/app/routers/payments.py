"""Payments router for Stripe webhook handling."""

import logging
import json
from typing import Dict, Any
from datetime import datetime

import stripe
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.payment import Payment, PaymentStatus

logger = logging.getLogger("payment-webhook")

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/health")
async def health():
    """Health check endpoint for payments service."""
    return {"status": "ok", "service": "payments-router"}


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
        payment.payment_status = PaymentStatus.COMPLETED
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
        payment.payment_status = PaymentStatus.EXPIRED
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
        payment.payment_status = PaymentStatus.FAILED
        payment.webhook_processed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(payment)
        
        logger.info(f"Updated payment status to failed for {payment.payment_intent_id}")
        
    except Exception as e:
        logger.error(f"Failed to update failed payment record: {e}")
        db.rollback()
        raise

