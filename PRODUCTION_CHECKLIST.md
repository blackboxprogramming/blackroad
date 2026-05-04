# Production Deployment Checklist

## ✅ Pre-Deployment (Before staging)

- [ ] **Code Review**
  - [ ] All endpoints tested locally
  - [ ] No hardcoded secrets in code
  - [ ] Error handling implemented
  - [ ] Logging in place

- [ ] **Security**
  - [ ] CORS configured correctly
  - [ ] Rate limiting enabled
  - [ ] Input validation on all endpoints
  - [ ] SQL injection prevention (ORM usage)
  - [ ] Authentication tokens validated

- [ ] **Database**
  - [ ] Alembic migrations tested
  - [ ] Backup strategy defined
  - [ ] Connection pooling configured
  - [ ] Indexes created for key queries
  - [ ] Archival plan for old data

- [ ] **Configuration**
  - [ ] All env vars documented in `.env.example`
  - [ ] No local configs in Git
  - [ ] Secrets manager integrated (AWS Secrets/HashiCorp Vault)
  - [ ] Config validation on startup

---

## 🚀 Staging Deployment

### Infrastructure Setup
- [ ] AWS/GCP/Azure account ready
- [ ] VPC/network configured
- [ ] Database provisioned (RDS, CloudSQL, etc)
- [ ] Redis cluster deployed
- [ ] Load balancer configured
- [ ] DNS records pointing to staging

### Application Deployment
```bash
# 1. Build Docker image
docker build -t blackroad:v1.0.0 .

# 2. Push to registry
docker push ghcr.io/blackroad/api:v1.0.0

# 3. Deploy using docker-compose or Kubernetes
docker-compose -f docker-compose.staging.yml up -d

# 4. Run migrations
docker-compose exec api alembic upgrade head

# 5. Verify health
curl https://staging-api.blackroad.dev/health
```

### Smoke Tests
- [ ] API responds to `/health` endpoint
- [ ] Authentication works (Clerk tokens validated)
- [ ] Charge endpoint accepts requests
- [ ] Database queries execute
- [ ] Redis cache responsive
- [ ] Webhook endpoint accessible

### Performance Baseline
- [ ] Run 100 concurrent users test
- [ ] Measure p95 latency (target: <500ms)
- [ ] Verify error rate < 1%
- [ ] No timeout errors
- [ ] Database CPU < 50%

---

## 🔧 Real Credential Integration

### Clerk Setup
```bash
# 1. Create Clerk account (https://clerk.com)
# 2. Create application
# 3. Get API key and add to staging secrets:
export CLERK_API_KEY=sk_test_xxxxx
# 4. Test token validation:
curl -X POST https://api.clerk.com/v1/sessions/verify \
  -H "Authorization: Bearer $CLERK_API_KEY" \
  -d '{"session_token": "test"}'
```

### Stripe Setup
```bash
# 1. Create Stripe account (https://stripe.com)
# 2. Get test API keys
# 3. Configure webhook endpoint:
#    URL: https://staging-api.blackroad.dev/api/webhooks/stripe/meter-events
#    Events: meter_event.created, invoice.created, invoice.payment_succeeded, invoice.payment_failed
# 4. Get webhook secret and add to .env:
export STRIPE_WEBHOOK_SECRET=whsec_test_xxxxx
# 5. Test webhook delivery:
#    Stripe Dashboard → Developers → Webhooks → Send test event
```

---

## 📊 Load Testing Before Production

### Scenario 1: Baseline (1K users)
```bash
k6 run --vus 1000 --duration 10m load-test.js
# Expected: p95 < 500ms, error rate < 1%
```

### Scenario 2: Sustained (5K users)
```bash
k6 run --vus 5000 --duration 15m load-test.js
# Expected: p95 < 800ms, error rate < 1%
```

### Scenario 3: Spike (10K users)
```bash
k6 run --vus 10000 --duration 5m load-test.js
# Expected: p95 < 1000ms, error rate < 2%
```

### Pass/Fail Criteria
- [ ] p95 latency < 1000ms at 10K users
- [ ] Error rate < 2% during spikes
- [ ] No database connection exhaustion
- [ ] Redis memory < 80%
- [ ] API instances stable (no crashes)

