# 🔒 DISASTER RECOVERY IMPLEMENTATION GUIDE
## Step-by-Step Setup for Automated Backups & Recovery

---

## PHASE 1: INITIAL SETUP (10 minutes)

### Step 1.1: Create Backup Directory Structure
```bash
cd /Users/alexa/blackroad

# Create all required directories
mkdir -p /backups/postgres/full
mkdir -p /backups/postgres/incremental
mkdir -p /backups/postgres/wal
mkdir -p /backups/redis/snapshots
mkdir -p /backups/config
mkdir -p /backups/volumes
mkdir -p /backups/metadata
mkdir -p logs

# Set permissions
chmod 700 /backups
chmod 700 /backups/postgres
chmod 700 /backups/redis
chmod 700 /backups/config

echo "✓ Backup directories created"
```

### Step 1.2: Verify Scripts Are Executable
```bash
# Make disaster recovery script executable
chmod +x disaster-recovery.sh

# Test that it runs
./disaster-recovery.sh --help || ./disaster-recovery.sh

# Output should show usage information
```

### Step 1.3: Set Up Environment Variables
```bash
# Create .env file for disaster recovery
cat >> .env << 'EOF'

# ========== DISASTER RECOVERY ==========
BACKUP_DIR=/backups
ENCRYPTION_KEY=changeme123                    # CHANGE THIS!
BACKUP_RETENTION_DAYS=30
POSTGRES_CONTAINER=postgres
REDIS_CONTAINER=redis
DOCKER_NETWORK=blackroad-network
EOF

# Change encryption key to something secure
sed -i '' 's/changeme123/'"$(openssl rand -hex 16)"'/' .env
echo "✓ Environment variables set"
```

---

## PHASE 2: MANUAL BACKUP TESTING (5 minutes)

### Step 2.1: Test PostgreSQL Backup
```bash
# Verify PostgreSQL is running
docker ps | grep postgres

# Create test backup
./disaster-recovery.sh backup-postgres

# Check backup was created
ls -lh /backups/postgres/full/
```

### Step 2.2: Test Redis Backup
```bash
# Verify Redis is running
docker ps | grep redis

# Create test backup
./disaster-recovery.sh backup-redis

# Check backup was created
ls -lh /backups/redis/snapshots/
```

### Step 2.3: Test Configuration Backup
```bash
# Create test backup
./disaster-recovery.sh backup-config

# Check backup was created
ls -lh /backups/config/
```

### Step 2.4: Create Full Backup
```bash
# Create full backup of everything
./disaster-recovery.sh backup-all

# Check all backups
./disaster-recovery.sh status
```

**Expected output:**
```
=== BACKUP STATUS REPORT ===

Backup Directory: /backups
Total Size: 1.2G

PostgreSQL:
  Latest backup: full_2026_05_04.sql.gz.enc
  Backup count: 1

Redis:
  Latest backup: redis_2026_05_04.rdb.gz.enc
  Backup count: 1
```

---

## PHASE 3: VERIFY BACKUP INTEGRITY (2 minutes)

### Step 3.1: Verify Backups
```bash
# Verify all backups using checksums
./disaster-recovery.sh verify

# Expected: "All backups verified ✓"
```

### Step 3.2: List Available Restore Points
```bash
# See what you can restore
./disaster-recovery.sh list-restore-points
```

---

## PHASE 4: RESTORE TESTING (10 minutes)

### Step 4.1: Test Restore Procedure (Non-Destructive)
```bash
# Test restore without actually restoring
# This is a DRY-RUN
./disaster-recovery.sh test-restore

# Expected: "Test restore procedure ready"
```

### Step 4.2: Verify System Health
```bash
# Check all services are healthy
./disaster-recovery.sh health

# Expected output:
# PostgreSQL: OK
# Redis: OK
# [all services]: UP/OK
```

---

## PHASE 5: AUTOMATED SCHEDULING (5 minutes)

### Step 5.1: Install Backup Cron Jobs
```bash
# View the cron schedule
cat disaster-recovery/crontab.conf

# Install cron jobs
crontab disaster-recovery/crontab.conf

# Verify cron jobs installed
crontab -l | grep disaster-recovery
```

**Scheduled tasks:**
- ✅ Daily backup @ 2:00 AM
- ✅ Daily verification @ 3:15 AM
- ✅ Weekly restore test @ 3:00 AM Sunday
- ✅ Monthly cleanup @ 4:00 AM on 1st
- ✅ Daily health checks every 5 minutes

