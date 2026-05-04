# Production Deployment Pipeline

**Blue/Green, Canary, and Automated Rollback for BlackRoad**

---

## Overview

This guide covers production deployment strategies for BlackRoad SaaS platform:

✅ **Blue/Green Deployment** - Zero-downtime updates with instant rollback
✅ **Canary Releases** - Gradual rollout with 5 stages (5% → 10% → 25% → 50% → 100%)
✅ **Automated Rollback** - Instant rollback on health check failures
✅ **Pre-deployment Checks** - Git status, Docker images, AWS credentials, tests
✅ **Smoke Tests** - Quick validation on new deployment
✅ **Load Tests** - Verify performance under load
✅ **Health Monitoring** - 5-minute continuous monitoring before full switch

---

## Quick Start

### 1. Prerequisites

```bash
# Install dependencies
pip install boto3 pyyaml

# Configure AWS
aws configure

# Login to ECR (AWS container registry)
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

### 2. Deploy to Staging (Blue/Green)

```bash
python deploy.py --env staging --strategy blue-green
```

**What happens:**
1. Runs pre-deployment checks (tests, git status, Docker images)
2. Deploys to GREEN environment
3. Runs smoke tests
4. Runs load tests (60 seconds)
5. Warms up cache
6. Switches traffic
7. Monitors for 5 minutes
8. Cleans up old BLUE environment

### 3. Deploy to Production (Canary)

```bash
python deploy.py --env production --strategy canary
```

**What happens:**
1. Pre-deployment checks
2. Deploy new version as CANARY
3. Route 5% of traffic → Monitor 60s → Check error rate < 1%
4. Route 10% of traffic → Monitor 60s → Check error rate < 1%
5. Route 25% of traffic → Monitor 60s → Check error rate < 1%
6. Route 50% of traffic → Monitor 60s → Check error rate < 1%
7. Route 100% of traffic → Full rollout complete

### 4. Rollback on Issues

```bash
python deploy.py --env production --rollback v1.5.2
```

---

## Deployment Strategies

### Blue/Green Deployment

**Strategy**: Two identical production environments (BLUE active, GREEN inactive)

**Timeline**:
1. Deploy to GREEN (2 min)
2. Smoke tests (30 sec)
3. Load tests (60 sec)
4. Cache warmup (30 sec)
5. Switch traffic (10 sec) ← All users instantly switch
6. Monitor (5 min)
7. Cleanup (2 min)

**Total time**: ~10 minutes from start to complete

**Advantages**:
- Instant rollback (revert traffic switch)
- Full environment testing before switch
- No partial deployments
- Easy A/B testing between versions

**Rollback procedure**:
```bash
# If issues detected within 5-minute window
# System automatically switches back to BLUE
# If manual rollback needed after 5 minutes:
python deploy.py --env production --rollback v1.5.1
```

**When to use**:
- ✅ Major feature releases
- ✅ Database schema changes
- ✅ When you need instant rollback
- ✅ Non-breaking infrastructure changes

---

### Canary Deployment

**Strategy**: Gradual traffic shift with continuous monitoring

**Stages**:
1. **Stage 1**: 5% traffic (100 users per 2000)
2. **Stage 2**: 10% traffic (200 users per 2000)
3. **Stage 3**: 25% traffic (500 users per 2000)
4. **Stage 4**: 50% traffic (1000 users per 2000)
5. **Stage 5**: 100% traffic (all users)

**Timeline per stage**:
- Deploy: 2 min
- Monitor: 60 sec
- Error rate check: instant
- Proceed or rollback: instant

**Total time**: ~5-8 minutes for full rollout (if all stages pass)

**Monitoring at each stage**:
```
✓ Error rate < 1%
✓ Latency < 500ms (p95)
✓ No critical alerts
✓ CPU < 80%
✓ Memory < 85%
```

**Auto-rollback triggers**:
- Error rate > 1%
- Latency spike > 1000ms
- Any CRITICAL alert
- Health check failure

**When to use**:
- ✅ API changes
- ✅ Performance-sensitive changes
- ✅ Algorithm updates
- ✅ When you want to catch issues early

---

### Pre-deployment Checks

All deployments run these checks first:

1. **Git Status Check**
   - Verify repository is clean
   - No uncommitted changes (stash if needed)
   - Correct branch

2. **Docker Images**
   - Verify blackroad:latest exists
   - Build if missing

3. **AWS Credentials**
   - Verify AWS CLI is configured
   - Check IAM permissions
   - Verify correct AWS account

4. **Database Migrations**
   - Check alembic version matches code
   - Verify pending migrations can be applied
   - Backup database before migration

5. **Configuration**
   - Verify all required environment variables
   - Check Stripe/Clerk API keys
   - Verify Redis connection

6. **Test Suite**
   - Run full test suite (pytest)
   - Verify no test failures
   - Check code coverage >80%

**If any check fails, deployment is aborted.**

---

## Smoke Tests

Quick validation of critical functionality:

1. **Health Endpoint** (/health)
   - Checks all services are running
   - Verifies database connection
   - Confirms Redis cache online

2. **Billing API** (/status)
   - Can fetch billing status
   - Database queries working

3. **Admin Dashboard** (/health)
   - Admin API responsive
   - Analytics computing

4. **Customer APIs** (/health)
   - Analytics service running
   - UI service running

---

## Load Tests

Verify performance under sustained load:

```
Duration: 60 seconds
Target: 10,000 requests total (~166 req/s)

