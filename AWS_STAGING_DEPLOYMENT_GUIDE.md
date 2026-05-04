# AWS Staging Deployment Guide

**Complete instructions for deploying BlackRoad to AWS staging environment**

---

## Prerequisites

### Required Tools
```bash
# AWS CLI v2
aws --version
# AWS CLI 2.x.x

# Terraform v1.0+
terraform -v
# Terraform v1.x.x

# Docker (for building images)
docker --version

# kubectl (for ECS Exec, optional)
kubectl version --client
```

### AWS Account Setup

1. **Create AWS Account** (if needed)
   - Go to https://aws.amazon.com
   - Create new account or use existing

2. **Set Up Credentials**
   ```bash
   aws configure
   # Enter Access Key ID
   # Enter Secret Access Key
   # Enter Default region: us-east-1
   # Enter Default output format: json
   ```

3. **Verify Access**
   ```bash
   aws sts get-caller-identity
   # Shows your AWS account ID and ARN
   ```

4. **Create S3 Bucket for Terraform State**
   ```bash
   aws s3 mb s3://blackroad-terraform-state-$(date +%s)
   # Enable versioning
   aws s3api put-bucket-versioning \
     --bucket blackroad-terraform-state-xxx \
     --versioning-configuration Status=Enabled
   ```

---

## Step 1: Prepare Environment

### Clone Repository
```bash
cd /workspace
git clone https://github.com/your-org/blackroad.git
cd blackroad
```

### Create AWS Configuration Files

Create `terraform/backend-staging.tf`:
```hcl
terraform {
  backend "s3" {
    bucket         = "blackroad-terraform-state-YOUR-BUCKET"
    key            = "staging/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

Create DynamoDB table for state locking:
```bash
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### Create Staging Terraform Variables

Create `terraform/environments/staging-override.tfvars`:
```hcl
# Override defaults for staging
environment = "staging"

# Smaller instances for cost savings
instance_type = "t3.medium"
rds_instance_class = "db.t3.small"
desired_count = 2  # Multiple instances for HA testing

# Reduced resources
redis_cache_node_type = "cache.t3.small"

# Enable monitoring and logs
enable_detailed_monitoring = true
log_retention_days = 7

# Use staging domain
domain_name = "staging-api.blackroad.com"
```

---

## Step 2: Configure AWS Secrets

### Create RDS Master Password
```bash
aws secretsmanager create-secret \
  --name blackroad/staging/rds-password \
  --description "RDS master password for staging" \
  --secret-string "$(openssl rand -base64 32)"
```

### Create Stripe Keys (TEST MODE)
```bash
# Get test keys from https://dashboard.stripe.com/test/apikeys
aws secretsmanager create-secret \
  --name blackroad/staging/stripe-secret-key \
  --secret-string "sk_test_xxxxxxxxxxxxx"

aws secretsmanager create-secret \
  --name blackroad/staging/stripe-publishable-key \
  --secret-string "pk_test_xxxxxxxxxxxxx"
```

### Create Clerk Keys
```bash
# Get keys from https://dashboard.clerk.com/settings/api-keys
aws secretsmanager create-secret \
  --name blackroad/staging/clerk-api-key \
  --secret-string "sk_test_xxxxxxxxxxxxx"

aws secretsmanager create-secret \
  --name blackroad/staging/clerk-frontend-api \
  --secret-string "pk_xxxxxxxxxxxxx"
```

### Create Admin Token
```bash
ADMIN_TOKEN=$(openssl rand -base64 32)
aws secretsmanager create-secret \
  --name blackroad/staging/admin-token \
  --secret-string "$ADMIN_TOKEN"

echo "Admin Token: $ADMIN_TOKEN"  # Save for later use
```

---

## Step 3: Build and Push Docker Images

### Configure ECR (Elastic Container Registry)

