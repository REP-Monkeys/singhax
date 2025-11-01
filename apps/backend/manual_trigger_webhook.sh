#!/bin/bash

# Manual webhook trigger for testing
# Use this when you complete a payment but the webhook didn't fire

echo "=================================================="
echo "🔧 Manual Webhook Trigger"
echo "=================================================="
echo ""

# Check if backend is running
echo "Checking backend..."
if ! curl -s http://localhost:8000/api/v1/payments/health > /dev/null 2>&1; then
    echo "❌ Backend is not running on localhost:8000"
    echo "   Start it with: cd apps/backend && uvicorn app.main:app --reload"
    exit 1
fi
echo "✅ Backend is running"
echo ""

# Get the most recent payment from logs
echo "Looking for recent payment sessions..."
echo ""

# Check if user provided session ID as argument
if [ -n "$1" ]; then
    SESSION_ID="$1"
    echo "Using provided session ID: $SESSION_ID"
else
    # Try to find from recent backend logs
    if [ -f "server.log" ]; then
        SESSION_ID=$(grep -o 'cs_test_[a-zA-Z0-9]*' server.log | tail -1)
        if [ -n "$SESSION_ID" ]; then
            echo "Found recent session ID in logs: $SESSION_ID"
        else
            echo "⚠️  Could not find session ID in logs"
            echo ""
            echo "Usage: ./manual_trigger_webhook.sh [stripe_session_id]"
            echo ""
            echo "Or find your session ID:"
            echo "  1. Check backend logs for 'cs_test_...'"
            echo "  2. Or query database:"
            echo "     SELECT stripe_session_id FROM payments ORDER BY created_at DESC LIMIT 1;"
            exit 1
        fi
    else
        echo "❌ No server.log found and no session ID provided"
        echo ""
        echo "Usage: ./manual_trigger_webhook.sh cs_test_YOUR_SESSION_ID"
        exit 1
    fi
fi

echo ""
echo "Triggering webhook for session: $SESSION_ID"
echo ""

# Call the test webhook endpoint
response=$(curl -s -w "\n%{http_code}" -X POST "http://localhost:8000/api/v1/payments/test-webhook/by-session/$SESSION_ID")
http_code=$(echo "$response" | tail -1)
body=$(echo "$response" | head -n -1)

echo ""
if [ "$http_code" == "200" ]; then
    echo "✅ Webhook triggered successfully!"
    echo ""
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
    echo ""
    echo "📝 Check:"
    echo "  1. Backend logs for policy creation"
    echo "  2. Chat conversation for confirmation message"
    echo "  3. Database: SELECT * FROM payments WHERE stripe_session_id = '$SESSION_ID';"
else
    echo "❌ Webhook trigger failed (HTTP $http_code)"
    echo ""
    echo "$body"
fi
echo ""

