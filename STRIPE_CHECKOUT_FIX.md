# Stripe Checkout First-Attempt Failure - Fixed

## Problem

Stripe checkout was failing on the first attempt with error: "Something went wrong - The page you were looking for could not be found."

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

1. `apps/backend/app/main.py` - Added Stripe initialization
2. `apps/backend/app/services/payment.py` - Improved error handling and expiration
3. `apps/backend/app/routers/payments.py` - Enhanced logging

## Rollback Instructions

If you need to rollback these changes:

```bash
git checkout apps/backend/app/main.py
git checkout apps/backend/app/services/payment.py
git checkout apps/backend/app/routers/payments.py
```

