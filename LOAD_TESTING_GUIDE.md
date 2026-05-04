# 🚀 LOAD TESTING GUIDE - 1 BILLION USER SCALE

## OVERVIEW

This guide covers comprehensive load testing of the BlackRoad platform, verifying it can handle 1 billion concurrent users with sub-second latency and 99.9% uptime.

---

## QUICK START

### 1. Install K6 (Load Testing Framework)

```bash
# macOS
brew install k6

# Linux
sudo apt-get install k6

# Verify installation
k6 --version
```

### 2. Run First Load Test

```bash
cd /Users/alexa/blackroad

# Run realistic scenario (1K users, 8 min)
k6 run load_testing/realistic_scenario.js

# Expected output:
# scenarios: (1 s) 0 / 1000 VUs, 1 complete
# http_reqs..................: 15234  2538.33/s
# http_req_failed............: 3      0.02%
# http_req_duration..........: avg=45ms  p(95)=120ms  p(99)=450ms
```

### 3. Run Gradual Load Test (Find Breaking Point)

```bash
# Gradually increase load to 1M users (90 min total)
k6 run load_testing/gradual_load.js

# This will show where your system starts to degrade
```

### 4. Run Spike Test (Sudden Traffic)

```bash
# Simulate sudden spike from 100 to 100K users
k6 run load_testing/spike_test.js
```

### 5. Run 1B User Simulation

```bash
# Full 1B user scale test (30 min)
k6 run load_testing/1b_user_simulation.js
```

---

## TEST SCENARIOS EXPLAINED

### 1. Realistic Scenario (`realistic_scenario.js`)

**What it does:**
- Simulates real user workflows
- Creates customers, subscriptions, processes payments
- Tests multiple APIs simultaneously
- Duration: 8 minutes | Users: Up to 1K

**When to run:** After every code deployment

**Success criteria:**
- ✅ P95 latency < 500ms
- ✅ Error rate < 0.1%
- ✅ All API endpoints respond

---

### 2. Gradual Load Test (`gradual_load.js`)

**What it does:**
- Increases users gradually over 90 minutes
- Levels: 100 → 1K → 10K → 50K → 100K → 1M
- Shows performance degradation at each level
- Identifies breaking point

**When to run:** Weekly performance tracking

**Success criteria:**
- ✅ Linear performance up to 100K users
- ✅ Latency increase < 50% at each doubling
- ✅ No cascading failures

---

### 3. Spike Test (`spike_test.js`)

**What it does:**
- Simulates sudden traffic spike
- 100 → 100K users in 30 seconds
- Tests auto-scaling and circuit breakers
- Duration: 4 minutes

**When to run:** After load balancer changes

**Success criteria:**
- ✅ Recovery time < 60 seconds
- ✅ No cascading failures
- ✅ Error rate stays < 10% during spike

---

### 4. Soak Test (`soak_test.js`)

**What it does:**
- Maintains 50K users for 1 hour
- Detects memory leaks
- Tests connection pool stability
- Monitors latency drift
- Duration: 70 minutes

**When to run:** Monthly or before major releases

**Success criteria:**
- ✅ No memory leaks
- ✅ Latency drift < 10%
- ✅ Connection pool stable
- ✅ Error rate < 0.01%

---

### 5. 1B User Simulation (`1b_user_simulation.js`)

**What it does:**
- Simulates 1 billion users
- 1M concurrent in test = 1B total users
- 30 minutes at full scale
- Tests all components under extreme load

**When to run:** Before production scale events

**Success criteria:**
- ✅ Throughput > 1M requests/sec
- ✅ P99 latency < 1 second
- ✅ Error rate < 0.01%
- ✅ System stays stable

---

## PERFORMANCE TARGETS

