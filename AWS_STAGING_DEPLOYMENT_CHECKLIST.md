# AWS Staging Deployment Checklist

Complete pre-deployment verification before deploying to AWS staging.

## Pre-Deployment (Day 1)

### AWS Account Setup
- [ ] AWS account created
- [ ] Billing enabled
- [ ] Root account MFA configured
- [ ] IAM user created with admin access
- [ ] AWS CLI v2 installed and configured
- [ ] Credentials verified (`aws sts get-caller-identity`)

### Local Prerequisites
- [ ] Terraform v1.0+ installed
- [ ] Docker installed and running
- [ ] kubectl installed (optional)
- [ ] git configured with SSH keys
- [ ] Python 3.9+ available

### Repository Preparation
- [ ] Repository cloned locally
- [ ] `.git/config` has correct remote
- [ ] All commits pushed to main branch
- [ ] No uncommitted changes (`git status`)
- [ ] Latest code pulled (`git pull`)

### Infrastructure Planning
- [ ] AWS region selected (default: us-east-1)
- [ ] Cost estimate reviewed
- [ ] Resource sizing approved
  - [ ] EC2 instance type: t3.medium (staging)
  - [ ] RDS instance: db.t3.small
  - [ ] Redis node type: cache.t3.small
- [ ] Backup strategy planned
- [ ] Disaster recovery procedure documented

---

## AWS Service Setup (Day 1)

### S3 for Terraform State
- [ ] S3 bucket created
- [ ] Versioning enabled
- [ ] Server-side encryption enabled
- [ ] DynamoDB table created for state locking
- [ ] Bucket policy reviewed for access control
- [ ] Bucket name noted: `s3://blackroad-terraform-state-xxx`

### Secrets Manager
- [ ] RDS password created and stored
- [ ] Stripe API keys (TEST MODE) stored
- [ ] Clerk API keys stored
- [ ] Admin token generated and stored
- [ ] All secrets properly tagged with `Environment: staging`

### Parameter Store
- [ ] Database credentials stored as SecureString
- [ ] All API keys stored as SecureString
- [ ] Configuration values stored as String
- [ ] Parameters organized with `/blackroad/staging/` prefix

### IAM Roles & Policies
- [ ] ECS task execution role created
- [ ] ECS task role created
- [ ] Terraform IAM user created with appropriate permissions
- [ ] EC2 instance role created
- [ ] Cross-account access configured (if applicable)

### Networking
- [ ] VPC planning completed
- [ ] Subnet strategy finalized (public/private)
- [ ] Route 53 hosted zone verified
- [ ] DNS records ready for staging domain

---

## Infrastructure Deployment (Day 2)

### Terraform Setup
- [ ] `backend-staging.tf` created with correct bucket/key
- [ ] `environments/staging.tfvars` reviewed
- [ ] `environments/staging-override.tfvars` created
- [ ] All variable values verified
- [ ] `terraform init` completed successfully
- [ ] `terraform plan` output reviewed (no errors)
- [ ] Resource count matches expectations

### Infrastructure Deployment
- [ ] `terraform apply` executed successfully
- [ ] All resources created (verify in AWS Console)
- [ ] VPC created with correct CIDR
- [ ] Subnets created in 2 AZs
- [ ] Internet Gateway attached
- [ ] NAT Gateway created
- [ ] RDS instance created (check status: "available")
- [ ] ElastiCache Redis created (check status: "available")
- [ ] ECS cluster created
- [ ] Application Load Balancer created and healthy
- [ ] CloudWatch log groups created

### Terraform Outputs Saved
- [ ] Load balancer DNS name captured
- [ ] RDS endpoint captured
- [ ] Redis endpoint captured
- [ ] ECR repository URLs captured
- [ ] Output file saved: `staging-outputs.json`

---

## Docker Build & Registry (Day 2)

### ECR Repositories
- [ ] 4 repositories created (api, admin, analytics, monitoring)
- [ ] Repositories named correctly
- [ ] Image scan enabled
- [ ] Lifecycle policy configured (retention: 30 days)