Create ECR repositories:
```bash
aws ecr create-repository \
  --repository-name blackroad/api \
  --region us-east-1

aws ecr create-repository \
  --repository-name blackroad/admin-dashboard \
  --region us-east-1

aws ecr create-repository \
  --repository-name blackroad/customer-analytics \
  --region us-east-1

aws ecr create-repository \
  --repository-name blackroad/monitoring \
  --region us-east-1
```

### Login to ECR
```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com
```

### Build and Push Images
```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGISTRY="$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com"

# Build and push API service
docker build -t blackroad/api:latest .
docker tag blackroad/api:latest $REGISTRY/blackroad/api:latest
docker push $REGISTRY/blackroad/api:latest

# Build and push Admin Dashboard
docker build -t blackroad/admin-dashboard:latest -f admin_dashboard_dockerfile .
docker tag blackroad/admin-dashboard:latest $REGISTRY/blackroad/admin-dashboard:latest
docker push $REGISTRY/blackroad/admin-dashboard:latest

# Build and push Customer Analytics
docker build -t blackroad/customer-analytics:latest -f customer_analytics_dockerfile .
docker tag blackroad/customer-analytics:latest $REGISTRY/blackroad/customer-analytics:latest
docker push $REGISTRY/blackroad/customer-analytics:latest

# Build and push Monitoring
docker build -t blackroad/monitoring:latest -f monitoring_dockerfile .
docker tag blackroad/monitoring:latest $REGISTRY/blackroad/monitoring:latest
docker push $REGISTRY/blackroad/monitoring:latest
```

### Create Dockerfiles (if not exists)

Create `Dockerfile` for main API:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Step 4: Deploy with Terraform

### Initialize Terraform
```bash
cd terraform
terraform init -backend-config=backend-staging.tf

# Verify initialization
terraform plan -var-file=environments/staging.tfvars
```

### Plan Deployment
```bash
terraform plan \
  -var-file=environments/staging.tfvars \
  -var-file=environments/staging-override.tfvars \
  -out=tfplan-staging
```

**Review the output carefully:**
- ✅ Correct number of resources
- ✅ Correct instance sizes
- ✅ Correct security groups
- ✅ Correct database configuration

### Apply Deployment
```bash
terraform apply tfplan-staging
```

**This will create:**
- VPC with public/private subnets (2 AZs)
- RDS PostgreSQL instance
- ElastiCache Redis cluster
- ECS Cluster with services
- Application Load Balancer (ALB)
- CloudWatch log groups
- IAM roles and policies

**Expected time: 15-20 minutes**

### Save Terraform Outputs
```bash
terraform output -json > staging-outputs.json

# Extract important values
LOAD_BALANCER_DNS=$(terraform output -raw load_balancer_dns)
echo "Load Balancer: $LOAD_BALANCER_DNS"

RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
echo "RDS Endpoint: $RDS_ENDPOINT"

REDIS_ENDPOINT=$(terraform output -raw redis_endpoint)
echo "Redis Endpoint: $REDIS_ENDPOINT"
```

---

## Step 5: Configure Environment Variables

### ECS Task Definition Updates

Update ECS task definitions with staging values:

```bash
# Create environment file for ECS
cat > staging-env.json << EOF
[
  {"name": "DATABASE_URL", "value": "postgresql://admin:password@$RDS_ENDPOINT:5432/blackroad"},
  {"name": "REDIS_URL", "value": "redis://$REDIS_ENDPOINT:6379"},
  {"name": "ENVIRONMENT", "value": "staging"},
  {"name": "DEBUG", "value": "false"},
  {"name": "LOG_LEVEL", "value": "INFO"},
  {"name": "API_PORT", "value": "8000"},
  {"name": "ADMIN_PORT", "value": "8001"},
  {"name": "ANALYTICS_PORT", "value": "8003"}
]
EOF
```

### Update Secrets in Parameter Store

