# Customer Analytics Dashboard UI Guide

**Self-service analytics platform for API users**

---

## Overview

The Customer Analytics Dashboard (port 8004) provides customers with real-time insights into their API usage, billing, and forecasts. Fully self-contained HTML/JavaScript UI with no external dependencies.

### Key Features

✅ **Real-Time Dashboard**
- 30-day usage trend visualization
- Monthly spend tracking
- Subscription tier display
- Cost forecast for next 30 days

✅ **Usage Analytics**
- Daily request counts
- Per-request cost breakdown
- Active user metrics
- Error tracking and analysis

✅ **Billing Management**
- 6-month billing history
- Payment status tracking
- Invoice due dates
- Cost per month

✅ **Forecasting**
- AI-powered usage forecast (30 days)
- Estimated costs and spending
- Weekly seasonality adjustments
- Trend analysis

✅ **Self-Service Export**
- Export usage as CSV
- Download billing history
- Schedule automated reports
- Data portability

---

## Quick Start

### 1. Start the Service

```bash
# Run locally
python3 customer_analytics_ui.py

# Or with Docker
docker-compose up customer-ui
```

Service will be available at: `http://localhost:8004`

### 2. Access the Dashboard

```bash
# Generate token (in production, use JWT from auth)
TOKEN="user_demo_key_123456"

# Open dashboard
open "http://localhost:8004/?token=$TOKEN"
```

### 3. View Your Data

- **Dashboard Tab**: Overview of current usage and tier
- **Daily Usage Tab**: Detailed daily breakdown
- **Billing History Tab**: Past invoices and payments
- **Forecast Tab**: Projected usage and costs

---

## API Endpoints

### Authentication
All endpoints require `Authorization: Bearer <token>` header

### Get Customer Profile

```bash
GET /api/customer/profile

# Response:
{
  "user_id": "user_abc123",
  "email": "user@example.com",
  "tier": "Light",
  "tier_limit_requests_per_hour": 7200,
  "monthly_limit": 180000,
  "joined_date": "2024-01-15",
  "payment_method": "•••• 4242"
}
```

### Get Usage Data (30 days)

```bash
GET /api/customer/usage

# Response:
[
  {
    "date": "2024-01-15",
    "requests": 12500,
    "cost": 125.00,
    "active_users": 625,
    "errors": 12
  },
  ...
]
```

### Get Billing History (6 months)

```bash
GET /api/customer/billing-history

# Response:
[
  {
    "month": "December 2023",
    "requests": 750000,
    "cost": 7500.00,
    "status": "Paid",
    "due_date": "2024-01-15"
  },
  ...
]
```

### Get Usage Forecast (30 days)

```bash
GET /api/customer/forecast

# Response:
[
  {
    "date": "2024-01-16",
    "requests": 13000,
    "cost": 130.00,
    "type": "forecast"
  },
  ...
]
```

### Get Usage Alerts

```bash
GET /api/customer/alerts

# Response:
[
  {
    "id": "1",
    "type": "usage_warning",
    "message": "You've used 75% of your monthly limit",
    "severity": "warning",
    "created_at": "2024-01-15T22:30:00Z"
  }
]
```

### Get Billing Portal Link

```bash
GET /api/customer/billing-portal

# Response:
{
  "portal_url": "https://billing.stripe.com/p/session_abc123"
}
```

### Export Usage Data

```bash
GET /api/customer/export

# Response: CSV file
Date,Requests,Cost,Active Users,Errors
2024-01-15,12500,125.00,625,12
2024-01-14,11800,118.00,590,10
...
```

---

## Dashboard Sections

### Stats Overview
Four key metrics at the top:
1. **This Month** - Total requests in current month
2. **Monthly Spend** - Total USD cost this month
3. **Subscription Tier** - Current plan level
4. **Monthly Forecast** - Projected spend for full month

### 30-Day Usage Trend
Line chart showing:
- Daily request volume
- Visual trend patterns
- Weekly seasonality
- Peak usage periods

### Cost Forecast Chart
Bar chart showing:
- Projected daily costs (next 30 days)
- Cumulative spending trend
- Comparison to actual usage

