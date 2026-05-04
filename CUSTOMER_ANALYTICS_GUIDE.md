# Customer Analytics Dashboard Guide

## Overview

The Customer Analytics Dashboard provides detailed insights into individual customer behavior, usage patterns, and revenue contribution. All endpoints require Bearer token authentication.

**Base URL**: `http://localhost:8003/api/analytics`

**Authentication**: Add header: `Authorization: Bearer <ADMIN_TOKEN>`

**Port**: 8003

---

## Endpoints (11 total)

### 1. List Customers

**GET** `/customers`

List all customers with summary statistics.

**Parameters**:
- `limit` (optional): Results per page (1-1000, default: 100)
- `offset` (optional): Pagination offset (default: 0)
- `tier` (optional): Filter by tier (free, light, power, enterprise)
- `sort_by` (optional): Sort field (created_at, revenue, usage)

**Response**:
```json
{
  "total": 10523,
  "limit": 100,
  "offset": 0,
  "customers": [
    {
      "customer_id": "cust_001",
      "stripe_id": "stripe_cust_123",
      "created_at": "2024-01-01T00:00:00",
      "tier": "enterprise",
      "charge_count": 450,
      "total_revenue_usd": 8500.00,
      "avg_charge_usd": 18.89,
      "current_month_usage": 125000
    }
  ]
}
```

**Use Cases**:
- Find high-value customers (sort by revenue)
- Identify power users (sort by usage)
- Segment customers by tier
- Export for email campaigns

**Examples**:

```bash
# Top 10 customers by revenue
curl -H "Authorization: Bearer <TOKEN>" \
  "http://localhost:8003/api/analytics/customers?limit=10&sort_by=revenue"

# Filter enterprise customers
curl -H "Authorization: Bearer <TOKEN>" \
  "http://localhost:8003/api/analytics/customers?tier=enterprise&limit=50"

# Get page 2 (offset by 100)
curl -H "Authorization: Bearer <TOKEN>" \
  "http://localhost:8003/api/analytics/customers?limit=100&offset=100"
```

---

### 2. Get Customer Profile

**GET** `/customer/{customer_id}/profile`

Get detailed profile for a specific customer.

**Response**:
```json
{
  "customer_id": "cust_001",
  "stripe_id": "stripe_cust_123",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-31T12:00:00",
  "tier": "enterprise",
  "tier_updated_at": "2024-01-15T10:30:00",
  "metrics": {
    "total_charges": 450,
    "total_revenue_usd": 8500.00,
    "current_month_usage": 125000,
    "monthly_limit": 259200000
  }
}
```

**Use Cases**:
- View complete customer history
- Check current tier and usage
- Analyze customer lifetime value
- Track tier upgrade/downgrade dates

---

### 3. Get Customer Revenue History

**GET** `/customer/{customer_id}/revenue`

Get revenue breakdown over time.

**Parameters**:
- `days` (optional): Look back period (1-365, default: 90)

**Response**:
```json
{
  "customer_id": "cust_001",
  "period_days": 90,
  "total_revenue_usd": 8500.00,
  "daily_breakdown": [
    {
      "date": "2024-01-01",
      "revenue_usd": 50.00,
      "charge_count": 5
    },
    {
      "date": "2024-01-02",
      "revenue_usd": 75.50,
      "charge_count": 7
    }
  ]
}
```

**Use Cases**:
- Identify spending patterns
- Detect customer activation events
- Analyze revenue growth over time
- Find seasonal patterns

---

### 4. Get Customer Usage

**GET** `/customer/{customer_id}/usage`

Get current month usage and quota status.

**Response**:
```json
{
  "customer_id": "cust_001",
  "year_month": "2024-01",
  "current_month_usage": 125000,
  "monthly_limit_requests": 259200000,
  "soft_limit_requests": 207360000,
  "hard_limit_requests": 259200000,
  "usage_percent": 48.2,
  "remaining": 134200000,
  "status": "active",
  "reset_date": "2024-02-01"
}
```

**Status Values**:
- `active`: < 90% usage
- `near_limit`: 90-100% usage (warn customer)
- `exceeded`: > 100% usage (enforce limits)

**Use Cases**:
- Check if customer is near quota
- Send usage warnings
- Identify power users approaching limits
- Track compliance with SLA

---

### 5. Get Customer Trend

**GET** `/customer/{customer_id}/trend`

Get customer trend data (revenue, usage, or charges over time).

**Parameters**:
- `metric` (optional): Trend metric (revenue, usage, charges)

**Response (Revenue)**:
```json
{
  "customer_id": "cust_001",
  "metric": "revenue",
  "trend": [
    {
      "period": "2024-01-01",
      "value": 150.00
    },
    {
      "period": "2024-01-08",
      "value": 250.00
    }
  ]
}
```

**Use Cases**:
- Visualize customer growth trajectory
- Predict churn risk (declining revenue/usage)
- Identify expansion opportunities
- Plan upsell campaigns

---

### 6. Get Customer Cohorts

**GET** `/cohorts`

Analyze customers by signup cohort.

