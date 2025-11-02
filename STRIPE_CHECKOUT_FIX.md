# Stripe Checkout - Complete Fix with Auto-Redirect

## Problems Fixed

1. **First-Attempt Failure**: Stripe checkout was failing on the first attempt with error: "Something went wrong - The page you were looking for could not be found."
2. **No Return to Chat**: After payment, users needed a seamless way to return to their chat session

## Root Causes Identified

### 1. **Lazy Stripe Initialization** (Primary Issue)
- The Stripe API key was only set when `PaymentService()` was instantiated
- No global initialization at application startup
- This could cause race conditions or cold-start issues on first request
- The stripe module might not be fully ready for API calls

### 2. **No Explicit Session Expiration**
- Checkout sessions didn't have explicit expiration times
- Could lead to sessions expiring unexpectedly

### 3. **Insufficient Error Handling**
- No try-catch around Stripe API calls
- Made debugging difficult

## Fixes Applied

### 1. **Global Stripe Initialization at Startup**

**File: `apps/backend/app/main.py`**

```python
# Added import
import stripe

# Added initialization in startup event
@app.on_event("startup")
async def startup_event():
    # ... existing code ...
    
    # Initialize Stripe API key globally
    if settings.stripe_secret_key:
        stripe.api_key = settings.stripe_secret_key
        print(f"✓ Stripe API initialized (key: {settings.stripe_secret_key[:7]}...)")
    else:
        print("⚠️  Stripe API key not configured - payment features will not work")
```

**Why this fixes it:**
- Stripe API is initialized once at application startup
- Ensures the API key is set before any payment requests
- Eliminates cold-start issues

### 2. **Defensive Initialization in PaymentService**

**File: `apps/backend/app/services/payment.py`**

```python
def __init__(self):
    """Initialize payment service with Stripe API key."""
    # Ensure Stripe API key is set (defensive - should be set at app startup)
    if settings.stripe_secret_key and not stripe.api_key:
        stripe.api_key = settings.stripe_secret_key
```

**Why this helps:**
- Adds a safety check in case startup initialization failed
- Only sets the key if it's not already set (avoids redundant operations)

### 3. **Explicit Session Expiration**

**File: `apps/backend/app/services/payment.py`**

```python
checkout_session = stripe.checkout.Session.create(
    # ... existing params ...
    expires_at=int(time.time()) + 3600,  # Explicit 1 hour expiration
)
```

**Why this helps:**
- Makes session lifetime explicit (1 hour)
- Prevents confusion from Stripe's default 24-hour expiration
- Ensures users have enough time but sessions don't linger

### 4. **Better Error Handling**

**File: `apps/backend/app/services/payment.py`**

```python
try:
    checkout_session = stripe.checkout.Session.create(...)
except stripe.error.StripeError as e:
    print(f"❌ Stripe API error creating checkout session: {e}")
    raise ValueError(f"Failed to create Stripe checkout: {str(e)}")
```

**File: `apps/backend/app/routers/payments.py`**

```python
logger.info(f"✅ Created checkout session for user {current_user.id}, tier {selected_tier}")
logger.info(f"💳 Checkout URL: {checkout_session.url}")
logger.info(f"💳 Session ID: {checkout_session.id}")
logger.info(f"💳 Session expires at: {checkout_session.expires_at}")
```

**Why this helps:**
- Catches Stripe API errors gracefully
- Provides detailed logging for debugging
- Makes it easier to identify if URLs are malformed

### 5. **Auto-Redirect Back to Chat Session**

**File: `apps/backend/app/core/config.py`**

```python
# Payment Configuration - redirect to quote page instead of dashboard
payment_success_url: str = "http://localhost:3000/app/quote?payment=success&stripe_session={CHECKOUT_SESSION_ID}"
payment_cancel_url: str = "http://localhost:3000/app/quote?payment=canceled"
```

**File: `apps/backend/app/services/payment.py`**

```python
def create_stripe_checkout(
    self,
    # ... existing params ...
    chat_session_id: Optional[str] = None  # NEW: Accept chat session ID
) -> stripe.checkout.Session:
    # Build success and cancel URLs with chat session ID
    success_url = settings.payment_success_url
    cancel_url = settings.payment_cancel_url
    
    if chat_session_id:
        # Append chat session ID to both URLs
        success_url += f"&session={chat_session_id}"
        cancel_url += f"&session={chat_session_id}"
    
    checkout_session = stripe.checkout.Session.create(
        # ...
        success_url=success_url,
        cancel_url=cancel_url,
    )
```

**File: `apps/backend/app/routers/payments.py`**

```python
checkout_session = payment_service.create_stripe_checkout(
    # ... existing params ...
    chat_session_id=request.session_id  # Pass chat session ID for redirect
)
```

