# AWS Infrastructure as Code (Terraform)

Complete production infrastructure for BlackRoad API with RDS, ElastiCache, and ECS.

## Architecture

```
┌─────────────────────────────────────────┐
│  CloudFlare / Route53 DNS               │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
┌──────────────┐      ┌──────────────┐
│  ALB (us-east-1)  │  ALB (us-west-2)
└──────────────┘      └──────────────┘
    │                         │
    ▼                         ▼
┌─────────────────────────────────────┐
│  ECS Cluster (Fargate)              │
│  - 2 tasks × 512 CPU / 1 GB RAM     │
│  - Auto-scaling (2-5 tasks)         │
│  - CloudWatch logging               │
└─────────────────────────────────────┘
    │
    ├─────────────────────────────────┐
    │                                 │
    ▼                                 ▼
┌──────────────────┐      ┌──────────────────┐
│  RDS PostgreSQL  │      │  ElastiCache     │
│  - db.t4g.medium │      │  - cache.t4g     │
│  - 100 GB storage│      │  - 2 nodes Redis │
│  - Multi-AZ      │      │  - Auto-failover │
│  - Backup 30d    │      │  - Encryption    │
└──────────────────┘      └──────────────────┘
```

## Prerequisites

### Install Tools
```bash
# macOS
brew install terraform aws-cli

# Linux
sudo apt-get install terraform awscli

# Verify
terraform version
aws --version
```

### AWS Setup
```bash
# 1. Create AWS account and IAM user
# 2. Configure AWS credentials
aws configure

# 3. Verify access
aws sts get-caller-identity
```

### Create terraform.tfvars
```bash
cat > terraform.tfvars << 'VARS'
environment = "staging"
aws_region  = "us-east-1"

# RDS Configuration
rds_instance_class    = "db.t4g.small"  # Change to db.t4g.large for production
rds_allocated_storage = 100              # 100 GB
rds_backup_retention  = 30              # 30 days
rds_multi_az          = true            # High availability
rds_username          = "admin"
rds_password          = "YOUR_STRONG_PASSWORD_HERE"

# Redis Configuration
redis_node_type = "cache.t4g.micro"  # cache.t4g.small for production
redis_num_nodes = 2                  # 2 nodes for failover

# ECS Configuration
container_image      = "ghcr.io/yourusername/blackroad:latest"
ecs_desired_count    = 2               # Start with 2 tasks
ecs_task_cpu         = 512             # 0.5 CPU
ecs_task_memory      = 1024            # 1 GB RAM

# Logging
log_level = "INFO"
VARS
```

⚠️ **Security Warning:** Never commit terraform.tfvars to Git!

```bash
echo "terraform.tfvars" >> .gitignore
```

## Deployment

### Initialize Terraform
```bash
terraform init
```

Creates `.terraform/` directory and downloads AWS provider.

### Preview Changes
```bash
terraform plan
```

Shows all resources that will be created. **Always review before apply!**

Example output:
```
Terraform will perform the following actions:

  # module.networking.aws_vpc.main will be created
  + resource "aws_vpc" "main" {
      + cidr_block = "10.0.0.0/16"
      + id         = (known after apply)
      ...
    }

Plan: 47 to add, 0 to change, 0 to destroy.
```

### Apply Configuration
```bash
terraform apply
```

Creates all AWS resources.

**First time takes ~15 minutes:**
- VPC, subnets, security groups (2 min)
- RDS instance (5-8 min)
- ElastiCache cluster (5 min)
- ECS cluster and services (3 min)

### Verify Deployment
```bash
# Get outputs
terraform output

# Example output:
# alb_dns_name = "blackroad-alb-123456.us-east-1.elb.amazonaws.com"
# rds_endpoint = "blackroad-db.c123456789.us-east-1.rds.amazonaws.com:5432"
# redis_endpoint = "blackroad-redis.abc123.ng.0001.use1.cache.amazonaws.com:6379"
```

### Test Connectivity
```bash
# Get ALB DNS name
ALB_DNS=$(terraform output -raw alb_dns_name)

# Health check
curl http://$ALB_DNS/health
```

## Scaling

### Change Task Count
```bash
# Edit terraform.tfvars
ecs_desired_count = 5  # Scale to 5 tasks

# Apply
terraform apply
```

### Change RDS Size
```bash
# Change instance class for production
rds_instance_class = "db.t4g.large"  # From medium to large

# RDS auto-scales storage (starts at 100 GB, grows automatically)

terraform apply
```

### Change Redis Size
```bash
redis_node_type = "cache.t4g.small"  # Larger nodes
redis_num_nodes = 3                  # More nodes

terraform apply
```

## Monitoring

### RDS Performance
```bash
# SSH to RDS bastion (jump box) or use AWS RDS Proxy
psql -h $(terraform output -raw rds_endpoint) -U admin

# Inside psql
SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;
```

