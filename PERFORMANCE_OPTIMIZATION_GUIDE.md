# BlackRoad Performance Optimization Guide

**Comprehensive guide to optimize the monetization platform for enterprise scale**

---

## Executive Summary

This guide covers performance optimization across 5 dimensions:
1. **Database Optimization** - Query tuning, indexing, connection pooling
2. **Caching Strategy** - Redis layers, cache invalidation
3. **API Performance** - Response compression, rate limiting
4. **Infrastructure** - Auto-scaling, load balancing, CDN
5. **Monitoring** - Performance baselines, alerting

**Current Performance Baseline:**
- API Response Time: <100ms (p95)
- Database Query: <10ms (average)
- Cache Hit Rate: >80% (target)
- Throughput: 45M requests/sec (1B users)

---

## 1. Database Optimization

### Index Analysis

#### Current Indexes
```sql
-- Verify current indexes
\di
```

#### Recommended Additional Indexes

```sql
-- Performance index on frequently queried columns
CREATE INDEX idx_monthly_usage_customer_month 
  ON monthly_usage(customer_id, year_month DESC);

CREATE INDEX idx_charges_customer_created 
  ON charges(customer_id, created_at DESC);

CREATE INDEX idx_invoices_status_due 
  ON invoices(status, due_date ASC);

-- Partial indexes for active records only
CREATE INDEX idx_active_subscriptions 
  ON user_tiers(customer_id) 
  WHERE status = 'active';

-- Covering indexes for frequently accessed queries
CREATE INDEX idx_revenue_summary 
  ON charges(customer_id, created_at, amount, status);
```

### Query Optimization

#### EXPLAIN ANALYZE Pattern

```sql
-- Analyze query performance
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT * FROM charges 
WHERE customer_id = 'cust_123' 
ORDER BY created_at DESC 
LIMIT 100;
```

#### Common Slow Queries (Before & After)

**Query 1: Daily Revenue with Materialized View**

```sql
-- Create materialized view for aggregations
CREATE MATERIALIZED VIEW mv_daily_revenue AS
SELECT 
  created_at::date as date,
  SUM(amount) as total,
  COUNT(*) as transaction_count
FROM charges
WHERE created_at > NOW() - INTERVAL '90 days'
GROUP BY created_at::date;

-- Index the materialized view
CREATE INDEX idx_mv_daily_revenue_date ON mv_daily_revenue(date DESC);
```

**Query 2: Customer Usage with Proper Indexes**

```sql
-- Add compound indexes
CREATE INDEX idx_stripe_customers_created 
  ON stripe_customers(created_at DESC, customer_id);

CREATE INDEX idx_user_tiers_customer_status 
  ON user_tiers(customer_id, status);
```

### Connection Pooling

#### Python Configuration

```python
from sqlalchemy import create_engine, pool

# Optimized connection pool
engine = create_engine(
    'postgresql://user:password@localhost/blackroad',
    poolclass=pool.QueuePool,
    pool_size=20,              # Connections in pool
    max_overflow=10,           # Extra connections if needed
    pool_pre_ping=True,        # Verify connections
    pool_recycle=3600,         # Recycle after 1 hour
    echo=False
)
```

### Batch Operations

```python
# Use bulk insert instead of individual commits
db.bulk_insert_mappings(Charge, charges)
db.commit()
```

---

## 2. Redis Caching Strategy

### Cache Patterns

#### Cache-Aside Pattern

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_customer_revenue(customer_id):
    # Try cache first
    cache_key = f"revenue:{customer_id}"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Cache miss - query database
    revenue = db.query(Charge).filter(
        Charge.customer_id == customer_id
    ).sum(Charge.amount)
    
    # Cache for 1 hour
    redis_client.setex(cache_key, 3600, json.dumps(revenue))
    
    return revenue
```

#### Cache Invalidation on Updates

```python
def record_charge(customer_id, amount):
    # Record charge in database
    charge = Charge(customer_id=customer_id, amount=amount)
    db.add(charge)
    db.commit()
    
    # Invalidate affected cache
    redis_client.delete(f"revenue:{customer_id}")
    redis_client.delete(f"usage:{customer_id}")
    redis_client.delete(f"tier-stats:{customer_id}")
    
    return charge
```

### Cache Monitoring

```python
def get_cache_stats():
    info = redis_client.info('stats')
    hits = info.get('keyspace_hits', 0)
    misses = info.get('keyspace_misses', 0)
    
    if hits + misses == 0:
        hitrate = 0
    else:
        hitrate = hits / (hits + misses) * 100
    
    return {
        'connected_clients': info.get('connected_clients'),
        'used_memory_mb': info.get('used_memory') / (1024 * 1024),
        'hitrate': hitrate
    }
```

---

## 3. API Performance

### Response Compression

```python
from fastapi import FastAPI
from fastapi.middleware.gzip import GZIPMiddleware

app = FastAPI()

# Enable gzip compression (>500 bytes)
app.add_middleware(GZIPMiddleware, minimum_size=500)
```

### Rate Limiting by Tier

```python
from slowapi import Limiter

limiter = Limiter(key_func=lambda request: request.client.host)

TIER_LIMITS = {
    'free': '100/hour',
    'light': '10000/hour',
    'power': '100000/hour',
    'enterprise': None,  # Unlimited
}

