# Admin Dashboard API Guide

## Overview

The Admin Dashboard API provides real-time revenue metrics, user analytics, and system health monitoring. All endpoints require Bearer token authentication.

**Base URL**: `http://localhost:8001/api/admin`

**Authentication**: Add header: `Authorization: Bearer <ADMIN_TOKEN>`

## Environment Setup

```bash
# Set admin token (change this in production!)
export ADMIN_TOKEN="your-secure-token-here"

# Run the admin dashboard
python admin_dashboard.py
```

The API runs on port 8001 by default and connects to the same database as the main app.

---

## Revenue Metrics Endpoints

### GET `/revenue/total`

Get total revenue over a time period.

**Parameters**:
- `days` (optional): Number of days to look back (1-365, default: 30)

**Response**:
```json
{
  "period_days": 30,
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2024-01-31T23:59:59",
  "total_revenue_usd": 15234.50,
  "total_charges": 1523,
  "avg_charge_usd": 10.00
}
```

**Use Cases**:
- Track daily/weekly/monthly revenue
- Monitor revenue trends
- Generate quick financial reports

---

### GET `/revenue/by-tier`

Break down revenue by user tier (Free, Light, Power, Enterprise).

**Parameters**:
- `days` (optional): Number of days to look back (1-365, default: 30)

**Response**:
```json
{
  "period_days": 30,
  "by_tier": [
    {
      "tier": "enterprise",
      "charge_count": 450,
      "total_revenue_usd": 8500.00,
      "avg_charge_usd": 18.89
    },
    {
      "tier": "power",
      "charge_count": 600,
      "total_revenue_usd": 4200.00,
      "avg_charge_usd": 7.00
    },
    {
      "tier": "light",
      "charge_count": 300,
      "total_revenue_usd": 1200.00,
      "avg_charge_usd": 4.00
    }
  ]
}
```

**Use Cases**:
- Identify highest-value customer segments
- Optimize pricing by tier
- Forecast growth in each segment

---

### GET `/revenue/daily`

Get daily revenue trend over a time period.

**Parameters**:
- `days` (optional): Number of days to look back (1-365, default: 30)

**Response**:
```json
{
  "period_days": 30,
  "daily_trend": [
    {
      "date": "2024-01-01",
      "revenue_usd": 512.34,
      "charge_count": 51
    },
    {
      "date": "2024-01-02",
      "revenue_usd": 623.45,
      "charge_count": 62
    }
  ]
}
```

**Use Cases**:
- Identify daily patterns (weekday vs weekend)
- Detect revenue spikes/drops
- Track growth over time

---

### GET `/revenue/projection`

Project annual revenue based on recent performance.

**Parameters**:
- `days_history` (optional): Number of recent days to base projection on (7-365, default: 30)

**Response**:
```json
{
  "annual_projection_usd": 5245612.50,
  "daily_average_usd": 14371.54,
  "recent_period_revenue_usd": 431158.20,
  "based_on_days": 30,
  "charge_count": 43116
}
```

**Calculation**:
```
annual_projection = (total_revenue / days) * 365
```

**Use Cases**:
- Quick revenue forecasting
- Investor presentations
- Growth rate analysis

---

## User Analytics Endpoints

### GET `/users/total`

Get total users by tier with usage statistics.

**Response**:
```json
{
  "total_users": 10523,
  "by_tier": [
    {
      "tier": "free",
      "user_count": 8234,
      "avg_monthly_usage": 1250,
      "max_monthly_usage": 8500
    },
    {
      "tier": "light",
      "user_count": 1450,
      "avg_monthly_usage": 5000,
      "max_monthly_usage": 25000
    },
    {
      "tier": "power",
      "user_count": 650,
      "avg_monthly_usage": 12500,
      "max_monthly_usage": 50000
    },
    {
      "tier": "enterprise",
      "user_count": 189,
      "avg_monthly_usage": 45000,
      "max_monthly_usage": 200000
    }
  ]
}
```

