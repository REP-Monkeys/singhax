#!/bin/bash

# Simple test script to verify payment integration setup
# Uses curl (available on all systems)

echo "============================================================"
echo "🧪 Payment Integration Test"
echo "============================================================"
echo ""

BACKEND_URL="http://localhost:8000/api/v1"
ALL_PASSED=true

# Function to test endpoint
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    
    echo -n "Testing $name... "
    
    # Use curl with timeout
    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        if [ "$response" == "$expected_status" ]; then
            echo "✅ Passed (HTTP $response)"
            return 0
        else
            echo "⚠️  Warning (HTTP $response, expected $expected_status)"
            return 1
        fi
    else
        echo "❌ Failed (connection error)"
        ALL_PASSED=false
        return 1
    fi
}

# Test services
echo "📡 Testing Services"
echo "-------------------"
test_endpoint "Backend Health" "${BACKEND_URL}/health" 200 || ALL_PASSED=false
test_endpoint "Payment Service" "${BACKEND_URL}/payments/health" 200 || ALL_PASSED=false  
test_endpoint "Chat Service" "${BACKEND_URL}/chat/health" 200 || ALL_PASSED=false
echo ""

# Test webhook endpoint (expects 400 without valid signature)
echo "🔔 Testing Webhook Endpoint"
echo "----------------------------"
echo -n "Testing webhook accessibility... "
webhook_response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 \
    -X POST "${BACKEND_URL}/payments/webhook/stripe" \
    -H "Content-Type: application/json" \
    -d '{}' 2>/dev/null)

if [ $? -eq 0 ]; then
    if [ "$webhook_response" == "400" ] || [ "$webhook_response" == "401" ]; then
        echo "✅ Accessible (HTTP $webhook_response - expected, requires Stripe signature)"
    elif [ "$webhook_response" == "404" ]; then
        echo "❌ Not Found (HTTP 404)"
        ALL_PASSED=false
    else
        echo "⚠️  Returned HTTP $webhook_response (expected 400/401)"
    fi
else
    echo "❌ Failed (connection error)"
    ALL_PASSED=false
fi
echo ""

# Check .env file
echo "⚙️  Checking Environment Configuration"
echo "---------------------------------------"

ENV_FILE="../../.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env file not found at: $ENV_FILE"
    ALL_PASSED=false
else
    echo "✅ .env file found"
    
    # Check for required variables
    required_vars=("STRIPE_SECRET_KEY" "STRIPE_PUBLISHABLE_KEY" "STRIPE_WEBHOOK_SECRET" "DATABASE_URL" "GROQ_API_KEY")
    
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" "$ENV_FILE" && ! grep -q "^${var}=$" "$ENV_FILE" && ! grep -q "^${var}=#" "$ENV_FILE"; then
            # Variable exists and has a value
            echo "✅ $var: Configured"
        else
            echo "❌ $var: Not set or empty"
            ALL_PASSED=false
        fi
    done
fi
echo ""

# Summary
echo "============================================================"
if [ "$ALL_PASSED" = true ]; then
    echo "✅ ALL CHECKS PASSED!"
    echo "============================================================"
    echo ""
    echo "🚀 Next Steps:"
    echo ""
    echo "1. Start Stripe webhook forwarding:"
    echo "   cd apps/backend"
    echo "   ./start_stripe_webhooks.sh"
    echo ""
    echo "2. Copy the webhook secret (whsec_...) to your .env file"
    echo ""
    echo "3. Test payment flow:"
    echo "   - Go to http://localhost:3000"
    echo "   - Get a quote and click 'Proceed to Payment'"
    echo "   - Use test card: 4242 4242 4242 4242"
    echo ""
    echo "📚 See QUICK_START_PAYMENTS.md for detailed guide"
    exit 0
else
    echo "⚠️  SOME CHECKS FAILED"
    echo "============================================================"
    echo ""
    echo "🔧 Please fix the issues above before testing payments."
    echo ""
    echo "Common fixes:"
    echo "  - Make sure backend is running: cd apps/backend && uvicorn app.main:app"
    echo "  - Check .env has all required values"
    echo "  - Verify services are accessible on localhost:8000"
    echo ""
    echo "📚 See PAYMENT_SETUP_GUIDE.md for help"
    exit 1
fi

