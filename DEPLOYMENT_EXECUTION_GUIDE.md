# 🚀 DEPLOYMENT EXECUTION GUIDE - BlackRoad Staging Deployment

**Date:** 2026-05-04  
**Target Environment:** AWS Staging  
**Deployment Type:** Full infrastructure + services  
**Estimated Time:** 60-90 minutes  
**Status:** Ready to execute  

---

## 📋 Pre-Execution Checklist

Before starting the deployment, ensure all of the following are complete:

### Prerequisites
- [ ] GitHub secrets configured (see GITHUB_SECRETS_SETUP.md)
- [ ] AWS account ready with appropriate permissions
- [ ] AWS CLI installed and authenticated locally
- [ ] Terraform installed (v1.0+)
- [ ] Git repository cloned locally
- [ ] ECR repository created in AWS

### GitHub Secrets Verified
- [ ] AWS_ACCOUNT_ID
- [ ] AWS_ACCESS_KEY_ID
- [ ] AWS_SECRET_ACCESS_KEY
- [ ] AWS_REGION (e.g., us-east-1)
- [ ] STRIPE_API_KEY (use test key for staging)
- [ ] STRIPE_WEBHOOK_SECRET

---

## 🎯 Deployment Execution Flow

### STEP 1: Create Develop Branch (Local)
**Time:** 2 minutes

```bash
# Clone if not already done
git clone https://github.com/blackboxprogramming/blackroad.git
cd blackroad

# Create develop branch
git checkout -b develop

# Push to trigger staging deployment
git push origin develop
```

**What happens next:**
- GitHub recognizes push to `develop` branch
- CI workflow starts (5 min)
- Build workflow starts (15 min)
- Deploy-staging workflow queued

---

### STEP 2: Monitor CI Workflow (5 minutes)
**Time:** 5 minutes  
**URL:** https://github.com/blackboxprogramming/blackroad/actions

#### CI Workflow Steps:
```
Step 1: Checkout code (30s)
Step 2: Set up Python 3.11 (20s)
Step 3: Install dependencies (45s)
  → pip install -r requirements.txt
Step 4: Run linting (60s)
  → pylint *.py
  → flake8 --max-line-length=120
Step 5: Run unit tests (90s)
  → pytest --cov=./ --cov-report=xml
  → Expected: 40+ tests passing
Step 6: Upload coverage (20s)

Total Duration: 5-7 minutes
Expected Result: ✅ ALL TESTS PASSING
```

**Expected Output:**
```
PASSED test_admin_dashboard.py::test_revenue_tracking
PASSED test_customer_analytics.py::test_churn_prediction
PASSED test_ml_engine.py::test_model_accuracy
PASSED test_stripe_webhooks.py::test_webhook_verification
PASSED test_onboarding.py::test_email_verification
...
40 tests passed, 0 failed
Coverage: 82%
```

---

### STEP 3: Monitor Build Workflow (15 minutes)
**Time:** 15 minutes  
**URL:** https://github.com/blackboxprogramming/blackroad/actions

#### Build Workflow Steps:
```
Step 1: Checkout code (30s)
Step 2: Configure AWS credentials (10s)
  → Export AWS_ACCESS_KEY_ID
  → Export AWS_SECRET_ACCESS_KEY
Step 3: Login to Amazon ECR (10s)
  → AWS ECR authentication
Step 4: Build Docker images (600s)
  → Build: billing-api image (60s)
  → Build: admin-dashboard image (60s)
  → Build: analytics image (60s)
  → Build: ml-engine image (120s)
  → Build: webhooks image (60s)
  → Build: onboarding image (60s)
  → Build: monitoring image (60s)
  → Build: prometheus image (60s)
Step 5: Push to Amazon ECR (120s)
  → Push 8 images to ECR
  → Total size: ~2.5 GB
Step 6: Output image URIs (10s)

Total Duration: 12-15 minutes
Expected Result: ✅ ALL IMAGES PUSHED TO ECR
```

**Expected Output:**
```
Built image: billing-api:78c301e
Pushed: 123456789.dkr.ecr.us-east-1.amazonaws.com/blackroad-services:billing-api-78c301e
Size: 245 MB

Built image: ml-engine:78c301e
Pushed: 123456789.dkr.ecr.us-east-1.amazonaws.com/blackroad-services:ml-engine-78c301e
Size: 890 MB

[8 images pushed successfully]
Total time: 14 minutes 23 seconds
```

---

### STEP 4: Monitor Deploy-Staging Workflow (30 minutes)
**Time:** 30 minutes  
**URL:** https://github.com/blackboxprogramming/blackroad/actions

#### Deploy-Staging Workflow Steps:

**PHASE 1: Terraform Initialization (3 min)**
```
Step 1: Checkout code (30s)
Step 2: Configure AWS credentials (10s)
Step 3: Setup Terraform (10s)
  → Install Terraform 1.5.x
  → Validate syntax
Step 4: Terraform init (120s)
  → Download AWS provider
  → Initialize state (local, can be moved to S3)

Time: 2-3 minutes
Status: ✅ Terraform ready
```

**PHASE 2: Terraform Plan (5 min)**
```
Step 1: Terraform plan (300s)
  → Validate configuration
  → Create execution plan
  → Show what will be created:
    - VPC (1)
    - Subnets (2 public, 2 private)
    - Security Groups (4)
    - Internet Gateway (1)
    - NAT Gateway (1)
    - ECS Cluster (1)
    - ECS Task Definition (8)
    - ECS Services (8)
    - RDS Instance (1)
    - ElastiCache Cluster (1)
    - ALB (1)
    - Target Groups (8)
    - IAM Roles (3)

Time: 4-5 minutes
Status: ✅ Plan successful
Output: "Plan: 45 to add, 0 to change, 0 to destroy"
```

**PHASE 3: Terraform Apply (20 min)**
```
Creating Infrastructure:

T+0min: VPC creation
  → VPC 10.0.0.0/16 created
  → Availability zones: us-east-1a, us-east-1b

T+1min: Networking
  → 2 Public subnets created
  → 2 Private subnets created
  → Internet Gateway attached
  → NAT Gateway created

T+3min: Security Groups
  → ALB security group created
  → ECS security group created
  → RDS security group created
  → ElastiCache security group created

T+5min: RDS Database
  → DB subnet group created
  → RDS instance launching (db.t3.micro)
  → Multi-AZ enabled
  → Automated backups enabled (3 days)
  → Estimated time: 5-8 minutes

T+10min: ElastiCache
  → Redis cluster launching
  → Node type: cache.t3.micro
  → Estimated time: 3-5 minutes

T+13min: ECS Cluster
  → Cluster "blackroad-staging" created
  → Fargate launch type enabled
  → CloudWatch logging configured

T+14min: IAM Roles
  → ecsTaskExecutionRole created
  → ecsTaskRole created
  → ALB role created

T+15min: ALB Setup
  → ALB created
  → Target groups created (8 services)
  → Listener created (port 80)
  → Health checks configured (30s interval)

T+18min: ECS Services
  → Service: billing-api (2 tasks)
  → Service: admin-dashboard (1 task)
  → Service: analytics (1 task)
  → Service: customer-ui (1 task)
  → Service: ml-engine (1 task)
  → Service: webhooks (1 task)
  → Service: onboarding (1 task)
  → Service: monitoring (1 task)

Time: 18-22 minutes
Status: ✅ All resources created
Output: "Apply complete! Resources: 45 added"
```

**PHASE 4: Post-Deployment Verification (2 min)**
```
Checking health:
  ✅ VPC ready
  ✅ Subnets ready
  ✅ RDS accessible (endpoint: blackroad-db-staging.xxxxx.rds.amazonaws.com)
  ✅ ElastiCache accessible (endpoint: blackroad-redis-staging.xxxxx.cache.amazonaws.com)
  ✅ ECS cluster healthy
  ✅ ALB active
  ✅ Services launching

Time: 1-2 minutes
Status: ✅ Infrastructure ready
```

**Total Deploy-Staging Time: 30-35 minutes**

---

## 📊 Expected Outcomes After Deployment

### Infrastructure Status
```
✅ VPC created (10.0.0.0/16)
✅ 4 Subnets deployed (2 public, 2 private)
✅ Security groups configured (4)
✅ ALB created and active
✅ RDS database running (db.t3.micro)
✅ ElastiCache Redis running (cache.t3.micro)
✅ ECS Cluster "blackroad-staging" active
✅ 8 ECS Services running
✅ 8 Tasks deployed (1-2 replicas each)
```

### Service Status (Expected)
```
After 5 minutes:

billing-api              RUNNING (2 tasks)
admin-dashboard          RUNNING (1 task)
customer-analytics       RUNNING (1 task)
customer-ui              RUNNING (1 task)
ml-engine                RUNNING (1 task)
stripe-webhooks          RUNNING (1 task)
onboarding-service       RUNNING (1 task)
monitoring-system        RUNNING (1 task)

Total: 10 services, 10 tasks running
CPU Usage: ~25-30%
Memory Usage: ~40-45%
```

### Health Checks
```
After 10 minutes:

ALB Health:
  billing-api              ✅ HEALTHY (3/3 targets)
  admin-dashboard          ✅ HEALTHY
  analytics                ✅ HEALTHY
  customer-ui              ✅ HEALTHY
  ml-engine                ✅ HEALTHY
  webhooks                 ✅ HEALTHY
  onboarding               ✅ HEALTHY
  monitoring               ✅ HEALTHY

Database Connectivity: ✅ CONFIRMED
Cache Connectivity: ✅ CONFIRMED
Logging to CloudWatch: ✅ CONFIRMED
```

