# 🚨 SCENARIO 1: PostgreSQL CORRUPTION OR FAILURE
# Recovery Time: < 5 minutes

## SYMPTOMS
- Database connection errors in logs
- Query timeouts
- High error rate in API responses
- Health checks failing for database connections

## AUTOMATED RECOVERY (Recommended)

```bash
# Use PITR (Point-in-Time Recovery) to 1 hour ago
./disaster-recovery.sh recover-database --pitr-age=1h

# Verify recovery
./disaster-recovery.sh health

# Check business data
docker exec postgres psql -U postgres -d roaddb -c "SELECT COUNT(*) FROM customers;"
```

## MANUAL RECOVERY (if automated fails)

### Step 1: Assess Damage (2 minutes)
```bash
# Check if database is responding
docker exec postgres pg_isready

# Check database size
docker exec postgres psql -U postgres -d roaddb -c "SELECT pg_size_pretty(pg_database_size('roaddb'));"

# Check for table corruption
docker exec postgres psql -U postgres -d roaddb -c "CHECK;"
```

### Step 2: Determine Recovery Point (1 minute)
```bash
# List available backups
./disaster-recovery.sh list-restore-points

# Find latest backup before issue
ls -lht /backups/postgres/full/ | head -5
```

### Step 3: Stop Services (1 minute)
```bash
# Stop all services to prevent write conflicts
docker-compose -f docker-compose.prod.yml stop

# Verify PostgreSQL is stopped
docker ps | grep postgres
```

### Step 4: Restore Database (2 minutes)
```bash
# Decrypt and restore from latest backup
./disaster-recovery.sh recover-database

# This will:
# 1. Decrypt the backup file
# 2. Drop corrupted database
# 3. Restore from backup
# 4. Verify integrity
```

### Step 5: Restart Services (1 minute)
```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to start
sleep 10

# Verify health
./disaster-recovery.sh health
```

### Step 6: Verify Data Integrity (1 minute)
```bash
# Run integrity checks
docker exec postgres psql -U postgres -d roaddb -c "ANALYZE;"

# Check critical tables
docker exec postgres psql -U postgres -d roaddb << 'SQL'
SELECT 
  COUNT(*) as total_records,
  MIN(created_at) as oldest_record,
  MAX(created_at) as newest_record
FROM customers;
SQL

# Verify application health
curl http://localhost:8000/health
```

## INCIDENT RESPONSE

### Notify Team
- Send notification to #incidents Slack channel
- Document: Issue time, symptoms, recovery time
- Tag: @database-team

### Root Cause Analysis (within 24 hours)
```bash
# Check PostgreSQL logs
docker logs postgres | tail -100

# Check for disk space issues
df -h

# Check for memory pressure
docker stats postgres

# Review backup logs
tail -50 logs/backup.log
```

### Post-Recovery Checklist
- [ ] All services passing health checks
- [ ] Customer impact: < 5 minutes downtime
- [ ] Data loss: < 1 hour
- [ ] Backup status: Running normally
- [ ] Monitoring alerts: Cleared
- [ ] Incident document: Created
- [ ] Team meeting: Scheduled for next day
- [ ] Automation improvements: Discussed

## PREVENTION FOR NEXT TIME

1. **Increase backup frequency**: Move from daily to every 6 hours
2. **Enable continuous WAL archiving**: Zero RPO
3. **Add replication**: Warm standby database
4. **Monitor disk space**: Alert at 80% utilization
5. **Test restore monthly**: Catch issues early

---

**Runbook Last Updated**: 2026-05-04  
**Recovery Procedure**: Documented ✓  
**Team Training**: Required  
**Contact**: infrastructure-team@example.com
