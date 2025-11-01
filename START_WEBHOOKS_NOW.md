# 🚨 WEBHOOK NOT RUNNING - Start It Now!

## The Problem

You completed payment, but the webhook didn't fire because **Stripe CLI is not forwarding events to your backend**.

Your current `.env` has:
```
STRIPE_WEBHOOK_SECRET=whsec_894e29229fd59b2b37163ebc5c0a6d0da4f61f62f568bb62ceb488e47fe7089d
```

But this webhook secret is only valid **while the Stripe CLI is running**.

## Fix It Now (2 Steps)

### Step 1: Install Stripe CLI (if not installed)

**Mac:**
```bash
brew install stripe/stripe-cli/stripe
```

**Windows:**
Download from: https://github.com/stripe/stripe-cli/releases/latest

**Linux:**
```bash
curl -L https://github.com/stripe/stripe-cli/releases/latest/download/stripe_linux_x86_64.tar.gz | tar -xz
sudo mv stripe /usr/local/bin/
```

### Step 2: Start Webhook Forwarding

**Open a NEW terminal** (keep it running) and run:

```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/Singhacks/apps/backend
./start_stripe_webhooks.sh
```

You should see:
```
Ready! You are using Stripe API Version [2024-xx-xx]. Your webhook signing secret is whsec_xyz123... (^C to quit)
```

**IMPORTANT:** If you see a DIFFERENT webhook secret (not `whsec_894e29229fd59b2b37163ebc5c0a6d0da4f61f62f568bb62ceb488e47fe7089d`), copy the NEW one and update your `.env` file, then restart the backend.

## Test Again

Now with webhook forwarding running:

1. Go to http://localhost:3000
2. Get a quote (or use existing session)
3. Click "Proceed to Payment"
4. Use test card: **4242 4242 4242 4242**
5. Complete payment

**Watch the webhook terminal** - you should see:
```
2025-11-01 23:30:00  --> checkout.session.completed [evt_xyz123]
2025-11-01 23:30:00  <-- [200] POST http://localhost:8000/api/v1/payments/webhook/stripe
```

**Check your chat** - you should see:
```
🎉 Payment Successful! Your Travel Insurance is Confirmed

Policy Number: POL-20250101-001
...
```

## Why This Happens

Stripe needs a way to send webhook events to your **localhost** during development. The Stripe CLI acts as a tunnel:

```
Stripe.com → Stripe CLI → localhost:8000/api/v1/payments/webhook/stripe
```

Without the Stripe CLI running, Stripe has no way to reach your local backend!

## Alternative: Manual Trigger

If you can't run Stripe CLI right now, you can manually trigger the webhook for testing:

```bash
# Find your most recent payment
curl -X POST "http://localhost:8000/api/v1/payments/test-webhook/by-session/YOUR_STRIPE_SESSION_ID"
```

Or check the database for the stripe_session_id:
```sql
SELECT stripe_session_id, payment_intent_id, payment_status 
FROM payments 
ORDER BY created_at DESC 
LIMIT 1;
```

Then trigger it:
```bash
curl -X POST "http://localhost:8000/api/v1/payments/test-webhook/by-session/cs_test_YOUR_SESSION_ID_HERE"
```

## Keep Webhook Running

**Pro Tip:** Keep the webhook terminal open in a separate window/tab while developing. It needs to stay running for payments to work!

Terminal layout:
```
Terminal 1: Backend (uvicorn)
Terminal 2: Frontend (npm run dev)  
Terminal 3: Stripe CLI (webhook forwarding) ← KEEP THIS RUNNING!
```

