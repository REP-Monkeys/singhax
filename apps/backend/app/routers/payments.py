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


@router.post("/test-webhook/by-session/{stripe_session_id}")
async def test_webhook_by_session(
    stripe_session_id: str,
    db: Session = Depends(get_db)
):
    """
    Manually trigger webhook handler by Stripe checkout session ID.
    
    This endpoint simulates a successful payment webhook event.
    Useful for testing when Stripe webhooks aren't configured locally.
    No authentication required for testing purposes.
    """
    logger.info(f"🧪 Manual webhook test triggered for stripe_session_id: {stripe_session_id}")
    
    # Find payment record by stripe_session_id
    payment = db.query(Payment).filter(
        Payment.stripe_session_id == stripe_session_id
    ).first()
    
    if not payment:
        # Try to find by payment_intent_id if session_id doesn't match
        payment = db.query(Payment).filter(
            Payment.payment_intent_id == stripe_session_id
        ).first()
    
    if not payment:
        raise HTTPException(
            status_code=404,
            detail=f"Payment not found for stripe_session_id or payment_intent_id: {stripe_session_id}"
        )
    
    logger.info(f"✅ Found payment: payment_intent_id={payment.payment_intent_id}, status={payment.payment_status}")
    
    # Create mock webhook event data
    mock_event_data = {
        "id": stripe_session_id if stripe_session_id.startswith("cs_") else f"cs_test_{payment.payment_intent_id[:20]}",
        "client_reference_id": payment.payment_intent_id,  # This is what we use to find the payment
        "payment_intent": payment.stripe_payment_intent or f"pi_test_{payment.payment_intent_id[:20]}",
        "payment_status": "paid"
    }
    
    logger.info(f"🔧 Calling handle_payment_success with mock data")
    logger.info(f"   client_reference_id: {mock_event_data['client_reference_id']}")
    
    try:
        await handle_payment_success(mock_event_data, db)
        return {
            "success": True,
            "message": "Webhook handler executed successfully",
            "payment_intent_id": payment.payment_intent_id,
            "stripe_session_id": stripe_session_id
        }
    except Exception as e:
        logger.error(f"❌ Manual webhook test failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Webhook handler failed: {str(e)}"
        )


@router.post("/test-webhook/{payment_intent_id}")
async def test_webhook_manually(
    payment_intent_id: str,
    current_user: User = Depends(get_current_user_supabase),
    db: Session = Depends(get_db)
):
    """
    Manually trigger webhook handler for testing (requires auth).
    
    This endpoint simulates a successful payment webhook event.
    Useful for testing when Stripe webhooks aren't configured locally.
    """
    logger.info(f"🧪 Manual webhook test triggered for payment_intent_id: {payment_intent_id}")
    
    # Find payment record
    payment = db.query(Payment).filter(
        Payment.payment_intent_id == payment_intent_id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=404,
            detail=f"Payment not found for payment_intent_id: {payment_intent_id}"
        )
    
    # Verify payment belongs to current user
    if payment.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Payment does not belong to current user"
        )
    
    # Create mock webhook event data
    mock_event_data = {
        "id": payment.stripe_session_id or f"cs_test_{payment_intent_id[:20]}",
        "client_reference_id": payment_intent_id,
        "payment_intent": payment.stripe_payment_intent or f"pi_test_{payment_intent_id[:20]}",
        "payment_status": "paid"
    }
    
    logger.info(f"🔧 Calling handle_payment_success with mock data")
    
    try:
        await handle_payment_success(mock_event_data, db)
        return {
            "success": True,
            "message": "Webhook handler executed successfully",
            "payment_intent_id": payment_intent_id
        }
    except Exception as e:
        logger.error(f"❌ Manual webhook test failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Webhook handler failed: {str(e)}"
        )


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
    logger.info("=" * 60)
    logger.info("🔔 STRIPE WEBHOOK RECEIVED")
    logger.info("=" * 60)
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    logger.info(f"Payload size: {len(payload)} bytes")
    logger.info(f"Signature header present: {sig_header is not None}")
    
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
    
    logger.info(f"📨 Received Stripe event: {event_type}")
    logger.info(f"   Event data keys: {list(event_data.keys())}")
    
    # Handle different event types
    if event_type == "checkout.session.completed":
        logger.info("✅ Processing checkout.session.completed event")
        await handle_payment_success(event_data, db)
        logger.info("✅ Completed processing checkout.session.completed")
    elif event_type == "checkout.session.expired":
        await handle_payment_expired(event_data, db)
    elif event_type == "payment_intent.payment_failed":
        await handle_payment_failed(event_data, db)
    else:
        logger.info(f"Unhandled event type: {event_type}")
    
    return JSONResponse({"status": "success"})