```bash
# Store database credentials
aws ssm put-parameter \
  --name /blackroad/staging/db-password \
  --value "YOUR_SECURE_PASSWORD" \
  --type SecureString \
  --overwrite

# Store API keys
aws ssm put-parameter \
  --name /blackroad/staging/stripe-secret-key \
  --value "sk_test_xxx" \
  --type SecureString \
  --overwrite

aws ssm put-parameter \
  --name /blackroad/staging/clerk-api-key \
  --value "sk_test_xxx" \
  --type SecureString \
  --overwrite
```

---

## Step 6: Initialize Database

### Connect to RDS

```bash
# Get RDS endpoint
RDS_ENDPOINT=$(terraform output -raw rds_endpoint)

# Connect using psql
psql -h $RDS_ENDPOINT -U admin -d blackroad

# Or use RDS Proxy (recommended)
# Update connection string to use proxy endpoint
```

### Run Database Migrations

Option 1: Use ECS Task
```bash
aws ecs run-task \
  --cluster blackroad-staging \
  --task-definition blackroad-migration:1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}"
```

Option 2: Connect Directly
```bash
export DATABASE_URL="postgresql://admin:password@$RDS_ENDPOINT:5432/blackroad"
alembic upgrade head
```

### Verify Database
```bash
psql -h $RDS_ENDPOINT -U admin -d blackroad << EOF
\dt  -- List tables
SELECT COUNT(*) FROM stripe_customers;
SELECT COUNT(*) FROM monthly_usage;
EOF
```

---

## Step 7: Verify Deployment

### Check ECS Services
```bash
# Get service status
aws ecs describe-services \
  --cluster blackroad-staging \
  --services blackroad-api blackroad-admin blackroad-analytics \
  --query 'services[*].[serviceName,status,runningCount,desiredCount]' \
  --output table

# Expected output:
# serviceName              | status   | runningCount | desiredCount
# blackroad-api            | ACTIVE   | 2            | 2
# blackroad-admin          | ACTIVE   | 2            | 2
# blackroad-analytics      | ACTIVE   | 2            | 2
```

### Check Load Balancer
```bash
LB_DNS=$(terraform output -raw load_balancer_dns)

# Health check endpoints
curl http://$LB_DNS:8000/status
curl http://$LB_DNS:8001/api/admin/revenue/total \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
curl http://$LB_DNS:8003/api/customers \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Check Logs
```bash
# View API logs
aws logs tail /ecs/blackroad-api --follow

# View admin dashboard logs
aws logs tail /ecs/blackroad-admin --follow

# View analytics logs
aws logs tail /ecs/blackroad-analytics --follow

# View errors only
aws logs tail /ecs/blackroad-api --follow --filter-pattern "ERROR"
```

---

## Step 8: Configure DNS

### Create Route 53 Records

```bash
# Get hosted zone ID
ZONE_ID=$(aws route53 list-hosted-zones-by-name \
  --dns-name blackroad.com \
  --query 'HostedZones[0].Id' \
  --output text)

# Get ALB DNS name
ALB_DNS=$(terraform output -raw load_balancer_dns)

# Create DNS record
aws route53 change-resource-record-sets \
  --hosted-zone-id $ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "staging-api.blackroad.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "'$ALB_DNS'"}]
      }
    }]
  }'

# Verify DNS propagation
nslookup staging-api.blackroad.com
dig staging-api.blackroad.com
```

### SSL Certificate Setup

```bash
# Request ACM certificate
aws acm request-certificate \
  --domain-name staging-api.blackroad.com \
  --validation-method DNS \
  --region us-east-1

# Get certificate details for DNS validation
CERT_ARN=$(aws acm list-certificates \
  --query 'CertificateSummaryList[0].CertificateArn' \
  --output text)

aws acm describe-certificate \
  --certificate-arn $CERT_ARN \
  --query 'Certificate.DomainValidationOptions'