### Step 5.2: Set Up Log Rotation
```bash
# Create logrotate configuration
cat > disaster-recovery/logrotate.conf << 'EOF'
/Users/alexa/blackroad/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0600 alexa staff
}
EOF

# Install logrotate
sudo logrotate -f disaster-recovery/logrotate.conf
```

---

## PHASE 6: CONFIGURE BACKUP STORAGE

### Step 6.1: Local Storage (Recommended for Demo)
```bash
# Use local /backups directory
# Already configured by default

# Monitor disk space
watch -n 5 'du -sh /backups'

# If /backups is low on space, mount external drive
sudo mount /dev/external-drive /backups
```

### Step 6.2: Optional: S3 Backup Replication
```bash
# Install AWS CLI
brew install awscli

# Configure AWS credentials
aws configure

# Create backup bucket
aws s3 mb s3://blackroad-backups-$(date +%s)

# Set up automatic replication
# Add to crontab:
# 0 3 * * * aws s3 sync /backups s3://blackroad-backups/ --sse AES256

# Or use rclone for other providers:
brew install rclone
rclone config  # Configure your storage
```

---

## PHASE 7: MONITORING & ALERTS

### Step 7.1: Update Grafana Dashboard
```bash
# Dashboard is already included:
# monitoring/grafana/provisioning/dashboards/backup-monitoring.json

# Access Grafana
open http://localhost:3000

# Navigate to: Home > Dashboards > Disaster Recovery & Backups
# You should see:
# - Backup storage usage
# - Latest backup status
# - Backup duration trends
# - Verification success rate
# - Available restore points
```

### Step 7.2: Set Up Alerts
```bash
# Update Prometheus alert rules
cat >> monitoring/alert-rules.yml << 'EOF'

  - alert: BackupFailed
    expr: backup_status_latest == 0
    for: 5m
    annotations:
      summary: "Backup failed - last backup > 25 hours old"

  - alert: BackupStorageLow
    expr: backup_storage_available_percent < 20
    for: 10m
    annotations:
      summary: "Backup storage < 20% available"

  - alert: BackupVerificationFailed
    expr: backup_verification_failed > 0
    for: 5m
    annotations:
      summary: "Backup verification failed"
EOF

# Reload Prometheus
docker exec prometheus kill -HUP 1
```

---

## PHASE 8: DOCUMENTATION & RUNBOOKS

### Step 8.1: Review Disaster Recovery Plan
```bash
# Read the complete plan
cat DISASTER_RECOVERY_PLAN.md

# Key sections:
# - Backup architecture (5 scenarios)
# - RTO/RPO targets
# - Recovery procedures
# - Root cause analysis templates
```

### Step 8.2: Review Runbooks
```bash
# Scenario 1: PostgreSQL Corruption
cat disaster-recovery/runbooks/scenario-1-postgres-corruption.md

# Scenario 2: Redis Failure
cat disaster-recovery/runbooks/scenario-2-redis-failure.md

# Scenario 3: Complete Data Center Failure
cat disaster-recovery/runbooks/scenario-3-data-center-failure.md

# Print and post in team area or share in Slack
```

### Step 8.3: Update Team Access
```bash
# Share documentation with team
# 1. Post DISASTER_RECOVERY_PLAN.md to Confluence/Wiki
# 2. Share runbooks folder with on-call team
# 3. Add to Slack: #incidents channel
# 4. Schedule team training (30 minutes)
```

---

## PHASE 9: DISASTER RECOVERY DRILL (30 minutes)

### Step 9.1: Plan the Drill (5 minutes)
```bash
# Schedule drill time (off-peak)
# Notify team 24 hours in advance
# Document what will be tested
```

### Step 9.2: Run the Drill (20 minutes)
```bash
# Scenario: "PostgreSQL database corrupted at 2PM"

# 1. Verify current data (1 min)
docker exec postgres psql -U postgres -d roaddb -c \
  "SELECT COUNT(*) FROM customers WHERE id > 0;"

# 2. Simulate corruption (simulate with stop, don't actually corrupt)
# docker-compose stop postgres

# 3. Run automated recovery (3 min)
# ./disaster-recovery.sh recover-database

# 4. Verify recovery (2 min)
# ./disaster-recovery.sh health

# 5. Verify data integrity (1 min)
# docker exec postgres psql -U postgres -d roaddb -c \
#   "SELECT COUNT(*) FROM customers WHERE id > 0;"

# 6. Run test suite (1 min)
# ./tests/run_tests.sh
```

