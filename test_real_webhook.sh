#!/bin/bash

# Test if webhooks are actually being received from Stripe

echo "=================================================="
echo "🧪 Webhook Reception Test"
echo "=================================================="
echo ""

echo "Step 1: Checking if Stripe CLI is running..."
if pgrep -f "stripe listen" > /dev/null 2>&1; then
    echo "✅ Stripe CLI is running"
    echo ""
    
    # Show the process
    echo "Process:"
    ps aux | grep "stripe listen" | grep -v grep
    echo ""
else
    echo "❌ Stripe CLI is NOT running!"
    echo ""
    echo "Start it with:"
    echo "  cd apps/backend"
    echo "  ./start_stripe_webhooks.sh"
    echo ""
    exit 1
fi

echo "Step 2: Testing webhook endpoint is accessible..."
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/payments/webhook/stripe -H "Content-Type: application/json" -d '{}')

if [ "$response" == "400" ] || [ "$response" == "401" ]; then
    echo "✅ Webhook endpoint is accessible (returned $response - expected)"
elif [ "$response" == "404" ]; then
    echo "❌ Webhook endpoint NOT FOUND (404)"
    echo "   Check that backend is running on port 8000"
    exit 1
else
    echo "⚠️  Webhook endpoint returned unexpected status: $response"
fi

echo ""
echo "Step 3: Trigger a test webhook event..."
echo ""
echo "Run this command in another terminal:"
echo ""
echo "  stripe trigger checkout.session.completed"
echo ""
echo "Then watch THIS terminal and your backend terminal for:"
echo "  - Stripe CLI: '--> checkout.session.completed'"
echo "  - Backend: '🔔 STRIPE WEBHOOK RECEIVED'"
echo ""
echo "If you see both, webhooks are working!"
echo ""
echo "=================================================="
echo ""
echo "Next: Complete a real payment and watch for:"
echo "  1. Stripe CLI terminal: Event received"
echo "  2. Backend terminal: Webhook processed"  
echo "  3. Chat: Confirmation message (refresh if needed)"
echo ""


