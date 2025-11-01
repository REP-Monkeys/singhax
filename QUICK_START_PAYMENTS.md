# 💳 Quick Start - Payment Integration

Get payments working in **3 simple steps** (5 minutes).

## ✅ Prerequisites

- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:3000`
- Stripe test account (free): https://dashboard.stripe.com/register

## 🚀 3-Step Setup

### Step 1: Add Stripe Keys to `.env`

```bash
# Get your keys from: https://dashboard.stripe.com/test/apikeys
STRIPE_SECRET_KEY=sk_test_YOUR_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_will_get_this_in_step_2
```

### Step 2: Start Webhook Forwarding

**Mac/Linux:**
```bash
cd apps/backend
./start_stripe_webhooks.sh
```

**Windows:**
```bash
cd apps\backend
start_stripe_webhooks.bat
```

**Copy the webhook secret** that appears (starts with `whsec_`) and paste it into your `.env` file as `STRIPE_WEBHOOK_SECRET`.

### Step 3: Test Payment

1. Go to http://localhost:3000
2. Log in and start a conversation
3. Get a travel insurance quote
4. Click **"Proceed to Payment"**
5. Use test card: `4242 4242 4242 4242` (any future expiry, any CVC, any ZIP)
6. Complete payment
7. ✅ Check chat for confirmation message!

## 🎉 What Happens Automatically

When payment completes:

1. ✅ **Payment status** updated to "completed" in database
2. ✅ **Policy created** with policy number (e.g., `POL-20250101-001`)
3. ✅ **Trip confirmed** status updated
4. ✅ **Email sent** to user (check backend logs)
5. ✅ **Chat message** added with policy details

## 🔍 Verify It Worked

**Check the chat:**
You should see a message like:

```
🎉 Payment Successful! Your Travel Insurance is Confirmed

Policy Number: POL-20250101-001
Coverage Tier: Elite
Destination: Tokyo, Japan
Coverage Period: January 15, 2025 to January 22, 2025
```

**Check backend logs:**
```bash
tail -f apps/backend/server.log | grep "payment"
```

You should see:
```
🔔 STRIPE WEBHOOK RECEIVED
💰 Payment successful for Stripe session: cs_test_...
Successfully created policy POL-20250101-001
Sent confirmation email to user@example.com
```

## 🆘 Troubleshooting

### Issue: "Failed to create checkout session"

**Fix:** Make sure backend is running and you're logged in to the frontend.

### Issue: Payment completes but no confirmation in chat

**Fix:** 
1. Check webhook is running: Look for `Ready! Your webhook signing secret is whsec_...`
2. Update `STRIPE_WEBHOOK_SECRET` in `.env` with the correct secret
3. Restart backend after updating `.env`

### Issue: "Webhook endpoint not found"

**Fix:** Make sure backend is running on port 8000 and accessible:
```bash
curl http://localhost:8000/api/v1/payments/health
# Should return: {"status": "ok", "service": "payments-router"}
```

## 📚 More Details

See [PAYMENT_SETUP_GUIDE.md](./PAYMENT_SETUP_GUIDE.md) for:
- Complete architecture diagram
- Testing different scenarios
- Production deployment
- Advanced troubleshooting

## 🧪 Test Script

Verify everything is configured correctly:

```bash
cd apps/backend
python test_payment_integration.py
```

This checks:
- Backend services are running
- Webhook endpoint is accessible
- Environment variables are set
- Email service is configured

---

**Need help?** Check [PAYMENT_SETUP_GUIDE.md](./PAYMENT_SETUP_GUIDE.md) for detailed instructions.