### Step 9.3: Debrief (5 minutes)
```bash
# What went well?
# What could be improved?
# Update runbooks if needed
# Schedule next drill (monthly)
```

---

## PHASE 10: OPERATIONAL PROCEDURES

### Weekly Tasks

```bash
# Every Monday at 9 AM
./disaster-recovery.sh status

# Review:
# - Backups completed successfully (yes/no)
# - Storage space available (>20% free)
# - Last 7 days of backups present
# - No verification failures
```

### Monthly Tasks

```bash
# First business day of month
# 1. Full restore test (45 minutes)
#    ./disaster-recovery.sh test-restore

# 2. Review disaster recovery plan
#    - Update RTO/RPO targets?
#    - Add new scenarios?
#    - Update team contacts?

# 3. Run disaster recovery drill
#    - Simulate different failure scenario
#    - Time the recovery
#    - Document lessons learned

# 4. Update documentation
#    - Commit changes to git
#    - Share with team
```

### Quarterly Tasks

```bash
# Once per quarter (every 90 days)
# 1. End-to-end recovery test
#    - Test restore to new infrastructure
#    - Verify data consistency
#    - Performance check

# 2. Backup security audit
#    - Review encryption keys
#    - Check access controls
#    - Verify encryption in transit

# 3. Update recovery procedures
#    - Any new services to backup?
#    - Any changes to infrastructure?
#    - Any lessons from past incidents?

# 4. Team training update
#    - Onboard new team members
#    - Refresh training for veterans
#    - Practice recovery procedures
```

---

## PHASE 11: TROUBLESHOOTING

### Issue: "docker: command not found"
```bash
# Make sure Docker is installed and running
docker --version
docker-compose --version

# Start Docker if stopped
open -a Docker   # macOS
```

### Issue: "Permission denied" on scripts
```bash
# Make scripts executable
chmod +x disaster-recovery.sh
chmod +x blackroad-cli.sh
```

### Issue: "No backup found"
```bash
# Create a backup first
./disaster-recovery.sh backup-all

# Or check backup directory exists
ls -la /backups/
```

### Issue: "Database connection refused"
```bash
# Make sure PostgreSQL is running
docker ps | grep postgres

# If not running, start it
docker-compose -f docker-compose.prod.yml up -d postgres
```

### Issue: "Out of disk space"
```bash
# Check disk usage
du -sh /backups

# Delete old backups
./disaster-recovery.sh cleanup

# Or cleanup system
docker system prune -f
```

---

## QUICK REFERENCE COMMANDS

### Daily Operations
```bash
# Check backup status
./disaster-recovery.sh status

# Verify system health
./disaster-recovery.sh health

# List available restore points
./disaster-recovery.sh list-restore-points
```

### Emergency Recovery
```bash
# Restore PostgreSQL only
./disaster-recovery.sh recover-database

# Restore Redis only
./disaster-recovery.sh recover-cache

# Full system recovery
./disaster-recovery.sh full-recovery
```

### Management
```bash
# Create full backup now
./disaster-recovery.sh backup-all

# Verify backup integrity
./disaster-recovery.sh verify

# Clean up old backups
./disaster-recovery.sh cleanup

# Test restore (non-destructive)
./disaster-recovery.sh test-restore
```

---

## SUPPORT & ESCALATION

### Level 1 Support (Try automated recovery)
```bash
./disaster-recovery.sh full-recovery
./disaster-recovery.sh health
```

### Level 2 Support (Manual recovery from runbook)
```bash
# Follow scenario runbooks in:
# disaster-recovery/runbooks/

# Example:
cat disaster-recovery/runbooks/scenario-1-postgres-corruption.md
```

### Level 3 Support (Contact team)
```
Email: infrastructure-team@example.com
Slack: #infrastructure or @database-team
Phone: On-call rotation (see wiki)
```

---

## NEXT STEPS

- [ ] Complete Phases 1-7 (setup takes ~30 minutes)
- [ ] Run initial full backup (Phase 2)
- [ ] Set up cron jobs (Phase 5)
- [ ] Schedule team training (Phase 8)
- [ ] Run first disaster recovery drill (Phase 9)
- [ ] Add to production monitoring

---

**Implementation Guide Last Updated**: 2026-05-04  
**Status**: ✅ Ready to deploy  
**Estimated Setup Time**: 1-2 hours (including team training)  
**Support**: infrastructure-team@example.com
