#!/bin/bash
# Test suite for Advanced ML Engine (port 8005)

echo "🧪 Advanced ML Engine Test Suite"
echo "=================================="

API_KEY="test-api-key-12345"
BASE_URL="http://localhost:8005"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

test_count=0
pass_count=0
fail_count=0

function test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    test_count=$((test_count+1))
    
    echo -e "\n📋 Test $test_count: $name"
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $API_KEY" \
            -H "Content-Type: application/json")
    else
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $API_KEY" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" == "200" ] || [ "$http_code" == "201" ]; then
        echo -e "${GREEN}✅ PASSED${NC} (HTTP $http_code)"
        echo "Response: $(echo $body | jq . 2>/dev/null || echo $body | head -c 100)..."
        pass_count=$((pass_count+1))
    else
        echo -e "${RED}❌ FAILED${NC} (HTTP $http_code)"
        echo "Response: $body"
        fail_count=$((fail_count+1))
    fi
}

# 1. Health check
echo -e "\n🏥 Health & Status Checks"
echo "========================="
test_endpoint "Health Check" "GET" "/api/ml/health" ""
test_endpoint "Model Status" "GET" "/api/ml/models/status" ""

# 2. Churn Prediction
echo -e "\n🔮 Churn Prediction Tests"
echo "=========================="

churn_data='{
  "requests_0": 1500,
  "active_hours_0": 8,
  "errors_0": 2,
  "api_calls_0": 500,
  "satisfied_0": true,
  "support_tickets_0": 0,
  "days_since_last_activity": 15,
  "support_tickets": 2,
  "usage_trend": 0.8,
  "failed_requests": 5,
  "satisfaction_score": 4.2
}'
test_endpoint "Churn Prediction (Low Risk)" "POST" "/api/ml/churn/predict" "$churn_data"

churn_high_risk='{
  "days_since_last_activity": 60,
  "support_tickets": 5,
  "usage_trend": 0.1,
  "failed_requests": 50,
  "satisfaction_score": 2.0
}'
test_endpoint "Churn Prediction (High Risk)" "POST" "/api/ml/churn/predict" "$churn_high_risk"

# 3. Segmentation
echo -e "\n👥 Customer Segmentation Tests"
echo "==============================="

segment_enterprise='{
  "lifetime_value": 50000,
  "monthly_spend": 4500,
  "usage_days": 350,
  "support_tickets": 1,
  "satisfaction_score": 4.9,
  "api_calls_per_day": 5000,
  "error_rate": 0.001,
  "feature_adoption": 9
}'
test_endpoint "Segment Enterprise Customer" "POST" "/api/ml/segment/predict" "$segment_enterprise"

segment_emerging='{
  "lifetime_value": 500,
  "monthly_spend": 50,
  "usage_days": 5,
  "support_tickets": 0,
  "satisfaction_score": 4.0,
  "api_calls_per_day": 100,
  "error_rate": 0.05,
  "feature_adoption": 2
}'
test_endpoint "Segment Emerging Customer" "POST" "/api/ml/segment/predict" "$segment_emerging"

# 4. LTV Forecasting
echo -e "\n📈 LTV Forecasting Tests"
echo "========================"

ltv_data='{
  "monthly_spend": 450,
  "account_age_months": 12,
  "churn_probability": 0.15,
  "growth_rate": 0.08,
  "cac": 500
}'
test_endpoint "LTV Forecast (Growing Customer)" "POST" "/api/ml/ltv/forecast" "$ltv_data"

ltv_stable='{
  "monthly_spend": 200,
  "account_age_months": 24,
  "churn_probability": 0.25,
  "growth_rate": 0.02,
  "cac": 400
}'
test_endpoint "LTV Forecast (Stable Customer)" "POST" "/api/ml/ltv/forecast" "$ltv_stable"

# 5. Anomaly Detection
echo -e "\n🚨 Anomaly Detection Tests"
echo "==========================="

normal_metrics='{
  "requests_per_hour": 500,
  "error_rate": 0.01,
  "response_time_ms": 150,
  "bandwidth_mb": 50,
  "unique_endpoints": 3,
  "geographic_spread": 2
}'
test_endpoint "Anomaly Detection (Normal)" "POST" "/api/ml/anomaly/detect" "$normal_metrics"

anomaly_metrics='{
  "requests_per_hour": 50000,
  "error_rate": 0.25,
  "response_time_ms": 5000,
  "bandwidth_mb": 10000,
  "unique_endpoints": 50,
  "geographic_spread": 150
}'
test_endpoint "Anomaly Detection (High Anomaly)" "POST" "/api/ml/anomaly/detect" "$anomaly_metrics"

# 6. Revenue Optimization
echo -e "\n💰 Revenue Optimization Tests"
echo "=============================="

revenue_data='{
  "lifetime_value": 5200,
  "price_elasticity": 1.2,
  "segment": "enterprise",
  "current_price": 29
}'
test_endpoint "Revenue Optimization (Enterprise)" "POST" "/api/ml/revenue/optimize" "$revenue_data"

revenue_at_risk='{
  "lifetime_value": 1500,
  "price_elasticity": 2.5,
  "segment": "at-risk",
  "current_price": 29
}'
test_endpoint "Revenue Optimization (At-Risk)" "POST" "/api/ml/revenue/optimize" "$revenue_at_risk"

# 7. Batch Predictions
echo -e "\n📦 Batch Prediction Tests"
echo "========================="

batch_data='{
  "customers": [
    {
      "id": "cust_001",
      "lifetime_value": 5200,
      "monthly_spend": 450,
      "usage_days": 280,
      "support_tickets": 3,
      "satisfaction_score": 4.7,
      "api_calls_per_day": 2500,
      "error_rate": 0.02,
      "feature_adoption": 8,
      "days_since_last_activity": 5,
      "churn_probability": 0.1,
      "growth_rate": 0.08,
      "cac": 500
    },
    {
      "id": "cust_002",
      "lifetime_value": 1200,
      "monthly_spend": 100,
      "usage_days": 20,
      "support_tickets": 0,
      "satisfaction_score": 4.2,
      "api_calls_per_day": 300,
      "error_rate": 0.05,
      "feature_adoption": 3,
      "days_since_last_activity": 30,
      "churn_probability": 0.4,
      "growth_rate": 0.02,
      "cac": 200
    }
  ]
}'
test_endpoint "Batch Predictions (2 customers)" "POST" "/api/ml/batch/predict" "$batch_data"

# Summary
echo -e "\n\n📊 Test Summary"
echo "==============="
echo "Total Tests: $test_count"
echo -e "Passed: ${GREEN}$pass_count${NC}"
echo -e "Failed: ${RED}$fail_count${NC}"
echo "Pass Rate: $(echo "scale=1; $pass_count * 100 / $test_count" | bc)%"

if [ $fail_count -eq 0 ]; then
    echo -e "\n${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed${NC}"
    exit 1
fi