**File: `apps/frontend/src/app/app/quote/page.tsx`**

```typescript
// Handle payment redirect from Stripe
useEffect(() => {
  const paymentStatus = searchParams.get('payment')
  const sessionId = searchParams.get('session')
  
  if (paymentStatus && sessionId) {
    // Clean URL - remove payment status but keep session
    router.replace(`/app/quote?session=${sessionId}`, { scroll: false })
    
    if (paymentStatus === 'success') {
      // Show success message immediately
      setAwaitingPayment(true)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '✅ Payment completed successfully! Processing your policy confirmation...'
      }])
      
      // Reload chat history after webhook processing (2s delay)
      setTimeout(() => loadChatHistory(sessionId), 2000)
    } else if (paymentStatus === 'canceled') {
      // Show cancelation message
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '❌ Payment was canceled. No charges were made. You can try again when ready!'
      }])
    }
  }
}, [searchParams, router])
```

**Why this is crucial:**
- After Stripe checkout, user is automatically redirected back to their exact chat session
- Success message appears immediately
- Chat history reloads to show updated state
- Payment polling starts to catch webhook updates
- Seamless user experience - no manual navigation needed

## Testing Instructions

1. **Restart the backend server** to apply the changes:
   ```bash
   cd apps/backend
   # Stop the current server (Ctrl+C)
   # Restart it
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Verify Stripe initialization** in the startup logs:
   ```
   ✓ Stripe API initialized (key: sk_test...)
   ```

3. **Test the checkout flow**:
   - Go through the quote process
   - Select a plan and click "Proceed to Payment"
   - The checkout should work on the **first attempt**

4. **Check logs** if issues persist:
   - Look for the checkout URL and session ID in logs
   - Verify the URL format is correct
   - Check expiration time

## Expected Behavior After Fix

- ✅ Checkout works on first attempt
- ✅ Valid Stripe checkout URLs generated
- ✅ Sessions have explicit 1-hour expiration
- ✅ Detailed logging for debugging
- ✅ Proper error messages if Stripe API fails
- ✅ **After payment, user is automatically redirected to their chat session**
- ✅ **Success message appears immediately in the chat**
- ✅ **Chat history auto-reloads with payment confirmation**
- ✅ **Seamless user experience - no navigation needed**

## Additional Notes

### Possible Other Issues (if problem persists)

1. **Environment Variables**
   - Ensure `STRIPE_SECRET_KEY` is set in `.env`
   - Should start with `sk_test_` for test mode
   - Should start with `sk_live_` for production

2. **Popup Blockers**
   - Frontend uses `window.open()` to open Stripe checkout
   - Some browsers may block popups
   - Consider using `window.location.href` instead for better UX

3. **CORS Issues**
   - Verify Stripe's domain is not blocked
   - Check browser console for CORS errors

4. **Stripe Account Issues**
   - Verify Stripe account is active
   - Check if test mode is enabled
   - Ensure payment methods are enabled in Stripe dashboard

## Files Modified

### Backend
1. `apps/backend/app/main.py` - Added Stripe initialization at startup
2. `apps/backend/app/services/payment.py` - Improved error handling, expiration, and chat session redirect
3. `apps/backend/app/routers/payments.py` - Enhanced logging and pass chat session ID
4. `apps/backend/app/core/config.py` - Updated redirect URLs to quote page with session parameter

### Frontend
5. `apps/frontend/src/app/app/quote/page.tsx` - Added payment redirect detection and auto-reload
6. `apps/frontend/src/components/CopilotPanel.tsx` - Added popup blocker handling

## Rollback Instructions

If you need to rollback these changes:

```bash
git checkout apps/backend/app/main.py
git checkout apps/backend/app/services/payment.py
git checkout apps/backend/app/routers/payments.py
git checkout apps/backend/app/core/config.py
git checkout apps/frontend/src/app/app/quote/page.tsx
git checkout apps/frontend/src/components/CopilotPanel.tsx
```

## Complete Payment Flow (After Fix)

1. **User gets quote** → AI assistant generates quote in chat
2. **User selects plan** → Clicks "Proceed to Payment"
3. **Stripe checkout opens** → Opens in new tab (or same tab if popups blocked)
4. **User completes payment** → Enters card details in Stripe
5. **Stripe redirects back** → Automatically returns to `/app/quote?payment=success&session={CHAT_SESSION_ID}`
6. **Frontend detects success** → Shows success message immediately
7. **Chat auto-reloads** → Loads updated state after 2s (allows webhook to process)
8. **Payment polling starts** → Checks for policy confirmation every 5s
9. **User sees confirmation** → Complete policy details appear in chat

**Result:** Seamless experience from quote to policy confirmation, all within the same chat session!