**Use Cases**:
- User distribution analysis
- Capacity planning
- Identify power users

---

### GET `/users/growth`

Track daily user signups over time.

**Parameters**:
- `days` (optional): Number of days to look back (1-365, default: 30)

**Response**:
```json
{
  "period_days": 30,
  "daily_signups": [
    {
      "date": "2024-01-01",
      "signups": 25
    },
    {
      "date": "2024-01-02",
      "signups": 32
    }
  ]
}
```

**Metrics to Track**:
- Average daily signups
- Signup velocity
- Growth rate (YoY, MoM)

---

### GET `/users/churn`

Calculate monthly churn rate (subscription cancellations).

**Parameters**:
- `days` (optional): Number of days to calculate churn for (1-365, default: 30)

**Response**:
```json
{
  "period_days": 30,
  "start_active_paid_users": 2500,
  "canceled_users": 125,
  "churn_rate_percent": 5.0
}
```

**Interpretation**:
- < 5%: Excellent (healthy SaaS)
- 5-10%: Good
- 10-15%: Concerning (investigate why users leave)
- > 15%: Critical (product issues or high price sensitivity)

---

### GET `/users/paid-conversion`

Calculate percentage of users who have paid.

**Response**:
```json
{
  "total_users": 10523,
  "paid_users": 2289,
  "free_users": 8234,
  "paid_conversion_rate_percent": 21.75
}
```

**Benchmark**:
- SaaS average: 2-5% conversion from free to paid
- Target for BlackRoad: 15-25% (premium service)

---

## System Health Endpoints

### GET `/health/database`

Check database connectivity and table sizes.

**Response**:
```json
{
  "status": "healthy",
  "connectivity_latency_ms": 2.34,
  "tables": [
    {
      "schema": "public",
      "table": "charges",
      "size": "245 MB"
    },
    {
      "schema": "public",
      "table": "monthly_usage",
      "size": "102 MB"
    }
  ]
}
```

**Alerts**:
- latency_ms > 100: Database performance issue
- Any table > 1GB: Consider partitioning/archiving

---

### GET `/health/pending-invoices`

Monitor invoices stuck in pending or failed state.

**Response**:
```json
{
  "pending_invoices": 23,
  "failed_invoices": 5,
  "total_issues": 28
}
```

**Action Items**:
- Pending > 10: Investigate stuck webhook processing
- Failed > 5: Check Stripe API credentials/limits

---

### GET `/health/failed-charges`

List recent failed charges (helps debug payment issues).

**Parameters**:
- `hours` (optional): Hours to look back (1-720, default: 24)

**Response**:
```json
{
  "time_window_hours": 24,
  "failed_charge_count": 12,
  "recent_failures": [
    {
      "charge_id": "ch_123456",
      "customer_id": "cust_001",
      "amount_usd": 50.00,
      "timestamp": "2024-01-31T14:23:45"
    }
  ]
}
```

**Troubleshooting**:
- Spikes in failed charges: Check Stripe status page
- Specific customer failures: Contact customer to update payment method

---

## Tier Management Endpoints

### GET `/tiers/distribution`

See how users are distributed across tiers and revenue contribution.

**Response**:
```json
{
  "total_users": 10523,
  "tier_breakdown": [
    {
      "tier": "free",
      "user_count": 8234,
      "percentage": 78.28,
      "total_revenue_usd": 0
    },
    {
      "tier": "light",
      "user_count": 1450,
      "percentage": 13.78,
      "total_revenue_usd": 36250
    },
    {
      "tier": "power",
      "user_count": 650,
      "percentage": 6.18,
      "total_revenue_usd": 146250
    },
    {
      "tier": "enterprise",
      "user_count": 189,
      "percentage": 1.80,
      "total_revenue_usd": 184275
    }
  ]
}
```

**Insights**:
- Enterprise is 1.8% of users but 44% of revenue
- 78% of users are free (typical SaaS)

---

### GET `/tiers/mrr`

Monthly Recurring Revenue by tier (assumes monthly subscriptions).

