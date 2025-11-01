#!/bin/bash

# Complete test of webhook flow with Stripe CLI

echo "=================================================="
echo "🧪 Complete Webhook Test with Stripe CLI"
echo "=================================================="
echo ""

# Step 1: Check Stripe CLI
echo "Step 1: Checking Stripe CLI..."
if ! pgrep -f "stripe listen" > /dev/null 2>&1; then
    echo "❌ Stripe CLI not running!"
    echo ""
    echo "Start it in another terminal:"
    echo "  cd /Users/winstonyang/Desktop/Coding/Hackathons/Singhacks/apps/backend"
    echo "  ./start_stripe_webhooks.sh"
    exit 1
fi
echo "✅ Stripe CLI is running"
echo ""

# Step 2: Trigger a test checkout event
echo "Step 2: Triggering test webhook event..."
echo "This will simulate a payment completion"
echo ""

stripe trigger checkout.session.completed

echo ""
echo "=================================================="
echo "✅ Test event sent!"
echo "=================================================="
echo ""
echo "Check your terminals:"
echo "  1. Stripe CLI terminal: Should show '--> checkout.session.completed'"
echo "  2. Backend terminal: Should show '🔔 STRIPE WEBHOOK RECEIVED'"
echo ""
echo "If you see both, webhooks are working!"
echo ""
echo "If NOT working, the issue is likely:"
echo "  - Backend not running on port 8000"
echo "  - Webhook endpoint has an error"
echo "  - STRIPE_WEBHOOK_SECRET mismatch"
echo ""