### Redis Memory
```bash
# From ECS task or bastion
redis-cli -h $(terraform output -raw redis_endpoint) info memory
```

### CloudWatch Logs
```bash
# View API logs
aws logs tail /ecs/blackroad --follow

# View errors only
aws logs tail /ecs/blackroad --filter-pattern "ERROR" --follow
```

## Maintenance

### Backup Database
```bash
# Manual backup (AWS does automatic backups based on backup_retention_period)
aws rds create-db-snapshot \
  --db-instance-identifier blackroad \
  --db-snapshot-identifier blackroad-backup-$(date +%Y%m%d)
```

### Update Container Image
```bash
# Update image in terraform.tfvars
container_image = "ghcr.io/yourusername/blackroad:v1.1.0"

# Apply
terraform apply
```

ECS automatically redeploys tasks with new image.

### Destroy Environment (Careful!)
```bash
# First, backup database
aws rds create-db-snapshot --db-instance-identifier blackroad

# Then destroy
terraform destroy

# Requires confirmation
```

⚠️ **Warning:** Destroy deletes everything including databases!

## Cost Estimation

### Monthly Costs (Staging)
- **ECS Fargate:** 2 tasks × 512 CPU × $0.04560/hour ≈ $67/month
- **RDS db.t4g.small:** $0.081/hour ≈ $59/month
- **ElastiCache cache.t4g.micro:** 2 nodes × $0.017/hour ≈ $25/month
- **Data Transfer:** ~$10-20/month
- **Backups/Snapshots:** ~$5/month

**Total: ~$166/month staging**

### Monthly Costs (Production)
- **ECS Fargate:** 5 tasks × 512 CPU × $0.04560/hour ≈ $167/month
- **RDS db.t4g.large:** $0.25/hour ≈ $183/month
- **ElastiCache cache.t4g.small:** 3 nodes × $0.051/hour ≈ $112/month
- **Data Transfer (cross-AZ):** ~$30-50/month
- **Backups:** ~$20/month

**Total: ~$512/month production**

To reduce costs:
- Use Reserved Instances (save 30-40%)
- Use Savings Plans (save 20-30%)
- Auto-scale down at night (dev/staging)

## State Management

### Local State (Development)
```bash
# terraform.tfstate is created in your directory
# ⚠️ Never commit to Git!
```

### Remote State (Production)
Create S3 + DynamoDB for remote state (recommended for teams):

```bash
# 1. Create S3 bucket and DynamoDB table
aws s3api create-bucket --bucket blackroad-terraform-state --region us-east-1
aws s3api put-bucket-versioning --bucket blackroad-terraform-state --versioning-configuration Status=Enabled

aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# 2. Uncomment backend block in main.tf
# 3. Re-initialize Terraform
terraform init
```

## Troubleshooting

### "terraform: command not found"
```bash
# Install Terraform
brew install terraform  # macOS

# Or download from: https://www.terraform.io/downloads
```

### "Error: AWS credentials not found"
```bash
# Configure AWS credentials
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
```

### "Error: RDS instance creation timeout"
RDS sometimes takes >15 minutes. Wait or:
```bash
# Check status
aws rds describe-db-instances --query 'DBInstances[0].DBInstanceStatus'

# If stuck, re-apply
terraform apply
```

### "Application can't connect to RDS"
```bash
# Check security group rules
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Check RDS endpoint
terraform output rds_endpoint

# Test from ECS task
aws ecs execute-command \
  --cluster blackroad \
  --task <task-id> \
  --command "/bin/sh" \
  --interactive

# Inside container
psql -h <rds-endpoint> -U admin
```

## Next Steps

1. **Deploy to Staging**
   ```bash
   terraform apply  # Creates staging environment
   ```

2. **Test with Load Tests**
   ```bash
   k6 run --vus 1000 \
     -e BASE_URL=http://$(terraform output -raw alb_dns_name) \
     load-test.js
   ```

3. **Monitor Performance**
   ```bash
   aws logs tail /ecs/blackroad --follow
   ```

4. **Deploy to Production**
   - Change `environment = "prod"` in terraform.tfvars
   - Change `rds_instance_class = "db.t4g.large"`
   - Change `ecs_desired_count = 5`
   - Run `terraform apply`

5. **Set Up DNS**
   - Point your domain to ALB DNS name (Route53 or CloudFlare)

## References

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [AWS RDS Documentation](https://docs.aws.amazon.com/rds/)
- [AWS ElastiCache Documentation](https://docs.aws.amazon.com/elasticache/)

## Support

For issues:
1. Check `terraform plan` output
2. Review AWS CloudTrail logs
3. Check CloudWatch logs: `aws logs tail /ecs/blackroad`
4. Review Terraform state: `terraform state list`