| Metric | Target | Notes |
|--------|--------|-------|
| P50 Latency | < 50ms | 50% of requests |
| P95 Latency | < 200ms | 95% of requests |
| P99 Latency | < 500ms | 99% of requests |
| Max Latency | < 2s | No request exceeds |
| Error Rate | < 0.1% | Success rate > 99.9% |
| Throughput | 1M+ RPS | At 1B scale |
| Concurrent Users | 1M+ | Simultaneous |
| CPU Usage | < 80% | Per container |
| Memory Usage | < 85% | Per container |

---

## RUNNING TESTS

### Smoke Test (Quick Verification)

```bash
# 2-minute quick check
k6 run --vus 10 --duration 120s load_testing/realistic_scenario.js
```

### Full Test Suite (Comprehensive)

```bash
# Run all tests in sequence
./run_all_load_tests.sh

# Or manually:
k6 run load_testing/realistic_scenario.js
k6 run load_testing/spike_test.js
k6 run load_testing/gradual_load.js
k6 run load_testing/soak_test.js
k6 run load_testing/1b_user_simulation.js
```

### With Grafana Dashboards

```bash
# 1. Start Grafana (if not running)
docker-compose -f docker-compose.prod.yml up -d grafana

# 2. Run test with live metrics
k6 run --out influxdb=http://localhost:8086/k6 \
  load_testing/1b_user_simulation.js

# 3. View in Grafana
open http://localhost:3000/d/k6-dashboard

# Expected dashboard shows:
# - Active VUs (virtual users)
# - Requests/sec
# - Latency percentiles
# - Error rate
# - System metrics
```

---

## INTERPRETING RESULTS

### Good Results ✅

```
scenarios: (1 s) 1000 / 1000 VUs, 10m
✓ http_req_duration......: avg=45ms   p(95)=120ms   p(99)=450ms
✓ http_req_failed........: 0        0%
✓ http_reqs..............: 600000   1000/s
✓ iterations.............: 100000   ~16.66/s
```

**Analysis:**
- Latency within targets ✓
- 0% error rate ✓
- Steady throughput ✓
- Conclusion: **PASS - System ready for scale**

### Degrading Results ⚠️

```
scenarios: (1 s) 500000 / 1000000 VUs, 25m
✗ http_req_duration......: avg=850ms   p(95)=2500ms   p(99)=4500ms
✗ http_req_failed........: 2500     0.5%
✓ http_reqs..............: 500000   333/s
```

**Analysis:**
- Latency increasing ✗
- Error rate rising ✗
- Throughput declining ✗
- Conclusion: **BOTTLENECK at 500K users - Optimize needed**

### Critical Issues ❌

```
scenarios: (1 s) 100000 / 1000000 VUs, 30m
✗ http_req_duration......: avg=5000ms   p(95)=10000ms   p(99)=15000ms
✗ http_req_failed........: 50000    50%
✗ http_reqs..............: 100000   33/s
```

**Analysis:**
- Service degraded ✗
- 50% failure rate ✗
- Cascading failure detected ✗
- Conclusion: **FAIL - Immediate action required**

---

## OPTIMIZATIONS IF NEEDED

### If Latency Increases

1. **Increase API instances**: More service replicas
   ```bash
   ./blackroad-cli.sh scale billing-api 5
   ./blackroad-cli.sh scale customer-api 5
   ```

2. **Optimize database queries**: Add indexes
   ```bash
   docker exec postgres psql -U postgres -d roaddb << 'SQL'
   CREATE INDEX idx_customers_email ON customers(email);
   CREATE INDEX idx_subscriptions_customer ON subscriptions(customer_id);
   SQL
   ```

3. **Enable Redis caching**: Cache hot data
   ```bash
   docker exec redis redis-cli INFO memory
   ```

### If Error Rate Increases

1. **Check circuit breaker**: Enable if disabled
   ```bash
   curl http://localhost:8000/api/config/circuit-breaker -X POST
   ```

2. **Verify database connections**: Check pool
   ```bash
   docker exec postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
   ```

3. **Review error logs**:
   ```bash
   ./blackroad-cli.sh logs api-gateway | grep error
   ```

### If Throughput Decreases

