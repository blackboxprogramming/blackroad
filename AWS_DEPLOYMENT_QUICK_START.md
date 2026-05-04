# AWS Deployment Quick Start

**Get BlackRoad running on AWS in 30 minutes**

---

## Prerequisites (10 minutes)

### 1. AWS Account Setup

```bash
# Install AWS CLI
brew install awscli

# Configure AWS credentials
aws configure
# Enter: Access Key ID
# Enter: Secret Access Key
# Enter: Region (default: us-east-1)
# Enter: Output format (default: json)

# Verify configuration
aws sts get-caller-identity
```

### 2. Install Terraform

```bash
# Install Terraform
brew install terraform

# Verify installation
terraform version
```

### 3. Create S3 Bucket for Terraform State

```bash
# This stores your infrastructure state
aws s3 mb s3://blackroad-terraform-state-$(date +%s) \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket blackroad-terraform-state-$(date +%s) \
  --versioning-configuration Status=Enabled
```

---

## Deploy to AWS Staging (20 minutes)

### Step 1: Initialize Terraform

```bash
cd terraform/environments/staging

# Initialize Terraform
terraform init

# This downloads AWS provider and configures backend
```

### Step 2: Review Infrastructure

```bash
# See what will be created
terraform plan

# Review output:
# - VPC with public/private subnets
# - RDS PostgreSQL database
# - ElastiCache Redis cluster
# - ECS cluster for containers
# - Application Load Balancer
# - Security groups and IAM roles
```

### Step 3: Deploy Infrastructure

```bash
# Create all AWS resources
terraform apply

# Review changes and type: yes

# Wait for deployment (10-15 minutes)
# Terraform output will show:
# - Load balancer DNS name
# - RDS endpoint
# - Redis endpoint
```

### Step 4: Configure Application

```bash
# Get outputs from Terraform
terraform output -json > outputs.json

# Update environment variables
export LOAD_BALANCER_DNS=$(terraform output -raw load_balancer_dns)
export DATABASE_URL=$(terraform output -raw database_url)
export REDIS_URL=$(terraform output -raw redis_url)

# Verify connections
curl http://$LOAD_BALANCER_DNS/health
```

### Step 5: Deploy Application

```bash
# Option 1: Using ECS (recommended)
./deploy-to-ecs.sh staging

# Option 2: Manual Docker push to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

docker build -t blackroad:latest .
docker tag blackroad:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/blackroad:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/blackroad:latest
```

### Step 6: Verify Deployment

```bash
# Check all services are running
curl http://$LOAD_BALANCER_DNS/api/status

# Expected response:
{
  "status": "ok",
  "services": [
    {"name": "billing", "status": "running"},
    {"name": "admin", "status": "running"},
    {"name": "customer-analytics", "status": "running"},
    {"name": "customer-ui", "status": "running"},
    {"name": "ml-analytics", "status": "running"}
  ]
}
```

---

## Deploy to AWS Production (After Staging Testing)

### Step 1: Prepare Production

```bash
cd terraform/environments/production

# Initialize
terraform init

# Plan
terraform plan -out=prod.tfplan

# Review carefully - production changes need approval
```

### Step 2: Deploy Infrastructure

```bash
# Apply production infrastructure
terraform apply prod.tfplan

# Terraform will create:
# - Multi-AZ RDS (High availability)
# - Multi-AZ ElastiCache
# - Auto-scaling ECS services
# - CloudFront CDN
# - Enhanced monitoring
```

### Step 3: Canary Deployment

```bash
# Deploy with canary strategy (recommended for production)
python deploy.py --env production --strategy canary

# This will:
# 1. Route 5% traffic to new version
# 2. Monitor for 60 seconds
# 3. Gradually increase: 10% → 25% → 50% → 100%
# 4. Auto-rollback if issues detected
```

### Step 4: Enable Monitoring

```bash
# Deploy Prometheus
docker run -d -p 9090:9090 prom/prometheus \
  --config.file=/etc/prometheus/prometheus.yml

# Deploy Grafana
docker run -d -p 3000:3000 grafana/grafana

# Access at: http://ALB_DNS:3000
```

---

## Verify Staging Deployment

### Health Checks

```bash
# Test each service
curl http://$LOAD_BALANCER_DNS:8000/health  # Billing
curl http://$LOAD_BALANCER_DNS:8001/health  # Admin
curl http://$LOAD_BALANCER_DNS:8003/health  # Analytics
curl http://$LOAD_BALANCER_DNS:8004/health  # UI
curl http://$LOAD_BALANCER_DNS:8005/health  # ML
```

### Database Tests

```bash
# Verify database is accessible
psql $DATABASE_URL -c "SELECT version();"

# Check migrations
psql $DATABASE_URL -c "SELECT * FROM alembic_version;"
```

### Cache Tests

```bash
# Verify Redis is accessible
redis-cli -u $REDIS_URL ping
# Expected: PONG
```

