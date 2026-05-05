#!/bin/bash

###############################################################################
# BlackRoad 1B User Load Testing Suite Runner
# Runs comprehensive load tests in sequence
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
LOAD_TEST_DIR="load_testing"
RESULTS_DIR="load_test_results"
LOG_FILE="$RESULTS_DIR/load_test_$(date +%Y%m%d_%H%M%S).log"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

check_k6() {
    if ! command -v k6 &> /dev/null; then
        log_error "K6 not found. Install with: brew install k6"
        exit 1
    fi
    log_success "K6 found: $(k6 --version)"
}

check_services() {
    log_info "Checking if services are running..."
    
    if ! curl -s http://localhost:8000/health &> /dev/null; then
        log_error "API not responding at localhost:8000"
        log_info "Run: ./deploy-local.sh"
        exit 1
    fi
    
    log_success "Services are running"
}

setup_results_dir() {
    mkdir -p "$RESULTS_DIR"
    touch "$LOG_FILE"
    log_info "Results will be saved to: $LOG_FILE"
}

run_test() {
    local test_name=$1
    local test_file=$2
    local duration=$3
    
    log_info "=========================================="
    log_info "Running: $test_name"
    log_info "Duration: $duration"
    log_info "=========================================="
    
    if [ ! -f "$LOAD_TEST_DIR/$test_file" ]; then
        log_error "Test file not found: $LOAD_TEST_DIR/$test_file"
        return 1
    fi
    
    k6 run "$LOAD_TEST_DIR/$test_file" 2>&1 | tee -a "$LOG_FILE"
    
    if [ $? -eq 0 ]; then
        log_success "$test_name completed"
    else
        log_error "$test_name failed"
        return 1
    fi
}

show_menu() {
    echo ""
    echo -e "${BLUE}BlackRoad Load Testing Suite${NC}"
    echo "================================"
    echo "1. Smoke Test (Quick - 2 min)"
    echo "2. Realistic Scenario (8 min)"
    echo "3. Spike Test (4 min)"
    echo "4. Gradual Load Test (90 min)"
    echo "5. Soak Test (70 min)"
    echo "6. 1B User Simulation (30 min)"
    echo "7. Run All Tests (Sequential)"
    echo "8. Show Help"
    echo "9. Exit"
    echo ""
}

run_smoke_test() {
    log_info "Running smoke test (quick verification)..."
    k6 run --vus 10 --duration 120s "$LOAD_TEST_DIR/realistic_scenario.js"
}

run_all_tests() {
    log_info "Starting complete load test suite..."
    log_info "Total estimated time: ~45 minutes"
    
    # Realistic scenario
    run_test "Realistic Scenario" "realistic_scenario.js" "8 min" || true
    sleep 30
    
    # Spike test
    run_test "Spike Test" "spike_test.js" "4 min" || true
    sleep 30
    
    # Gradual load
    log_warning "Gradual load test is long (90 min). Run separately if needed:"
    log_warning "  k6 run load_testing/gradual_load.js"
    
    # 1B simulation
    run_test "1B User Simulation" "1b_user_simulation.js" "30 min" || true
    
    log_success "Load test suite completed!"
    log_info "Results saved to: $LOG_FILE"
}

show_help() {
    cat << 'HELP'

BlackRoad 1B User Load Testing Suite

QUICK START:
  ./run_load_tests.sh          # Interactive menu
  ./run_load_tests.sh all      # Run all tests
  ./run_load_tests.sh smoke    # Run quick smoke test

TESTS AVAILABLE:
  smoke       - 2 min, 10 users (quick check)
  realistic   - 8 min, 1K users (real workflows)
  spike       - 4 min, 100K spike (traffic spike)
  gradual     - 90 min, 1M users (find breaking point)
  soak        - 70 min, 50K sustained (stability)
  1b          - 30 min, 1M users (1B scale sim)

DIRECT K6 COMMANDS:
  k6 run load_testing/realistic_scenario.js
  k6 run load_testing/spike_test.js
  k6 run load_testing/gradual_load.js
  k6 run load_testing/soak_test.js
  k6 run load_testing/1b_user_simulation.js

PERFORMANCE TARGETS:
  P50 Latency: < 50ms
  P95 Latency: < 200ms
  P99 Latency: < 500ms
  Error Rate:  < 0.1%
  Throughput:  1M+ RPS (at 1B scale)

HELP
}

###############################################################################
# MAIN
###############################################################################

main() {
    check_k6
    setup_results_dir
    check_services
    
    if [ $# -eq 0 ]; then
        # Interactive mode
        while true; do
            show_menu
            read -p "Select test (1-9): " choice
            
            case $choice in
                1) run_smoke_test ;;
                2) run_test "Realistic Scenario" "realistic_scenario.js" "8 min" ;;
                3) run_test "Spike Test" "spike_test.js" "4 min" ;;
                4) run_test "Gradual Load" "gradual_load.js" "90 min" ;;
                5) run_test "Soak Test" "soak_test.js" "70 min" ;;
                6) run_test "1B User Simulation" "1b_user_simulation.js" "30 min" ;;
                7) run_all_tests ;;
                8) show_help ;;
                9) echo "Exiting..."; exit 0 ;;
                *) echo "Invalid selection" ;;
            esac
        done
    else
        # Command-line mode
        case $1 in
            smoke)   run_smoke_test ;;
            realistic) run_test "Realistic Scenario" "realistic_scenario.js" "8 min" ;;
            spike)   run_test "Spike Test" "spike_test.js" "4 min" ;;
            gradual) run_test "Gradual Load" "gradual_load.js" "90 min" ;;
            soak)    run_test "Soak Test" "soak_test.js" "70 min" ;;
            1b)      run_test "1B User Simulation" "1b_user_simulation.js" "30 min" ;;
            all)     run_all_tests ;;
            help)    show_help ;;
            *)       echo "Unknown command: $1"; show_help; exit 1 ;;
        esac
    fi
}

main "$@"
