# Monitoring & Alerting Guide

## Overview

BlackRoad includes a comprehensive monitoring and alerting system with:
- **Real-time metrics collection** from the admin dashboard API
- **Prometheus** for metrics storage and time-series analysis
- **Grafana** for visual dashboards
- **Automated alerts** with multiple delivery channels (Email, Slack, Webhooks)
- **Health checks** for critical system components

---

## Architecture

```
Admin Dashboard API (8001)
         ↓
 Monitoring System (Python)
    ├── Health Checks
    ├── Metric Collection
    └── Alert Generation
         ↓
Prometheus Exporter (8002)
         ↓
Prometheus (9090)
         ↓
Grafana (3000)
    ├── Dashboards
    ├── Alerts
    └── Notifications
         ↓
Notification Channels
    ├── Email (SendGrid/AWS SES)
    ├── Slack (Webhooks)
    └── Custom Webhooks
```

---

## Quick Start

### 1. Install Dependencies

```bash
pip install prometheus-client requests
```

### 2. Set Environment Variables

```bash
export ADMIN_TOKEN="your-admin-token"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."  # Optional
export ALERT_EMAIL="alerts@blackroad.com"                         # Optional
export ALERT_WEBHOOK_URL="https://your-webhook.com/alerts"        # Optional
```

### 3. Start Monitoring Stack

#### Option A: Standalone (Development)

```bash
# Terminal 1: Start monitoring daemon
python monitoring_system.py daemon 60

# Terminal 2: Start Prometheus exporter
python prometheus_exporter.py 8002 30

# Terminal 3: Start Prometheus (requires prometheus installed)
prometheus --config.file=prometheus.yml
```

#### Option B: Docker Compose (Production)

Update `docker-compose.yml` to include:

```yaml
prometheus:
  image: prom/prometheus:latest
  container_name: blackroad-prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
    - ./alert_rules.yml:/etc/prometheus/alert_rules.yml
    - prometheus_data:/prometheus
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'

grafana:
  image: grafana/grafana:latest
  container_name: blackroad-grafana
  ports:
    - "3000:3000"
  environment:
    GF_SECURITY_ADMIN_PASSWORD: admin
    GF_USERS_ALLOW_SIGN_UP: 'false'
  volumes:
    - grafana_data:/var/lib/grafana
    - ./grafana-dashboard.json:/etc/grafana/provisioning/dashboards/blackroad.json
  depends_on:
    - prometheus

monitoring:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: blackroad-monitoring
  command: python3 monitoring_system.py daemon 60
  environment:
    ADMIN_TOKEN: ${ADMIN_TOKEN}
    SLACK_WEBHOOK_URL: ${SLACK_WEBHOOK_URL}
    ALERT_EMAIL: ${ALERT_EMAIL}
  depends_on:
    - api

exporter:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: blackroad-exporter
  ports:
    - "8002:8002"
  command: python3 prometheus_exporter.py 8002 30
  environment:
    ADMIN_TOKEN: ${ADMIN_TOKEN}
  depends_on:
    - admin-dashboard
```

Start with:

```bash
docker-compose up -d prometheus grafana monitoring exporter
```

---

## Monitoring System Components

### 1. Monitoring Daemon (`monitoring_system.py`)

Periodically checks:
- Revenue metrics (daily drop, tier breakdown)
- User metrics (churn, conversion, growth)
- System health (database, API connectivity)
- Invoice status (pending, failed)
- Payment health (failed charges)

**Run Modes**:

```bash
# Single check
python monitoring_system.py

# Continuous daemon (checks every 60 seconds)
python monitoring_system.py daemon 60
```

**Output**:

```json
{
  "timestamp": "2024-01-31T23:59:59",
  "overall_status": "healthy",
  "health_checks": [
    {
      "service": "database",
      "status": "healthy",
      "latency_ms": 2.34,
      "message": "Database latency: 2.34ms"
    }
  ],
  "alerts": {
    "critical": 0,
    "warning": 2,
    "total": 2,
    "details": [...]
  }
}
```

### 2. Prometheus Exporter (`prometheus_exporter.py`)

Exposes metrics in Prometheus format for scraping.

**Metrics Exported** (38 total):

**Revenue**:
- `blackroad_revenue_total_usd` - Total revenue
- `blackroad_revenue_by_tier_usd` - Revenue by tier
- `blackroad_daily_revenue_usd` - Daily revenue
- `blackroad_revenue_projection_annual_usd` - Annual forecast

**Users**:
- `blackroad_total_users` - Total users by tier
- `blackroad_daily_signups` - Daily signups
- `blackroad_churn_rate_percent` - Churn rate
- `blackroad_paid_conversion_rate_percent` - Conversion rate

**System**:
- `blackroad_database_latency_ms` - DB latency
- `blackroad_health_check_status` - Service health (1=healthy, 0=unhealthy)
- `blackroad_health_check_latency_ms` - Health check latency

