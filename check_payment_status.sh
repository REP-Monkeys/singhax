#!/bin/bash

# Check payment and policy status

echo "=================================================="
echo "💳 Payment & Policy Status Check"
echo "=================================================="
echo ""

SESSION_ID="335a4bf7-5c34-46fa-8ec7-3df2415a016d"
PAYMENT_ID="payment_a3cfa9d008ed"

echo "Checking payment status..."
curl -s "http://localhost:8000/api/v1/payments/test-webhook/by-session/cs_test_a1b6vrbxoI8SVwdnIcZwL9epxsVcxvmqlg7GsMkrOlSUrqEGVzzdbSnV8p" | python3 -m json.tool

echo ""
echo "=================================================="
echo "✅ Webhook triggered!"
echo ""
echo "Next steps:"
echo "1. Refresh your browser at http://localhost:3000"
echo "2. You should see the confirmation message in chat"
echo "3. If not, check backend console for errors"
echo "=================================================="

