# 🚨 SCENARIO 3: COMPLETE DATA CENTER FAILURE
# Recovery Time: < 15 minutes (to new infrastructure)

## SYMPTOMS
- All services unreachable
- No response to health checks
- All monitoring alerts firing
- Cannot SSH to servers
- All containers down

## AUTOMATED FULL RECOVERY

```bash
# Complete system recovery to new infrastructure
./disaster-recovery.sh full-recovery

# This will:
# 1. Verify Docker environment
# 2. Deploy all services from images
# 3. Restore PostgreSQL database
# 4. Restore Redis cache
# 5. Verify all services are healthy
```

**Total time: < 15 minutes**

## MANUAL FULL RECOVERY (if automated fails)

### Phase 1: Environment Setup (5 minutes)

#### Step 1.1: Prepare New Infrastructure
```bash
# On new server/VM with Docker installed
git clone https://github.com/blackboxprogramming/blackroad.git
cd blackroad

# Set environment variables
export BACKUP_LOCATION="s3://backups/latest"  # or local path
export ENCRYPTION_KEY="<your-encryption-key>"
```

#### Step 1.2: Download Latest Backups
```bash
# If using S3 (AWS S3 or MinIO)
aws s3 cp s3://backups/latest /backups --recursive

# If using local backup drive
cp /mnt/backup-drive/backups /backups -r

# Verify backups
ls -lah /backups/postgres/full/
ls -lah /backups/redis/snapshots/
```

#### Step 1.3: Verify Infrastructure
```bash
# Ensure Docker is running
docker --version
docker-compose --version

# Ensure network connectivity
ping 8.8.8.8
```

### Phase 2: Database Recovery (7 minutes)

#### Step 2.1: Start Infrastructure Services
```bash
# Start only database and monitoring services first
docker-compose -f docker-compose.prod.yml up -d postgres redis prometheus

# Wait for services to be ready
sleep 30

# Verify they're running
docker-compose -f docker-compose.prod.yml ps
```

#### Step 2.2: Restore PostgreSQL
```bash
# Check latest backup
ls -lt /backups/postgres/full/ | head -1

# Restore database (encrypted backup)
./disaster-recovery.sh recover-database

# Verify restoration
docker exec postgres psql -U postgres -d roaddb -c "SELECT COUNT(*) FROM customers;"
```

#### Step 2.3: Restore Redis
```bash
# Check latest Redis backup
ls -lt /backups/redis/snapshots/ | head -1

# Restore cache (encrypted backup)
./disaster-recovery.sh recover-cache

# Verify restoration
docker exec redis redis-cli DBSIZE
```

### Phase 3: Application Deployment (3 minutes)

#### Step 3.1: Start All Application Services
```bash
# Start all remaining services
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to start
sleep 30

# Check service status
docker-compose -f docker-compose.prod.yml ps
```

#### Step 3.2: Restore Configuration
```bash
# Configuration was backed up; restore if needed
if [ -f /backups/config/config_*.tar.gz ]; then
    tar -xzf /backups/config/config_*.tar.gz
fi
```

### Phase 4: Verification & Health Check (2 minutes)

#### Step 4.1: Verify All Services
```bash
# Run comprehensive health check
./disaster-recovery.sh health

# Expected output:
# PostgreSQL: OK
# Redis: OK
# api-gateway: UP
# billing-service: UP
# [etc for all services]
```

#### Step 4.2: Smoke Tests
```bash
# Test critical endpoints
curl -s http://localhost:8000/health | jq .

# Test API functionality
curl -s http://localhost:8000/api/customers | jq .

# Check metrics collection
curl -s http://localhost:9090/api/v1/targets | jq .
```

#### Step 4.3: Verify Data Integrity
```bash
# Spot-check critical data
docker exec postgres psql -U postgres -d roaddb << 'SQL'
SELECT 
  (SELECT COUNT(*) FROM customers) as customers,
  (SELECT COUNT(*) FROM subscriptions) as subscriptions,
  (SELECT COUNT(*) FROM transactions) as transactions,
  (SELECT COUNT(*) FROM metrics) as metrics;
SQL
```

### Phase 5: Recovery Confirmation (1 minute)

```bash
# Display recovery summary
echo "=== RECOVERY COMPLETE ==="
echo "Time to recovery: $(date -d '...' +%s)s"
echo "Data loss: < 1 hour"
echo "Services operational: $(docker-compose ps --services | wc -l)"
./disaster-recovery.sh status
```

## DEPLOYMENT TO NEW INFRASTRUCTURE

### AWS EC2 Deployment

```bash
# 1. Create new EC2 instance
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.large \
  --key-name my-key

# 2. SSH to instance and clone repo
ssh -i my-key.pem ec2-user@<instance-ip>
git clone https://github.com/blackboxprogramming/blackroad.git

# 3. Run recovery
./disaster-recovery.sh full-recovery
```

### Docker Swarm Deployment

```bash
# 1. Initialize swarm on new leader
docker swarm init

# 2. Deploy stack with backups
docker stack deploy -c docker-compose.prod.yml blackroad

# 3. Restore databases
./disaster-recovery.sh recover-database
./disaster-recovery.sh recover-cache
```

### Kubernetes Deployment

```bash
# 1. Create namespace
kubectl create namespace blackroad

# 2. Create secrets for backups
kubectl create secret generic backup-keys \
  --from-literal=encryption-key=$ENCRYPTION_KEY \
  -n blackroad

# 3. Deploy services
kubectl apply -f k8s/ -n blackroad

# 4. Restore data
./disaster-recovery.sh recover-database
./disaster-recovery.sh recover-cache
```

## DNS & TRAFFIC SWITCHING

### Update DNS (for users)
```bash
# Point domain to new infrastructure
# Add A record: blackroad.example.com -> <new-ip>
# TTL: 60 seconds (for quick failover)

# Via AWS Route53:
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890 \
  --change-batch file://update.json
```

### Update Load Balancer
```bash
# If using external load balancer, update target:
aws elbv2 register-targets \
  --target-group-arn arn:aws:elasticloadbalancing:... \
  --targets Id=<new-instance-id>
```

## POST-RECOVERY TASKS

### Immediate (within 1 hour)
- [ ] Verify all data in new environment
- [ ] Test critical business workflows
- [ ] Check monitoring dashboards
- [ ] Monitor error rates

### Short-term (within 24 hours)
- [ ] Run comprehensive test suite
- [ ] Performance testing vs baseline
- [ ] Customer communication
- [ ] Incident postmortem

### Medium-term (within 1 week)
- [ ] Root cause analysis
- [ ] Update runbooks
- [ ] Team training
- [ ] Process improvements

## EXPECTED METRICS

| Metric | Target | Achieved |
|--------|--------|----------|
| Time to restore DB | < 10 min | |
| Time to restore Cache | < 2 min | |
| Data loss | < 1 hour | |
| RTO total | < 15 min | |
| RPO (normal ops) | < 1 hour | |
| Services healthy | 100% | |

---

**Runbook Last Updated**: 2026-05-04  
**Recovery Procedure**: Documented ✓  
**Team Training**: In progress  
**Last Test**: 2026-05-04  
**Contact**: infrastructure-team@example.com
