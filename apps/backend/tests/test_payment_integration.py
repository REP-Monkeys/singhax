"""
Integration tests for Stripe payment functionality.

These tests make REAL API calls to Stripe (using test keys).
Requires STRIPE_SECRET_KEY to be set in environment.

To run these tests:
    pytest tests/test_payment_integration.py -v -s
"""

import pytest
import uuid
import json
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import stripe
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from sqlalchemy.orm import Session
from app.core.db import get_db, SessionLocal
from app.services.payment import PaymentService
from app.models.payment import Payment, PaymentStatus
from app.models.quote import Quote, QuoteStatus, ProductType
from app.models.user import User
from app.models.trip import Trip


@pytest.fixture(scope="session")
def verify_stripe_configured():
    """Verify Stripe is configured before running integration tests."""
    if not settings.stripe_secret_key:
        pytest.skip("STRIPE_SECRET_KEY not set - skipping Stripe integration tests")
    if not settings.stripe_secret_key.startswith("sk_test_"):
        pytest.skip("STRIPE_SECRET_KEY must be a test key for integration tests")
    print("\n✓ Stripe test configuration verified")
    return True


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session):
    """Create test user."""
    user = User(
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        name="Test User",
        hashed_password="test_password_hash"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    yield user
    # Cleanup
    db_session.delete(user)
    db_session.commit()


@pytest.fixture
def test_trip(db_session, test_user):
    """Create test trip."""
    trip = Trip(
        user_id=test_user.id,
        destination="Japan",
        start_date=datetime.now() + timedelta(days=30),
        end_date=datetime.now() + timedelta(days=37),
        travelers=[{"name": "Test User", "age": 30}]
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)
    yield trip
    # Cleanup
    db_session.delete(trip)
    db_session.commit()


@pytest.fixture
def test_quote(db_session, test_user, test_trip):
    """Create test quote with firm price."""
    quote = Quote(
        user_id=test_user.id,
        trip_id=test_trip.id,
        product_type=ProductType.SINGLE,
        travelers=[{"age": 30}],
        activities=[{"type": "general"}],
        price_firm=Decimal("50.00"),
        currency="SGD",
        status=QuoteStatus.FIRMED,
        breakdown={
            "tier": "standard",
            "coverage": {
                "medical_coverage": 50000,
                "trip_cancellation": 5000
            },
            "price": 50.00
        }
    )
    db_session.add(quote)
    db_session.commit()
    db_session.refresh(quote)
    yield quote
    # Cleanup - delete related payments first
    db_session.query(Payment).filter(Payment.quote_id == quote.id).delete()
    db_session.delete(quote)
    db_session.commit()


class TestStripeIntegration:
    """Integration tests with real Stripe API."""
    
    def test_stripe_api_connection(self, verify_stripe_configured):
        """Test that we can connect to Stripe API."""
        # Set API key
        stripe.api_key = settings.stripe_secret_key
        
        # Make a simple API call to verify connection
        account = stripe.Account.retrieve()
        
        assert account is not None
        assert hasattr(account, "id")
        print(f"\n✓ Connected to Stripe account: {account.id}")
    
    def test_create_stripe_checkout_session(
        self,
        verify_stripe_configured,
        db_session,
        test_user,
        test_quote
    ):
        """Test creating a real Stripe checkout session."""
        # Initialize payment service
        payment_service = PaymentService()
        
        # Create payment intent in our database
        payment_result = payment_service.create_payment_intent(
            quote=test_quote,
            user=test_user,
            db=db_session
        )
        
        payment_intent_id = payment_result["payment_intent_id"]
        print(f"\n✓ Created payment intent: {payment_intent_id}")
        
        # Verify payment record exists
        payment = db_session.query(Payment).filter(
            Payment.payment_intent_id == payment_intent_id
        ).first()
        
        assert payment is not None
        assert payment.payment_status == PaymentStatus.PENDING
        assert payment.amount == Decimal("5000")  # $50.00 in cents
        
        # Create real Stripe checkout session
        checkout_session = payment_service.create_stripe_checkout(
            payment_intent_id=payment_intent_id,
            amount=5000,  # $50.00 in cents
            product_name=f"Travel Insurance - {test_quote.product_type.value.title()}",
            user_email=test_user.email,
            db=db_session
        )
        
        # Verify checkout session was created
        assert checkout_session is not None
        assert checkout_session.id is not None
        assert checkout_session.url is not None
        assert checkout_session.id.startswith("cs_")
        assert "checkout.stripe.com" in checkout_session.url
        
        print(f"\n✓ Created Stripe checkout session: {checkout_session.id}")
        print(f"✓ Checkout URL: {checkout_session.url}")
        
        # Verify payment record was updated with session ID
        db_session.refresh(payment)
        assert payment.stripe_session_id == checkout_session.id
        
        # Verify checkout session has correct client_reference_id
        assert checkout_session.client_reference_id == payment_intent_id
        
        # Verify session details
        assert checkout_session.mode == "payment"
        assert checkout_session.payment_status == "unpaid"
        
        # Cleanup - expire the session
        stripe.checkout.Session.expire(checkout_session.id)
        print(f"\n✓ Expired checkout session: {checkout_session.id}")
    
    def test_retrieve_stripe_checkout_session(
        self,
        verify_stripe_configured,
        db_session,
        test_user,
        test_quote
    ):
        """Test retrieving a Stripe checkout session."""
        payment_service = PaymentService()
        
        # Create checkout session
        payment_result = payment_service.create_payment_intent(
            quote=test_quote,
            user=test_user,
            db=db_session
        )
        
        checkout_session = payment_service.create_stripe_checkout(
            payment_intent_id=payment_result["payment_intent_id"],
            amount=5000,
            product_name="Travel Insurance Test",
            user_email=test_user.email,
            db=db_session
        )
        
        # Retrieve the session from Stripe
        retrieved_session = stripe.checkout.Session.retrieve(checkout_session.id)
        
        assert retrieved_session.id == checkout_session.id
        assert retrieved_session.client_reference_id == payment_result["payment_intent_id"]
        assert retrieved_session.mode == "payment"
        
        print(f"\n✓ Retrieved checkout session: {retrieved_session.id}")
        
        # Cleanup
        stripe.checkout.Session.expire(checkout_session.id)
    
    def test_payment_status_check(
        self,
        verify_stripe_configured,
        db_session,
        test_user,
        test_quote
    ):
        """Test checking payment status from database."""
        payment_service = PaymentService()
        
        # Create payment intent
        payment_result = payment_service.create_payment_intent(
            quote=test_quote,
            user=test_user,
            db=db_session
        )
        
        payment_intent_id = payment_result["payment_intent_id"]
        
        # Check status (should be pending)
        status = payment_service.check_payment_status(
            payment_intent_id=payment_intent_id,
            db=db_session
        )
        
        assert status == "pending"
        print(f"\n✓ Payment status: {status}")
    
    def test_webhook_event_simulation(
        self,
        verify_stripe_configured,
        db_session,
        test_user,
        test_quote
    ):
        """Test webhook event handling with simulated Stripe event."""
        payment_service = PaymentService()
        
        # Create payment intent and checkout session
        payment_result = payment_service.create_payment_intent(
            quote=test_quote,
            user=test_user,
            db=db_session
        )
        
        checkout_session = payment_service.create_stripe_checkout(
            payment_intent_id=payment_result["payment_intent_id"],
            amount=5000,
            product_name="Travel Insurance Test",
            user_email=test_user.email,
            db=db_session
        )
        
        # Simulate checkout.session.completed event
        event_data = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": checkout_session.id,
                    "client_reference_id": payment_result["payment_intent_id"],
                    "payment_intent": checkout_session.payment_intent or f"pi_test_{uuid.uuid4().hex[:24]}",
                    "payment_status": "paid"
                }
            }
        }
        
        # Manually process the webhook event (simulating what the webhook handler does)
        from app.routers.payments import handle_payment_success
        
        # Import as async function
        import asyncio
        asyncio.run(handle_payment_success(event_data["data"]["object"], db_session))
        
        # Verify payment status was updated
        payment = db_session.query(Payment).filter(
            Payment.payment_intent_id == payment_result["payment_intent_id"]
        ).first()
        
        db_session.refresh(payment)
        assert payment.payment_status == PaymentStatus.COMPLETED
        assert payment.webhook_processed_at is not None
        
        print(f"\n✓ Payment status updated to: {payment.payment_status.value}")
        print(f"✓ Webhook processed at: {payment.webhook_processed_at}")
        
        # Cleanup
        stripe.checkout.Session.expire(checkout_session.id)
    
    def test_full_payment_flow(
        self,
        verify_stripe_configured,
        db_session,
        test_user,
        test_quote
    ):
        """Test complete payment flow from creation to completion."""
        payment_service = PaymentService()
        
        print("\n=== Testing Full Payment Flow ===")
        
        # Step 1: Create payment intent
        payment_result = payment_service.create_payment_intent(
            quote=test_quote,
            user=test_user,
            db=db_session
        )
        payment_intent_id = payment_result["payment_intent_id"]
        print(f"Step 1: Created payment intent - {payment_intent_id}")
        
        # Verify initial status
        status = payment_service.check_payment_status(payment_intent_id, db_session)
        assert status == "pending"
        print(f"Step 2: Initial status verified - {status}")
        
        # Step 3: Create checkout session
        checkout_session = payment_service.create_stripe_checkout(
            payment_intent_id=payment_intent_id,
            amount=5000,
            product_name="Travel Insurance - Test",
            user_email=test_user.email,
            db=db_session
        )
        print(f"Step 3: Created checkout session - {checkout_session.id}")
        print(f"        URL: {checkout_session.url}")
        
        # Step 4: Verify session details
        retrieved_session = stripe.checkout.Session.retrieve(checkout_session.id)
        assert retrieved_session.client_reference_id == payment_intent_id
        assert retrieved_session.mode == "payment"
        print(f"Step 4: Verified checkout session details")
        
        # Step 5: Simulate payment completion via webhook
        event_data = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": checkout_session.id,
                    "client_reference_id": payment_intent_id,
                    "payment_intent": f"pi_test_{uuid.uuid4().hex[:24]}",
                    "payment_status": "paid"
                }
            }
        }
        
        from app.routers.payments import handle_payment_success
        import asyncio
        asyncio.run(handle_payment_success(event_data["data"]["object"], db_session))
        
        # Step 6: Verify final status
        final_status = payment_service.check_payment_status(payment_intent_id, db_session)
        assert final_status == "completed"
        print(f"Step 5: Payment completed - status: {final_status}")
        
        # Verify payment record
        payment = db_session.query(Payment).filter(
            Payment.payment_intent_id == payment_intent_id
        ).first()
        db_session.refresh(payment)
        
        assert payment.payment_status == PaymentStatus.COMPLETED
        assert payment.stripe_session_id == checkout_session.id
        assert payment.webhook_processed_at is not None
        
        print(f"\n✓ Full payment flow completed successfully!")
        print(f"  Payment ID: {payment.id}")
        print(f"  Status: {payment.payment_status.value}")
        print(f"  Amount: ${payment.amount / 100:.2f} {payment.currency}")
        
        # Cleanup
        stripe.checkout.Session.expire(checkout_session.id)

