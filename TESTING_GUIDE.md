# 🧪 TESTING GUIDE - BlackRoad SaaS Platform

Complete guide to testing your entire platform locally.

---

## 📋 OVERVIEW

The testing suite includes:
- **Integration Tests** (20+ tests across all services)
- **Service Health Checks** (all 8 microservices)
- **Database Connectivity Tests** (PostgreSQL)
- **Cache Tests** (Redis)
- **API Endpoint Tests** (billing, analytics, ML, admin, etc.)
- **Performance Tests** (latency, throughput)
- **End-to-End Workflow Tests** (complete user journeys)

---

## 🚀 QUICK START

### 1. Deploy Your Platform

```bash
cd /Users/alexa/blackroad
./deploy-local.sh
```

Wait for all services to be healthy (5-10 minutes).

### 2. Load Sample Data

```bash
python tests/seed_data.py
```

This populates your database with:
- 5 sample customers
- 5 sample subscriptions
- 15 sample transactions
- 5 sample analytics records

### 3. Run Integration Tests

```bash
./tests/run_tests.sh
```

This automatically:
- Checks all services are healthy
- Installs test dependencies
- Runs 20+ integration tests
- Reports results

---

## 🧪 TEST CATEGORIES

### Service Health Tests

Tests that all 8 microservices are running and healthy:

```bash
pytest tests/integration/test_complete_platform.py::TestServiceHealth -v
```

**What's tested:**
- ✓ Billing API health
- ✓ Admin Dashboard health
- ✓ Analytics Engine health
- ✓ ML Analytics health
- ✓ Customer UI health
- ✓ Stripe Webhooks health
- ✓ Onboarding Service health
- ✓ Monitoring System health

### Database Tests

Tests PostgreSQL connectivity and data operations:

```bash
pytest tests/integration/test_complete_platform.py::TestDatabaseConnectivity -v
```

**What's tested:**
- ✓ Database connection
- ✓ Required tables exist
- ✓ Data integrity constraints
- ✓ Insert/select operations

### Cache Tests

Tests Redis connectivity:

```bash
pytest tests/integration/test_complete_platform.py::TestCacheConnectivity -v
```

**What's tested:**
- ✓ Redis connection
- ✓ Set/Get operations
- ✓ Key expiration

### API Tests

Tests endpoints on all services:

```bash
pytest tests/integration/test_complete_platform.py::TestBillingAPI -v
pytest tests/integration/test_complete_platform.py::TestAnalyticsEngine -v
pytest tests/integration/test_complete_platform.py::TestMLAnalytics -v
```

**What's tested:**
- ✓ Endpoint accessibility
- ✓ Request/response formats
- ✓ Error handling

### Load Balancer Tests

Tests Nginx load balancer and routing:

```bash
pytest tests/integration/test_complete_platform.py::TestLoadBalancer -v
```

**What's tested:**
- ✓ Load balancer accessible
- ✓ API routing works
- ✓ Rate limiting enabled

### Performance Tests

Tests performance characteristics:

```bash
pytest tests/integration/test_complete_platform.py::TestPerformance -v
```

**What's tested:**
- ✓ API latency < 1 second
- ✓ Database queries < 100ms
- ✓ Cache operations < 10ms

### End-to-End Workflow Tests

Tests complete user journeys:

```bash
pytest tests/integration/test_complete_platform.py::TestEndToEndWorkflow -v
```

**What's tested:**
- ✓ Customer signup workflow
- ✓ Subscription payment workflow

---

## 📊 SAMPLE DATA

The `seed_data.py` script creates:

### Sample Customers

```
1. Alice Johnson (alice@acmecorp.com) - Enterprise plan
2. Bob Smith (bob@techstartup.io) - Pro plan
3. Carol White (carol@smallbiz.com) - Starter plan
4. David Brown (david@consulting.co) - Pro plan
5. Eve Davis (eve@retail.shop) - Starter plan
```

### Sample Subscriptions

- Enterprise: $299.99/month (1M requests)
- Pro: $99.99/month (100K requests)
- Starter: $29.99/month (10K requests)

### Sample Transactions

3 months of transaction history for each customer.

### Analytics Records

Daily API usage statistics for each customer.

---

## 🔧 RUNNING TESTS

### Run All Tests

```bash
./tests/run_tests.sh
```

This is the recommended way - it checks services are healthy first.

### Run Specific Test Class

```bash
pytest tests/integration/test_complete_platform.py::TestBillingAPI -v
```

### Run Specific Test