**Response**:
```json
{
  "monthly_recurring_revenue_usd": 366775,
  "annual_run_rate_usd": 4401300,
  "by_tier": [
    {
      "tier": "light",
      "user_count": 1450,
      "monthly_per_user_usd": 25,
      "tier_mrr_usd": 36250
    },
    {
      "tier": "power",
      "user_count": 650,
      "monthly_per_user_usd": 225,
      "tier_mrr_usd": 146250
    },
    {
      "tier": "enterprise",
      "user_count": 189,
      "monthly_per_user_usd": 975,
      "tier_mrr_usd": 184275
    }
  ]
}
```

**Key Metric**: MRR is the most important metric for SaaS businesses.

---

## Invoice Endpoints

### GET `/invoices/summary`

High-level invoice status summary.

**Response**:
```json
{
  "by_status": [
    {
      "status": "paid",
      "invoice_count": 2450,
      "total_revenue_usd": 612500
    },
    {
      "status": "unpaid",
      "invoice_count": 45,
      "total_revenue_usd": 11250
    },
    {
      "status": "failed",
      "invoice_count": 8,
      "total_revenue_usd": 2000
    }
  ]
}
```

**Healthy State**:
- Paid invoices: > 95%
- Unpaid: < 3%
- Failed: < 1%

---

### GET `/invoices/overdue`

Find invoices that are overdue for payment.

**Parameters**:
- `days_overdue` (optional): Days past due date (default: 30)

**Response**:
```json
{
  "overdue_threshold_days": 30,
  "overdue_invoice_count": 12,
  "total_overdue_usd": 3000,
  "recent_overdue": [
    {
      "invoice_id": "inv_001",
      "customer_id": "cust_001",
      "amount_usd": 250.00,
      "due_date": "2023-12-01"
    }
  ]
}
```

**Actions**:
- Send dunning emails to customers
- Suspend service for > 60 days overdue
- Contact sales team for enterprise customers

---

## Export Endpoints

### GET `/export/daily-report`

Comprehensive daily report (good for dashboards/emails).

**Response**:
```json
{
  "date": "2024-01-31",
  "generated_at": "2024-01-31T23:59:59",
  "daily_metrics": {
    "revenue_usd": 8234.50,
    "new_signups": 45
  },
  "user_metrics": {
    "total_users": 10523,
    "paid_users": 2289,
    "free_users": 8234
  }
}
```

**Use Cases**:
- Email to executives daily
- Dashboard display
- Automated alerts

---

## Health Check

### GET `/ping`

