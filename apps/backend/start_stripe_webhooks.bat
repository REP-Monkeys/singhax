@echo off
REM Start Stripe CLI webhook forwarding for local development (Windows)
REM This forwards Stripe webhook events to your local backend at port 8000

echo ==================================================
echo 🔔 Starting Stripe Webhook Forwarding
echo ==================================================
echo.

REM Check if Stripe CLI is installed
where stripe >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Stripe CLI is not installed!
    echo.
    echo 📦 Install Stripe CLI for Windows:
    echo    Download from: https://github.com/stripe/stripe-cli/releases/latest
    echo    Extract stripe.exe and add to your PATH
    echo.
    pause
    exit /b 1
)

echo ✅ Stripe CLI is installed
echo.

REM Check if logged in
stripe config --list >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 🔐 You need to log in to Stripe first:
    echo.
    stripe login
    echo.
)

echo 📡 Forwarding Stripe webhooks to http://localhost:8000/api/v1/payments/webhook/stripe
echo.
echo ⚠️  IMPORTANT: Copy the webhook signing secret from the output below
echo    and update STRIPE_WEBHOOK_SECRET in your .env file
echo.
echo ==================================================
echo.

REM Start forwarding webhooks
stripe listen --forward-to localhost:8000/api/v1/payments/webhook/stripe

echo.
echo ==================================================
echo ✅ Stripe webhook forwarding stopped
echo ==================================================
pause