Success criteria:
✓ Error rate < 1%
✓ Latency p99 < 1000ms
✓ No timeouts
✓ Cache hit rate > 80%
```

**What gets tested**:
- API throughput
- Database query performance
- Cache hit rates
- Error handling
- Connection pooling

---

## Health Monitoring

After traffic switch, continuous monitoring for 5 minutes:

```
Checked every 10 seconds:
- Error rate (should be < 0.1%)
- Latency p95 (should be < 500ms)
- CPU usage (should be < 70%)
- Memory usage (should be < 75%)
- Database connection pool (should be < 40 connections)
- Cache hit rate (should be > 80%)
```

**Auto-rollback if any threshold exceeded:**
- Error rate > 1%
- Latency > 1000ms
- CPU > 90%
- Memory > 95%
- Any service restart

---

## Rollback Procedures

### Automatic Rollback (During Deployment)

Triggered during monitoring phase if health check fails:

```
[Monitor] Error rate: 2.5% ❌ THRESHOLD EXCEEDED
[Rollback] Switching traffic back to previous version...
[Rollback] ✅ Rollback completed
[Alert] Deployment failed - error rate spike detected
```

### Manual Rollback (After Deployment)

```bash
# If issues discovered hours/days after deployment:
python deploy.py --env production --rollback v1.5.1

# Or to specific commit:
git checkout abc1234
python deploy.py --env production --rollback abc1234
```

**Rollback timeline**:
- Identify version: 1 min
- Deploy previous version: 2 min
- Run tests: 1 min
- Switch traffic: 1 min
- Monitor: 2 min

**Total**: ~7 minutes to complete rollback

---

## Deployment Logging

Every deployment creates a detailed log:

```
deployment-production-blue_green-1234567890.json
```

Contents:
```json
{
  "deployment_id": "production-blue_green-1234567890",
  "environment": "production",
  "strategy": "blue_green",
  "timestamp": "2024-01-15T10:30:00Z",
  "log": [
    {
      "timestamp": "2024-01-15T10:30:05Z",
      "level": "INFO",
      "message": "Running pre-deployment checks..."
    },
    ...
  ]
}
```

**Use for**:
- Post-deployment review
- Incident analysis
- Performance trending
- Team documentation

---

## Real-World Scenarios

### Scenario 1: Deploy New Feature to Production

```bash
# 1. Develop and test locally
git checkout -b feature/churn-alerts
git commit -m "Add churn detection alerts"

# 2. Push to GitHub and create PR
git push origin feature/churn-alerts

# 3. Tests run automatically via GitHub Actions
# 4. PR approved and merged

# 5. Deploy to staging first
git checkout main && git pull
python deploy.py --env staging --strategy blue-green
# Monitor for issues...

# 6. Deploy to production using canary
python deploy.py --env production --strategy canary
# Gradually routes traffic: 5% → 10% → 25% → 50% → 100%
# Each stage monitored for 60 seconds
```

### Scenario 2: Critical Bug Fix

```bash
# 1. Identify bug
# Error rate spike in production: 5% (normal 0.1%)

# 2. Root cause: Database query timeout
git checkout -b hotfix/query-timeout
# Fix the query
git commit -m "Fix slow query in revenue calculation"