### Load Balancer Tests

```bash
# Test routing
curl -I http://$LOAD_BALANCER_DNS/api/billing/status
curl -I http://$LOAD_BALANCER_DNS/api/admin/revenue
curl -I http://$LOAD_BALANCER_DNS/api/customer/usage
```

---

## Cost Estimation

### Staging Environment

```
RDS (db.t3.medium):           $0.47/day (~$14/mo)
ElastiCache (t3.micro):       $0.30/day (~$9/mo)
ECS Fargate (2 vCPU):         $1.20/day (~$36/mo)
ALB:                          $0.20/day (~$6/mo)
Data transfer:                $0.10/day (~$3/mo)
────────────────────────────────
Total Staging:                ~$68/month
```

### Production Environment

```
RDS Multi-AZ (db.r6i.xlarge): $3.00/day (~$90/mo)
ElastiCache (r6g.xlarge):     $1.50/day (~$45/mo)
ECS Fargate (4 vCPU × 3):     $3.60/day (~$108/mo)
ALB:                          $0.20/day (~$6/mo)
CloudFront (100GB/mo):        $0.50/day (~$15/mo)
Data transfer:                $0.50/day (~$15/mo)
────────────────────────────────
Total Production:             ~$279/month
```

---

## Troubleshooting

### Services Not Responding

```bash
# Check ECS tasks
aws ecs list-tasks --cluster staging
aws ecs describe-tasks --cluster staging --tasks <task-arn>

# Check logs
aws logs tail /ecs/blackroad-billing --follow

# Restart services
aws ecs update-service --cluster staging \
  --service billing --force-new-deployment
```

### Database Connection Issues

```bash
# Check RDS security group
aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=blackroad-db"

# Test connection
psql -h $RDS_ENDPOINT -U admin -d blackroad -c "SELECT 1;"
```

### Load Balancer Issues

```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn <ARN>

# Check access logs
aws s3 ls s3://blackroad-alb-logs/
```

---

## Scale Up

### Auto-Scaling Policy

```bash
# Set desired capacity
aws ecs update-service --cluster staging \
  --service billing \
  --desired-count 5

# Enable auto-scaling
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/staging/billing \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10
```

### Database Scaling

```bash
# Scale RDS (multi-AZ)
aws rds modify-db-instance \
  --db-instance-identifier blackroad-staging \
  --db-instance-class db.r6i.xlarge \
  --apply-immediately
```

---

## Security Hardening

### Enable AWS WAF

```bash
# Create WAF rules
aws wafv2 create-web-acl \
  --name blackroad-waf \
  --scope REGIONAL \
  --default-action Block={}

# Attach to ALB
aws wafv2 associate-web-acl \
  --web-acl-arn <WAF-ARN> \
  --resource-arn <ALB-ARN>
```

### Enable CloudTrail

```bash
# Log all API calls
aws cloudtrail create-trail --name blackroad-trail \
  --s3-bucket-name blackroad-cloudtrail-logs
```

### Enable VPC Flow Logs

```bash
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids <VPC-ID> \
  --traffic-type ALL \
  --log-group-name /aws/vpc/blackroad
```

---

## Monitoring

### CloudWatch Dashboards

```bash
# Create monitoring dashboard
aws cloudwatch put-dashboard \
  --dashboard-name BlackRoad \
  --dashboard-body file://dashboard.json
```

### Set Up Alarms

```bash
# High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name blackroad-error-rate \
  --alarm-description "Error rate > 1%" \
  --metric-name ErrorRate \
  --namespace AWS/ApplicationELB \
  --statistic Average \
  --period 300 \
  --threshold 0.01 \
  --comparison-operator GreaterThanThreshold
```

---

## Useful Commands

```bash
# View all AWS resources
terraform state list

# View specific resource
terraform state show aws_ecs_cluster.main

# Destroy infrastructure (staging only!)
terraform destroy

# View Terraform outputs
terraform output

# SSH into EC2 instance
aws ssm start-session --target i-1234567890

# View logs
aws logs tail /ecs/blackroad-billing --follow

# Scale service
aws ecs update-service --cluster staging \
  --service billing --desired-count 5
```

---

## Next Steps After Deployment

✅ **Staging (24 hours)**
- Run integration tests
- Verify all services working
- Check performance metrics
- Test payment processing (Stripe test mode)
- Load test with customer data

✅ **Production (After staging validated)**
- Use canary deployment (not blue/green for first prod deploy)
- Monitor for 24 hours
- Have rollback plan ready
- Alert team of deployment
- Check customer access

✅ **Post-Deployment (1 week)**
- Monitor error rates
- Collect performance metrics
- Get customer feedback
- Document any issues
- Plan optimizations

---

**Status:** Ready to deploy  
**Estimated Time:** 30 minutes  
**Cost:** Staging $68/mo, Production $279/mo  
**Rollback Time:** < 10 minutes