### Daily Usage Table
Detailed breakdown by day:
- Request count
- Cost in USD
- Active users
- Error count
- Sortable columns
- CSV export button

### Billing History Table
6-month invoice history:
- Month and year
- Total requests
- Total cost
- Payment status (Paid/Current)
- Due date

### Forecast Table
30-day forecast:
- Date
- Projected request count
- Projected cost
- Comparison to baseline

---

## Configuration

### Customize Forecast Algorithm

Edit `forecast_usage()` in `customer_analytics_ui.py`:

```python
def forecast_usage(current_usage, days_ahead=30):
    # Adjust forecast parameters
    recent = current_usage[-7:]  # Use last 7 days
    avg_daily_requests = sum(u['requests'] for u in recent) / len(recent)
    
    # Adjust seasonality factor (1.15 = 15% weekly variation)
    seasonality_factor = 1.15
    
    # Apply growth rate (0 = no growth)
    growth_rate = 0.02  # 2% daily growth
    
    forecast = []
    for i in range(days_ahead):
        requests = int(avg_daily_requests * (1 + (i % 7) * seasonality_factor) * (1 + growth_rate * i))
        ...
```

### Customize Tier Limits

Modify `get_profile()`:

```python
return jsonify({
    'tier': 'Power',
    'tier_limit_requests_per_hour': 50000,  # Adjust
    'monthly_limit': 1000000,  # Adjust
    'monthly_cost': 225  # Subscription base cost
})
```

### Add Custom Alerts

Edit `get_alerts()` to return custom warnings:

```python
alerts = [
    {
        'type': 'approaching_limit',
        'message': f"You've used {usage_pct}% of your monthly limit",
        'severity': 'warning' if usage_pct > 75 else 'info'
    },
    {
        'type': 'recommended_upgrade',
        'message': 'Based on your growth, consider upgrading to Power tier',
        'severity': 'info'
    }
]
```

---

## Styling & Customization

### Theme Colors

```css
/* Primary gradient */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Adjust in DASHBOARD_HTML CSS */
--primary-color: #667eea;
--secondary-color: #764ba2;
--success-color: #4CAF50;
--warning-color: #FFC107;
```

### Chart Colors

```javascript
// Usage chart
borderColor: '#667eea',
backgroundColor: 'rgba(102, 126, 234, 0.1)',

// Forecast chart
backgroundColor: '#764ba2'
```

### Responsive Design

Already mobile-optimized with:
- Responsive grid layout
- Touch-friendly buttons
- Mobile-first CSS
- Tablet/desktop breakpoints

---

## Integration Examples

### Python Client

```python
import requests
import json

class CustomerAnalyticsClient:
    def __init__(self, token, base_url='http://localhost:8004'):
        self.token = token
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {token}'}
    
    def get_profile(self):
        return requests.get(f'{self.base_url}/api/customer/profile', 
                           headers=self.headers).json()
    
    def get_usage(self):
        return requests.get(f'{self.base_url}/api/customer/usage', 
                           headers=self.headers).json()
    
    def get_forecast(self):
        return requests.get(f'{self.base_url}/api/customer/forecast', 
                           headers=self.headers).json()

# Usage
client = CustomerAnalyticsClient(token='user_key_123')
profile = client.get_profile()
usage = client.get_usage()
forecast = client.get_forecast()
```

### JavaScript Integration

```javascript
const token = 'user_key_123';
const baseUrl = 'http://localhost:8004';

async function getUsageData() {
  const response = await fetch(`${baseUrl}/api/customer/usage`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
}

async function getForecast() {
  const response = await fetch(`${baseUrl}/api/customer/forecast`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
}

// Display in your app
getUsageData().then(data => {
  console.log('Usage:', data);
});
```

### Embed in Website

```html
<iframe 
  src="https://api.example.com:8004/?token=YOUR_TOKEN"
  width="100%"
  height="600"
  style="border: none; border-radius: 8px;"
></iframe>
```

---

## Deployment

### Production Setup

1. **Use Nginx reverse proxy** (SSL/TLS)
   ```nginx
   location /analytics {
       proxy_pass http://localhost:8004;
       proxy_set_header Authorization $http_authorization;
   }
   ```

