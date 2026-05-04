# Performance Testing Guide

**Benchmark and validate performance optimizations**

---

## Quick Start

### 1. Establish Baseline (Before Optimization)

```bash
# Start fresh environment
docker-compose down
docker-compose up -d

# Wait for services to be ready
sleep 10

# Run baseline test
python3 -c "
import requests
import time

times = []
for i in range(100):
    start = time.time()
    requests.get('http://localhost:8000/status')
    times.append(time.time() - start)

import statistics
print(f'Mean: {statistics.mean(times)*1000:.2f}ms')
print(f'Median: {statistics.median(times)*1000:.2f}ms')
print(f'Stdev: {statistics.stdev(times)*1000:.2f}ms')
print(f'Min: {min(times)*1000:.2f}ms')
print(f'Max: {max(times)*1000:.2f}ms')
"
```

### 2. Apply Optimizations

```bash
# Run database optimization
python3 optimize_database.py

# Verify cache is running
docker-compose logs redis
```

### 3. Test After Optimization

```bash
# Run same test again
python3 -c "
import requests
import time

times = []
for i in range(100):
    start = time.time()
    requests.get('http://localhost:8000/status')
    times.append(time.time() - start)

import statistics
print(f'Mean: {statistics.mean(times)*1000:.2f}ms')
print(f'Median: {statistics.median(times)*1000:.2f}ms')
print(f'Stdev: {statistics.stdev(times)*1000:.2f}ms')
print(f'Min: {min(times)*1000:.2f}ms')
print(f'Max: {max(times)*1000:.2f}ms')
"
```

---

## Load Testing with K6

### Basic Load Test

```bash
k6 run k6-scenarios.js
```

### View Cache Statistics

```bash
# Connect to Redis
docker exec -it blackroad_redis_1 redis-cli

# Check stats
> INFO stats

# Monitor in real-time
> MONITOR
```

---

## Performance Metrics to Track

- **API Latency**: p50, p95, p99
- **Database Query Time**: Slowest 10 queries
- **Cache Hit Rate**: Should exceed 80%
- **Error Rate**: Should be <0.01%
- **Throughput**: Requests per second

---

**Version:** 1.0  
**Status:** Ready to Test
