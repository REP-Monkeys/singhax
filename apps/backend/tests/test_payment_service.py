"""Tests for payment service."""

import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import datetime

from app.services.payment import PaymentService
from app.models.payment import Payment, PaymentStatus
from app.models.quote import Quote, QuoteStatus, ProductType
from app.models.user import User


@pytest.fixture
def mock_user():
    """Create mock user."""
    user = Mock(spec=User)
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_quote():
    """Create mock quote with firm price."""
    quote = Mock(spec=Quote)
    quote.id = uuid.uuid4()
    quote.price_firm = Decimal("50.00")
    quote.currency = "SGD"
    quote.status = QuoteStatus.FIRMED
    quote.product_type = ProductType.SINGLE
    return quote


@pytest.fixture
def payment_service():
    """Create payment service instance."""
    with patch('app.services.payment.stripe'):
        service = PaymentService()
        return service


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    
    # Mock query chain for check_payment_status
    query_mock = Mock()
    filter_mock = Mock()
    query_mock.filter.return_value = filter_mock
    db.query.return_value = query_mock
    
    return db


class TestPaymentService:
    """Test PaymentService class."""
    
    def test_create_payment_intent_success(
        self,
        payment_service,
        mock_user,
        mock_quote,
        mock_db
    ):
        """Test successful payment intent creation."""
        result = payment_service.create_payment_intent(
            quote=mock_quote,
            user=mock_user,
            db=mock_db
        )
        
        assert "payment_intent_id" in result
        assert result["payment_intent_id"].startswith("payment_")
        assert result["payment"] is not None
        assert result["payment"].payment_status == PaymentStatus.PENDING
        assert result["payment"].amount == Decimal("5000")  # $50.00 in cents
        assert result["payment"].currency == "SGD"
        
        # Verify payment was added to database
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_create_payment_intent_no_firm_price(
        self,
        payment_service,
        mock_user,
        mock_db
    ):
        """Test payment intent creation fails when quote has no firm price."""
        quote = Mock(spec=Quote)
        quote.price_firm = None
        
        with pytest.raises(ValueError, match="does not have a firm price"):
            payment_service.create_payment_intent(
                quote=quote,
                user=mock_user,
                db=mock_db
            )
    
    def test_create_payment_intent_with_product_name(
        self,
        payment_service,
        mock_user,
        mock_quote,
        mock_db
    ):
        """Test payment intent creation with custom product name."""
        result = payment_service.create_payment_intent(
            quote=mock_quote,
            user=mock_user,
            db=mock_db,
            product_name="Custom Product Name"
        )
        
        assert result["payment"].product_name == "Custom Product Name"
    
    @patch('app.services.payment.stripe.checkout.Session.create')
    def test_create_stripe_checkout_success(
        self,
        mock_stripe_create,
        payment_service,
        mock_db
    ):
        """Test successful Stripe checkout session creation."""
        payment_intent_id = "payment_123456789"
        amount = 5000  # $50.00 in cents
        product_name = "Travel Insurance"
        user_email = "test@example.com"
        
        # Mock Stripe checkout session
        mock_session = Mock()
        mock_session.id = "cs_test_123"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test_123"
        mock_stripe_create.return_value = mock_session
        
        # Mock payment record in database
        mock_payment = Mock(spec=Payment)
        mock_payment.payment_intent_id = payment_intent_id
        mock_db.query.return_value.filter.return_value.first.return_value = mock_payment
        
        result = payment_service.create_stripe_checkout(
            payment_intent_id=payment_intent_id,
            amount=amount,
            product_name=product_name,
            user_email=user_email,
            db=mock_db
        )
        
        assert result == mock_session
        mock_stripe_create.assert_called_once()
        
        # Verify checkout session was created with correct parameters
        call_args = mock_stripe_create.call_args
        assert call_args[1]['payment_method_types'] == ['card']
        assert call_args[1]['mode'] == 'payment'
        assert call_args[1]['client_reference_id'] == payment_intent_id
        assert call_args[1]['customer_email'] == user_email
        
        # Verify payment record was updated
        assert mock_payment.stripe_session_id == mock_session.id
        mock_db.commit.assert_called()
    
    def test_create_stripe_checkout_no_secret_key(
        self,
        payment_service,
        mock_db
    ):
        """Test checkout creation fails when Stripe secret key not configured."""
        with patch('app.services.payment.settings.stripe_secret_key', None):
            with pytest.raises(ValueError, match="Stripe secret key not configured"):
                payment_service.create_stripe_checkout(
                    payment_intent_id="payment_123",
                    amount=5000,
                    product_name="Test",
                    user_email="test@example.com",
                    db=mock_db
                )
    
    def test_check_payment_status_found(
        self,
        payment_service,
        mock_db
    ):
        """Test checking payment status when payment exists."""
        payment_intent_id = "payment_123456789"
        mock_payment = Mock(spec=Payment)
        mock_payment.payment_status = PaymentStatus.COMPLETED
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_payment
        
        status = payment_service.check_payment_status(
            payment_intent_id=payment_intent_id,
            db=mock_db
        )
        
        assert status == "completed"
    
    def test_check_payment_status_not_found(
        self,
        payment_service,
        mock_db
    ):
        """Test checking payment status when payment doesn't exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        status = payment_service.check_payment_status(
            payment_intent_id="payment_nonexistent",
            db=mock_db
        )
        
        assert status is None
    
    @patch('app.services.payment.time.sleep')
    @patch('app.services.payment.time.time')
    def test_wait_for_payment_completion_success(
        self,
        mock_time,
        mock_sleep,
        payment_service,
        mock_db
    ):
        """Test waiting for payment completion when payment succeeds."""
        payment_intent_id = "payment_123456789"
        
        # Mock time progression
        mock_time.side_effect = [0, 3, 6]  # Start, after first poll, after second poll
        
        # Mock payment status progression
        mock_payment_pending = Mock(spec=Payment)
        mock_payment_pending.payment_status = PaymentStatus.PENDING
        mock_payment_completed = Mock(spec=Payment)
        mock_payment_completed.payment_status = PaymentStatus.COMPLETED
        
        query_mock = mock_db.query.return_value.filter.return_value.first
        query_mock.side_effect = [mock_payment_pending, mock_payment_completed]
        
        result = payment_service.wait_for_payment_completion(
            payment_intent_id=payment_intent_id,
            db=mock_db,
            timeout=300
        )
        
        assert result is True
        assert mock_sleep.call_count == 1  # One sleep before completion
    
    @patch('app.services.payment.time.sleep')
    @patch('app.services.payment.time.time')
    def test_wait_for_payment_completion_timeout(
        self,
        mock_time,
        mock_sleep,
        payment_service,
        mock_db
    ):
        """Test waiting for payment completion when timeout occurs."""
        payment_intent_id = "payment_123456789"
        
        # Mock time progression (exceeds timeout)
        mock_time.side_effect = [0, 3, 6, 301]  # Timeout after 301 seconds
        
        # Mock payment stays pending
        mock_payment = Mock(spec=Payment)
        mock_payment.payment_status = PaymentStatus.PENDING
        mock_db.query.return_value.filter.return_value.first.return_value = mock_payment
        
        result = payment_service.wait_for_payment_completion(
            payment_intent_id=payment_intent_id,
            db=mock_db,
            timeout=300
        )
        
        assert result is False
    
    @patch('app.services.payment.time.sleep')
    @patch('app.services.payment.time.time')
    def test_wait_for_payment_completion_failed(
        self,
        mock_time,
        mock_sleep,
        payment_service,
        mock_db
    ):
        """Test waiting for payment completion when payment fails."""
        payment_intent_id = "payment_123456789"
        
        # Mock time progression
        mock_time.side_effect = [0, 3]
        
        # Mock payment fails
        mock_payment = Mock(spec=Payment)
        mock_payment.payment_status = PaymentStatus.FAILED
        mock_db.query.return_value.filter.return_value.first.return_value = mock_payment
        
        result = payment_service.wait_for_payment_completion(
            payment_intent_id=payment_intent_id,
            db=mock_db,
            timeout=300
        )
        
        assert result is False