**Subscriptions**:
- `blackroad_mrr_total_usd` - Monthly Recurring Revenue
- `blackroad_mrr_by_tier_usd` - MRR by tier
- `blackroad_arr_total_usd` - Annual Recurring Revenue

**Invoices**:
- `blackroad_pending_invoices` - Pending invoices
- `blackroad_failed_invoices` - Failed invoices
- `blackroad_failed_charges_total` - Failed charges (24h)

**Alerts**:
- `blackroad_alerts_active` - Active alerts by severity
- `blackroad_alerts_total` - Total alerts triggered

**Run**:

```bash
# Port 8002, update every 30 seconds
python prometheus_exporter.py 8002 30
```

**Access**: http://localhost:8002/metrics

### 3. Prometheus (`prometheus.yml`)

Time-series database for metrics.

**Scrape Jobs**:
- `blackroad-exporter` - Main metrics (30s interval)
- `node` - System metrics from Node Exporter
- `cadvisor` - Docker container metrics

**Configuration**:
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'blackroad-exporter'
    static_configs:
      - targets: ['localhost:8002']
    scrape_interval: 30s
```

**Access**: http://localhost:9090

---

## Alert Rules (`alert_rules.yml`)

### Alert Categories

#### Revenue Alerts (4 rules)

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| DailyRevenueDropped | Daily revenue < 50% of average | WARNING | Investigate | 
| RevenueProjectionLow | Annual projection < MRR×12×0.8 | WARNING | Review pricing |

#### User Metrics Alerts (4 rules)

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| HighChurnRate | Churn > 10% | CRITICAL | Emergency support |
| ChurnRateElevated | Churn 5-10% | WARNING | Analyze churn |
| LowPaidConversion | Conversion < 5% | WARNING | Review funnel |
| NoSignups | Zero signups in 24h | CRITICAL | Check marketing |

#### System Health Alerts (6 rules)

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| DatabaseLatencyHigh | > 500ms | CRITICAL | Scale database |
| DatabaseLatencyWarning | 100-500ms | WARNING | Monitor |
| DatabaseUnhealthy | Health check fails | CRITICAL | Emergency restart |
| PendingInvoicesPiled | > 25 invoices | CRITICAL | Investigate webhook |
| PendingInvoicesWarning | 10-25 invoices | WARNING | Monitor |
| FailedChargesHigh | > 5% failure rate | CRITICAL | Contact Stripe |

#### Invoice/Payment Alerts (2 rules)

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| FailedInvoices | > 5 failed | WARNING | Check payment methods |

#### Subscription Alerts (2 rules)

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| MRRDecline | MRR trending down | WARNING | Analyze churn |
| ARRTargetMissed | ARR < $5M | INFO | Report to exec |

#### Alert System Alerts (2 rules)

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| HighAlertVolume | > 5 critical active | CRITICAL | Investigate |
| AlertStorm | > 10 alerts/5min | CRITICAL | Check system |

#### Growth Alerts (2 rules)

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| LowUserGrowth | < 10 users/day avg | INFO | Review marketing |
| NegativeGrowth | User count declining | WARNING | Address churn |

---

## Grafana Dashboards

The main dashboard (`grafana-dashboard.json`) shows:

### Top Row (Key Metrics)
- Total Revenue (30d) - Green/Yellow/Red thresholds
- Monthly Recurring Revenue - Tracks subscription health
- Churn Rate (%) - Alerts if > 5%
- Total Users by Tier - Pie chart distribution

### Middle Rows
- Daily Revenue Trend - Line chart, identify spikes/drops
- MRR by Tier - Stacked area chart
- Active Alerts - Real-time alert count
- Critical Alerts by Metric - Breakdown
- Database Latency - Performance monitoring
- Pending Invoices - Financial health

### Bottom Rows
- Paid Conversion Rate - Funnel metric
- Failed Charges - Payment health

### Access

```bash
# After starting Grafana
open http://localhost:3000

# Default credentials
Username: admin
Password: admin
```

### Import Dashboard

1. Open Grafana UI
2. Click "+" → "Import"
3. Upload `grafana-dashboard.json`
4. Select Prometheus data source
5. Click "Import"

### Add Data Source

1. Configuration → Data Sources
2. Click "Add data source"
3. Select "Prometheus"
4. URL: `http://localhost:9090`
5. Click "Save & Test"

---

## Alert Delivery Channels

### Email Alerts

```python
import os
from monitoring_system import AlertNotifier, AlertSeverity, Alert

# Configure
os.environ['ALERT_EMAIL'] = 'ops@blackroad.com'

# Send
alert = Alert(...)
AlertNotifier.send_email(alert, 'ops@blackroad.com')
```

**Provider Setup** (SendGrid example):

```bash
export SENDGRID_API_KEY="sg_..."
```

### Slack Alerts

1. Create Slack App at https://api.slack.com/apps
2. Enable Incoming Webhooks
3. Create channel webhook
4. Set environment variable:

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

5. Send test:

```bash
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text": "Test alert"}'
```

### Custom Webhooks

```bash
export ALERT_WEBHOOK_URL="https://your-system.com/webhooks/alerts"
```

Payload:

```json
{
  "title": "High Churn Rate",
  "message": "Churn rate is 12.5% (threshold: 10%)",
  "severity": "critical",
  "metric": "churn_rate",
  "current_value": 12.5,
  "threshold": 10,
  "timestamp": "2024-01-31T23:59:59"
}
```

---

## Health Checks

### Database Health

```python
from monitoring_system import MonitoringSystem

monitoring = MonitoringSystem()
db_health = monitoring.check_database_health()

print(f"Status: {db_health.status}")
print(f"Latency: {db_health.latency_ms}ms")
```

Expected response:

```
Status: healthy
Latency: 2.34ms
```

Healthy thresholds:
- Status: `healthy`
- Latency: < 100ms (warning at 100ms, critical at 500ms)

### API Health

```python
api_health = monitoring.check_api_connectivity()
```

### Full Status Report

```python
report = monitoring.run_all_checks()
print(json.dumps(report, indent=2, default=str))
```

---

## Threshold Tuning

Adjust thresholds in `monitoring_system.py`:

```python
class AlertThresholds:
    # Revenue metrics
    DAILY_REVENUE_DROP_PERCENT = 50  # ← Adjust here
    
    # User metrics
    CHURN_RATE_WARNING = 10
    CHURN_RATE_CRITICAL = 15
    
    # System health
    DB_LATENCY_WARNING_MS = 100
    DB_LATENCY_CRITICAL_MS = 500
```

### Recommended Settings

**High-Risk Environment**:
- Churn warning: 5%, Critical: 10%
- DB latency warning: 50ms, Critical: 200ms
- Revenue drop: 25%

**Stable Environment**:
- Churn warning: 10%, Critical: 15%
- DB latency warning: 100ms, Critical: 500ms
- Revenue drop: 50%

**Development**:
- Disable most alerts (too noisy)
- Focus on critical system health

---

## Performance Optimization

### Reduce Check Frequency

For large deployments, reduce check frequency:

```bash
# Check every 2 minutes instead of 1 minute
python monitoring_system.py daemon 120
```

### Batch Metrics Collection

```python
# Instead of individual requests
monitoring.run_all_checks()  # Collects all metrics in batch
```

### Prometheus Storage Optimization

```yaml
# Reduce retention
prometheus \
  --storage.tsdb.retention.time=30d \
  --storage.tsdb.path=/prometheus
```

### Grafana Query Optimization

Use range vectors to reduce data:

```promql
# Instead of
blackroad_daily_revenue_usd

# Use (if only need 7-day average)
avg_over_time(blackroad_daily_revenue_usd[7d])
```

---

## Troubleshooting

### No metrics appearing in Prometheus

1. Check exporter is running:
   ```bash
   curl http://localhost:8002/metrics
   ```

2. Check Prometheus config:
   ```
   curl http://localhost:9090/api/v1/targets
   ```

3. Check dashboard access:
   ```bash
   curl http://localhost:9090/api/v1/query?query=blackroad_revenue_total_usd
   ```

### Alerts not firing

1. Verify rule syntax:
   ```bash
   promtool check rules alert_rules.yml
   ```

2. Check alert status in Prometheus:
   ```
   http://localhost:9090/alerts
   ```

3. Verify thresholds are being met:
   ```bash
   curl http://localhost:9090/api/v1/query?query=blackroad_churn_rate_percent
   ```

### Slow queries

1. Check Prometheus memory usage:
   ```
   http://localhost:9090/api/v1/status/runtimeinfo
   ```

2. Optimize query:
   ```promql
   # Slow
   rate(blackroad_revenue_total_usd[1s])
   
   # Fast
   rate(blackroad_revenue_total_usd[5m])
   ```

### Slack webhooks failing

```bash
# Test webhook
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test"}'

# Should return 200 OK
```

---

## Production Checklist

- [ ] Prometheus configured for 30-day retention
- [ ] Grafana behind authentication (not default admin/admin)
- [ ] Slack webhooks configured
- [ ] Email alerts configured
- [ ] Alert thresholds tuned for your business
- [ ] Dashboards reviewed by ops team
- [ ] Alert rules validated in dev environment
- [ ] Monitoring daemon running on separate container
- [ ] Database backed up before production deployment
- [ ] On-call rotation configured for critical alerts

---

## Support

For issues:

1. Check logs:
   ```bash
   docker logs blackroad-monitoring
   docker logs blackroad-exporter
   docker logs blackroad-prometheus
   ```

2. Verify admin dashboard is running:
   ```bash
   curl -H "Authorization: Bearer $ADMIN_TOKEN" \
     http://localhost:8001/api/admin/ping
   ```

3. Check data flow:
   - Admin Dashboard → Monitoring System → Prometheus Exporter → Prometheus → Grafana

Contact: engineering@blackroad.com