**Response**:
```json
{
  "cohorts": [
    {
      "cohort_month": "2024-01-01",
      "cohort_size": 245,
      "avg_revenue_per_user": 34.67
    },
    {
      "cohort_month": "2023-12-01",
      "cohort_size": 189,
      "avg_revenue_per_user": 48.92
    }
  ]
}
```

**Insights**:
- Compare cohort quality
- Identify best-performing onboarding periods
- Track revenue curve maturation
- Forecast revenue from new cohorts

---

### 7. Get Cohort Retention

**GET** `/cohort/{cohort_month}/retention`

Analyze retention rate for a specific cohort.

**Parameters**:
- `cohort_month`: Month in format YYYY-MM (e.g., "2024-01")

**Response**:
```json
{
  "cohort_month": "2024-01",
  "cohort_size": 245,
  "retention": [
    {
      "month_offset": 0,
      "active_customers": 245,
      "retention_rate": 100.0
    },
    {
      "month_offset": 1,
      "active_customers": 183,
      "retention_rate": 74.7
    },
    {
      "month_offset": 2,
      "active_customers": 165,
      "retention_rate": 67.3
    }
  ]
}
```

**Benchmark**:
- Month 1: 70-80% retention (healthy)
- Month 3: 50-60% retention (healthy)
- Month 6: 40-50% retention (healthy)

**Use Cases**:
- Identify weak cohorts
- Compare retention across periods
- Forecast churn
- Plan retention campaigns

---

### 8. Get Customer Segments

**GET** `/segments`

Analyze customer distribution across segments.

**Response**:
```json
{
  "total_customers": 10523,
  "segments": [
    {
      "name": "VIP",
      "description": "High value customers (> $1000 total revenue)",
      "count": 189,
      "percentage": 1.8
    },
    {
      "name": "Growing",
      "description": "Power and Enterprise tier users",
      "count": 650,
      "percentage": 6.2
    },
    {
      "name": "At Risk",
      "description": "Free tier users (high churn risk)",
      "count": 8234,
      "percentage": 78.3
    },
    {
      "name": "Inactive",
      "description": "No charges in last 30 days",
      "count": 1450,
      "percentage": 13.8
    }
  ]
}
```

**Typical Distribution**:
- VIP: 1-2% (highest value)
- Growing: 5-10% (future VIP candidates)
- At Risk: 70-80% (free tier)
- Inactive: 10-20% (churned or sleeping)

**Use Cases**:
- Target VIP for upsell/retention
- Nurture Growing segment
- Engage At Risk with discounts
- Re-activate Inactive customers

---

### 9. Get Churn Risk Customers

**GET** `/churn-risk`

Identify customers at high risk of churning.

**Response**:
```json
{
  "at_risk_count": 15,
  "at_risk_customers": [
    {
      "customer_id": "cust_002",
      "current_tier": "free",
      "downgraded_at": "2024-01-15T10:30:00",
      "last_revenue_usd": 150.00
    }
  ]
}
```

**Criteria** (downgraded to free in last 30 days):
- Previously paid customer
- Recently downgraded tier
- Last 30 days activity

**Actions**:
- Send win-back email
- Offer special discount
- Request feedback
- Assign to sales team

---

## Integration Examples

### JavaScript/React

```javascript
// Fetch customer list
async function getCustomers(tier = null, sortBy = 'revenue') {
  const token = localStorage.getItem('adminToken');
  const params = new URLSearchParams({
    limit: 100,
    offset: 0,
    ...(tier && { tier }),
    sort_by: sortBy,
  });
  
  const response = await fetch(
    `http://localhost:8003/api/analytics/customers?${params}`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  return response.json();
}