Simple health check (requires authentication).

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-31T23:59:59"
}
```

---

## Integration Examples

### JavaScript/Frontend

```javascript
async function getRevenue(days = 30) {
  const token = localStorage.getItem('adminToken');
  const response = await fetch(
    `http://localhost:8001/api/admin/revenue/total?days=${days}`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  return response.json();
}

async function getUserStats() {
  const token = localStorage.getItem('adminToken');
  const response = await fetch(
    'http://localhost:8001/api/admin/users/total',
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  return response.json();
}
```

### Python

```python
import requests

BASE_URL = "http://localhost:8001/api/admin"
TOKEN = "your-admin-token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

def get_revenue(days=30):
    resp = requests.get(
        f"{BASE_URL}/revenue/total",
        params={"days": days},
        headers=HEADERS
    )
    return resp.json()

def get_daily_report():
    resp = requests.get(
        f"{BASE_URL}/export/daily-report",
        headers=HEADERS
    )
    return resp.json()
```

### cURL

```bash
# Get total revenue
curl -H "Authorization: Bearer <TOKEN>" \
  http://localhost:8001/api/admin/revenue/total?days=30

# Get users by tier
curl -H "Authorization: Bearer <TOKEN>" \
  http://localhost:8001/api/admin/users/total

# Get MRR
curl -H "Authorization: Bearer <TOKEN>" \
  http://localhost:8001/api/admin/tiers/mrr

# Daily report
curl -H "Authorization: Bearer <TOKEN>" \
  http://localhost:8001/api/admin/export/daily-report
```

---

## Monitoring & Alerts

### Recommended Alerts

Set up alerts for these conditions:

```python
# Alert if daily revenue drops > 50%
avg_daily = total_revenue / days
today_revenue = get_today_revenue()
if today_revenue < avg_daily * 0.5:
    alert("Revenue drop detected!")

# Alert if churn > 10%
churn = get_churn()
if churn > 10:
    alert("High churn rate!")

# Alert if failed charges > 5%
failed = get_failed_charges()
if failed / total_charges > 0.05:
    alert("High charge failure rate!")
```

### Dashboard Metrics

Build a dashboard with these 12 key metrics:

1. **Revenue Metrics**:
   - Total MRR
   - Daily revenue
   - Monthly revenue
   - Revenue growth (%)

2. **User Metrics**:
   - Total users
   - Paid users
   - Free users
   - Conversion rate (%)

3. **Health Metrics**:
   - Failed charges (%)
   - Churn rate (%)
   - Overdue invoices
   - Pending invoices

---

## Security Best Practices

1. **Change admin token in production**:
   ```bash
   export ADMIN_TOKEN="$(openssl rand -hex 32)"
   ```

2. **Use HTTPS in production**:
   - Requires valid SSL certificate
   - Update base URL to `https://api.blackroad.com`

3. **Rate limit admin endpoints**:
   - 100 requests/minute per token
   - Prevents brute force attacks

4. **Audit logging**:
   - Log all admin API calls
   - Track who accessed what and when

5. **IP whitelisting** (optional):
   - Only allow admin requests from specific IPs
   - Further restricts unauthorized access

---

## Performance Optimization

### Large Dataset Queries

For large datasets, add pagination:

```python
@app.get("/revenue/daily")
async def get_daily_revenue(
    _: str = Depends(verify_admin_token),
    days: int = Query(30),
    limit: int = Query(100, le=1000),  # Max 1000 rows
    offset: int = Query(0)
):
    # ... add LIMIT and OFFSET to query
```

### Caching

Cache frequently requested metrics:

```python
from functools import lru_cache
from datetime import datetime, timedelta

cached_at = {}

def get_cached_revenue(days=30):
    key = f"revenue_{days}"
    cache_age = datetime.utcnow() - cached_at.get(key, datetime.utcnow())
    
    # Refresh cache every 5 minutes
    if cache_age > timedelta(minutes=5):
        cached_at[key] = datetime.utcnow()
        # ... fetch fresh data
    
    return cached_data
```

---

## Troubleshooting

### Connection Failed

```
Error: Connection refused on port 8001
```

**Solution**:
```bash
# Check if admin dashboard is running
lsof -i :8001

# Start the admin dashboard
python admin_dashboard.py
```

### Authentication Failed

```
Error: 401 Unauthorized
```

**Solution**:
```bash
# Verify admin token
echo $ADMIN_TOKEN

# Update request header
Authorization: Bearer $ADMIN_TOKEN
```

### No Data Returned

```
"total_users": 0
"total_revenue": 0
```

**Solution**:
- Verify database connection: `GET /health/database`
- Check if charges have been created
- Ensure proper timestamps in database

---

## Maintenance

### Regular Tasks

- **Daily**: Check daily-report, monitor failed charges
- **Weekly**: Review churn rate, analyze revenue trends
- **Monthly**: Calculate MRR, project annual revenue
- **Quarterly**: Review tier distribution, adjust pricing

### Database Maintenance

```bash
# Analyze table performance
python manage-migrations.py verify

# Archive old data (quarterly)
DELETE FROM charges WHERE created_at < DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 year');
DELETE FROM request_logs WHERE created_at < DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 year');
```

---

## Support

For issues with the admin dashboard:

1. Check `/health/database` endpoint
2. Review error logs: `docker logs blackroad_api`
3. Verify database connectivity
4. Check authentication headers

Contact: engineering@blackroad.com