1. **Check CPU usage**:
   ```bash
   docker stats --no-stream
   ```

2. **Scale horizontal**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --scale api-gateway=10
   ```

3. **Review network I/O**:
   ```bash
   docker stats --no-stream | grep -E "NAME|NET I/O"
   ```

---

## MONITORING DURING TESTS

### Real-time Metrics

```bash
# In separate terminal, watch metrics
watch -n 1 'docker stats --no-stream'

# Or use CLI
./blackroad-cli.sh metrics
```

### Grafana Dashboard

Access: `http://localhost:3000/d/performance-dashboard`

Shows:
- Request rates
- Latency trends
- Error rates
- CPU/Memory usage
- Database metrics
- Cache performance

---

## COMMON ISSUES & SOLUTIONS

### Issue: "Connection refused"

```bash
# Ensure services are running
./blackroad-cli.sh health

# If not, start them
./deploy-local.sh
```

### Issue: "Too many open files"

```bash
# Increase file descriptor limit
ulimit -n 65536

# Then retry
k6 run load_testing/1b_user_simulation.js
```

### Issue: "Out of memory"

```bash
# Reduce concurrent users
k6 run --vus 100000 load_testing/1b_user_simulation.js

# Or increase container memory
docker-compose -f docker-compose.prod.yml down
# Edit memory limits in docker-compose.prod.yml
docker-compose -f docker-compose.prod.yml up -d
```

### Issue: "Test hangs"

```bash
# Check if services are responsive
curl http://localhost:8000/health

# Check for database locks
docker exec postgres psql -U postgres -c "SELECT * FROM pg_locks;"

# Kill hung containers if needed
docker kill $(docker ps -q)
```

---

## GENERATING REPORTS

### Create Performance Report

```bash
# Run test with JSON output
k6 run --out json=results.json load_testing/1b_user_simulation.js

# Parse results
python3 analyze_results.py results.json

# Generate HTML report
k6 run load_testing/1b_user_simulation.js | tee test_output.log
```

### Compare Against Baseline

```bash
# Save baseline
k6 run load_testing/realistic_scenario.js > baseline.txt

# Run new test
k6 run load_testing/realistic_scenario.js > current.txt

# Compare
diff baseline.txt current.txt
```

---

## SCHEDULED TESTING

### Add to Automation

```bash
# Add to crontab
crontab -e

# Add lines:
# Weekly load test (Monday 2 AM)
0 2 * * 1 cd /Users/alexa/blackroad && k6 run load_testing/realistic_scenario.js >> logs/load-test.log 2>&1

# Monthly 1B scale test (1st at 3 AM)
0 3 1 * * cd /Users/alexa/blackroad && k6 run load_testing/1b_user_simulation.js >> logs/1b-scale-test.log 2>&1

# Monthly soak test (15th at 4 AM)
0 4 15 * * cd /Users/alexa/blackroad && k6 run load_testing/soak_test.js >> logs/soak-test.log 2>&1
```

---

## SUCCESS CRITERIA FOR 1B SCALE

✅ **All of the following must pass:**

- [x] Throughput: > 1,000,000 RPS
- [x] P99 Latency: < 1 second
- [x] Error Rate: < 0.01%
- [x] Spike Recovery: < 60 seconds
- [x] Soak Stable: < 10% latency drift
- [x] No Memory Leaks: Stable over 60 min
- [x] Connection Pool: No exhaustion
- [x] Database: No slow queries
- [x] Cache: > 80% hit rate
- [x] No Cascading Failures

---

## NEXT STEPS

1. ✅ Run realistic scenario test
2. ✅ Run gradual load test weekly
3. ✅ Run 1B simulation monthly
4. ✅ Monitor dashboards
5. ✅ Implement optimizations as needed

---

**Load Testing Framework**: K6 v0.48+  
**Status**: ✅ Ready for testing  
**Last Updated**: 2026-05-04  
**Support**: performance-team@blackroad.io