# Update ALB to use HTTPS listener
aws elbv2 create-listener \
  --load-balancer-arn $(terraform output -raw alb_arn) \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=$CERT_ARN \
  --default-actions Type=forward,TargetGroupArn=$(terraform output -raw api_target_group_arn)
```

---

## Step 9: Load Testing

### Prepare Load Test

```bash
# Update k6 script with staging endpoint
cat > k6-staging-test.js << 'EOF'
import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = 'http://staging-api.blackroad.com';
const ADMIN_TOKEN = 'your-admin-token';

export const options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp up
    { duration: '5m', target: 50 },   // Hold
    { duration: '2m', target: 100 },  // Peak
    { duration: '5m', target: 50 },   // Reduce
    { duration: '2m', target: 0 },    // Ramp down
  ],
};

export default function () {
  // Test /status endpoint
  let res = http.get(BASE_URL + ':8000/status');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });

  // Test admin endpoint
  res = http.get(BASE_URL + ':8001/api/admin/revenue/total', {
    headers: { 'Authorization': 'Bearer ' + ADMIN_TOKEN },
  });
  check(res, {
    'admin status is 200': (r) => r.status === 200,
  });
}
EOF

# Run k6 load test
k6 run k6-staging-test.js
```

### Monitor During Load Test

```bash
# Watch CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average,Maximum

# Watch ECS CPU/Memory
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=blackroad-api \
                 Name=ClusterName,Value=blackroad-staging \
  --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average,Maximum
```

---

## Step 10: Integration Testing

### Test API Endpoints

```bash
ADMIN_TOKEN="your-admin-token"
API_URL="http://staging-api.blackroad.com:8000"
ADMIN_URL="http://staging-api.blackroad.com:8001"

# Test billing API
echo "Testing Billing API..."
curl -X POST $API_URL/charge \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust_staging_1",
    "amount": 5.00,
    "description": "Test charge"
  }'

# Test usage endpoint
curl $API_URL/usage \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Test admin dashboard
echo "Testing Admin Dashboard..."
curl $ADMIN_URL/api/admin/revenue/total \
  -H "Authorization: Bearer $ADMIN_TOKEN"

curl $ADMIN_URL/api/admin/users/total \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Test customer analytics
echo "Testing Customer Analytics..."
curl http://staging-api.blackroad.com:8003/api/customers \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Test Stripe Integration

```bash
# Use Stripe test cards to test payment flow
STRIPE_API_KEY="sk_test_xxx"

# Create test customer
curl https://api.stripe.com/v1/customers \
  -u $STRIPE_API_KEY: \
  -d description="Staging Test Customer"

# Create test billing meter
curl https://api.stripe.com/v1/billing/meters \
  -u $STRIPE_API_KEY: \
  -d display_name="API Requests" \
  -d event_name="api_request"
```

---

## Step 11: Monitoring Setup

### Create CloudWatch Dashboards

```bash
aws cloudwatch put-dashboard \
  --dashboard-name BlackRoad-Staging \
  --dashboard-body file://monitoring-dashboard.json
```

Create `monitoring-dashboard.json`:
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ApplicationELB", "TargetResponseTime", {"stat": "Average"}],
          ["AWS/RDS", "CPUUtilization"],
          ["AWS/ECS", "CPUUtilization"],
          ["AWS/ECS", "MemoryUtilization"],
          ["AWS/ElastiCache", "CPUUtilization"]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Staging Infrastructure Health"
      }
    }
  ]
}
```

### Create CloudWatch Alarms

```bash
# High response time alarm
aws cloudwatch put-metric-alarm \
  --alarm-name BlackRoad-Staging-HighResponseTime \
  --alarm-description "Alert when response time exceeds 500ms" \
  --metric-name TargetResponseTime \
  --namespace AWS/ApplicationELB \
  --statistic Average \
  --period 300 \
  --threshold 500 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:xxx:alerts

