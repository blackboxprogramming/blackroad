#!/bin/bash

# Security Testing Suite - Automated security checks
# Run comprehensive security tests against your API

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_URL="${1:-http://localhost:8000}"
REPORT_FILE="security_report_$(date +%Y%m%d_%H%M%S).json"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       🔒 SECURITY TESTING SUITE - AUTOMATED CHECKS        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Target API: $API_URL"
echo "Report File: $REPORT_FILE"
echo ""

# Function to check security header
check_header() {
    local header=$1
    local description=$2
    
    echo -n "Checking $description... "
    
    response=$(curl -s -I "$API_URL" 2>/dev/null | grep -i "^$header:" || true)
    
    if [ -n "$response" ]; then
        echo "✅ PASS"
        echo "$response" | cut -d: -f2- >> "$REPORT_FILE"
        return 0
    else
        echo "❌ FAIL"
        return 1
    fi
}

# Function to test rate limiting
test_rate_limit() {
    echo -n "Testing rate limiting... "
    
    # Send 100 rapid requests
    responses=0
    for i in {1..100}; do
        status=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")
        if [ "$status" == "429" ]; then
            echo "✅ PASS (Rate limit triggered at request $i)"
            echo "Rate limit triggered at request $i" >> "$REPORT_FILE"
            return 0
        fi
        responses=$((responses+1))
    done
    
    echo "⚠️  WARNING (No rate limit detected after 100 requests)"
    return 1
}

# Function to test HTTPS redirect
test_https_redirect() {
    echo -n "Testing HTTPS redirect... "
    
    if [[ "$API_URL" == https://* ]]; then
        echo "✅ PASS (Already using HTTPS)"
        return 0
    else
        location=$(curl -s -L -o /dev/null -w "%{redirect_url}" "http://localhost:8000" 2>/dev/null || true)
        if [[ "$location" == https://* ]]; then
            echo "✅ PASS (HTTP redirects to HTTPS)"
            return 0
        else
            echo "⚠️  WARNING (No HTTPS redirect configured)"
            return 1
        fi
    fi
}

# Function to test SQL injection prevention
test_sql_injection() {
    echo -n "Testing SQL injection prevention... "
    
    payload="' OR '1'='1"
    status=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/test?query=$payload" 2>/dev/null || echo "000")
    
    # Should either reject (4xx) or safely handle
    if [ "$status" == "400" ] || [ "$status" == "403" ]; then
        echo "✅ PASS (Injection blocked with $status)"
        return 0
    elif [ "$status" == "404" ]; then
        echo "✅ PASS (Endpoint not found, safe)"
        return 0
    else
        echo "❌ FAIL (Unexpected response: $status)"
        return 1
    fi
}

# Function to test XSS prevention
test_xss_prevention() {
    echo -n "Testing XSS prevention... "
    
    payload="<script>alert(1)</script>"
    response=$(curl -s "$API_URL/api/test?input=$payload" 2>/dev/null || echo "")
    
    if echo "$response" | grep -q "<script>"; then
        echo "❌ FAIL (XSS payload reflected)"
        return 1
    else
        echo "✅ PASS (XSS payload not reflected)"
        return 0
    fi
}

# Initialize report
echo "{" > "$REPORT_FILE"
echo "  \"test_date\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"," >> "$REPORT_FILE"
echo "  \"target_url\": \"$API_URL\"," >> "$REPORT_FILE"
echo "  \"security_tests\": {" >> "$REPORT_FILE"

# Run tests
echo ""
echo "Running Security Tests:"
echo "─────────────────────────────────────────────────────────"

passed=0
failed=0

# Security Header Tests
echo ""
echo "📋 Security Headers:"
check_header "Strict-Transport-Security" "HSTS" && ((passed++)) || ((failed++))
check_header "X-Frame-Options" "Clickjacking Protection" && ((passed++)) || ((failed++))
check_header "X-Content-Type-Options" "MIME Type Sniffing" && ((passed++)) || ((failed++))
check_header "Content-Security-Policy" "XSS Protection" && ((passed++)) || ((failed++))

# Protocol Tests
echo ""
echo "🔐 Protocol Security:"
test_https_redirect && ((passed++)) || ((failed++))

# Attack Prevention Tests
echo ""
echo "🛡️  Attack Prevention:"
test_rate_limit && ((passed++)) || ((failed++))
test_sql_injection && ((passed++)) || ((failed++))
test_xss_prevention && ((passed++)) || ((failed++))

# Calculate score
total=$((passed + failed))
score=$((passed * 100 / total))

# Print summary
echo ""
echo "─────────────────────────────────────────────────────────"
echo "📊 SECURITY TEST SUMMARY"
echo "─────────────────────────────────────────────────────────"
echo "Total Tests: $total"
echo "Passed:      $passed ✅"
echo "Failed:      $failed ❌"
echo "Score:       $score/100"
echo ""

# Determine security level
if [ $score -ge 90 ]; then
    security_level="🟢 EXCELLENT"
elif [ $score -ge 75 ]; then
    security_level="🟡 GOOD"
elif [ $score -ge 60 ]; then
    security_level="🟠 FAIR"
else
    security_level="🔴 POOR"
fi

echo "Security Level: $security_level"
echo ""
echo "Report saved to: $REPORT_FILE"

# Add summary to report
echo "  }," >> "$REPORT_FILE"
echo "  \"summary\": {" >> "$REPORT_FILE"
echo "    \"total_tests\": $total," >> "$REPORT_FILE"
echo "    \"passed\": $passed," >> "$REPORT_FILE"
echo "    \"failed\": $failed," >> "$REPORT_FILE"
echo "    \"score\": $score," >> "$REPORT_FILE"
echo "    \"security_level\": \"$security_level\"" >> "$REPORT_FILE"
echo "  }" >> "$REPORT_FILE"
echo "}" >> "$REPORT_FILE"

# Exit code
if [ $failed -eq 0 ]; then
    echo ""
    echo "✅ All security tests passed!"
    exit 0
else
    echo ""
    echo "❌ Some security tests failed. Review the report for details."
    exit 1
fi