2. **Deploy with Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8004 customer_analytics_ui:app
   ```

3. **Docker production image**
   ```dockerfile
   FROM python:3.11
   COPY customer_analytics_ui.py /app/
   COPY requirements.txt /app/
   RUN pip install -r /app/requirements.txt
   CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8004", "customer_analytics_ui:app"]
   ```

### AWS Deployment

```bash
# Push to ECR
aws ecr push customer-analytics-ui:latest

# Deploy to ECS
aws ecs create-service \
  --cluster prod \
  --service-name customer-analytics-ui \
  --task-definition customer-analytics-ui:1 \
  --desired-count 3
```

---

## Performance Optimization

### Caching Strategy

Add to `customer_analytics_ui.py`:

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@app.route('/api/customer/usage')
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_usage():
    ...
```

### Database Optimization

```sql
-- Index for fast user lookups
CREATE INDEX idx_customer_user_id ON customers(user_id);

-- Materialized view for daily aggregates
CREATE MATERIALIZED VIEW customer_daily_usage AS
SELECT 
  user_id,
  DATE(created_at) as date,
  COUNT(*) as requests,
  SUM(cost) as cost
FROM usage_logs
GROUP BY user_id, DATE(created_at);
```

---

## Monitoring

### Key Metrics

Track in Prometheus:

```prometheus
# Page load time
customer_ui_load_time_ms

# API response times
customer_ui_api_response_time_ms{endpoint="/api/customer/usage"}

# User sessions
customer_ui_active_sessions

# Errors
customer_ui_errors_total
```

### Alerts

```yaml
- alert: CustomerUILatency
  expr: customer_ui_api_response_time_ms > 1000
  for: 5m
  annotations:
    summary: "Customer UI API latency > 1 second"

- alert: CustomerUIErrors
  expr: rate(customer_ui_errors_total[5m]) > 0.01
  for: 5m
  annotations:
    summary: "Customer UI error rate > 1%"
```

---

## Testing

### Unit Tests

```python
import unittest
from customer_analytics_ui import app

class TestCustomerUI(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def test_get_usage(self):
        response = self.client.get('/api/customer/usage',
            headers={'Authorization': 'Bearer test_token_12345'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertIn('requests', data[0])

if __name__ == '__main__':
    unittest.main()
```

### Manual Testing

```bash
# Test with token
TOKEN="user_demo_key_123"

# Profile
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/customer/profile

# Usage
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/customer/usage

# Forecast
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/customer/forecast

# Export
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/customer/export > usage.csv
```

---

## Troubleshooting

### Dashboard Not Loading
- Check token is valid: `echo $TOKEN`
- Verify service is running: `curl http://localhost:8004/health`
- Check browser console for errors (F12)

### Charts Not Rendering
- Verify Chart.js loads: Check network tab
- Check console for JavaScript errors
- Ensure data API endpoints return valid JSON

### Data Not Updating
- Check API response: `curl -H "Authorization: Bearer $TOKEN" http://localhost:8004/api/customer/usage`
- Verify mock data is being generated
- Clear browser cache (Ctrl+Shift+R)

### Export File Not Downloading
- Check browser downloads folder
- Verify Content-Disposition header is set
- Try different browser if issue persists

---

## Future Enhancements

- [ ] **Advanced Reporting** - Custom date ranges, filters
- [ ] **Usage Alerts** - Email notifications when approaching limits
- [ ] **Team Management** - Multi-user access control
- [ ] **Payment History** - Detailed invoice details and payment records
- [ ] **API Keys Dashboard** - View and rotate API keys
- [ ] **Integration Logs** - Webhook delivery status and logs
- [ ] **Custom Dashboards** - User-defined widgets and layouts
- [ ] **Data Import** - Load historical data from external sources

---

**Version:** 1.0  
**Status:** Production Ready ✅  
**Location:** `/Users/alexa/blackroad/customer_analytics_ui.py`  
**Port:** 8004  
**Dependencies:** Flask, Flask-CORS, Chart.js (CDN)
