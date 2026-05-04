#!/bin/bash
# Test Stripe Webhooks Handler

echo "🪝 Stripe Webhooks Test Suite"
echo "============================="

API_KEY="test-api-key"
ADMIN_TOKEN="${ADMIN_TOKEN:-dev-admin-token-change-in-prod}"
BASE_URL="http://localhost:8006"
WEBHOOK_SECRET="${STRIPE_WEBHOOK_SECRET:-whsec_test_fake}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

test_count=0
pass_count=0

function test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local auth=$5
    
    test_count=$((test_count+1))
    echo -e "\n📋 Test $test_count: $name"
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $auth" \
            2>/dev/null)
    else
        # For webhooks, simulate Stripe signature
        timestamp=$(date +%s)
        signed_content="$timestamp.$data"
        signature=$(echo -n "$signed_content" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" -hex | cut -d' ' -f2)
        
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" \
            -H "Stripe-Signature: t=$timestamp.$signature" \
            -H "Content-Type: application/json" \
            -d "$data" \
            2>/dev/null)
    fi
    
    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | head -n -1)
    
    if [[ "$http_code" =~ ^(200|201|202)$ ]]; then
        echo -e "${GREEN}✅ PASSED${NC} (HTTP $http_code)"
        pass_count=$((pass_count+1))
    else
        echo -e "${RED}❌ FAILED${NC} (HTTP $http_code)"
        echo "Response: $body"
    fi
}

# 1. Health & Status
echo -e "\n🏥 Health & Status"
echo "==================="
test_endpoint "Webhook Service Status" "GET" "/api/webhooks/status" "" ""

# 2. Test Events
echo -e "\n📨 Webhook Events"
echo "=================="

# Charge succeeded
charge_data='{
  "id": "evt_charge_succ_001",
  "type": "charge.succeeded",
  "data": {
    "object": {
      "id": "ch_123456",
      "customer": "cust_test_001",
      "amount": 5000,
      "currency": "usd",
      "invoice": "inv_123"
    }
  }
}'
test_endpoint "Charge Succeeded" "POST" "/api/webhooks/stripe" "$charge_data" "$API_KEY"

# Charge failed
charge_failed='{
  "id": "evt_charge_fail_001",
  "type": "charge.failed",
  "data": {
    "object": {
      "id": "ch_failed_123",
      "customer": "cust_test_002",
      "failure_code": "card_declined",
      "failure_message": "Your card was declined"
    }
  }
}'
test_endpoint "Charge Failed" "POST" "/api/webhooks/stripe" "$charge_failed" "$API_KEY"

# Invoice paid
invoice_paid='{
  "id": "evt_invoice_paid_001",
  "type": "invoice.paid",
  "data": {
    "object": {
      "id": "inv_456",
      "customer": "cust_test_001",
      "number": "INV-0001",
      "amount_paid": 9900
    }
  }
}'
test_endpoint "Invoice Paid" "POST" "/api/webhooks/stripe" "$invoice_paid" "$API_KEY"

# Subscription created
sub_created='{
  "id": "evt_sub_created_001",
  "type": "customer.subscription.created",
  "data": {
    "object": {
      "id": "sub_123",
      "customer": "cust_test_003",
      "status": "active"
    }
  }
}'
test_endpoint "Subscription Created" "POST" "/api/webhooks/stripe" "$sub_created" "$API_KEY"

# Subscription deleted
sub_deleted='{
  "id": "evt_sub_deleted_001",
  "type": "customer.subscription.deleted",
  "data": {
    "object": {
      "id": "sub_456",
      "customer": "cust_test_003"
    }
  }
}'
test_endpoint "Subscription Deleted" "POST" "/api/webhooks/stripe" "$sub_deleted" "$API_KEY"

# 3. Get Logs
echo -e "\n📋 Webhook Logs"
echo "==============="
test_endpoint "Get All Webhook Logs" "GET" "/api/webhooks/logs?limit=10" "" ""

# 4. Admin Operations
echo -e "\n🔧 Admin Operations"
echo "==================="
test_endpoint "Trigger Manual Retry" "POST" "/api/webhooks/retry" '{}' "$ADMIN_TOKEN"

# Summary
echo -e "\n\n📊 Summary"
echo "=========="
echo "Total Tests: $test_count"
echo -e "Passed: ${GREEN}$pass_count${NC}"
echo -e "Failed: ${RED}$((test_count - pass_count))${NC}"

if [ $pass_count -eq $test_count ]; then
    echo -e "\n${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed${NC}"
    exit 1
fi