### Docker Build
- [ ] Dockerfile created for main API
- [ ] admin_dashboard_dockerfile created
- [ ] customer_analytics_dockerfile created
- [ ] monitoring_dockerfile created
- [ ] All Dockerfiles tested locally (`docker build`)
- [ ] All images run successfully (`docker run`)

### ECR Push
- [ ] ECR login successful (`aws ecr get-login-password...`)
- [ ] API image built, tagged, and pushed
- [ ] Admin image built, tagged, and pushed
- [ ] Analytics image built, tagged, and pushed
- [ ] Monitoring image built, tagged, and pushed
- [ ] All images verified in ECR console
- [ ] Image tags match expected format

---

## Database & Migrations (Day 2-3)

### RDS Access
- [ ] Security group allows inbound on port 5432
- [ ] psql connected successfully to RDS
- [ ] Database `blackroad` created
- [ ] Master user credentials working

### Database Migrations
- [ ] Alembic initialized (if not already)
- [ ] Migration files generated (`alembic revision --autogenerate`)
- [ ] Migrations reviewed for correctness
- [ ] Migrations applied successfully (`alembic upgrade head`)
- [ ] All tables created (verify with `\dt`)

### Data Verification
- [ ] `stripe_customers` table verified
- [ ] `monthly_usage` table verified
- [ ] `user_tiers` table verified
- [ ] `charges` table verified
- [ ] `invoices` table verified
- [ ] Indexes created correctly (`\di`)
- [ ] Test data inserted (optional, for testing)

---

## ECS Deployment (Day 3)

### Task Definitions
- [ ] API task definition created
- [ ] Admin task definition created
- [ ] Analytics task definition created
- [ ] Monitoring task definition created
- [ ] All task definitions reference correct ECR images
- [ ] Environment variables configured
- [ ] Secrets referenced correctly
- [ ] Log configuration set to CloudWatch

### ECS Services
- [ ] API service created with desired count = 2
- [ ] Admin service created with desired count = 2
- [ ] Analytics service created with desired count = 2
- [ ] All services configured with health checks
- [ ] Services attached to correct target groups
- [ ] Service discovery enabled (if using Service Connect)
- [ ] Auto-scaling configured (if using Application Auto Scaling)

### Service Health
- [ ] All services in ACTIVE status
- [ ] Running task count = Desired task count
- [ ] Task status shows RUNNING for all tasks
- [ ] CloudWatch logs populated for all services
- [ ] No failed task launches

---

## Load Balancer & DNS (Day 3)

### Load Balancer Configuration
- [ ] ALB created and in "active" state
- [ ] Target groups created for each service
- [ ] Health checks configured with appropriate thresholds
- [ ] Listeners configured on ports 80, 8000, 8001, 8003
- [ ] Security groups allow inbound on ports 80, 443, 8000-8003
- [ ] Outbound rules allow egress to ECS tasks

### Target Group Health
- [ ] All targets in "healthy" state
- [ ] No targets showing "unhealthy"
- [ ] Health check response code: 200
- [ ] Health check path configured correctly
- [ ] Deregistration delay set appropriately

### DNS Configuration
- [ ] Route 53 hosted zone identified
- [ ] CNAME record created for `staging-api.blackroad.com`
- [ ] DNS propagation verified (`nslookup`, `dig`)
- [ ] DNS resolves to ALB DNS name
- [ ] SSL certificate requested (ACM)
- [ ] Certificate validation completed
- [ ] HTTPS listener configured

---

## Secrets & Configuration (Day 3)

### Environment Variables
- [ ] DATABASE_URL set in task definition
- [ ] REDIS_URL set in task definition
- [ ] ENVIRONMENT set to "staging"
- [ ] DEBUG set to false
- [ ] LOG_LEVEL set to INFO
- [ ] All API ports configured correctly