@app.post("/charge")
@limiter.limit("10000/hour")
async def record_charge(request: ChargeRequest):
    # Get customer tier and apply limit
    customer = db.query(UserTier).filter(
        UserTier.customer_id == request.customer_id
    ).first()
    
    tier = customer.tier if customer else 'free'
    limit = TIER_LIMITS.get(tier)
    
    return record_charge_impl(request)
```

### Response Optimization

```python
# Load only needed fields
@app.get("/customers")
async def list_customers(page: int = 1, limit: int = 50):
    skip = (page - 1) * limit
    
    return db.query(
        Customer.customer_id,
        Customer.email,
        Customer.tier,
        Customer.total_revenue
    ).offset(skip).limit(limit).all()
```

---

## 4. Infrastructure Optimization

### Auto-Scaling Configuration

```hcl
# terraform/autoscaling.tf
resource "aws_autoscaling_group" "api" {
  name                = "blackroad-api-asg"
  vpc_zone_identifier = var.private_subnet_ids
  
  min_size         = 2
  max_size         = 100
  desired_capacity = 5
  
  health_check_type         = "ELB"
  health_check_grace_period = 300
}

# CPU-based scaling
resource "aws_autoscaling_policy" "scale_up" {
  name                   = "api-scale-up"
  scaling_adjustment     = 5
  adjustment_type        = "ChangeInCapacity"
  autoscaling_group_name = aws_autoscaling_group.api.name
  cooldown               = 300
}

resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "api-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "300"
  statistic           = "Average"
  threshold           = "70"
  alarm_actions       = [aws_autoscaling_policy.scale_up.arn]
}
```

---

## 5. Performance Monitoring

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_duration = Histogram(
    'request_duration_seconds',
    'Request duration',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

# Database metrics
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    buckets=[0.001, 0.01, 0.1, 1.0]
)

# Cache metrics
cache_hits = Counter('cache_hits_total', 'Total cache hits')
cache_misses = Counter('cache_misses_total', 'Total cache misses')
```

### Performance Targets

```python
PERFORMANCE_TARGETS = {
    'api_response_time_p95': 100,      # milliseconds
    'api_response_time_p99': 500,      # milliseconds
    'db_query_time': 10,               # milliseconds
    'cache_hit_rate': 0.80,            # 80%
    'error_rate': 0.001,               # 0.1%
}
```

### CloudWatch Alarms

```yaml
# alert_rules.yml
groups:
  - name: performance
    rules:
      - alert: HighAPILatency
        expr: histogram_quantile(0.95, rate(request_duration_seconds_bucket[5m])) > 0.1
        for: 5m
        annotations:
          summary: "High API latency (p95 > 100ms)"
      
      - alert: LowCacheHitRate
        expr: cache_hits / (cache_hits + cache_misses) < 0.75
        for: 5m
        annotations:
          summary: "Cache hit rate below 75%"
      
      - alert: SlowDatabaseQueries
        expr: histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m])) > 0.05
        for: 5m
        annotations:
          summary: "Database queries > 50ms"
```

---

## Performance Optimization Checklist

### Database (High Impact)
- [ ] Add recommended indexes
- [ ] Implement materialized views
- [ ] Set up connection pooling
- [ ] Run EXPLAIN ANALYZE on slow queries
- [ ] Archive old data (>1M rows)

### Caching (High Impact)
- [ ] Configure Redis connection pool
- [ ] Implement cache-aside pattern
- [ ] Set up cache invalidation
- [ ] Monitor cache hit rate
- [ ] Set appropriate TTLs

### API (Medium Impact)
- [ ] Enable gzip compression
- [ ] Implement rate limiting by tier
- [ ] Optimize response payloads
- [ ] Add pagination
- [ ] Implement request timeouts

### Infrastructure (Medium Impact)
- [ ] Configure auto-scaling policies
- [ ] Set up performance alerts
- [ ] Enable detailed monitoring
- [ ] Optimize instance types
- [ ] Configure CDN for static content

### Monitoring (Ongoing)
- [ ] Track API latency (p50, p95, p99)
- [ ] Monitor database performance
- [ ] Watch cache hit rate
- [ ] Alert on degradation
- [ ] Weekly performance reviews

---

## Expected Improvements

### Before Optimization
- Average API response: 150-200ms
- Database query time: 50-100ms
- Cache hit rate: 40-50%
- Request throughput: 100 req/sec
- Error rate: 0.5-1%

### After Optimization
- Average API response: 20-50ms (75% improvement)
- Database query time: 5-10ms (85% improvement)
- Cache hit rate: 80-90% (100% improvement)
- Request throughput: 10,000+ req/sec (100x improvement)
- Error rate: <0.01% (50x improvement)

---

## Implementation Timeline

**Week 1:**
- Database indexing and connection pooling
- Redis caching setup
- Performance monitoring

**Week 2:**
- API optimization
- Load testing
- Infrastructure scaling

**Week 3:**
- Canary deployment
- Production validation
- Baseline documentation

---

## Resources

- PostgreSQL Performance: https://www.postgresql.org/docs/current/performance-tips.html
- Redis Best Practices: https://redis.io/topics/performance
- FastAPI Performance: https://fastapi.tiangolo.com/deployment/concepts/
- AWS Performance: https://docs.aws.amazon.com/whitepapers/

---

**Version:** 1.0  
**Last Updated:** 2024-01-31  
**Status:** Ready for Implementation