async def handle_payment_success(session_data: Dict[str, Any], db: Session):
    """Handle successful payment checkout session."""
    logger.info("🔧 handle_payment_success called")
    logger.info(f"   Session data keys: {list(session_data.keys())}")
    
    stripe_session_id = session_data.get("id")
    client_reference_id = session_data.get("client_reference_id")  # Our payment_intent_id
    stripe_payment_intent = session_data.get("payment_intent")
    
    logger.info(f"💰 Payment successful for Stripe session: {stripe_session_id}")
    logger.info(f"   client_reference_id: {client_reference_id}")
    logger.info(f"   stripe_payment_intent: {stripe_payment_intent}")
    
    if not client_reference_id:
        logger.warning(f"No client_reference_id found for session {stripe_session_id}")
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
        
        # Get trip via payment -> quote -> trip
        quote = payment.quote
        if not quote:
            logger.error(f"Quote not found for payment {client_reference_id}")
            return
        
        trip = quote.trip
        if not trip:
            logger.error(f"Trip not found for quote {quote.id}")
            return
        
        # Get chat session_id from trip
        chat_session_id = trip.session_id
        logger.info(f"📝 Trip session_id: {chat_session_id}")
        if not chat_session_id:
            logger.warning(f"⚠️ No session_id found for trip {trip.id}")
            # Continue with policy creation even without chat session
        
        # Create policy using ConversationTools
        from app.agents.tools import ConversationTools
        from app.agents.llm_client import GroqLLMClient
        
        tools = ConversationTools(db, GroqLLMClient())
        policy_result = tools.create_policy_from_payment(client_reference_id)
        
        if not policy_result.get("success"):
            logger.error(f"Failed to create policy: {policy_result.get('error')}")
            # Don't raise - payment is already recorded as completed
            return
        
        policy_number = policy_result.get("policy_number")
        policy_id = policy_result.get("policy_id")
        logger.info(f"Successfully created policy {policy_number} (ID: {policy_id})")
        
        # Update trip status to "completed" (payment successful, policy created)
        trip.status = "completed"
        
        # Update trip total_cost to show actual price paid instead of range
        if quote.price_firm:
            # Format as "SGD {price:.2f}" to match the format used elsewhere
            actual_price = float(quote.price_firm)
            trip.total_cost = f"SGD {actual_price:.2f}"
            logger.info(f"💰 Updated trip {trip.id} total_cost to actual price: {trip.total_cost}")
        elif payment.amount:
            # Fallback to payment amount (stored in cents, convert to dollars)
            actual_price = float(payment.amount) / 100.0
            trip.total_cost = f"SGD {actual_price:.2f}"
            logger.info(f"💰 Updated trip {trip.id} total_cost from payment amount: {trip.total_cost}")
        
        db.commit()
        logger.info(f"✅ Updated trip {trip.id} status to completed")
        
        # Send confirmation message to chat session if session_id exists
        if chat_session_id:
            logger.info(f"💬 Attempting to add message to chat session: {chat_session_id}")
            try:
                confirmation_message = generate_payment_confirmation_message(
                    policy_number=policy_number,
                    trip=trip,
                    quote=quote
                )
                logger.info(f"   Generated confirmation message ({len(confirmation_message)} chars)")
                
                await add_message_to_chat_session(
                    session_id=chat_session_id,
                    message_content=confirmation_message,
                    db=db
                )
                logger.info(f"✅ Added confirmation message to chat session {chat_session_id}")
            except Exception as e:
                logger.error(f"❌ Failed to add message to chat session: {e}")
                import traceback
                traceback.print_exc()
                # Don't fail the whole webhook if chat message fails
        else:
            logger.warning("⚠️ Skipping chat message - no session_id available")
        
        # Send confirmation email
        try:
            from app.services.email import EmailService
            from app.models.user import User
            
            user = db.query(User).filter(User.id == payment.user_id).first()
            if user and user.email:
                email_service = EmailService()
                
                # Prepare policy details for email
                policy_details = {
                    "effective_date": trip.start_date.isoformat() if trip.start_date else "N/A",
                    "expiry_date": trip.end_date.isoformat() if trip.end_date else "N/A",
                    "selected_tier": quote.selected_tier,
                    "destination": ", ".join(trip.destinations) if trip.destinations else "N/A",
                    "coverage": quote.breakdown.get("coverage", {}) if quote.breakdown else {}
                }
                
                email_service.send_policy_confirmation(
                    to_email=user.email,
                    policy_number=policy_number,
                    policy_details=policy_details
                )
                logger.info(f"Sent confirmation email to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {e}")
            # Don't fail the whole webhook if email fails
        
    except Exception as e:
        logger.error(f"Failed to process payment success: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        # Don't raise - payment is already marked as completed


def generate_payment_confirmation_message(
    policy_number: str,
    trip,
    quote
) -> str:
    """Generate confirmation message for chat."""
    destination = ", ".join(trip.destinations) if trip.destinations else "your destination"
    start_date = trip.start_date.strftime("%B %d, %Y") if trip.start_date else "your travel dates"
    end_date = trip.end_date.strftime("%B %d, %Y") if trip.end_date else ""
    tier = quote.selected_tier.title() if quote.selected_tier else "Selected"
    
    date_range = f"{start_date}"
    if end_date:
        date_range = f"{start_date} to {end_date}"
    
    message = f"""🎉 **Payment Successful! Your Travel Insurance is Confirmed**

Your travel insurance policy has been successfully activated:

**Policy Number:** {policy_number}
**Coverage Tier:** {tier}
**Destination:** {destination}
**Coverage Period:** {date_range}

Your policy is now active and you're covered for your trip. A confirmation email with your policy details has been sent to your registered email address.

You can request a copy of your policy anytime by asking me to email it to you.

Safe travels! ✈️"""
    
    return message


async def add_message_to_chat_session(
    session_id: str,
    message_content: str,
    db: Session
):
    """Add an AIMessage to a LangGraph conversation session."""
    try:
        from app.agents.graph import create_conversation_graph, get_or_create_checkpointer
        from langchain_core.messages import AIMessage, HumanMessage
        import asyncio
        import time
        from concurrent.futures import ThreadPoolExecutor
        
        logger.info(f"📝 Adding message to chat session: {session_id}")
        print(f"📝 Adding message to chat session: {session_id}")
        
        graph = create_conversation_graph(db)
        config = {"configurable": {"thread_id": session_id}}
        
        # Get current state to verify session exists
        current_state = graph.get_state(config)
        
        if not current_state or not current_state.values:
            logger.warning(f"⚠️ No state found for session {session_id}")
            print(f"⚠️ No state found for session {session_id}")
            return
        
        existing_messages = current_state.values.get("messages", [])
        logger.info(f"📊 Current message count: {len(existing_messages)}")
        print(f"📊 Current message count: {len(existing_messages)}")
        
        # Create new AIMessage
        new_message = AIMessage(content=message_content)
        
        # Use invoke with a HumanMessage that triggers END immediately
        # This ensures the message is persisted via the checkpointer
        # We'll use a special message that the orchestrator will skip but still persists
        # Actually, better approach: invoke with just the AIMessage - it should skip orchestrator
        # because last message is AI, and the checkpointer will persist it
        
        logger.info(f"🔄 Creating checkpoint with new AIMessage using minimal graph")
        print(f"🔄 Creating checkpoint with new AIMessage using minimal graph")
        
        # Prepare updated state with new message appended
        updated_messages = list(existing_messages) + [new_message]
        updated_state_values = dict(current_state.values)
        updated_state_values["messages"] = updated_messages
        
        # Create a minimal graph with a pass-through node that just returns state
        # This will create a checkpoint without triggering the main graph logic
        from langgraph.graph import StateGraph, END
        from app.agents.graph import ConversationState
        
        def passthrough_node(state: ConversationState) -> ConversationState:
            """Just return state as-is - creates checkpoint without processing"""
            return state
        
        # Create minimal graph
        minimal_graph = StateGraph(ConversationState)
        minimal_graph.add_node("passthrough", passthrough_node)
        minimal_graph.set_entry_point("passthrough")
        minimal_graph.add_edge("passthrough", END)
        
        # Compile with same checkpointer
        checkpointer = get_or_create_checkpointer()
        if checkpointer:
            compiled_minimal = minimal_graph.compile(checkpointer=checkpointer)
        else:
            compiled_minimal = minimal_graph.compile()
        
        # Invoke with updated state - this will create a checkpoint
        try:
            logger.info(f"🔄 Invoking minimal graph to create checkpoint")
            print(f"🔄 Invoking minimal graph to create checkpoint")
            result = compiled_minimal.invoke(updated_state_values, config)
            logger.info(f"✅ Checkpoint created via minimal graph")
            print(f"✅ Checkpoint created via minimal graph")
        except Exception as invoke_error:
            logger.warning(f"⚠️ Minimal graph invoke failed: {invoke_error}, trying update_state")
            print(f"⚠️ Minimal graph invoke failed: {invoke_error}, trying update_state")
            # Fallback to update_state
            graph.update_state(config, {"messages": [new_message]})
        
        # Verify the message was added by reading state back
        time.sleep(0.3)  # Small delay for checkpoint to be committed
        updated_state = graph.get_state(config)
        
        if updated_state and updated_state.values:
            final_messages = updated_state.values.get("messages", [])
            logger.info(f"✅ Final message count: {len(final_messages)}")
            print(f"✅ Final message count: {len(final_messages)}")
            
            # Check if our message is in the list
            last_message = final_messages[-1] if final_messages else None
            if last_message and isinstance(last_message, AIMessage):
                if message_content[:50] in str(last_message.content):
                    logger.info(f"✅ Confirmation message successfully added and persisted!")
                    print(f"✅ Confirmation message successfully added and persisted!")
                    print(f"   Message preview: {message_content[:100]}...")
                else:
                    logger.warning(f"⚠️ Last message doesn't match expected content")
                    print(f"⚠️ Last message doesn't match expected content")
                    print(f"   Expected: {message_content[:50]}...")
                    print(f"   Got: {str(last_message.content)[:50]}...")
            else:
                logger.warning(f"⚠️ Last message is not an AIMessage or missing")
                print(f"⚠️ Last message is not an AIMessage or missing")
                if last_message:
                    print(f"   Last message type: {type(last_message).__name__}")
        else:
            logger.error(f"❌ Failed to read updated state")
            print(f"❌ Failed to read updated state")
        
        logger.info(f"✅ Added confirmation message to session {session_id}")
        print(f"✅ Added confirmation message to session {session_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to add message to chat session {session_id}: {e}")
        print(f"❌ Failed to add message to chat session {session_id}: {e}")
        import traceback
        traceback.print_exc()
        # Don't raise - allow webhook to continue even if chat message fails


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

