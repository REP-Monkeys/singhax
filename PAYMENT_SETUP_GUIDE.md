# 💳 Payment Setup Guide - Complete Stripe Integration

This guide explains how to set up and test the complete payment flow with webhooks for local development.

## 🏗️ Architecture Overview

```
┌─────────────────┐
│   Frontend      │
│  (Port 3000)    │
└────────┬────────┘
         │ 1. User clicks "Proceed to Payment"
         │
         ▼
┌─────────────────┐
│   Backend API   │
│  (Port 8000)    │──────┐
└────────┬────────┘      │ 2. Creates Quote & Payment record
         │               │ 3. Returns Stripe checkout URL
         │               │
         │               ▼
         │        ┌─────────────────┐
         │        │   Stripe API    │
         │        │  (checkout.com) │
         │        └────────┬────────┘
         │                 │ 4. User completes payment
         │                 │
         │                 ▼
         │        ┌─────────────────┐
         │        │  Stripe CLI     │
         │        │  (Webhook Fwd)  │
         │        └────────┬────────┘
         │                 │ 5. Forwards webhook events
         │                 │
         └◄────────────────┘
           6. Webhook handler:
              ✅ Updates payment status
              ✅ Creates policy
              ✅ Sends confirmation email
              ✅ Adds message to chat
```

## 📋 Prerequisites

1. **Stripe CLI** (for local webhook forwarding)
   ```bash
   # macOS
   brew install stripe/stripe-cli/stripe
   
   # Linux
   curl -L https://github.com/stripe/stripe-cli/releases/latest/download/stripe_linux_x86_64.tar.gz | tar -xz
   sudo mv stripe /usr/local/bin/
   
   # Windows
   # Download from: https://github.com/stripe/stripe-cli/releases/latest
   ```

2. **Stripe Account** with test API keys
   - Get your keys from: https://dashboard.stripe.com/test/apikeys

3. **Backend and Frontend Running**
   - Backend: `http://localhost:8000`
   - Frontend: `http://localhost:3000`

## 🚀 Quick Start (3 Steps)

### Step 1: Configure Stripe API Keys

Update `.env` file with your Stripe test keys:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_...your_secret_key_here...
STRIPE_PUBLISHABLE_KEY=pk_test_...your_publishable_key_here...
STRIPE_WEBHOOK_SECRET=whsec_...will_be_generated_in_step_2...

# Payment URLs (already configured)
PAYMENT_SUCCESS_URL=http://localhost:8085/success?session_id={CHECKOUT_SESSION_ID}
PAYMENT_CANCEL_URL=http://localhost:8085/cancel
```

### Step 2: Start Stripe Webhook Forwarding

Run the webhook forwarding script:

```bash
cd apps/backend
./start_stripe_webhooks.sh
```

This will:
1. Check if Stripe CLI is installed
2. Log you in to Stripe (if not already)
3. Start forwarding webhooks to `localhost:8000`
4. **Display a webhook signing secret** (looks like `whsec_...`)

**IMPORTANT:** Copy the `whsec_...` secret and update `STRIPE_WEBHOOK_SECRET` in your `.env` file!

Expected output:
```
Ready! Your webhook signing secret is whsec_1234567890abcdef (^C to quit)
```

### Step 3: Test the Payment Flow

1. **Start a conversation** on the frontend
2. **Get a quote** by providing trip details
3. **Click "Proceed to Payment"** button
4. **Use Stripe test card**:
   - Card: `4242 4242 4242 4242`
   - Expiry: Any future date
   - CVC: Any 3 digits
   - ZIP: Any 5 digits
5. **Complete payment**
6. **Check the results**:
   - ✅ Payment status updated to "completed" in database
   - ✅ Policy created with policy number
   - ✅ Confirmation email sent (check logs)
   - ✅ Confirmation message appears in chat

## 🔍 Verifying Everything Works

### Check Webhook Events

When payment is completed, you should see logs like:

```
🔔 STRIPE WEBHOOK RECEIVED
📨 Received Stripe event: checkout.session.completed
✅ Processing checkout.session.completed event
💰 Payment successful for Stripe session: cs_test_...
Updated payment status to completed for payment_123
Successfully created policy POL-20250101-001
Updated trip 123 status to confirmed
💬 Added confirmation message to chat session
Sent confirmation email to user@example.com
✅ Completed processing checkout.session.completed
```

### Check Database

```sql
-- Check payment was updated
SELECT * FROM payments WHERE payment_status = 'completed' ORDER BY created_at DESC LIMIT 1;

-- Check policy was created
SELECT * FROM policies ORDER BY created_at DESC LIMIT 1;