---

## 📈 Monitoring Setup

### Datadog / New Relic
- [ ] Application Performance Monitoring (APM) enabled
- [ ] Database query monitoring active
- [ ] Custom metrics for business KPIs:
  - [ ] Charges per second
  - [ ] Revenue per hour
  - [ ] Error rate by endpoint
- [ ] Alerting rules configured:
  - [ ] Latency p95 > 1000ms
  - [ ] Error rate > 5%
  - [ ] Database CPU > 80%
  - [ ] Memory usage > 85%

### Logging
- [ ] ELK stack / CloudWatch configured
- [ ] Log aggregation working
- [ ] Search/filtering functional
- [ ] Log retention policy set (30 days minimum)

### Dashboards
- [ ] Real-time metrics dashboard
- [ ] Business KPIs dashboard (revenue, usage, churn)
- [ ] Infrastructure dashboard (CPU, memory, disk)
- [ ] Alert history dashboard

---

## 🔐 Security Checklist

- [ ] SSL/TLS certificate valid and auto-renewing
- [ ] API keys rotated every 90 days
- [ ] Webhook signatures verified
- [ ] Rate limiting enforced (100 req/min per API key)
- [ ] SQL injection prevention verified (parameterized queries)
- [ ] XSS protection enabled (if applicable)
- [ ] CORS only allows whitelisted origins
- [ ] Sensitive data never logged (PII, tokens)
- [ ] Database backups encrypted
- [ ] VPC security groups restrictive

---

## 📋 Runbooks Created

- [ ] **API Restart**: Steps to gracefully restart without data loss
- [ ] **Database Connection Error**: Troubleshooting and recovery
- [ ] **High Latency Investigation**: Identify bottleneck (DB, cache, API)
- [ ] **Out of Memory**: Steps to safely increase resources
- [ ] **Data Corruption**: Backup recovery procedure
- [ ] **Stripe Webhook Failure**: Manual webhook replay

---

## ✅ Final Production Readiness

### Code
- [ ] All tests passing
- [ ] Code coverage > 80%
- [ ] No security vulnerabilities (OWASP top 10)
- [ ] Load test results documented

### Documentation
- [ ] API documentation complete (Swagger/OpenAPI)
- [ ] Architecture diagrams included
- [ ] Runbooks for common issues
- [ ] Scaling roadmap documented

### Team
- [ ] On-call rotation established
- [ ] Incident response process defined
- [ ] Escalation procedures clear
- [ ] Team trained on new system

### Operations
- [ ] Monitoring dashboards live
- [ ] Alerting configured and tested
- [ ] Backup/restore procedure tested
- [ ] Disaster recovery plan reviewed

---

## 🚢 Production Deployment

Once all checkboxes complete:

```bash
# 1. Tag release
git tag -a v1.0.0 -m "Production release"
git push origin v1.0.0

# 2. Build production image
docker build -t blackroad:v1.0.0 .
docker push ghcr.io/blackroad/api:v1.0.0

# 3. Deploy to production
# (Use infrastructure as code - Terraform, CloudFormation, etc)
terraform apply -var env=production

# 4. Run migrations
kubectl exec -it pod/api-0 -- alembic upgrade head

# 5. Verify production health
curl https://api.blackroad.dev/health

# 6. Monitor metrics
# Watch dashboard for 1 hour
# - API latency stable
# - Error rate < 0.1%
# - Database healthy
# - Revenue tracking normally
```

---

## 📞 Post-Deployment

- [ ] Customer notifications sent
- [ ] Status page updated
- [ ] Changelog published
- [ ] Team debriefing scheduled
- [ ] Metrics baseline captured

---

## 🔄 Scaling Milestones

| Users | Deployment | Timeframe |
|-------|-----------|-----------|
| 1K | Local dev | Week 1 |
| 10K | Staging | Week 2 |
| 100K | Production (Phase 1) | Month 1 |
| 1M | Horizontal scaling | Month 3 |
| 10M | Multi-region | Month 6 |
| 100M | Database sharding | Month 12 |
| 1B | Hyperscale (see roadmap) | Month 36 |

See: `SCALE_TO_1B_ROADMAP.md` for detailed architecture changes at each phase.
