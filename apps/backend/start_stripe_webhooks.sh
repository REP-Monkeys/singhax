#!/bin/bash

# Start Stripe CLI webhook forwarding for local development
# This forwards Stripe webhook events to your local backend at port 8000

echo "=================================================="
echo "🔔 Starting Stripe Webhook Forwarding"
echo "=================================================="
echo ""

# Check if Stripe CLI is installed
if ! command -v stripe &> /dev/null; then
    echo "❌ Stripe CLI is not installed!"
    echo ""
    echo "📦 Install Stripe CLI:"
    echo ""
    echo "   macOS (Homebrew):"
    echo "   $ brew install stripe/stripe-cli/stripe"
    echo ""
    echo "   Linux:"
    echo "   $ curl -L https://github.com/stripe/stripe-cli/releases/latest/download/stripe_linux_x86_64.tar.gz | tar -xz"
    echo "   $ sudo mv stripe /usr/local/bin/"
    echo ""
    echo "   Windows:"
    echo "   Download from: https://github.com/stripe/stripe-cli/releases/latest"
    echo ""
    exit 1
fi

echo "✅ Stripe CLI is installed"
echo ""

# Check if logged in
if ! stripe config --list &> /dev/null; then
    echo "🔐 You need to log in to Stripe first:"
    echo ""
    stripe login
    echo ""
fi

echo "📡 Forwarding Stripe webhooks to http://localhost:8000/api/v1/payments/webhook/stripe"
echo ""
echo "⚠️  IMPORTANT: Copy the webhook signing secret from the output below"
echo "   and update STRIPE_WEBHOOK_SECRET in your .env file"
echo ""
echo "=================================================="
echo ""

# Start forwarding webhooks
# This will output a webhook signing secret (whsec_...) that you need to copy to .env
stripe listen --forward-to localhost:8000/api/v1/payments/webhook/stripe

echo ""
echo "=================================================="
echo "✅ Stripe webhook forwarding stopped"
echo "=================================================="