### Secrets Manager
- [ ] STRIPE_SECRET_KEY accessible from task role
- [ ] CLERK_API_KEY accessible from task role
- [ ] ADMIN_TOKEN accessible from task role
- [ ] RDS password accessible from task role
- [ ] All secrets have proper IAM policies attached

### Parameter Store
- [ ] All parameters accessible from ECS tasks
- [ ] Secrets not stored as plain text in task definitions
- [ ] Parameter paths documented
- [ ] Access policies reviewed

---

## Integration Testing (Day 3-4)

### Health Checks
- [ ] `/status` endpoint returns 200
- [ ] Database connectivity verified
- [ ] Redis connectivity verified
- [ ] Stripe connectivity verified (test mode)
- [ ] Clerk connectivity verified

### API Testing
- [ ] POST `/charge` - test charge recorded
- [ ] GET `/usage` - test usage retrieved
- [ ] POST `/billing` - test subscription change
- [ ] GET `/api/admin/revenue/total` - test admin endpoint
- [ ] GET `/api/customers` - test analytics endpoint

### Load Testing
- [ ] k6 test scenario created
- [ ] Load test executed with 100 concurrent users
- [ ] Response times logged
- [ ] No 5xx errors during load test
- [ ] Database performance acceptable under load
- [ ] Monitoring dashboards show expected metrics

### Stripe Integration Testing
- [ ] Test API key verified in use
- [ ] Test webhook received correctly
- [ ] Test payment processed successfully
- [ ] Test meter event recorded
- [ ] Test invoice generated

### Clerk Integration Testing
- [ ] Test API key verified in use
- [ ] Test user created successfully
- [ ] Test authentication flow working
- [ ] Test API key validation working

---

## Monitoring Setup (Day 4)

### CloudWatch Dashboards
- [ ] Executive dashboard created
- [ ] Operational dashboard created
- [ ] All key metrics displayed
- [ ] Auto-refresh configured (30 seconds)
- [ ] Dashboards accessible to team

### CloudWatch Alarms
- [ ] High response time alarm configured (>500ms)
- [ ] High CPU alarm configured (>80%)
- [ ] High memory alarm configured (>80%)
- [ ] High error rate alarm configured (>5%)
- [ ] Database latency alarm configured
- [ ] All alarms have SNS notifications
- [ ] SNS topics created and subscribed to

### CloudWatch Logs
- [ ] Log groups created for all services
- [ ] Log retention set to 7 days (staging)
- [ ] Log streaming working
- [ ] Logs searchable and queryable
- [ ] Error logs easy to identify

### Prometheus/Grafana (Optional)
- [ ] Prometheus deployed and scraping metrics
- [ ] Grafana dashboard configured
- [ ] Alert rules defined
- [ ] Alert evaluation working

---

## Backup & Disaster Recovery (Day 4)

### RDS Backups
- [ ] Automated backups enabled (30-day retention)
- [ ] Backup window set (e.g., 03:00-04:00 UTC)
- [ ] First backup completed successfully
- [ ] Manual backup created and verified
- [ ] Backup can be restored successfully
- [ ] Backup restore time estimated

### Backup Documentation
- [ ] Backup schedule documented
- [ ] Restore procedure documented
- [ ] Recovery time objective (RTO) defined (e.g., 1 hour)
- [ ] Recovery point objective (RPO) defined (e.g., 24 hours)
- [ ] Runbook created for disaster recovery

---

## Performance Baseline (Day 4)

### Metrics Captured
- [ ] API response time baseline (p50, p95, p99)
- [ ] Database query latency baseline
- [ ] Redis cache hit rate
- [ ] Request throughput baseline
- [ ] Error rate baseline

### Load Profile
- [ ] Peak concurrent users estimated
- [ ] Expected daily active users
- [ ] Projected monthly usage
- [ ] Scaling thresholds defined

### Autoscaling Configuration
- [ ] ECS service autoscaling policy created
- [ ] Scale-up threshold defined
- [ ] Scale-down threshold defined
- [ ] Min/max replicas configured
- [ ] Autoscaling tested and working

---

## Security Hardening (Day 4-5)