### Network Access
```
ALB DNS Name: blackroad-staging-xxx.us-east-1.elb.amazonaws.com

Test commands:
$ curl http://blackroad-staging-xxx.us-east-1.elb.amazonaws.com/health
✅ {"status": "healthy", "timestamp": "2026-05-04T15:30:00Z"}

$ curl http://blackroad-staging-xxx.us-east-1.elb.amazonaws.com/api/billing/tiers
✅ [{"name": "free", "price": 0}, ...]

$ curl http://blackroad-staging-xxx.us-east-1.elb.amazonaws.com/api/analytics/churn
✅ {"predictions": [...], "models": "ready"}
```

---

## 🔍 Monitoring During Deployment

### CloudWatch Logs
```
Location: /ecs/blackroad-staging

Viewing logs:
$ aws logs tail /ecs/blackroad-staging --follow

Expected output:
[billing-api] Starting Flask app on 0.0.0.0:5000
[admin-dashboard] Connected to database
[ml-engine] Loading model: churn_prediction
[webhooks] Webhook processor ready
[onboarding] Email service initialized
[monitoring] Health check endpoint ready
```

### CloudWatch Metrics
```
Metrics to monitor (1-minute resolution):

CPU Utilization:
  Expected: 15-35% during startup, 10-20% at rest
  Alert threshold: >80%

Memory Utilization:
  Expected: 30-50% during startup, 25-40% at rest
  Alert threshold: >85%

Network In:
  Expected: 100-500 KB/s
  Normal: <100 KB/s at rest

Network Out:
  Expected: 100-500 KB/s
  Normal: <100 KB/s at rest

Task Count:
  Expected: 10 tasks total
  Desired: 10
  Running: 10
  Status: ✅ All running
```

### GitHub Actions Monitoring
```
URL: https://github.com/blackboxprogramming/blackroad/actions

Workflow runs:
1. CI Workflow (5-7 min)     ✅ PASSED
2. Build Workflow (12-15 min) ✅ PASSED
3. Deploy-Staging (30-35 min) ✅ PASSED (in progress)

Total elapsed: 47-57 minutes
Estimated completion: 55-65 minutes total
```

---

## ✅ Validation Steps After Deployment

### Step 1: Verify ALB Response (5 min)
```bash
# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --region us-east-1 \
  --query 'LoadBalancers[?LoadBalancerName==`blackroad-staging`].DNSName' \
  --output text)

echo "ALB DNS: $ALB_DNS"

# Test health endpoint
curl http://$ALB_DNS/health
Expected: {"status": "healthy"}

# Test API endpoints
curl http://$ALB_DNS/api/billing/tiers
curl http://$ALB_DNS/api/admin/revenue
curl http://$ALB_DNS/api/analytics/churn
curl http://$ALB_DNS/api/ml/predictions
```

### Step 2: Verify Database Connection (5 min)
```bash
# Get RDS endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances \
  --query 'DBInstances[?DBInstanceIdentifier==`blackroad-db-staging`].Endpoint.Address' \
  --output text)

echo "RDS Endpoint: $RDS_ENDPOINT"

# Test connection
psql -h $RDS_ENDPOINT -U postgres -d blackroad -c "SELECT VERSION();"
Expected: PostgreSQL 15.x

# Verify tables
psql -h $RDS_ENDPOINT -U postgres -d blackroad -c "\dt"
Expected: All tables listed
```

### Step 3: Verify Cache Connection (5 min)
```bash
# Get ElastiCache endpoint
REDIS_ENDPOINT=$(aws elasticache describe-cache-clusters \
  --query 'CacheClusters[?CacheClusterId==`blackroad-redis-staging`].CacheNodes[0].Endpoint.Address' \
  --output text)

echo "Redis Endpoint: $REDIS_ENDPOINT"

# Test connection
redis-cli -h $REDIS_ENDPOINT ping
Expected: PONG

# Test data storage
redis-cli -h $REDIS_ENDPOINT SET test_key "test_value"
redis-cli -h $REDIS_ENDPOINT GET test_key
Expected: "test_value"
```

### Step 4: Verify Services Health (10 min)
```bash
# Check all services
for service in billing admin analytics customer ml webhooks onboarding monitoring; do
  echo "Checking $service..."
  curl -s http://$ALB_DNS/api/$service/health | jq .
done

Expected: All return {"status": "healthy"}
```

