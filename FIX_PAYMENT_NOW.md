# 🚨 Payment Not Working - Here's The Fix

## The Problem

Your payment integration has everything configured EXCEPT the webhook forwarding is not running.

**What's happening:**
1. ✅ You click "Proceed to Payment" → Works
2. ✅ Backend creates checkout → Works  
3. ✅ You complete payment on Stripe → Works
4. ❌ **Webhook never fires** → Backend never receives the "payment completed" event
5. ❌ No policy created, no email sent, no chat confirmation

## The Solution: Start Stripe CLI Webhook Forwarding

### Option 1: Start Webhook Forwarding (RECOMMENDED)

**Open a NEW terminal window** (keep it running) and run:

```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/Singhacks/apps/backend
./start_stripe_webhooks.sh
```

**What you'll see:**
```
Ready! You are using Stripe API Version [2024-xx-xx]. 
Your webhook signing secret is whsec_abc123xyz... (^C to quit)
```

**IMPORTANT STEPS:**

1. **Copy the new webhook secret** (starts with `whsec_`)
2. **Open your `.env` file** (currently viewing)
3. **Update line 16** with the new secret:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_THE_NEW_SECRET_FROM_STRIPE_CLI
   ```
4. **Restart your backend** (Ctrl+C and restart uvicorn)
5. **Keep the webhook terminal running!**

Now try the payment again - it will work!

---

### Option 2: Manually Trigger Webhook (Quick Test)

If you **already completed a payment** and just want to trigger the webhook manually:

```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/Singhacks/apps/backend
./manual_trigger_webhook.sh
```

This will:
- Find your most recent payment session
- Manually trigger the webhook
- Create the policy and send confirmations

**Note:** This only works for testing. For real payments, you need Option 1 (Stripe CLI).

---

## Why This Happens

**The webhook secret in your `.env` is from a PREVIOUS Stripe CLI session that's no longer running.**

Each time you run Stripe CLI, it generates a NEW webhook secret. Your backend needs the CURRENT secret to verify webhook events.

Think of it like this:
```
Stripe.com ----webhook event----> 🚫 No tunnel running
                                    (Stripe CLI not started)
```

Vs. what you need:
```
Stripe.com ----webhook event----> ✅ Stripe CLI (running)
                                       |
                                       v
                                  localhost:8000
                                  → Policy created
                                  → Email sent
                                  → Chat updated
```

## Quick Setup (Terminal Layout)

Keep 3 terminals open:

**Terminal 1 - Backend:**
```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/Singhacks/apps/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/Singhacks/apps/frontend
npm run dev
```

**Terminal 3 - Webhook Forwarding:** ← **THIS IS WHAT'S MISSING!**
```bash
cd /Users/winstonyang/Desktop/Coding/Hackathons/Singhacks/apps/backend
./start_stripe_webhooks.sh
```

## Test It's Working

After starting webhook forwarding, test a payment:

1. Go to http://localhost:3000
2. Get a quote (or continue existing session)
3. Click "Proceed to Payment"
4. Use test card: `4242 4242 4242 4242`
5. Complete payment

**Watch Terminal 3 (webhook)** - you should see:
```
2025-11-01 23:45:00  --> checkout.session.completed [evt_xyz]
2025-11-01 23:45:00  <-- [200] POST http://localhost:8000/api/v1/payments/webhook/stripe [evt_xyz]
```

**Check chat** - you should see:
```
🎉 Payment Successful! Your Travel Insurance is Confirmed

Policy Number: POL-20251101-001
Coverage Tier: Elite
Destination: South Korea
...
```

## Still Not Working?

1. **Check Stripe CLI is installed:**
   ```bash
   stripe --version
   ```
   If not installed: `brew install stripe/stripe-cli/stripe` (Mac)

2. **Check backend is running:**
   ```bash
   curl http://localhost:8000/api/v1/payments/health
   ```
   Should return: `{"status":"ok","service":"payments-router"}`

3. **Check webhook endpoint:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/payments/webhook/stripe
   ```
   Should return 400 (expected - needs Stripe signature)

4. **Check logs:**
   ```bash
   tail -f apps/backend/server.log | grep -i webhook
   ```

## Need Help?

See detailed guides:
- `START_WEBHOOKS_NOW.md` - Step-by-step webhook setup
- `PAYMENT_SETUP_GUIDE.md` - Complete architecture and troubleshooting
- `QUICK_START_PAYMENTS.md` - Quick start guide

---

**TL;DR: Start the webhook forwarding script and keep it running! That's all you need to do.**