// Get customer profile
async function getCustomerProfile(customerId) {
  const token = localStorage.getItem('adminToken');
  const response = await fetch(
    `http://localhost:8003/api/analytics/customer/${customerId}/profile`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  return response.json();
}

// Render customer list
async function showCustomers() {
  const customers = await getCustomers('enterprise', 'revenue');
  const html = customers.customers.map(c => `
    <tr>
      <td>${c.customer_id}</td>
      <td>${c.tier}</td>
      <td>$${c.total_revenue_usd.toFixed(2)}</td>
      <td>${c.charge_count}</td>
      <td>${c.current_month_usage}</td>
    </tr>
  `).join('');
  
  document.getElementById('customers-table').innerHTML = html;
}
```

### Python

```python
import requests

class CustomerAnalytics:
    def __init__(self, base_url='http://localhost:8003/api/analytics', token=None):
        self.base_url = base_url
        self.token = token or os.getenv('ADMIN_TOKEN')
        self.headers = {'Authorization': f'Bearer {self.token}'}
    
    def list_customers(self, tier=None, sort_by='revenue', limit=100):
        params = {'limit': limit, 'sort_by': sort_by}
        if tier:
            params['tier'] = tier
        
        resp = requests.get(
            f'{self.base_url}/customers',
            params=params,
            headers=self.headers
        )
        return resp.json()
    
    def get_customer_profile(self, customer_id):
        resp = requests.get(
            f'{self.base_url}/customer/{customer_id}/profile',
            headers=self.headers
        )
        return resp.json()
    
    def get_revenue_history(self, customer_id, days=90):
        resp = requests.get(
            f'{self.base_url}/customer/{customer_id}/revenue',
            params={'days': days},
            headers=self.headers
        )
        return resp.json()

# Usage
analytics = CustomerAnalytics()
top_customers = analytics.list_customers(sort_by='revenue', limit=10)
for customer in top_customers['customers']:
    profile = analytics.get_customer_profile(customer['customer_id'])
    print(f"Customer: {profile['customer_id']}, Revenue: ${profile['metrics']['total_revenue_usd']}")
```

### cURL

```bash
# List top enterprise customers by revenue
curl -H "Authorization: Bearer <TOKEN>" \
  "http://localhost:8003/api/analytics/customers?tier=enterprise&sort_by=revenue&limit=10"

# Get customer profile
curl -H "Authorization: Bearer <TOKEN>" \
  "http://localhost:8003/api/analytics/customer/cust_001/profile"

# Get revenue history (last 6 months)
curl -H "Authorization: Bearer <TOKEN>" \
  "http://localhost:8003/api/analytics/customer/cust_001/revenue?days=180"

# Get usage status
curl -H "Authorization: Bearer <TOKEN>" \
  "http://localhost:8003/api/analytics/customer/cust_001/usage"

# Get customer segments
curl -H "Authorization: Bearer <TOKEN>" \
  "http://localhost:8003/api/analytics/segments"

# Get churn risk customers
curl -H "Authorization: Bearer <TOKEN>" \
  "http://localhost:8003/api/analytics/churn-risk"
```

---

## Use Cases

### Sales: Finding Expansion Opportunities

```python
# Find customers ready to upgrade
analytics = CustomerAnalytics()
growing = analytics.list_customers(tier='power', sort_by='revenue', limit=50)

for customer in growing['customers']:
    if customer['total_revenue_usd'] > 500:
        profile = analytics.get_customer_profile(customer['customer_id'])
        print(f"Expansion candidate: {customer['customer_id']} (${customer['total_revenue_usd']})")
```

### Product: Identifying Feature Requests

```python
# Find power users (high usage, low cost impact)
analytics = CustomerAnalytics()
all_customers = analytics.list_customers(sort_by='usage', limit=100)

power_users = [
    c for c in all_customers['customers']
    if c['current_month_usage'] > 200000
]

print(f"Found {len(power_users)} power users to contact for feedback")
```

### Support: Proactive Customer Health

```python
# Check for at-risk customers
churn_risk = analytics.churn_risk()

for customer in churn_risk['at_risk_customers']:
    profile = analytics.get_customer_profile(customer['customer_id'])
    print(f"At-risk: {customer['customer_id']} (downgraded from {customer['last_revenue_usd']})")
```

### Executives: Business Insights

```python
# Cohort analysis
cohorts = analytics.get_customer_cohorts()

for cohort in cohorts['cohorts']:
    retention = analytics.get_cohort_retention(cohort['cohort_month'])
    print(f"Cohort {cohort['cohort_month']}: {cohort['cohort_size']} users, "
          f"${cohort['avg_revenue_per_user']:.2f} ARU")
```

---

## Performance Tips

### Optimize Queries

1. **Use pagination for large datasets**:
   ```bash
   # Good (paginated)
   curl "...?limit=100&offset=0"
   
   # Bad (all at once)
   curl "...?limit=10000"
   ```

2. **Filter before fetching**:
   ```bash
   # Good (filter on server)
   curl "...?tier=enterprise&sort_by=revenue"
   
   # Bad (fetch all then filter)
   curl "...?limit=10000" | grep enterprise
   ```

3. **Cache frequently accessed data**:
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def get_customer_profile(customer_id):
       return analytics.get_customer_profile(customer_id)
   ```

---

## Production Deployment

1. **Update docker-compose.yml** with analytics service:

```yaml
analytics:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: blackroad-analytics
  ports:
    - "8003:8003"
  environment:
    ADMIN_TOKEN: ${ADMIN_TOKEN}
  command: python3 customer_analytics.py
  depends_on:
    admin-dashboard:
      condition: service_healthy
```

2. **Start the service**:

```bash
docker-compose up -d analytics
```

3. **Test endpoint**:

```bash
curl -H "Authorization: Bearer <TOKEN>" \
  http://localhost:8003/api/analytics/ping
```

---

## Troubleshooting

### "Customer not found"

- Verify customer_id is correct
- Check customer exists in database
- May need to wait for sync from Stripe

### No usage data

- Check MonthlyUsage table
- Verify year_month format
- Usage only tracked if API called

### Cohort retention always shows 100%

- Ensure database has at least 2 months of history
- Check Charge table has records
- Verify year_month calculations

---

## Support

For questions about the Customer Analytics Dashboard:

1. Check MONITORING_GUIDE.md for related metrics
2. Check ADMIN_DASHBOARD_GUIDE.md for revenue/user analytics
3. Review alert_rules.yml for automated alerts
4. Contact: engineering@blackroad.com

