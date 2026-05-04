# BlackRoad Load Testing & Deployment Setup

## Quick Start

### Prerequisites
```bash
# Install k6 (load testing)
brew install k6          # macOS
apt-get install k6       # Linux
# or download from https://k6.io/docs/getting-started/installation/

# Install Docker & Docker Compose
docker --version
docker-compose --version
```

---

## 1. Local Development Setup

### Start Services
```bash
# Build and start all services (PostgreSQL, Redis, API)
docker-compose up -d

# Verify services
docker-compose ps

# Check API health
curl http://localhost:8000/health
```

### Access Services
- **API**: http://localhost:8000
- **PostgreSQL**: localhost:5432 (user: blackroad, password: dev-password)
- **Redis**: localhost:6379
- **pgAdmin**: http://localhost:5050 (admin@blackroad.dev / admin)

### Stop Services
```bash
docker-compose down
```

---

## 2. Load Testing

### Run Single Load Test
```bash
# Basic load test (1K users for 10 minutes)
k6 run load-test.js

# With custom parameters
k6 run \
  --vus 5000 \
  --duration 15m \
  --out json=results.json \
  load-test.js
```

### Run All 5 Scenarios
```bash
chmod +x run-load-tests.sh
./run-load-tests.sh
```

This will run:
1. **Baseline** (1K users, 10 min)
2. **Sustained** (5K users, 15 min)
3. **Spike** (10K users, 5 min)
4. **Cache Behavior** (1K users, 60 min)
5. **Mixed Workload** (5K users, 20 min)

### Analyze Results
```bash
# Analyze a specific test
python3 analyze-load-test.py load-test-results/scenario1_baseline_*.json

# Save report to file
python3 analyze-load-test.py load-test-results/scenario1_baseline_*.json \
  -o scenario1_report.txt
```

---

## 3. Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| API Latency (p95) | < 500ms | TBD |
| API Latency (p99) | < 1000ms | TBD |
| Error Rate | < 1% | TBD |
| Throughput (req/sec) | > 10K | TBD |

---

## 4. Deployment Pipeline

### GitHub Actions Workflow

The `.github/workflows/ci-cd.yml` runs on every push to `main` or `develop`:

1. **Test** - Run unit tests, linting
2. **Build** - Build Docker image
3. **Load Test** - Run baseline load test (main branch only)
4. **Deploy** - Deploy to staging (main branch only)

### Manual Build & Push

```bash
# Build Docker image locally
docker build -t blackroad:latest .

# Tag for registry
docker tag blackroad:latest ghcr.io/yourusername/blackroad:latest

# Push to registry (requires auth)
docker login ghcr.io
docker push ghcr.io/yourusername/blackroad:latest
```

---

## 5. Staging Deployment

### Prerequisites
```bash
# Set GitHub secrets for your repo:
# - STAGING_DEPLOY_KEY: SSH private key for staging server
# - STAGING_HOST: staging server hostname
# - CLERK_API_KEY: Clerk API key
# - STRIPE_SECRET_KEY: Stripe secret key
# - STRIPE_WEBHOOK_SECRET: Stripe webhook secret
```

### Manual Deploy
```bash
# SSH to staging server
ssh deploy@staging-api.blackroad.dev

# Navigate to app
cd /app/blackroad

# Pull latest image
docker-compose pull api

# Apply migrations
docker-compose exec api alembic upgrade head

# Restart service
docker-compose up -d

# Verify health
curl http://localhost:8000/health
```

---

## 6. Environment Variables

### Local Development (.env)
```env
# Database
DATABASE_URL=postgresql://blackroad:dev-password@postgres:5432/blackroad_dev

# Cache
REDIS_URL=redis://redis:6379

# Authentication
CLERK_API_KEY=test-key

# Stripe
STRIPE_SECRET_KEY=sk_test_fake
STRIPE_WEBHOOK_SECRET=whsec_test_fake

# Logging
LOG_LEVEL=DEBUG
```

