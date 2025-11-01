# 🔔 Stripe Webhook Setup Guide

## Quick Setup Steps

### Step 1: Authenticate Stripe CLI

When you run `./start_stripe_webhooks.sh`, you'll see a pairing code and URL. Do one of the following:

**Option A: Browser Authentication (Easiest)**
1. Copy the URL from the terminal (looks like: `https://dashboard.stripe.com/stripecli/confirm_auth?t=...`)
2. Open it in your browser
3. Click "Allow access" in the Stripe dashboard
4. Return to your terminal - authentication should complete automatically

**Option B: Manual Pairing**
1. Copy the pairing code (e.g., `gusto-winner-gained-tidy`)
2. Visit: https://dashboard.stripe.com/stripecli/confirm_auth
3. Enter the pairing code
4. Click "Allow access"

### Step 2: Get Webhook Signing Secret

After authentication, the Stripe CLI will start forwarding webhooks and display output like:

```
> Ready! Your webhook signing secret is whsec_1234567890abcdef1234567890abcdef (^C to quit)
```

**IMPORTANT:** Copy the `whsec_...` secret that appears!

### Step 3: Update .env File

1. Open your `.env` file
2. Find the line: `STRIPE_WEBHOOK_SECRET=whsec_local_testing_12345`
3. Replace it with the real secret from Step 2:
   ```
   STRIPE_WEBHOOK_SECRET=whsec_1234567890abcdef1234567890abcdef
   ```
4. Save the file

### Step 4: Restart Backend (if running)

If your backend is already running, restart it to pick up the new webhook secret:
```bash
# Stop the backend (Ctrl+C)
# Then restart it
cd apps/backend
python -m uvicorn app.main:app --reload --port 8000
```

## Verification

Once everything is set up, you should see:

1. **Stripe CLI terminal** showing:
   ```
   > Ready! Your webhook signing secret is whsec_...
   > Forwarding events to http://localhost:8000/api/v1/payments/webhook/stripe
   ```

2. **Backend logs** showing webhook events when payments complete:
   ```
   🔔 STRIPE WEBHOOK RECEIVED
   📨 Received Stripe event: checkout.session.completed
   ```

## Troubleshooting

### Issue: Authentication not completing

**Solution:**
- Make sure you click "Allow access" in the Stripe dashboard
- The pairing code expires after a few minutes - if it expires, press Ctrl+C and restart the script
- Try opening the URL directly in your browser instead of pressing Enter

### Issue: Can't find webhook secret

**Solution:**
- The secret appears right after authentication completes
- Look for a line starting with `whsec_`
- If you missed it, stop the CLI (Ctrl+C) and restart - it will show the secret again

### Issue: Webhook secret not working

**Solution:**
- Make sure you copied the ENTIRE secret (starts with `whsec_` and is quite long)
- Verify there are no extra spaces or newlines in your `.env` file
- Restart your backend after updating `.env`

## Testing

After setup, test with a payment:

1. Use Stripe test card: `4242 4242 4242 4242`
2. Complete a payment through your app
3. Check the Stripe CLI terminal - you should see webhook events being forwarded
4. Check backend logs - you should see webhook processing messages

## Production Setup

For production, you don't use Stripe CLI. Instead:

1. Go to: https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. Enter your production URL: `https://your-domain.com/api/v1/payments/webhook/stripe`
4. Select events: `checkout.session.completed`, `checkout.session.expired`, `payment_intent.payment_failed`
5. Copy the signing secret and update `STRIPE_WEBHOOK_SECRET` in production `.env`


