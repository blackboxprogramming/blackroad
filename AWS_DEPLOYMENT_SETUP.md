# 🚀 AWS Deployment Setup - BlackRoad SaaS Platform

**Status:** ⏳ Preparing for staging deployment  
**Target:** AWS ECS + RDS + ElastiCache + ALB  
**Estimated Deployment Time:** 30-45 minutes  

---

## 📋 Pre-Deployment Checklist

### AWS Account Setup
- [ ] AWS account created
- [ ] AWS CLI installed and configured
- [ ] IAM user created with sufficient permissions
- [ ] AWS credentials in environment or ~/.aws/config

### GitHub Secrets Configuration
- [ ] AWS_ACCOUNT_ID set
- [ ] AWS_ACCESS_KEY_ID set
- [ ] AWS_SECRET_ACCESS_KEY set
- [ ] AWS_REGION set (e.g., us-east-1)
- [ ] AWS_ECR_REGISTRY set

### Required Services
- [ ] ECR registry created
- [ ] RDS PostgreSQL available
- [ ] ElastiCache Redis available (optional)
- [ ] VPC and security groups configured
- [ ] ALB created and configured

---

## 🏗️ Architecture Overview

### Deployment Model: ECS Fargate + RDS + ALB

```
┌─────────────────────────────────────────────┐
│           AWS Load Balancer (ALB)            │
│          (Route HTTP/HTTPS traffic)         │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
    ┌───▼───┐  ┌───▼───┐  ┌──▼────┐
    │ECS    │  │ECS    │  │ECS    │
    │Task 1 │  │Task 2 │  │Task 3 │
    │(Svcs) │  │(Svcs) │  │(Svcs) │
    └───┬───┘  └───┬───┘  └───┬───┘
        │          │          │
        └──────────┼──────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼────┐  ┌─────▼──────┐  ┌────▼───┐
│RDS     │  │ElastiCache │  │S3      │
│Postgres│  │Redis       │  │Backups │
└────────┘  └────────────┘  └────────┘
```

---

## 🔧 AWS Infrastructure Components

### 1. ECR (Elastic Container Registry)
```
Repository: blackroad-services
Images:
├─ billing-api
├─ admin-dashboard
├─ analytics
├─ ml-engine
├─ webhooks
├─ onboarding
├─ monitoring
└─ prometheus
```

### 2. ECS Cluster
```
Cluster: blackroad-cluster
Launch Type: Fargate
CPU: 4096 units per task
Memory: 8192 MiB per task
Task Desired Count: 3
Task Min: 2, Max: 10 (auto-scaling)
```

### 3. RDS Database
```
Engine: PostgreSQL 15
Instance Type: db.t3.medium
Storage: 100 GB
Multi-AZ: Yes
Backup: 7 days retention
```

### 4. ElastiCache (Optional)
```
Engine: Redis 7
Node Type: cache.t3.micro
Nodes: 1 (can scale to 3 for HA)
Auto-failover: Enabled
```

### 5. Application Load Balancer
```
Scheme: Internet-facing
Protocol: HTTP/HTTPS
Port: 80/443
Health Check: /health (30s)
Sticky Sessions: Enabled (1 day)
```

---

## 📦 Terraform Configuration Structure

```
terraform/
├── main.tf              (Main configuration)
├── variables.tf         (Input variables)
├── outputs.tf           (Output values)
├── vpc.tf              (VPC + Security Groups)
├── ecs.tf              (ECS Cluster + Tasks)
├── rds.tf              (RDS Database)
├── elasticache.tf      (Redis Cache)
├── alb.tf              (Load Balancer)
├── iam.tf              (IAM Roles)
└── environments/
    ├── staging.tfvars
    └── production.tfvars
```

---

## 🎯 Deployment Steps

### Phase 1: Prepare (10 min)
1. Create AWS ECR repository
2. Get AWS account credentials
3. Configure GitHub secrets
4. Set Terraform variables

### Phase 2: Build Docker Images (20 min)
1. GitHub Actions build workflow runs
2. Docker images created
3. Images pushed to ECR
4. Image digests recorded

### Phase 3: Deploy Infrastructure (30 min)
1. Terraform applies VPC + security groups
2. RDS database created
3. ElastiCache cluster created
4. ALB configured
5. ECS cluster deployed
6. Tasks running in Fargate

### Phase 4: Verify (10 min)
1. Health checks passing
2. API endpoints responding
3. Database connected
4. Cache operational

### Total Time: ~70 minutes

---

## 📊 Staging Environment Configuration

```
Environment: staging
Region: us-east-1
Availability Zones: us-east-1a, us-east-1b
VPC CIDR: 10.0.0.0/16
Public Subnets: 10.0.1.0/24, 10.0.2.0/24
Private Subnets: 10.0.10.0/24, 10.0.11.0/24
RDS Endpoint: blackroad-db-staging.xxxxx.rds.amazonaws.com
Redis Endpoint: blackroad-redis-staging.xxxxx.cache.amazonaws.com
ALB DNS: blackroad-staging-xxxx.us-east-1.elb.amazonaws.com
```

