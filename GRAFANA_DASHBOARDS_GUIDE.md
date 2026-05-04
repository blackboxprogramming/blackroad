# 📊 Advanced Grafana Dashboards Guide

Your platform comes with 4 pre-configured professional dashboards.

---

## 🚀 ACCESSING DASHBOARDS

After deployment:

```bash
open http://localhost:3000
```

**Login:**
- Username: `admin`
- Password: `grafana_admin_pass`

---

## 📊 AVAILABLE DASHBOARDS

### 1. System Health Dashboard
**URL:** http://localhost:3000/d/system-health

**Metrics:**
- CPU Usage (%)
- Memory Usage (%)
- Network Receive (bytes)
- Network Transmit (bytes)

**Use Case:** Monitor infrastructure health

### 2. Application Performance Dashboard
**URL:** http://localhost:3000/d/application-performance

**Metrics:**
- Requests/sec (throughput)
- Latency p95 (milliseconds)
- Error Rate (%)
- Active Services (count)
- Requests by Service
- Latency Trend

**Use Case:** Monitor application performance in real-time

### 3. Database Performance Dashboard
**URL:** http://localhost:3000/d/database-performance

**Metrics:**
- Queries/sec
- Active Connections
- Average Query Time
- Database Disk Usage
- Query Rate by Type
- Connection State

**Use Case:** Monitor database performance and connections

### 4. Business Metrics Dashboard
**URL:** http://localhost:3000/d/business-metrics

**Metrics:**
- Revenue (24h) in USD
- Active Subscriptions (count)
- Retention Rate (%)
- Average LTV (Customer Lifetime Value)
- Hourly Revenue by Plan
- Subscriptions by Plan

**Use Case:** Monitor business KPIs

---

## 🎯 COMMON MONITORING PATTERNS

### Real-time Monitoring

1. Open Application Performance Dashboard
2. Set time range to "Last 1 hour"
3. Watch requests, latency, and errors in real-time

### Performance Troubleshooting

1. Open Application Performance Dashboard
2. Check for:
   - Error Rate spikes
   - Latency spikes
   - Service count changes
3. Check Database Performance Dashboard
4. Check System Health Dashboard

### Business Analytics

1. Open Business Metrics Dashboard
2. Set time range to "Last 30 days"
3. Monitor:
   - Revenue trends
   - Subscription trends
   - Retention rate
   - Plan distribution

### Capacity Planning

1. Check System Health for trends
2. Check Database Performance for connection trends
3. Monitor growth over time

---

## 🔧 CUSTOMIZING DASHBOARDS

### Adding a New Panel

1. Open any dashboard
2. Click "Add panel" (top right)
3. Select data source (Prometheus)
4. Enter Prometheus query
5. Set visualization type
6. Click "Save dashboard"

### Useful Prometheus Queries

**HTTP Requests:**
```
sum(rate(http_requests_total[5m]))
```

**Error Rate:**
```
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100
```

**Latency p95:**
```
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) * 1000
```

**Service Health:**
```
up{job=~".*-api"}
```

**Database Connections:**
```
pg_stat_activity_count
```

**Redis Memory:**
```
redis_memory_used_bytes / redis_memory_max_bytes * 100
```

---

## 📈 DASHBOARD TIME RANGES

Each dashboard supports different time ranges:

**System Health:** Last 6 hours (real-time monitoring)
**Application Performance:** Last 1 hour (current behavior)
**Database Performance:** Last 1 hour (current behavior)
**Business Metrics:** Last 30 days (trends)

### Changing Time Range

1. Click time range selector (top right)
2. Choose from:
   - Last 5 minutes
   - Last 1 hour
   - Last 24 hours
   - Last 7 days
   - Last 30 days
   - Custom range

---

## 🎨 DASHBOARD TIPS & TRICKS

### Auto-Refresh

1. Click "Refresh" button (top right)
2. Select auto-refresh interval:
   - Off
   - 10s
   - 30s
   - 1m
   - 5m
   - 10m

### Exporting Dashboards

1. Click dashboard settings (gear icon)
2. Click "Export"
3. Download as JSON

### Sharing Dashboards

1. Click share icon (top right)
2. Generate public link
3. Share URL with team

### Full-Screen Mode

1. Click any panel
2. Press `E` to expand
3. Press `Escape` to close

---

## 🚨 SETTING UP ALERTS

### Alert Rules Already Configured

The platform includes 19 pre-configured alert rules:

**Service Health:**
- Service down > 2 minutes
- High error rate > 5%
- High latency p95 > 1 second

**Database:**
- PostgreSQL down
- Connection pool > 80%
- High query time

**Cache:**
- Redis down
- Memory usage > 90%

**System:**
- High CPU usage > 80%
- High memory usage > 85%
- Disk usage > 90%

### Creating Custom Alerts

1. Open any metric in Prometheus
2. Click "Create alert rule"
3. Set threshold and duration
4. Configure notification channel
5. Save alert

### Viewing Alerts

Visit Prometheus Alerts: http://localhost:9093

---

## 📊 METRICS COLLECTION

The platform collects **38 metrics** across all services:

**HTTP Metrics (8):**
- http_requests_total
- http_request_duration_seconds
- http_requests_in_progress
- ... (5 more)

**Database Metrics (6):**
- database_queries_total
- database_query_duration_seconds
- database_connections_active
- ... (3 more)

**Cache Metrics (5):**
- redis_hits_total
- redis_misses_total
- redis_evictions_total
- redis_memory_used_bytes
- redis_memory_max_bytes

**Business Metrics (8):**
- billing_transactions_total
- billing_active_subscriptions
- billing_churn
- ... (5 more)

**System Metrics (6):**
- process_resident_memory_bytes
- process_cpu_seconds_total
- disk_usage_bytes
- ... (3 more)

**ML Metrics (5):**
- ml_inference_duration_seconds
- ml_model_accuracy
- ml_predictions_total
- ... (2 more)

---

## 🎯 MONITORING CHECKLIST

Daily Monitoring:

- [ ] Application Performance dashboard - no errors
- [ ] Latency p95 < 250ms
- [ ] Error rate < 0.1%
- [ ] All services healthy (8/8)
- [ ] Database connections normal
- [ ] Redis memory < 80%

Weekly Monitoring:

- [ ] Business Metrics dashboard - revenue trend
- [ ] Retention rate > 95%
- [ ] System Health - no capacity issues
- [ ] Database growth rate
- [ ] Alert rule effectiveness

Monthly Monitoring:

- [ ] Full month revenue review
- [ ] Subscription growth trend
- [ ] Performance optimization opportunities
- [ ] Capacity planning
- [ ] Cost optimization

---

## 🔗 QUICK LINKS

- **Grafana:** http://localhost:3000
- **Prometheus:** http://localhost:9090
- **AlertManager:** http://localhost:9093
- **Application:** http://localhost

---

## 💡 NEXT STEPS

1. Deploy platform: `./deploy-local.sh`
2. Open Grafana: http://localhost:3000
3. Select a dashboard
4. Set appropriate time range
5. Monitor your platform

**Your dashboards are ready to use!** 🎉