### Step 5: Verify CloudWatch Logs (10 min)
```bash
# Tail logs from each service
aws logs tail /ecs/blackroad-staging --follow --since 5m

Expected output:
[billing-api] Request to /api/billing/tiers completed in 45ms
[admin-dashboard] Revenue calculation completed
[ml-engine] Churn prediction: 87% accuracy
[webhooks] Stripe webhook received and processed
[onboarding] Verification email sent to user@example.com
[monitoring] All services healthy
```

---

## 🎯 Success Criteria

After ~60 minutes of deployment, you should have:

### Infrastructure ✅
- [ ] VPC created with 4 subnets
- [ ] RDS PostgreSQL running and accessible
- [ ] ElastiCache Redis running and accessible
- [ ] ALB created with all target groups healthy
- [ ] ECS Cluster active with 8 services

### Services ✅
- [ ] All 10 services running (10 tasks total)
- [ ] All health checks passing (10/10 healthy)
- [ ] All endpoints responding with HTTP 200
- [ ] CPU <30%, Memory <50%
- [ ] No errors in CloudWatch logs

### Data ✅
- [ ] Database tables created and populated
- [ ] Cache working (PING response)
- [ ] Logs flowing to CloudWatch
- [ ] Metrics visible in CloudWatch Dashboards
- [ ] Webhooks endpoint accessible

### Integration ✅
- [ ] API gateway responding to requests
- [ ] Services communicating with database
- [ ] Services communicating with cache
- [ ] Monitoring system operational
- [ ] Alerting system ready

---

## 📈 Performance Baseline (Staging)

After stabilization (5-10 minutes):

```
API Latency:
  GET /health:          10-20ms
  GET /api/billing:     50-100ms
  GET /api/analytics:   100-200ms
  GET /api/ml:          200-400ms
  POST /api/webhook:    100-150ms

Error Rate:            <0.1%
Availability:          99.9%
CPU Usage:             15-25%
Memory Usage:          35-45%
Network Latency:       <10ms
Database Query Time:   <100ms
Cache Hit Rate:        80%+
```

---

## 🆘 Troubleshooting Common Issues

### Issue: Tasks failing to start
**Symptom:** Tasks in STOPPED state, health checks failing
**Solution:**
```bash
# Check logs
aws logs tail /ecs/blackroad-staging --follow

# Check task definition
aws ecs describe-task-definition --task-definition blackroad-staging

# Common causes:
# 1. Image not found in ECR
# 2. Database connection string incorrect
# 3. Memory too low for container
# 4. IAM role missing permissions
```

### Issue: Database connection timeout
**Symptom:** Services can't connect to RDS
**Solution:**
```bash
# Verify security group
aws ec2 describe-security-groups \
  --query 'SecurityGroups[?GroupName==`blackroad-rds-sg`]'

# Ensure ECS security group can reach RDS
aws ec2 authorize-security-group-ingress \
  --group-id sg-rds \
  --source-security-group-id sg-ecs \
  --protocol tcp \
  --port 5432
```

### Issue: High CPU usage
**Symptom:** CPU >70%, containers slow
**Solution:**
```bash
# Increase container resources
# Edit task definition: increase CPU (256→512 units)
# Edit task definition: increase memory (512→1024 MB)

# Or add more replicas
aws ecs update-service \
  --cluster blackroad-staging \
  --service billing-api \
  --desired-count 3
```

---

## 📞 Next Steps After Successful Staging Deployment

1. **Run Integration Tests** (10 min)
   ```bash
   ./test_*.sh
   ```

2. **Run Performance Tests** (30 min)
   ```bash
   # Simulate 1000 concurrent users
   ./performance_test.py --users 1000 --duration 10min
   ```

3. **Verify Monitoring** (10 min)
   - Check CloudWatch dashboards
   - Verify alarm rules
   - Test Slack notifications

4. **Load Stripe Test Keys** (5 min)
   - Configure webhook URL in Stripe dashboard
   - Point to staging ALB DNS

5. **Create Smoke Test Users** (15 min)
   - Sign up test user
   - Complete onboarding flow
   - Process test payment

6. **Approve for Production** 
   - If all tests pass
   - Schedule production deployment
   - Create deployment window

---

## 📋 Post-Deployment Checklist

After successful staging deployment:

- [ ] All services running (10/10)
- [ ] All health checks passing
- [ ] CloudWatch logs flowing
- [ ] Metrics visible in dashboards
- [ ] API endpoints responding
- [ ] Database operational
- [ ] Cache operational
- [ ] ALB responding
- [ ] No errors in logs
- [ ] Performance baseline met
- [ ] Integration tests passing
- [ ] Security verified
- [ ] Monitoring alerts working
- [ ] Team notified
- [ ] Ready for production

---

**Status: Ready to execute staging deployment**

Next: Run deployment workflow and monitor for completion!

