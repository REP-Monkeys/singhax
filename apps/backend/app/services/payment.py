"""Payment service for handling Stripe payments."""

import uuid
import time
import stripe
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from decimal import Decimal

from app.core.config import settings
from app.models.payment import Payment, PaymentStatus
from app.models.quote import Quote, QuoteStatus
from app.models.user import User


class PaymentService:
    """Service for handling payment operations."""
    
    def __init__(self):
        """Initialize payment service with Stripe API key."""
        if settings.stripe_secret_key:
            stripe.api_key = settings.stripe_secret_key
    
    def create_payment_intent(
        self,
        quote: Quote,
        user: User,
        db: Session,
        product_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a payment intent and store payment record in database.
        
        Args:
            quote: Quote model instance
            user: User model instance
            db: Database session
            product_name: Optional product name override
            
        Returns:
            Dict with payment_intent_id and payment record
            
        Raises:
            ValueError: If quote doesn't have firm price or invalid status
        """
        # Validate quote has firm price
        if not quote.price_firm:
            raise ValueError("Quote does not have a firm price set")
        
        # Validate quote status (should be FIRMED for purchase)
        if quote.status != QuoteStatus.FIRMED:
            # Allow if quote has price_firm set, even if status isn't FIRMED yet
            if quote.price_firm is None:
                raise ValueError(f"Quote status is {quote.status.value}, cannot create payment")
        
        # Generate unique payment_intent_id (using pattern from reference)
        payment_intent_id = f"payment_{uuid.uuid4().hex[:12]}"
        
        # Convert price_firm to cents (Stripe expects integer cents)
        # price_firm is Decimal in dollars, multiply by 100 to get cents
        amount_cents = int(float(quote.price_firm) * 100)
        
        # Determine product name
        if not product_name:
            product_name = f"Travel Insurance - {quote.product_type.value.title()}"
        
        # Create payment record
        payment = Payment(
            payment_intent_id=payment_intent_id,
            user_id=user.id,
            quote_id=quote.id,
            payment_status=PaymentStatus.PENDING,
            amount=Decimal(amount_cents),
            currency=quote.currency or "SGD",
            product_name=product_name
        )
        
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        return {
            "payment_intent_id": payment_intent_id,
            "payment": payment
        }
    
    def create_stripe_checkout(
        self,
        payment_intent_id: str,
        amount: int,
        product_name: str,
        user_email: str,
        db: Session
    ) -> stripe.checkout.Session:
        """
        Create a Stripe checkout session.
        
        Args:
            payment_intent_id: Payment intent ID (our internal ID)
            amount: Amount in cents
            product_name: Product name for Stripe
            user_email: User email for Stripe
            db: Database session
            
        Returns:
            Stripe checkout session object
        """
        if not settings.stripe_secret_key:
            raise ValueError("Stripe secret key not configured")
        
        # Create checkout session (following reference pattern)
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'sgd',  # lowercase for Stripe
                    'unit_amount': amount,  # in cents
                    'product_data': {
                        'name': product_name,
                        'description': 'Travel Insurance Policy',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=settings.payment_success_url,
            cancel_url=settings.payment_cancel_url,
            client_reference_id=payment_intent_id,  # CRITICAL: Links Stripe to our DB
            customer_email=user_email,
        )
        
        # Update payment record with stripe_session_id
        payment = db.query(Payment).filter(
            Payment.payment_intent_id == payment_intent_id
        ).first()
        
        if payment:
            payment.stripe_session_id = checkout_session.id
            db.commit()
        
        return checkout_session
    
    def check_payment_status(
        self,
        payment_intent_id: str,
        db: Session
    ) -> Optional[str]:
        """
        Check payment status from database.
        
        Args:
            payment_intent_id: Payment intent ID
            db: Database session
            
        Returns:
            Payment status string or None if not found
        """
        payment = db.query(Payment).filter(
            Payment.payment_intent_id == payment_intent_id
        ).first()
        
        if not payment:
            return None
        
        return payment.payment_status.value
    
    def wait_for_payment_completion(
        self,
        payment_intent_id: str,
        db: Session,
        timeout: int = 300
    ) -> bool:
        """
        Poll database for payment completion.
        
        Args:
            payment_intent_id: Payment intent ID
            db: Database session
            timeout: Maximum seconds to wait (default 300 = 5 minutes)
            
        Returns:
            True if payment completed, False if timeout or failed/expired
        """
        start_time = time.time()
        poll_interval = 3  # seconds
        
        while (time.time() - start_time) < timeout:
            status = self.check_payment_status(payment_intent_id, db)
            
            if status == PaymentStatus.COMPLETED.value:
                return True
            elif status in [PaymentStatus.FAILED.value, PaymentStatus.EXPIRED.value]:
                return False
            
            # Wait before next poll
            time.sleep(poll_interval)
        
        # Timeout reached
        return False

