#!/bin/bash

# BlackRoad Load Testing Suite
# Runs 5 different scenarios to validate system performance at scale

set -e

BASE_URL="${BASE_URL:-http://localhost:8000}"
CLERK_TOKEN="${CLERK_TOKEN:-test-clerk-token}"
RESULTS_DIR="load-test-results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create results directory
mkdir -p "$RESULTS_DIR"

echo "╔════════════════════════════════════════════╗"
echo "║  BlackRoad Load Testing Suite              ║"
echo "║  Target: $BASE_URL                          ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# Check if k6 is installed
if ! command -v k6 &> /dev/null; then
    echo "❌ k6 not found. Install with: brew install k6 (macOS) or apt-get install k6 (Linux)"
    exit 1
fi

# Scenario 1: Baseline Performance (1K concurrent users)
echo "📊 Scenario 1: Baseline Performance (1K users)"
echo "   Duration: 10 minutes | Expected: <500ms p95 latency"
echo ""

k6 run \
  --vus 1000 \
  --duration 10m \
  --out json="$RESULTS_DIR/scenario1_baseline_${TIMESTAMP}.json" \
  -e BASE_URL="$BASE_URL" \
  -e CLERK_TOKEN="$CLERK_TOKEN" \
  load-test.js \
  2>&1 | tee "$RESULTS_DIR/scenario1_baseline_${TIMESTAMP}.log"

echo ""
echo "✅ Scenario 1 complete"
echo ""

# Scenario 2: Sustained Load (5K concurrent users)
echo "📊 Scenario 2: Sustained Load (5K users)"
echo "   Duration: 15 minutes | Expected: <800ms p95 latency"
echo ""

k6 run \
  --vus 5000 \
  --duration 15m \
  --out json="$RESULTS_DIR/scenario2_sustained_${TIMESTAMP}.json" \
  -e BASE_URL="$BASE_URL" \
  -e CLERK_TOKEN="$CLERK_TOKEN" \
  load-test.js \
  2>&1 | tee "$RESULTS_DIR/scenario2_sustained_${TIMESTAMP}.log"

echo ""
echo "✅ Scenario 2 complete"
echo ""

# Scenario 3: Spike Test (10K concurrent users)
echo "📊 Scenario 3: Spike Test (10K users)"
echo "   Duration: 5 minutes @ peak | Expected: <1000ms p95 latency"
echo ""

k6 run \
  --vus 10000 \
  --duration 5m \
  --out json="$RESULTS_DIR/scenario3_spike_${TIMESTAMP}.json" \
  -e BASE_URL="$BASE_URL" \
  -e CLERK_TOKEN="$CLERK_TOKEN" \
  load-test.js \
  2>&1 | tee "$RESULTS_DIR/scenario3_spike_${TIMESTAMP}.log"

echo ""
echo "✅ Scenario 3 complete"
echo ""

# Scenario 4: Cache Behavior (1K users, 60 min)
echo "📊 Scenario 4: Cache Behavior (1K users, 60 min)"
echo "   Duration: 60 minutes | Expected: Improving latency (cache warmup)"
echo ""

k6 run \
  --vus 1000 \
  --duration 60m \
  --out json="$RESULTS_DIR/scenario4_cache_${TIMESTAMP}.json" \
  -e BASE_URL="$BASE_URL" \
  -e CLERK_TOKEN="$CLERK_TOKEN" \
  load-test.js \
  2>&1 | tee "$RESULTS_DIR/scenario4_cache_${TIMESTAMP}.log"

echo ""
echo "✅ Scenario 4 complete"
echo ""

# Scenario 5: Mixed Workload (5K users, mixed request types)
echo "📊 Scenario 5: Mixed Workload (5K users, varied patterns)"
echo "   Duration: 20 minutes | Expected: Heterogeneous latency"
echo ""

k6 run \
  --vus 5000 \
  --duration 20m \
  --out json="$RESULTS_DIR/scenario5_mixed_${TIMESTAMP}.json" \
  -e BASE_URL="$BASE_URL" \
  -e CLERK_TOKEN="$CLERK_TOKEN" \
  load-test.js \
  2>&1 | tee "$RESULTS_DIR/scenario5_mixed_${TIMESTAMP}.log"

echo ""
echo "✅ Scenario 5 complete"
echo ""

echo "╔════════════════════════════════════════════╗"
echo "║  Load Testing Complete!                    ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "📁 Results saved to: $RESULTS_DIR/"
echo ""
echo "To analyze results:"
echo "  1. View logs:    cat $RESULTS_DIR/scenario*.log"
echo "  2. Generate reports: npm run load-test:report"
echo ""