# 3. Push to GitHub, merge
git push origin hotfix/query-timeout

# 4. Deploy with blue/green (fastest rollback)
python deploy.py --env production --strategy blue-green

# 5. Monitor for 5 minutes
# Error rate returns to 0.1% ✅

# 6. Issue resolved!
```

### Scenario 3: Rollback Required

```bash
# 1. Deploy new version
python deploy.py --env production --strategy canary
# At 10% traffic: Error rate spikes to 2%

# 2. Auto-rollback triggered
# System switches back to v1.5.1 automatically
[Rollback] Error rate > 1%. Rolling back...
[Rollback] ✅ Deployment rolled back

# 3. Investigate issue
git log v1.5.2...v1.5.3
# Identify bad change

# 4. Fix and re-deploy
git revert abc1234
python deploy.py --env production --strategy blue-green
```

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Deploy
        run: |
          pip install -r requirements.txt
          python deploy.py --env production --strategy canary
      
      - name: Slack notification
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Deployment ${{ job.status }}: ${{ github.ref_name }}"
            }
```

---

## Monitoring & Alerts

### CloudWatch Alarms (During Deployment)

```
Error Rate Alert: > 1% for 60 seconds → Trigger rollback
Latency Alert: p95 > 1000ms for 120 seconds → Trigger rollback
CPU Alert: > 90% for 180 seconds → Scale up + monitor
Memory Alert: > 95% for 120 seconds → Scale up + monitor
Database Alert: connections > 50 → Scale database
```

### Deployment Metrics

Track these metrics before/after deployment:

```
Before:  Error rate: 0.08%, Latency: 120ms, Throughput: 8000 req/s
After:   Error rate: 0.10%, Latency: 130ms, Throughput: 7900 req/s
Status:  ✅ Within acceptable range
```

---

## Troubleshooting

### Smoke Test Fails

```
[ERROR] Health check failed on customer-ui
[DEBUG] Checking logs...
[DEBUG] Port 8004 not responding

Possible causes:
1. Service not started
2. Port binding issue
3. Configuration missing

Solution:
docker logs customer-ui
# Fix issue and retry deployment
```

### Load Test Shows High Error Rate

```
[ERROR] Load test failed: 5.2% error rate (> 1%)
[DEBUG] Checking error logs...
[DEBUG] 80% of errors are timeout errors

Possible causes:
1. Database slow queries
2. External API timeout
3. Cache not warmed up
4. Resource constraints

Solution:
1. Run database optimization
2. Increase connection pool size
3. Extend cache warmup period
4. Scale database/app instances
```

### Rollback Stalls

```
[ERROR] Rollback monitoring stalled at 60s
[DEBUG] Traffic split is 50/50 (stuck)

Possible causes:
1. Load balancer configuration error
2. DNS propagation delay
3. Regional ALB sync issue

Solution:
1. Manually switch traffic to primary
2. Verify ALB target group health
3. Check Route 53 health checks
4. Contact AWS support if persists
```

---

## Best Practices

✅ **Always deploy to staging first**
- Catch issues before production
- Warm up caches
- Verify scaling policies

✅ **Use canary for risky changes**
- Database schema changes
- Algorithm changes
- High-traffic-impact features

✅ **Use blue/green for safe changes**
- Documentation updates
- Configuration changes
- Non-breaking updates

✅ **Monitor for 24 hours after production deploy**
- Watch error rates
- Monitor customer reports
- Check performance metrics

✅ **Keep old versions running for 2+ hours**
- Allows quick rollback
- Helps debug issues
- Provides comparison data

✅ **Tag all production deployments**
- Enables easy rollback
- Tracks deployment history
- Helps identify regressions

---

## Command Reference

```bash
# Deploy to staging with blue/green
python deploy.py --env staging --strategy blue-green

# Deploy to production with canary
python deploy.py --env production --strategy canary

# Rollback to previous version
python deploy.py --env production --rollback v1.5.1

# Health check only (no deployment)
python deploy.py --health-check

# View deployment logs
cat deployment-production-*.json | jq .

# SSH into production to debug
aws ssm start-session --target i-1234567890abcdef0
```

---

**Version:** 1.0  
**Status:** Production Ready ✅  
**Last Updated:** 2024-01-15