```bash
pytest tests/integration/test_complete_platform.py::TestBillingAPI::test_create_subscription -v
```

### Run with Output

```bash
pytest tests/integration/test_complete_platform.py -v -s
```

The `-s` flag shows print statements.

### Run with Coverage

```bash
pytest tests/integration/test_complete_platform.py --cov
```

---

## 📈 EXPECTED RESULTS

### Service Health Tests

```
✓ All 8 services healthy
✓ Response time < 1 second each
✓ Status: "healthy"
```

### Database Tests

```
✓ Connection successful
✓ All required tables exist
✓ Data integrity OK
```

### Performance Tests

```
✓ API latency: <1s (target: <250ms)
✓ Database queries: <100ms
✓ Cache operations: <10ms
```

### Test Summary

```
Passed: 20+
Failed: 0
Errors: 0
```

---

## 🐛 TROUBLESHOOTING

### "Connection refused" Error

**Problem:** Services are not running.

**Solution:**
```bash
./deploy-local.sh
```

### "FAILED - SKIPPED" in Tests

**Problem:** Dependencies not installed.

**Solution:**
```bash
pip install pytest requests psycopg2-binary redis
```

### "Database error" in Tests

**Problem:** PostgreSQL not accessible.

**Solution:**
```bash
docker-compose -f docker-compose.prod.yml exec postgres psql -U blackroad -d blackroad_prod -c "SELECT 1"
```

### "Redis error" in Tests

**Problem:** Redis cache not accessible.

**Solution:**
```bash
docker-compose -f docker-compose.prod.yml exec redis redis-cli -a cache_secure_pass_12345 PING
```

### "Rate limit" Error in Tests

**Problem:** Tests are rate-limited.

**Solution:** Wait a few seconds and re-run tests.

---

## 📊 TEST METRICS

### Coverage

The test suite covers:
- 100% of microservices (8/8)
- 100% of health endpoints
- Database connectivity (read/write)
- Cache operations
- API gateway routing
- Performance characteristics

### Execution Time

- Full test suite: ~30 seconds
- Individual test class: ~5-10 seconds
- Single test: ~1-2 seconds

### Success Rate

- All tests should pass (100% success)
- No failures expected
- No errors expected

---

## 🎯 VALIDATION CHECKLIST

Use this checklist after running tests:

- [ ] All 8 services healthy
- [ ] Database connectivity OK
- [ ] Cache working
- [ ] API endpoints responsive
- [ ] Load balancer routing traffic
- [ ] Performance within targets
- [ ] No errors in logs
- [ ] Sample data loaded

---

## 📚 INTEGRATION TEST FEATURES

### Service Health Testing

Each service is tested for:
- HTTP 200 response
- JSON response format
- "healthy" status
- Uptime information

### Database Testing

Tests verify:
- Connection establishment
- Required tables exist
- CRUD operations work
- Data persistence

### Cache Testing

Tests verify:
- Key/value operations
- Expiration handling
- Performance < 10ms

### API Testing

Tests verify:
- Endpoints exist
- Requests accepted
- Responses formatted
- Error codes correct

### Performance Testing

Tests verify:
- Latency < 1 second
- Throughput adequate
- No timeouts
- Graceful degradation

---

## 🔍 WHAT GETS TESTED

### Platform Components

- [x] Billing API - Payment processing
- [x] Admin Dashboard - Revenue tracking
- [x] Analytics Engine - Customer insights
- [x] ML Analytics - Predictions
- [x] Customer UI - User dashboard
- [x] Stripe Webhooks - Payment events
- [x] Onboarding Service - User signup
- [x] Monitoring System - Health checks

### Infrastructure

- [x] PostgreSQL Database
- [x] Redis Cache
- [x] Nginx Load Balancer
- [x] Prometheus Metrics
- [x] Docker Network

### Workflows

- [x] Customer signup
- [x] Subscription creation
- [x] Payment processing
- [x] Analytics tracking

---

## 🚀 NEXT STEPS

After testing:

1. **Review Metrics** - Check Grafana dashboards
2. **Check Logs** - Review service logs for warnings
3. **Load Test** - Run performance testing at scale
4. **Monitor Alerts** - Verify alert rules work
5. **Plan Deployment** - Ready for production

---

## 📞 SUPPORT

If tests fail:

1. Check services are running: `./blackroad-cli.sh status`
2. View logs: `./blackroad-cli.sh logs [service]`
3. Health check: `./blackroad-cli.sh health`
4. Restart services: `./blackroad-cli.sh restart`

---

**Testing Guide Complete! Your platform is ready for validation.** ✅