### Network Security
- [ ] VPC isolation verified
- [ ] Security group rules reviewed (least privilege)
- [ ] Network ACLs reviewed (if used)
- [ ] NACLs deny unnecessary ports
- [ ] VPC Flow Logs enabled

### IAM Security
- [ ] IAM policies reviewed and least privilege
- [ ] Cross-account access restricted
- [ ] Root account not used for daily operations
- [ ] MFA enabled for admin users
- [ ] Access key rotation scheduled

### Secrets Security
- [ ] No secrets in environment variables
- [ ] All secrets encrypted at rest (Secrets Manager)
- [ ] All secrets encrypted in transit (TLS)
- [ ] Secrets rotation policy defined
- [ ] Secrets audit logging enabled

### SSL/TLS
- [ ] HTTPS enforced (redirect HTTP to HTTPS)
- [ ] TLS 1.2+ required
- [ ] Certificate renewal automated
- [ ] Cipher suites hardened
- [ ] SSL Labs rating: A or A+

---

## Documentation (Day 5)

### Runbooks
- [ ] Deployment runbook created
- [ ] Rollback procedure documented
- [ ] Incident response plan created
- [ ] On-call rotation established
- [ ] Escalation contacts documented

### Architecture
- [ ] Architecture diagram created
- [ ] Component relationships documented
- [ ] Data flow documented
- [ ] Deployment topology documented

### Troubleshooting
- [ ] Common issues documented
- [ ] Troubleshooting steps provided
- [ ] Log locations documented
- [ ] Debug procedures provided

---

## Sign-Off & Promotion (Day 5)

### Code Review
- [ ] All code reviewed by team lead
- [ ] Code standards compliance verified
- [ ] Security review completed
- [ ] Performance review completed

### Testing Verification
- [ ] All integration tests passed
- [ ] Load test targets met
- [ ] Security tests passed
- [ ] Reliability targets met

### Stakeholder Sign-Off
- [ ] Architecture approved by tech lead
- [ ] Security approved by security team
- [ ] Operations approved by ops team
- [ ] Product approved by product team

### Release Notes
- [ ] Release notes prepared
- [ ] Known limitations documented
- [ ] Rollback plan documented
- [ ] Customer communications prepared

### Deployment Approval
- [ ] Change request submitted and approved
- [ ] Change window scheduled
- [ ] Deployment team assigned
- [ ] Rollback plan reviewed with team
- [ ] **APPROVED FOR STAGING DEPLOYMENT** ✅

---

## Post-Deployment (Day 6+)

### Monitor First 24 Hours
- [ ] Error rates monitored
- [ ] Response times monitored
- [ ] Resource utilization monitored
- [ ] No incidents reported
- [ ] System stable and performing

### User Acceptance Testing
- [ ] Test users created in staging
- [ ] UAT scenarios executed
- [ ] UAT sign-off obtained
- [ ] Feedback incorporated (if needed)

### Production Readiness
- [ ] Staging deployment stable for 48+ hours
- [ ] All metrics within targets
- [ ] Load testing completed successfully
- [ ] Ready to promote to production

### Knowledge Transfer
- [ ] Team trained on deployment
- [ ] Team trained on monitoring
- [ ] Team trained on troubleshooting
- [ ] Documentation reviewed with team

---

## Status Tracking

| Phase | Date | Status | Notes |
|-------|------|--------|-------|
| AWS Setup | / | [ ] Pending | |
| Infrastructure | / | [ ] Pending | |
| Build & Push | / | [ ] Pending | |
| Database | / | [ ] Pending | |
| ECS Deploy | / | [ ] Pending | |
| Integration Tests | / | [ ] Pending | |
| Monitoring | / | [ ] Pending | |
| Security | / | [ ] Pending | |
| Documentation | / | [ ] Pending | |
| **READY FOR PROD** | / | [ ] Pending | |

---

**Checklist Version:** 1.0  
**Last Updated:** 2024-01-31  
**Next Review:** After first staging deployment
