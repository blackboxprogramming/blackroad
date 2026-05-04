#!/bin/bash

echo "🧪 Testing BlackRoad Dashboard Integration..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
API_BASE="http://localhost:8000"
DASHBOARD_URL="http://localhost:3000"
TEST_TOKEN="test_token_$(date +%s)"

# Counter
PASSED=0
FAILED=0

# Helper function
test_endpoint() {
  local method=$1
  local endpoint=$2
  local expected_code=$3
  local data=$4
  
  if [ -n "$data" ]; then
    response=$(curl -s -w "\n%{http_code}" -X $method \
      -H "Authorization: Bearer $TEST_TOKEN" \
      -H "Content-Type: application/json" \
      -d "$data" \
      "$API_BASE$endpoint")
  else
    response=$(curl -s -w "\n%{http_code}" -X $method \
      -H "Authorization: Bearer $TEST_TOKEN" \
      "$API_BASE$endpoint")
  fi
  
  http_code=$(echo "$response" | tail -n1)
  body=$(echo "$response" | head -n-1)
  
  if [ "$http_code" -eq "$expected_code" ]; then
    echo -e "${GREEN}✓${NC} $method $endpoint (HTTP $http_code)"
    ((PASSED++))
  else
    echo -e "${RED}✗${NC} $method $endpoint (Expected $expected_code, got $http_code)"
    ((FAILED++))
  fi
}

# Check if services are running
echo "Checking service availability..."
echo ""

services=(
  "Billing API:8000"
  "Admin Dashboard:8001"
  "Customer Analytics:8003"
  "ML Analytics:8005"
  "Dashboard UI:3000"
)

for service in "${services[@]}"; do
  name=${service%:*}
  port=${service#*:}
  
  if curl -s http://localhost:$port/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} $name running on port $port"
  else
    echo -e "${YELLOW}⚠${NC} $name not accessible on port $port"
  fi
done

echo ""
echo "Testing Dashboard Endpoints..."
echo ""

# Billing endpoints
test_endpoint "GET" "/api/billing/usage" 200
test_endpoint "GET" "/api/billing/subscription" 200
test_endpoint "GET" "/api/billing/invoices" 200
test_endpoint "GET" "/api/billing/forecast" 200

echo ""
echo "Testing Admin Endpoints..."
echo ""

test_endpoint "GET" "/api/admin/dashboard" 200
test_endpoint "GET" "/api/admin/revenue" 200
test_endpoint "GET" "/api/admin/customers" 200

echo ""
echo "Testing Analytics Endpoints..."
echo ""

test_endpoint "GET" "/api/customer-analytics/insights" 200
test_endpoint "GET" "/api/customer-analytics/ltv" 200
test_endpoint "GET" "/api/customer-analytics/churn" 200
test_endpoint "GET" "/api/customer-analytics/segmentation" 200

echo ""
echo "Testing ML Endpoints..."
echo ""

test_endpoint "GET" "/api/ml/churn-prediction" 200
test_endpoint "GET" "/api/ml/ltv-forecast" 200
test_endpoint "GET" "/api/ml/cohort-analysis" 200

echo ""
echo "Testing Dashboard UI..."
echo ""

# Check if dashboard loads
dashboard_response=$(curl -s -o /dev/null -w "%{http_code}" $DASHBOARD_URL)
if [ "$dashboard_response" -eq 200 ]; then
  echo -e "${GREEN}✓${NC} Dashboard UI loads successfully (HTTP 200)"
  ((PASSED++))
else
  echo -e "${RED}✗${NC} Dashboard UI not accessible (HTTP $dashboard_response)"
  ((FAILED++))
fi

echo ""
echo "==========================================="
echo -e "Results: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC}"
echo "==========================================="

if [ $FAILED -eq 0 ]; then
  echo -e "${GREEN}✓ All dashboard integrations working!${NC}"
  exit 0
else
  echo -e "${RED}✗ Some tests failed. Check services and try again.${NC}"
  exit 1
fi
