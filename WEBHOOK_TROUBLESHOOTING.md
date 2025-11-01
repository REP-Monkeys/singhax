# 🔍 Webhook Not Auto-Triggering - Troubleshooting

## The Problem

You completed payment on Stripe, but the webhook didn't automatically fire. Here's why and how to fix it:

## Root Cause

When you open the Stripe payment page in a **new tab/window**, the webhook events ARE sent to your `localhost:8000`, but you might not see them because:

1. **Stripe CLI terminal is hidden/minimized** - Check if it's actually receiving events
2. **Test mode checkout URL** - Test payments need the CLI running to forward webhooks
3. **Network timing** - Stripe sends the event, but there might be a delay

## Solution 1: Check Stripe CLI Terminal

**Look at your Stripe CLI terminal** (the one running `./start_stripe_webhooks.sh`):

You should see lines like:
```
2025-11-01 23:45:00  --> checkout.session.completed [evt_abc123]
2025-11-01 23:45:01  <-- [200] POST http://localhost:8000/api/v1/payments/webhook/stripe
```

If you DON'T see these lines after completing payment, the webhook isn't reaching your local server.

### Fix: Verify Stripe CLI

```bash
# Check if Stripe CLI is still running
ps aux | grep "stripe listen"

# If not running, restart it:
cd /Users/winstonyang/Desktop/Coding/Hackathons/Singhacks/apps/backend
./start_stripe_webhooks.sh
```

## Solution 2: Enable Real-Time Polling (AUTO-REFRESH)

I've created a polling mechanism that automatically checks for payment completion without refreshing.

### Add to Frontend

Edit `apps/frontend/src/app/app/quote/page.tsx`:

```typescript
import { usePaymentPolling } from '@/hooks/usePaymentPolling'

// Inside QuotePage component, add:
const [awaitingPayment, setAwaitingPayment] = useState(false)

// After handleSendMessage function, add:
const { isPolling } = usePaymentPolling({
  sessionId: currentSessionId,
  onPaymentComplete: async () => {
    // Reload chat history to get the confirmation message
    await loadChatHistory(currentSessionId)
    setAwaitingPayment(false)
    
    // Show success notification
    alert('✅ Payment confirmed! Your policy is ready.')
  },
  enabled: awaitingPayment
})

// In CopilotPanel, when payment is initiated:
<CopilotPanel 
  conversationState={conversationState} 
  sessionId={currentSessionId || ''}
  onPaymentInitiated={() => setAwaitingPayment(true)}
/>
```

This will automatically poll every 5 seconds for payment completion!

## Solution 3: Test Webhook is Working

### Step 1: Complete a Test Payment

1. Click "Proceed to Payment"
2. Use test card: `4242 4242 4242 4242`
3. Complete payment
4. **Keep the Stripe success page open**

### Step 2: Check Webhook Received

In your **Stripe CLI terminal**, you should see:
```
2025-11-01 23:45:00  --> checkout.session.completed [evt_xyz]
```

If you see this line, the webhook WAS received!

### Step 3: Check Backend Logs

In your **backend terminal** (uvicorn), look for:
```
🔔 STRIPE WEBHOOK RECEIVED
💰 Payment successful for Stripe session: cs_test_...
Successfully created policy POL-20251101-001
✅ Added confirmation message to chat session
Sent confirmation email to winstony29@gmail.com
```

If you see all of these, the webhook worked perfectly!

### Step 4: Refresh Chat

Go back to your chat tab and **refresh** (Cmd+R / Ctrl+R). You should see the confirmation message.

## Solution 4: Debug Webhook Endpoint

Test that your webhook endpoint is accessible:

```bash
# Test webhook endpoint
curl -X POST http://localhost:8000/api/v1/payments/webhook/stripe \
  -H "Content-Type: application/json" \
  -d '{}'

# Should return 400 (expected - needs Stripe signature)
# If returns 404, your endpoint is not registered correctly
```

## Solution 5: Manual Trigger (Backup)

If automatic webhooks still don't work, manually trigger after each payment:

```bash
# After completing payment, run:
cd /Users/winstonyang/Desktop/Coding/Hackathons/Singhacks/apps/backend
./manual_trigger_webhook.sh
```

This will find your most recent payment and trigger the webhook manually.

## Common Issues & Fixes

### Issue: "No webhook events appearing in Stripe CLI"

**Cause:** Stripe CLI lost connection or stopped running

**Fix:**
```bash
# Kill any existing Stripe CLI processes
pkill -f "stripe listen"

# Restart webhook forwarding
cd apps/backend
./start_stripe_webhooks.sh
```

### Issue: "Webhook returns 500 error"

**Cause:** Backend error processing the webhook

**Fix:** Check backend logs for the error:
```bash
tail -100 apps/backend/server.log | grep -A 20 "STRIPE WEBHOOK"
```

### Issue: "Payment completes but no policy created"

**Cause:** Quote or Trip missing session_id

**Fix:** Check database:
```sql
-- Check payment was created
SELECT * FROM payments ORDER BY created_at DESC LIMIT 1;

-- Check trip has session_id
SELECT t.id, t.session_id, t.status 
FROM trips t
JOIN quotes q ON q.trip_id = t.id
JOIN payments p ON p.quote_id = q.id
ORDER BY p.created_at DESC LIMIT 1;
```

### Issue: "Webhook triggered but no chat message"

**Cause:** Message added to wrong session or checkpointer issue

**Fix:** The `add_message_to_chat_session` function should log:
```
✅ Confirmation message successfully added and persisted!
```

If you don't see this, the chat update failed. Check for errors in backend logs.

## Production Solution

For production (not using Stripe CLI), you need to:

1. **Add Stripe webhook endpoint:**
   - Go to: https://dashboard.stripe.com/webhooks
   - Add endpoint: `https://your-domain.com/api/v1/payments/webhook/stripe`
   - Select events: `checkout.session.completed`
   - Copy signing secret → update `STRIPE_WEBHOOK_SECRET` in production `.env`

2. **No Stripe CLI needed** - webhooks go directly to your public URL

3. **Real-time updates still work** via polling mechanism

## Quick Checklist

After each payment, verify:

- [ ] Stripe CLI shows webhook event received
- [ ] Backend logs show policy created
- [ ] Backend logs show email sent
- [ ] Backend logs show chat message added
- [ ] Database has payment status = 'completed'
- [ ] Database has new policy record
- [ ] Trip status = 'confirmed'

If any of these fail, check that specific step's logs.

## Still Not Working?

1. **Restart everything:**
   ```bash
   # Stop all services (Ctrl+C in each terminal)
   # Then restart in this order:
   
   # Terminal 1: Backend
   cd apps/backend
   source venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Terminal 2: Stripe CLI
   cd apps/backend  
   ./start_stripe_webhooks.sh
   
   # Terminal 3: Frontend
   cd apps/frontend
   npm run dev
   ```

2. **Test with manual trigger:**
   ```bash
   # Complete payment first, then:
   cd apps/backend
   ./manual_trigger_webhook.sh
   ```

3. **Check all services are accessible:**
   ```bash
   curl http://localhost:8000/api/v1/payments/health  # Should return 200
   curl http://localhost:3000  # Frontend should load
   ps aux | grep "stripe listen"  # Should show running process
   ```

---

**TL;DR:**
- Keep Stripe CLI terminal visible to see webhook events
- After payment, check that terminal for events
- If no events appear, restart Stripe CLI
- Use manual trigger script as backup
- Enable polling mechanism for auto-refresh (no page reload needed)

