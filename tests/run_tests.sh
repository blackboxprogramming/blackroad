#!/bin/bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   BlackRoad Integration Test Suite                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}\n"

# Check if services are running
echo -e "${YELLOW}Checking if services are running...${NC}\n"

SERVICES=(
    "http://localhost:8001"
    "http://localhost:8002"
    "http://localhost:8003"
    "http://localhost:8004"
    "http://localhost:8005"
    "http://localhost:8006"
    "http://localhost:8007"
    "http://localhost:8008"
    "http://localhost:5432"
    "http://localhost:6379"
)

HEALTHY=0
for url in "${SERVICES[@]}"; do
    if curl -s "$url/health" > /dev/null 2>&1 || nc -zv "${url##*://}" 2>&1 | grep -q succeeded; then
        echo -e "${GREEN}✓${NC} Service $url is healthy"
        ((HEALTHY++))
    else
        echo -e "${RED}✗${NC} Service $url is down"
    fi
done

echo ""

if [ $HEALTHY -lt ${#SERVICES[@]} ]; then
    echo -e "${RED}Some services are not running. Please start them with:${NC}"
    echo "  ./deploy-local.sh"
    exit 1
fi

echo -e "${GREEN}All services are healthy!${NC}\n"

# Install test dependencies
echo -e "${YELLOW}Installing test dependencies...${NC}\n"

pip install -q pytest requests psycopg2-binary redis 2>/dev/null || pip3 install -q pytest requests psycopg2-binary redis

echo -e "${GREEN}Dependencies installed${NC}\n"

# Run tests
echo -e "${BLUE}Running integration tests...${NC}\n"

pytest tests/integration/test_complete_platform.py -v \
    --tb=short \
    --timeout=30 \
    2>&1 | tee test_results.txt

# Summary
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Test Results Summary                                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}\n"

PASSED=$(grep -c "PASSED" test_results.txt || echo 0)
FAILED=$(grep -c "FAILED" test_results.txt || echo 0)
ERRORS=$(grep -c "ERROR" test_results.txt || echo 0)

echo -e "  ${GREEN}Passed: $PASSED${NC}"
echo -e "  ${RED}Failed: $FAILED${NC}"
echo -e "  ${RED}Errors: $ERRORS${NC}"
echo ""

if [ $FAILED -eq 0 ] && [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}\n"
    echo -e "${GREEN}Your platform is production-ready.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed.${NC}\n"
    echo "Review the output above for details."
    exit 1
fi