# High CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name BlackRoad-Staging-HighCPU \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:xxx:alerts
```

---

## Step 12: Backup & Disaster Recovery

### Configure RDS Backups

```bash
# Enable automated backups (already set in Terraform)
aws rds modify-db-instance \
  --db-instance-identifier blackroad-staging \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00" \
  --apply-immediately
```

### Create Manual Snapshot

```bash
aws rds create-db-snapshot \
  --db-instance-identifier blackroad-staging \
  --db-snapshot-identifier blackroad-staging-backup-$(date +%Y%m%d-%H%M%S)
```

### Test Restore

```bash
# Create a test restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier blackroad-staging-restore-test \
  --db-snapshot-identifier blackroad-staging-backup-xxx \
  --db-instance-class db.t3.small
```

---

## Troubleshooting

### Services Not Starting

```bash
# Check task logs
aws ecs describe-tasks \
  --cluster blackroad-staging \
  --tasks $(aws ecs list-tasks --cluster blackroad-staging --output text) \
  --query 'tasks[*].[taskDefinitionArn,lastStatus,stoppedReason]'

# View CloudWatch logs
aws logs tail /ecs/blackroad-api --follow --filter-pattern "ERROR"
```

### Database Connection Issues

```bash
# Test database connectivity
psql -h $RDS_ENDPOINT -U admin -d blackroad -c "SELECT version();"

# Check security group
aws ec2 describe-security-groups \
  --filters "Name=group-id,Values=sg-xxx"
```

### High Latency

```bash
# Check ALB metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=app/blackroad-staging/xxx \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average,Maximum,p99
```

---

## Cost Management

### Estimate Costs

```bash
# View resource costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE
```

### Cost Optimization Tips

1. **Use Reserved Instances** - 30-40% savings
2. **Schedule RDS Downtime** - Stop during off-hours
3. **Use Spot Instances** - 70% savings for stateless services
4. **Enable S3 Lifecycle** - Archive old logs
5. **Right-size Instances** - Start small, scale based on metrics

---

## Cleanup & Teardown

### Destroy Staging Environment

```bash
# WARNING: This will delete all AWS resources

# First, backup database
aws rds create-db-snapshot \
  --db-instance-identifier blackroad-staging \
  --db-snapshot-identifier blackroad-staging-final-backup

# Destroy infrastructure
cd terraform
terraform destroy \
  -var-file=environments/staging.tfvars \
  -var-file=environments/staging-override.tfvars

# Clean up ECR repositories (optional)
aws ecr delete-repository \
  --repository-name blackroad/api \
  --force

# Clean up secrets
aws secretsmanager delete-secret \
  --secret-id blackroad/staging/stripe-secret-key \
  --force-delete-without-recovery
```

---

## Next Steps

1. **Automated Testing**
   - Set up CI/CD pipeline to run tests on each deploy
   - Configure automatic rollback on test failures

2. **Blue/Green Deployment**
   - Set up second environment for zero-downtime deployments
   - Use Route 53 weighted routing

3. **Production Deployment**
   - After staging validation, deploy to production
   - Use same Terraform templates with prod.tfvars

4. **Custom Domain**
   - Update DNS records to point to staging ALB
   - Configure SSL certificate

---

## Support & Resources

**AWS Documentation:**
- https://docs.aws.amazon.com/ecs/
- https://docs.aws.amazon.com/rds/
- https://docs.aws.amazon.com/terraform/

**Terraform Registry:**
- https://registry.terraform.io/providers/hashicorp/aws/latest/docs

**BlackRoad Documentation:**
- See DEPLOYMENT_SETUP.md for local deployment
- See SCALE_TO_1B_ROADMAP.md for scaling strategy

---

**Deployment Status:** Ready for Staging

**Estimated Time:** 30-45 minutes (first deployment)

**Support:** engineering@blackroad.com

---

**Version:** 1.0.0  
**Last Updated:** 2024-01-31  
**AWS Region:** us-east-1 (configurable)
