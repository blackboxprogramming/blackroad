# 🚨 SCENARIO 2: REDIS CACHE FAILURE OR DATA LOSS
# Recovery Time: < 2 minutes

## SYMPTOMS
- Increased API latency
- High memory usage spikes
- Cache miss rate > 80%
- Redis connection errors in logs
- Database queries spike (cache not working)

## AUTOMATED RECOVERY (Recommended)

```bash
# Restore Redis from latest snapshot
./disaster-recovery.sh recover-cache

# Verify recovery (should show cached data)
docker exec redis redis-cli DBSIZE

# Check cache hit rate
docker exec redis redis-cli INFO stats | grep hits
```

## MANUAL RECOVERY (if automated fails)

### Step 1: Assess Situation (30 seconds)
```bash
# Check if Redis is running
docker ps | grep redis

# Get Redis info
docker exec redis redis-cli INFO

# Check memory usage
docker exec redis redis-cli INFO memory
```

### Step 2: Determine Issue Type (30 seconds)

**If Redis is responsive but data is corrupted:**
```bash
# Option A: Restart and reload cache
docker-compose -f docker-compose.prod.yml restart redis

# Redis will reload from RDB file automatically
# Cache will be repopulated from database on next query
```

**If Redis is completely down:**
```bash
# Option B: Restore from backup
./disaster-recovery.sh recover-cache
```

### Step 3: Stop Writing to Redis (immediate)
```bash
# Prevent application from writing stale data during recovery
docker exec redis redis-cli CONFIG SET maxmemory-policy "noeviction"
```

### Step 4: Restore Cache (1-2 minutes)
```bash
# Find latest Redis backup
ls -lht /backups/redis/snapshots/

# Restore the latest backup
./disaster-recovery.sh recover-cache

# This will:
# 1. Stop Redis container
# 2. Replace dump.rdb with backup copy
# 3. Restart Redis
# 4. Verify connection
```

### Step 5: Re-enable Cache Writes (30 seconds)
```bash
# Re-enable normal cache operation
docker exec redis redis-cli CONFIG SET maxmemory-policy "allkeys-lru"

# Flush any stale data (optional)
docker exec redis redis-cli FLUSHDB
```

### Step 6: Warm Up Cache (2-5 minutes)
```bash
# Trigger background cache warming
curl http://localhost:8000/api/cache/warm

# Or manually run cache loading
python tests/seed_data.py
```

### Step 7: Verify Recovery (1 minute)
```bash
# Check Redis is healthy
docker exec redis redis-cli PING

# Verify data is present
docker exec redis redis-cli DBSIZE

# Monitor hit rate
watch -n 1 'docker exec redis redis-cli INFO stats | grep hits'
```

## INCIDENT RESPONSE

### Customer Communication
- **If < 2 min downtime**: No communication needed
- **If 2-5 min downtime**: Send status update
- **If > 5 min downtime**: Notify customers, provide ETA

### Metrics During Recovery
```bash
# Monitor key metrics in Grafana
# - Cache hit rate (should recover to 85%+)
# - API latency (should return to baseline)
# - Database queries (should decrease)
# - Redis memory (should be at capacity)
```

### Root Cause Analysis (within 24 hours)
```bash
# Check Redis logs
docker logs redis | tail -100

# Check if issue was memory related
docker exec redis redis-cli INFO memory | grep used_memory

# Check if issue was connection related
docker exec redis redis-cli INFO stats | grep connections_received

# Review backup logs
tail -50 logs/backup.log | grep redis
```

## PREVENTION FOR NEXT TIME

1. **Enable Redis Replication**: Active-standby setup
2. **Increase Memory Limit**: Reduce eviction frequency
3. **Monitor Hit Rate**: Alert if < 80%
4. **Monitor Memory**: Alert if > 85%
5. **Test Recovery**: Monthly restore tests

## EXPECTED IMPACT

### Data Loss
- **With RDB backup**: < 1 hour
- **With AOF enabled**: < 1 minute
- **With replication**: < 1 second

### Performance Impact
- **During recovery**: Baseline + 2-3x latency
- **After recovery**: Back to baseline immediately
- **Cache warm-up**: 5-10 minutes for full speed

### Business Impact
- **Revenue impact**: < $100 (depends on cache hit rate)
- **Customers affected**: None (graceful degradation)
- **SLA impact**: 2-minute window acceptable

---

**Runbook Last Updated**: 2026-05-04  
**Recovery Procedure**: Tested ✓  
**Team Training**: Scheduled  
**Contact**: infrastructure-team@example.com
