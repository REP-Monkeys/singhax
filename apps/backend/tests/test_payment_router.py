"""Tests for payment router and webhook handling."""

import pytest
import json
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.models.payment import Payment, PaymentStatus
from app.core.config import settings


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_payment():
    """Create mock payment record."""
    payment = Mock(spec=Payment)
    payment.id = uuid.uuid4()
    payment.payment_intent_id = "payment_123456789"
    payment.stripe_session_id = None
    payment.stripe_payment_intent = None
    payment.payment_status = PaymentStatus.PENDING
    payment.user_id = uuid.uuid4()
    payment.quote_id = uuid.uuid4()
    return payment


@pytest.fixture
def mock_db(mock_payment):
    """Create mock database session."""
    db = Mock()
    
    # Mock query chain
    query_mock = Mock()
    filter_mock = Mock()
    
    filter_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = mock_payment
    query_mock.filter.return_value = filter_mock
    db.query.return_value = query_mock
    db.commit = Mock()
    db.rollback = Mock()
    
    return db


class TestPaymentWebhook:
    """Test payment webhook endpoint."""
    
    def test_webhook_health_check(self, client):
        """Test payment router health check endpoint."""
        response = client.get("/api/v1/payments/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "payments-router"
    
    @patch('app.routers.payments.stripe.Webhook.construct_event')
    def test_webhook_checkout_session_completed(
        self,
        mock_stripe_construct,
        client,
        mock_db,
        mock_payment
    ):
        """Test webhook for successful checkout session."""
        # Mock Stripe event
        event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "client_reference_id": "payment_123456789",
                    "payment_intent": "pi_test_123"
                }
            }
        }
        
        mock_stripe_construct.return_value = event
        
        # Mock database dependency
        app.dependency_overrides = {}
        
        with patch('app.routers.payments.get_db', return_value=mock_db):
            # Mock request body
            payload = json.dumps(event).encode()
            
            response = client.post(
                "/api/v1/payments/webhook/stripe",
                content=payload,
                headers={"stripe-signature": "test_signature"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        # Verify payment status was updated
        assert mock_payment.payment_status == PaymentStatus.COMPLETED
        assert mock_payment.stripe_payment_intent == "pi_test_123"
        assert mock_payment.webhook_processed_at is not None
        mock_db.commit.assert_called()
    
    @patch('app.routers.payments.json.loads')
    def test_webhook_local_testing_mode(
        self,
        mock_json_loads,
        client,
        mock_db,
        mock_payment
    ):
        """Test webhook in local testing mode (no signature verification)."""
        event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "client_reference_id": "payment_123456789",
                    "payment_intent": "pi_test_123"
                }
            }
        }
        
        mock_json_loads.return_value = event
        
        with patch('app.routers.payments.get_db', return_value=mock_db):
            with patch('app.routers.payments.settings.stripe_webhook_secret', 'whsec_local_testing_12345'):
                payload = json.dumps(event).encode()
                
                response = client.post(
                    "/api/v1/payments/webhook/stripe",
                    content=payload
                )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    @patch('app.routers.payments.stripe.Webhook.construct_event')
    def test_webhook_checkout_session_expired(
        self,
        mock_stripe_construct,
        client,
        mock_db,
        mock_payment
    ):
        """Test webhook for expired checkout session."""
        event = {
            "type": "checkout.session.expired",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "client_reference_id": "payment_123456789"
                }
            }
        }
        
        mock_stripe_construct.return_value = event
        
        with patch('app.routers.payments.get_db', return_value=mock_db):
            payload = json.dumps(event).encode()
            
            response = client.post(
                "/api/v1/payments/webhook/stripe",
                content=payload,
                headers={"stripe-signature": "test_signature"}
            )
        
        assert response.status_code == 200
        
        # Verify payment status was updated to expired
        assert mock_payment.payment_status == PaymentStatus.EXPIRED
        mock_db.commit.assert_called()
    
    @patch('app.routers.payments.stripe.Webhook.construct_event')
    def test_webhook_payment_intent_failed(
        self,
        mock_stripe_construct,
        client,
        mock_db,
        mock_payment
    ):
        """Test webhook for failed payment intent."""
        event = {
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": "pi_test_123"
                }
            }
        }
        
        mock_stripe_construct.return_value = event
        
        # Mock payment query by stripe_payment_intent
        mock_payment.stripe_payment_intent = "pi_test_123"
        
        with patch('app.routers.payments.get_db', return_value=mock_db):
            payload = json.dumps(event).encode()
            
            response = client.post(
                "/api/v1/payments/webhook/stripe",
                content=payload,
                headers={"stripe-signature": "test_signature"}
            )
        
        assert response.status_code == 200
        
        # Verify payment status was updated to failed
        assert mock_payment.payment_status == PaymentStatus.FAILED
        mock_db.commit.assert_called()
    
    @patch('app.routers.payments.stripe.Webhook.construct_event')
    def test_webhook_invalid_signature(
        self,
        mock_stripe_construct,
        client
    ):
        """Test webhook with invalid signature."""
        mock_stripe_construct.side_effect = Exception("Invalid signature")
        
        payload = json.dumps({"type": "test"}).encode()
        
        with patch('app.routers.payments.settings.stripe_webhook_secret', 'whsec_real_secret'):
            response = client.post(
                "/api/v1/payments/webhook/stripe",
                content=payload,
                headers={"stripe-signature": "invalid_signature"}
            )
        
        assert response.status_code == 400
        data = response.json()
        assert "signature" in data["detail"].lower() or "invalid" in data["detail"].lower()
    
    @patch('app.routers.payments.stripe.Webhook.construct_event')
    def test_webhook_unhandled_event_type(
        self,
        mock_stripe_construct,
        client,
        mock_db
    ):
        """Test webhook with unhandled event type."""
        event = {
            "type": "customer.created",
            "data": {
                "object": {}
            }
        }
        
        mock_stripe_construct.return_value = event
        
        with patch('app.routers.payments.get_db', return_value=mock_db):
            payload = json.dumps(event).encode()
            
            response = client.post(
                "/api/v1/payments/webhook/stripe",
                content=payload,
                headers={"stripe-signature": "test_signature"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    @patch('app.routers.payments.stripe.Webhook.construct_event')
    def test_webhook_no_client_reference_id(
        self,
        mock_stripe_construct,
        client,
        mock_db
    ):
        """Test webhook when checkout session has no client_reference_id."""
        event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "client_reference_id": None,
                    "payment_intent": "pi_test_123"
                }
            }
        }
        
        mock_stripe_construct.return_value = event
        
        # Mock query to return None (payment not found)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('app.routers.payments.get_db', return_value=mock_db):
            payload = json.dumps(event).encode()
            
            response = client.post(
                "/api/v1/payments/webhook/stripe",
                content=payload,
                headers={"stripe-signature": "test_signature"}
            )
        
        # Should still return success (just logs warning)
        assert response.status_code == 200