---

## 💾 Environment Variables for ECS

```
FLASK_ENV=staging
DATABASE_URL=postgresql://user:pass@blackroad-db-staging.xxxxx.rds.amazonaws.com:5432/blackroad
REDIS_URL=redis://blackroad-redis-staging.xxxxx.cache.amazonaws.com:6379
JWT_SECRET_KEY=<generated>
FLASK_SECRET_KEY=<generated>
STRIPE_API_KEY=<test key from GitHub secret>
STRIPE_WEBHOOK_SECRET=<from GitHub secret>
SENDGRID_API_KEY=<from GitHub secret>
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus
AWS_REGION=us-east-1
LOG_LEVEL=INFO
```

---

## 🚀 Quick Start Commands

### 1. Create ECR Repository
```bash
aws ecr create-repository \
  --repository-name blackroad-services \
  --region us-east-1
```

### 2. Configure GitHub Secrets
```bash
gh secret set AWS_ACCOUNT_ID -R blackboxprogramming/blackroad
gh secret set AWS_ACCESS_KEY_ID -R blackboxprogramming/blackroad
gh secret set AWS_SECRET_ACCESS_KEY -R blackboxprogramming/blackroad
gh secret set AWS_REGION -R blackboxprogramming/blackroad -b "us-east-1"
```

### 3. Trigger Build & Deploy
```bash
# Create develop branch
git checkout -b develop
git push origin develop

# This triggers:
# 1. Build workflow (Docker images)
# 2. Deploy-staging workflow (ECS deployment)
```

### 4. Monitor Deployment
```bash
# View workflow
gh run list -R blackboxprogramming/blackroad

# View logs
gh run view <run-id> -R blackboxprogramming/blackroad --log
```

---

## 📈 Scaling Configuration

### Auto-Scaling Targets

**ECS Services:**
```
Min Replicas: 2
Desired: 3
Max Replicas: 10
Scale-up threshold: 70% CPU or 80% memory
Scale-down threshold: 20% CPU and 30% memory
Scale-up cooldown: 60 seconds
Scale-down cooldown: 300 seconds
```

**Database:**
```
Auto-scaling: Enabled
Min: db.t3.medium
Max: db.r6i.xlarge
Scale trigger: 70% CPU
```

---

## 🔐 Security Configuration

### Network Security
- VPC isolation
- Security groups restrict traffic
- Private subnets for database
- NAT gateway for outbound
- No direct internet access to RDS

### Secrets Management
- AWS Secrets Manager for credentials
- Environment variables for config
- Never commit secrets
- Rotate credentials every 90 days

### IAM Permissions
```json
{
  "Effect": "Allow",
  "Action": [
    "ecr:GetAuthorizationToken",
    "ecr:BatchGetImage",
    "ecr:GetDownloadUrlForLayer",
    "ecs:*",
    "rds:*",
    "elasticache:*",
    "ec2:*",
    "logs:*"
  ],
  "Resource": "*"
}
```

---

## 📊 Monitoring & Logging

### CloudWatch
- Container logs: /ecs/blackroad-staging
- Application logs: /aws/lambda/blackroad
- Performance metrics: 1-minute resolution
- Alarms: High CPU, failed health checks

### Prometheus
- 38 metrics exported
- Scrape interval: 15 seconds
- Retention: 15 days
- Grafana dashboards included

---

## �� Troubleshooting

### "Access Denied" on ECR
**Solution:** Verify IAM permissions include ECR full access

### Task fails to start
**Solution:** Check CloudWatch logs for error messages

### Database connection timeout
**Solution:** Verify security group allows port 5432 from ECS

### Health check failing
**Solution:** Ensure /health endpoint returns 200 OK

---

## ✅ Verification Checklist

After deployment:
- [ ] ALB shows healthy targets (3/3)
- [ ] RDS database accessible
- [ ] Redis cache connected
- [ ] API endpoints responding
- [ ] Health checks passing
- [ ] CloudWatch logs flowing
- [ ] Metrics visible in Prometheus
- [ ] No alarms triggered

---

## 📞 Support & Documentation

- AWS Fargate Docs: https://docs.aws.amazon.com/ecs/
- Terraform AWS: https://registry.terraform.io/providers/hashicorp/aws/
- RDS Best Practices: https://docs.aws.amazon.com/rds/
- ECS Blue/Green: https://docs.aws.amazon.com/codedeploy/

---

## 🎯 Timeline

- **T+0:** Add secrets to GitHub
- **T+5 min:** Build workflow starts
- **T+25 min:** Docker images pushed to ECR
- **T+30 min:** Deploy workflow starts
- **T+35 min:** Terraform applies
- **T+60 min:** All services running
- **T+65 min:** Health checks green
- **T+70 min:** Ready for testing!

---

**Status: ⏳ Ready for staging deployment**

Next: Configure GitHub secrets → Trigger deploy → Staging live! 🚀