-- Check trip was confirmed
SELECT * FROM trips WHERE status = 'confirmed' ORDER BY updated_at DESC LIMIT 1;
```

### Check Chat History

Visit the frontend and reload the conversation - you should see the confirmation message:

```
🎉 Payment Successful! Your Travel Insurance is Confirmed

Your travel insurance policy has been successfully activated:

Policy Number: POL-20250101-001
Coverage Tier: Elite
Destination: Tokyo, Japan
Coverage Period: January 15, 2025 to January 22, 2025

Your policy is now active and you're covered for your trip...
```

## 🧪 Testing Different Scenarios

### Test Card Numbers

| Card Number | Scenario |
|-------------|----------|
| `4242 4242 4242 4242` | ✅ Payment succeeds |
| `4000 0000 0000 9995` | ❌ Card declined |
| `4000 0000 0000 0341` | ⚠️ Attach succeeds, charge fails |

### Manual Webhook Testing

If webhooks aren't working, you can manually trigger them:

```bash
# Using the test endpoint (no auth required)
curl -X POST "http://localhost:8000/api/v1/payments/test-webhook/by-session/{stripe_session_id}"

# Or with authentication
curl -X POST "http://localhost:8000/api/v1/payments/test-webhook/{payment_intent_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🛠️ Troubleshooting

### Issue: Webhook not receiving events

**Solution:**
1. Ensure Stripe CLI is running (`./start_stripe_webhooks.sh`)
2. Check that `STRIPE_WEBHOOK_SECRET` matches the one from Stripe CLI
3. Verify backend is accessible at `http://localhost:8000`

```bash
# Test webhook endpoint is accessible
curl http://localhost:8000/api/v1/payments/health
# Should return: {"status": "ok", "service": "payments-router"}
```

### Issue: Email not sending

**Solution:**
The email service is in dev mode - it logs emails instead of sending them. Check backend logs:

```
[EMAIL SERVICE] Would send email to user@example.com
Subject: Travel Insurance Policy Confirmed - POL-20250101-001
```

To enable real emails, configure SMTP settings in `.env`:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@travelinsurance.com
SMTP_USE_TLS=true
```

### Issue: Payment status not updating

**Solution:**
1. Check webhook is being received (look for logs)
2. Verify `client_reference_id` in Stripe matches `payment_intent_id` in database
3. Check for errors in webhook handler logs
4. Try manual webhook trigger (see Testing section above)

### Issue: Policy not created

**Solution:**
Check the webhook logs for errors:

```bash
# Should show policy creation
grep "Successfully created policy" apps/backend/server.log
```

If you see errors, check:
- Quote exists and has a trip_id
- Trip has a session_id
- User exists in database

## 📱 Production Deployment

For production, instead of Stripe CLI:

1. **Add webhook endpoint in Stripe Dashboard**:
   - Go to: https://dashboard.stripe.com/webhooks
   - Click "Add endpoint"
   - URL: `https://your-domain.com/api/v1/payments/webhook/stripe`
   - Events: `checkout.session.completed`, `checkout.session.expired`, `payment_intent.payment_failed`

2. **Copy the signing secret** and set as `STRIPE_WEBHOOK_SECRET`

3. **Update payment URLs** in `.env`:
   ```bash
   PAYMENT_SUCCESS_URL=https://your-domain.com/payment/success
   PAYMENT_CANCEL_URL=https://your-domain.com/payment/cancel
   ```

## 🎯 Complete Payment Flow Summary

1. **Frontend**: User clicks "Proceed to Payment" → calls `/payments/create-checkout`
2. **Backend**: Creates Quote + Payment record → returns Stripe checkout URL
3. **User**: Redirected to Stripe → enters card details → completes payment
4. **Stripe**: Sends webhook event `checkout.session.completed`
5. **Stripe CLI**: Forwards webhook to `localhost:8000/api/v1/payments/webhook/stripe`
6. **Backend Webhook Handler**:
   - Updates payment status to "completed"
   - Creates Policy with policy number
   - Updates trip status to "confirmed"
   - Sends confirmation email
   - Adds confirmation message to chat
7. **User**: Sees confirmation in chat interface

## 📚 Related Files

- **Backend Webhook Handler**: `apps/backend/app/routers/payments.py`
- **Payment Service**: `apps/backend/app/services/payment.py`
- **Email Service**: `apps/backend/app/services/email.py`
- **Frontend Payment UI**: `apps/frontend/src/components/CopilotPanel.tsx`
- **Environment Config**: `.env`

## 🆘 Need Help?

1. Check backend logs: `tail -f apps/backend/server.log`
2. Check frontend console for errors
3. Verify all services are running:
   ```bash
   curl http://localhost:8000/health  # Backend
   curl http://localhost:3000          # Frontend
   ```

---

✅ **Ready to test!** Follow the Quick Start guide above.