### Staging Production
```env
DATABASE_URL=postgresql://user:password@prod-db.example.com:5432/blackroad_prod
REDIS_URL=redis://prod-cache.example.com:6379
CLERK_API_KEY=<real-key>
STRIPE_SECRET_KEY=<real-key>
STRIPE_WEBHOOK_SECRET=<real-key>
LOG_LEVEL=INFO
```

---

## 7. Monitoring & Debugging

### View Logs
```bash
# API logs
docker-compose logs api -f

# Database logs
docker-compose logs postgres -f

# All services
docker-compose logs -f
```

### Database Access
```bash
# Connect to PostgreSQL
psql postgresql://blackroad:dev-password@localhost:5432/blackroad_dev

# Query active connections
SELECT datname, usename, state FROM pg_stat_activity;

# View tables
\dt
```

### Redis Access
```bash
# Connect to Redis
redis-cli -h localhost -p 6379

# Check memory usage
info memory

# View all keys
keys *
```

---

## 8. Load Test Results Interpretation

### Example Output
```
Charge Endpoint:
  Samples: 45,000
  Mean:    245ms
  p95:     380ms
  p99:     620ms

✅ p95 PASS: 380ms < 500ms threshold
✅ p99 PASS: 620ms < 1000ms threshold
✅ ERRORS PASS: 0.2% < 1% threshold
```

### What to Look For

**Good Signs:**
- p95 < 500ms (95% of requests fast)
- p99 < 1000ms (only 1% of requests slow)
- Error rate < 1%
- Consistent latency over time (no degradation)

**Bad Signs:**
- p95 > 800ms (too many slow requests)
- p99 > 1500ms (outliers too bad)
- Error rate > 5%
- Increasing latency over time (resource leak)

---

## 9. Scaling Path

### Phase 1: Baseline (10K users)
1. Run load test with 1K concurrent users
2. Verify p95 < 500ms
3. Monitor database CPU < 70%

### Phase 2: Scaling (100K users)
1. Add Redis caching layer ✅
2. Run 5K concurrent user test
3. Verify p95 < 800ms

### Phase 3: Horizontal (1M users)
1. Deploy 5 API instances (load balancer)
2. Add database read replicas
3. Run 10K concurrent user test

### Phase 4: Extreme Scale (1B users)
See: `SCALE_TO_1B_ROADMAP.md`

---

## 10. Troubleshooting

### Load Test Fails
```bash
# Check API is running
curl http://localhost:8000/health

# Check database connectivity
psql $DATABASE_URL -c "SELECT 1"

# Check Redis connectivity
redis-cli -h localhost ping

# View API logs
docker-compose logs api --tail 50
```

### High Latency During Test
```bash
# Check database queries
docker-compose exec postgres psql -U blackroad -d blackroad_dev \
  -c "SELECT query, calls, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Check Redis memory
redis-cli info memory

# Check CPU usage
docker stats
```

### Out of Memory
```bash
# Increase Docker limits in docker-compose.yml:
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 8G
```

---

## 11. CI/CD Pipeline Secrets Setup

### For GitHub Actions

1. Go to repository Settings → Secrets and variables → Actions
2. Add these secrets:

```
STAGING_DEPLOY_KEY          (SSH private key)
STAGING_HOST                (staging.example.com)
CLERK_API_KEY               (your Clerk key)
STRIPE_SECRET_KEY           (your Stripe key)
STRIPE_WEBHOOK_SECRET       (your Stripe webhook secret)
```

3. Pipeline will run automatically on push to `main`

---

## 12. Next Steps

- [ ] Set up real Clerk and Stripe credentials
- [ ] Run 10K user load test in staging
- [ ] Deploy to production with real keys
- [ ] Set up monitoring (Datadog/New Relic)
- [ ] Create runbooks for common issues
- [ ] Schedule weekly load tests

---

## Support

For issues or questions:
- Check logs: `docker-compose logs`
- Run diagnostic: `./run-load-tests.sh` baseline only
- Review: `SCALE_TO_1B_ROADMAP.md` for architecture context
