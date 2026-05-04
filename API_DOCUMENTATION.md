# BlackRoad API Documentation

**Complete OpenAPI/Swagger documentation for all 29 endpoints**

---

## Quick Start

### Viewing Documentation

1. **OpenAPI Spec** (machine-readable)
   ```bash
   cat openapi.json
   ```

2. **Swagger UI** (interactive web UI)
   ```bash
   # Option 1: Run locally
   python3 -m http.server 8888 &
   # Open http://localhost:8888/swagger-ui.html
   
   # Option 2: Use online Swagger Editor
   # https://editor.swagger.io → File → Import URL → (your openapi.json URL)
   ```

3. **Postman** (API testing)
   ```bash
   # Import BlackRoad_API_Postman.json into Postman
   # Set admin_token variable to your Bearer token
   ```

4. **VS Code** (with OpenAPI extension)
   ```bash
   # Install: openapi-designer extension
   # File → Open → openapi.json
   ```

---

## API Overview

### Three Services

| Service | Port | Purpose | Endpoints |
|---------|------|---------|-----------|
| **Billing API** | 8000 | Core usage tracking and billing | 4 |
| **Admin Dashboard** | 8001 | Business analytics and metrics | 18 |
| **Customer Analytics** | 8003 | Per-customer insights and reporting | 11 |

### Authentication

All endpoints (except `/status`) require Bearer token authentication:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/usage
```

**Token Sources:**
- Admin panel (when deployed)
- Environment variable `ADMIN_TOKEN`
- Clerk authentication service

---

## Billing API (Port 8000)

Base URL: `http://localhost:8000`

### 1. Record Charge

**Endpoint:** `POST /charge`

**Description:** Submit a charge for API usage. Automatically deducts from free tier, applies paid rate if needed.

**Request:**
```json
{
  "customer_id": "cust_123456",
  "amount": 5.00,
  "description": "100 API requests",
  "metadata": {
    "endpoint": "/api/analyze",
    "count": 100
  }
}
```

**Response (200):**
```json
{
  "charge_id": "charge_abc123",
  "customer_id": "cust_123456",
  "amount": 5.00,
  "timestamp": "2024-01-31T13:32:00Z",
  "billing_status": "charged"
}
```

**Error Cases:**
- `400`: Invalid customer_id or amount
- `401`: Missing/invalid Bearer token
- `402`: Payment required (quota exceeded, payment method invalid)

**Usage Example:**
```bash
curl -X POST http://localhost:8000/charge \
  -H "Authorization: Bearer token123" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust_123456",
    "amount": 5.00,
    "description": "API usage"
  }'
```

---

### 2. Get Usage

**Endpoint:** `GET /usage`

**Description:** Retrieve current month usage, quota limits, and billing status.

**Query Parameters:**
- `customer_id` (optional): Admin-only, retrieve usage for different customer

**Response (200):**
```json
{
  "customer_id": "cust_123456",
  "tier": "power",
  "current_month_usage": 1500000,
  "monthly_limit": 7200000,
  "free_tier_hours": 5.0,
  "free_tier_used": 3.25,
  "free_tier_remaining": 1.75,
  "paid_hours_used": 0.5,
  "current_rate": "$5/hour",
  "current_charges_month": 2.50,
  "next_charge_date": "2024-02-01",
  "reset_date": "2024-02-01",
  "quota_status": "active",
  "days_remaining": 2
}
```

**Usage Example:**
```bash
curl -H "Authorization: Bearer token123" \
  http://localhost:8000/usage
```

---

### 3. Manage Subscription

**Endpoint:** `POST /billing`

**Description:** Change subscription tier for customer.

**Request:**
```json
{
  "customer_id": "cust_123456",
  "tier": "power",
  "promo_code": "SAVE20"
}
```

**Response (200):**
```json
{
  "customer_id": "cust_123456",
  "tier": "power",
  "previous_tier": "light",
  "status": "tier_changed",
  "next_billing_date": "2024-02-01",
  "effective_date": "2024-01-31"
}
```

**Tier Options:**
- `free`: $0/month, 5 hours/month, 1.8M requests/month
- `light`: $25/month, unlimited requests
- `power`: $225/month, priority support
- `enterprise`: $975/month, SLA, custom limits

**Usage Example:**
```bash
curl -X POST http://localhost:8000/billing \
  -H "Authorization: Bearer token123" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust_123456",
    "tier": "power"
  }'
```

---

### 4. Health Check

**Endpoint:** `GET /status`

**Description:** Check system health (no auth required).

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "up",
  "cache": "up",
  "stripe": "connected",
  "latency_ms": 12,
  "timestamp": "2024-01-31T13:32:00Z"
}
```

**Usage Example:**
```bash
curl http://localhost:8000/status
```

---

## Admin Dashboard API (Port 8001)

Base URL: `http://localhost:8001`

**All endpoints require Bearer token (admin role)**

### Revenue Metrics

#### 1. Total Revenue

**Endpoint:** `GET /api/admin/revenue/total`

**Response:**
```json
{
  "total_revenue": 124500.50,
  "by_tier": {
    "free": 0,
    "light": 12500.00,
    "power": 56000.00,
    "enterprise": 56000.50
  },
  "currency": "USD"
}
```

---

#### 2. Daily Revenue Trend

**Endpoint:** `GET /api/admin/revenue/daily?days=30`

**Query Parameters:**
- `days`: 1-365, default 30

**Response:**
```json
{
  "period": "last_30_days",
  "data": [
    {
      "date": "2024-01-31",
      "revenue": 4150.25,
      "transactions": 23,
      "tier_breakdown": {
        "light": 500,
        "power": 2000,
        "enterprise": 1650.25
      }
    },
    ...
  ],
  "total_period_revenue": 124500.50
}
```

---

#### 3. Monthly Revenue Trend

**Endpoint:** `GET /api/admin/revenue/monthly?months=12`

**Query Parameters:**
- `months`: 1-36, default 12

**Response:**
```json
{
  "period": "last_12_months",
  "data": [
    {
      "month": "2024-01",
      "revenue": 125000,
      "mrr": 125000,
      "growth_percent": 5.2,
      "customer_count": 320
    },
    ...
  ],
  "average_monthly_revenue": 120000,
  "growth_trend": "positive"
}
```

---

#### 4. Annual Revenue Projection

**Endpoint:** `GET /api/admin/revenue/projection`

**Response:**
```json
{
  "daily_run_rate": 4150.25,
  "monthly_projection": 124500.00,
  "annual_projection": 1494000.00,
  "mrr": 124500.00,
  "arr": 1494000.00,
  "confidence": 0.85,
  "based_on_days": 31
}
```

---

### User Metrics

#### 5. Total Users by Tier

**Endpoint:** `GET /api/admin/users/total`

**Response:**
```json
{
  "total_users": 1250,
  "by_tier": {
    "free": 850,
    "light": 200,
    "power": 150,
    "enterprise": 50
  },
  "paying_users": 400,
  "paid_conversion_rate": 0.32
}
```

---

#### 6. Growth Metrics

**Endpoint:** `GET /api/admin/users/growth`

**Response:**
```json
{
  "period": "last_30_days",
  "daily_signups": 15,
  "daily_churn": 3,
  "net_growth": 12,
  "churn_rate": 0.24,
  "growth_rate": 0.96,
  "trend": [
    {"date": "2024-01-31", "signups": 15, "churn": 3},
    ...
  ]
}
```

---

#### 7. Conversion Rate

**Endpoint:** `GET /api/admin/users/conversion`

**Response:**
```json
{
  "paid_conversion_rate": 0.32,
  "free_tier_users": 850,
  "paid_tier_users": 400,
  "conversion_trend": [
    {"period": "2024-01", "rate": 0.28},
    {"period": "2024-02", "rate": 0.32}
  ],
  "best_converting_tier": "light"
}
```

---

#### 8. Churn Rate

**Endpoint:** `GET /api/admin/users/churn`

**Response:**
```json
{
  "monthly_churn_rate": 0.15,
  "churn_by_tier": {
    "free": 0.18,
    "light": 0.12,
    "power": 0.08,
    "enterprise": 0.05
  },
  "at_risk_count": 45,
  "churn_trend": [
    {"month": "2024-01", "rate": 0.15}
  ]
}
```

---

### Health Checks

#### 9. Database Health

**Endpoint:** `GET /api/admin/health/database`

**Response:**
```json
{
  "status": "healthy",
  "latency_ms": 8,
  "connections": {
    "active": 12,
    "idle": 5,
    "max": 50
  },
  "queries_per_second": 450,
  "last_check": "2024-01-31T13:32:00Z"
}
```

---

#### 10. Stripe Integration Health

**Endpoint:** `GET /api/admin/health/stripe`

**Response:**
```json
{
  "status": "connected",
  "account_id": "acct_1234567890",
  "api_version": "2023-10-16",
  "meter_events_month": 45000,
  "last_webhook": "2024-01-31T13:25:00Z",
  "sync_status": "current"
}
```

---

#### 11. Cache Health

**Endpoint:** `GET /api/admin/health/cache`

**Response:**
```json
{
  "status": "healthy",
  "memory_used_mb": 256,
  "memory_max_mb": 512,
  "keys_count": 1250,
  "hit_rate": 0.85,
  "evictions": 150
}
```

---

### Invoice Management

#### 12. Pending Invoices

**Endpoint:** `GET /api/admin/invoices/pending`

**Response:**
```json
{
  "count": 8,
  "total_amount": 4250.00,
  "invoices": [
    {
      "invoice_id": "inv_123",
      "customer_id": "cust_456",
      "amount": 500.00,
      "due_date": "2024-02-15",
      "days_overdue": 0,
      "status": "pending"
    }
  ]
}
```

---

#### 13. Failed Invoices

**Endpoint:** `GET /api/admin/invoices/failed`

**Response:**
```json
{
  "count": 3,
  "total_amount": 1500.00,
  "failed_invoices": [
    {
      "invoice_id": "inv_789",
      "customer_id": "cust_789",
      "amount": 500.00,
      "reason": "card_declined",
      "retry_count": 2,
      "next_retry": "2024-02-05"
    }
  ]
}
```

---

### Tier Management

#### 14. Tier Distribution

**Endpoint:** `GET /api/admin/tiers/distribution`

**Response:**
```json
{
  "free": {
    "users": 850,
    "revenue": 0,
    "percentage": 68
  },
  "light": {
    "users": 200,
    "revenue": 5000,
    "percentage": 16
  },
  "power": {
    "users": 150,
    "revenue": 33750,
    "percentage": 12
  },
  "enterprise": {
    "users": 50,
    "revenue": 48750,
    "percentage": 4
  }
}
```

---

#### 15. MRR by Tier

**Endpoint:** `GET /api/admin/tiers/mrr`

**Response:**
```json
{
  "total_mrr": 87500,
  "by_tier": {
    "free": 0,
    "light": 5000,
    "power": 33750,
    "enterprise": 48750
  },
  "growth_percent": 5.2,
  "trend": [
    {"month": "2024-01", "mrr": 83000},
    {"month": "2024-02", "mrr": 87500}
  ]
}
```

---

### Export

#### 16. Export Revenue Report

**Endpoint:** `GET /api/admin/export/revenue?format=json`

**Query Parameters:**
- `format`: `json` or `csv`, default `json`

**Response (JSON):**
```json
{
  "export_date": "2024-01-31T13:32:00Z",
  "period": "all_time",
  "data": [
    {
      "customer_id": "cust_123",
      "tier": "power",
      "total_revenue": 1500,
      "monthly_revenue": 225,
      "signup_date": "2024-01-01"
    }
  ]
}
```

**Response (CSV):**
```csv
customer_id,tier,total_revenue,monthly_revenue,signup_date
cust_123,power,1500,225,2024-01-01
cust_456,light,500,25,2024-01-15
```

---

## Customer Analytics API (Port 8003)

Base URL: `http://localhost:8003`

**All endpoints require Bearer token**

### Customer Management

#### 1. List Customers

**Endpoint:** `GET /api/customers?page=1&limit=50&tier=power&search=acme`

**Query Parameters:**
- `page`: 1-based, default 1
- `limit`: 1-500, default 50
- `tier`: filter by subscription tier
- `search`: search by email or company name

**Response:**
```json
{
  "data": [
    {
      "customer_id": "cust_123",
      "email": "alice@acme.com",
      "tier": "power",
      "total_revenue": 2250,
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1250,
  "page": 1,
  "limit": 50,
  "total_pages": 25
}
```

---

#### 2. Get Customer Profile

**Endpoint:** `GET /api/customers/{customer_id}`

**Response:**
```json
{
  "customer_id": "cust_123",
  "email": "alice@acme.com",
  "tier": "power",
  "status": "active",
  "signup_date": "2024-01-01T00:00:00Z",
  "total_revenue": 2250,
  "total_usage": 2250000,
  "lifetime_value": 2250,
  "monthly_spend": 225,
  "last_activity": "2024-01-31T13:25:00Z",
  "payment_method": "card",
  "days_since_signup": 30
}
```

---

### Customer Analysis

#### 3. Customer Revenue Analysis

**Endpoint:** `GET /api/customers/{customer_id}/revenue?months=12`

**Query Parameters:**
- `months`: 1-36, default 12

**Response:**
```json
{
  "customer_id": "cust_123",
  "total_revenue": 2250,
  "by_month": [
    {
      "month": "2024-01",
      "revenue": 225,
      "transactions": 5,
      "tier": "power"
    }
  ]
}
```

---

#### 4. Customer Usage Analysis

**Endpoint:** `GET /api/customers/{customer_id}/usage`

**Response:**
```json
{
  "customer_id": "cust_123",
  "total_requests": 2250000,
  "by_endpoint": [
    {
      "endpoint": "/api/analyze",
      "requests": 1500000,
      "percentage": 66.7
    }
  ],
  "by_month": [
    {
      "month": "2024-01",
      "requests": 750000
    }
  ]
}
```

---

#### 5. Customer Trends

**Endpoint:** `GET /api/customers/{customer_id}/trends`

**Response:**
```json
{
  "customer_id": "cust_123",
  "usage_trend": "increasing",
  "revenue_trend": "stable",
  "engagement_trend": "high",
  "churn_risk": "low",
  "forecast_next_month_revenue": 225
}
```

---

### Analytics & Insights

#### 6. Cohort Retention Analysis

**Endpoint:** `GET /api/analytics/cohorts?cohort_month=2024-01`

**Query Parameters:**
- `cohort_month`: optional, analyze specific signup month

**Response:**
```json
{
  "cohort": "2024-01",
  "size": 150,
  "retention": [
    {
      "month": 0,
      "retained": 150,
      "retention_rate": 1.0
    },
    {
      "month": 1,
      "retained": 120,
      "retention_rate": 0.80
    }
  ]
}
```

---

#### 7. Customer Segmentation

**Endpoint:** `GET /api/analytics/segmentation`

**Response:**
```json
{
  "vip": {
    "count": 12,
    "average_revenue": 3500,
    "criteria": "revenue > $1000"
  },
  "growing": {
    "count": 78,
    "average_revenue": 350,
    "criteria": "power/enterprise tier"
  },
  "at_risk": {
    "count": 850,
    "average_revenue": 0,
    "criteria": "free tier"
  },
  "inactive": {
    "count": 310,
    "average_revenue": 0,
    "criteria": "no activity 30+ days"
  }
}
```

---

#### 8. Churn Detection

**Endpoint:** `GET /api/analytics/churn`

**Response:**
```json
{
  "at_risk_count": 45,
  "customers": [
    {
      "customer_id": "cust_999",
      "email": "bob@xyz.com",
      "previous_tier": "power",
      "current_tier": "free",
      "downgrade_date": "2024-01-25",
      "last_activity": "2024-01-28"
    }
  ],
  "churn_rate": 0.15
}
```

---

#### 9. Platform Trends

**Endpoint:** `GET /api/analytics/trends`

**Response:**
```json
{
  "revenue_trend": {
    "direction": "up",
    "percent_change": 5.2,
    "data": [...]
  },
  "user_trend": {
    "direction": "up",
    "percent_change": 3.1,
    "data": [...]
  },
  "engagement_trend": {
    "direction": "stable",
    "percent_change": 0.0,
    "data": [...]
  }
}
```

---

## Integration Examples

### Python

```python
import requests
import json

BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = "your-bearer-token"

headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}",
    "Content-Type": "application/json"
}

# Record a charge
response = requests.post(
    f"{BASE_URL}/charge",
    headers=headers,
    json={
        "customer_id": "cust_123",
        "amount": 5.00,
        "description": "API usage"
    }
)
print(response.json())

# Get usage
response = requests.get(f"{BASE_URL}/usage", headers=headers)
print(response.json())
```

---

### JavaScript

```javascript
const ADMIN_TOKEN = "your-bearer-token";

async function getUsage() {
    const response = await fetch('http://localhost:8000/usage', {
        headers: {
            'Authorization': `Bearer ${ADMIN_TOKEN}`
        }
    });
    return response.json();
}

async function recordCharge(customerId, amount) {
    const response = await fetch('http://localhost:8000/charge', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${ADMIN_TOKEN}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            customer_id: customerId,
            amount: amount,
            description: 'API usage'
        })
    });
    return response.json();
}
```

---

### cURL

```bash
# Record charge
curl -X POST http://localhost:8000/charge \
  -H "Authorization: Bearer your-bearer-token" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust_123",
    "amount": 5.00,
    "description": "API usage"
  }'

# Get usage
curl http://localhost:8000/usage \
  -H "Authorization: Bearer your-bearer-token"

# Get admin revenue
curl http://localhost:8001/api/admin/revenue/total \
  -H "Authorization: Bearer your-bearer-token"

# List customers
curl "http://localhost:8003/api/customers?page=1&limit=50" \
  -H "Authorization: Bearer your-bearer-token"
```

---

## Error Handling

### Standard Error Response

```json
{
  "error": "invalid_request",
  "message": "Customer ID is required",
  "details": {
    "field": "customer_id",
    "reason": "missing_required_field"
  }
}
```

### Common Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Charge recorded, usage retrieved |
| 400 | Bad Request | Invalid customer_id, missing field |
| 401 | Unauthorized | Missing/invalid Bearer token |
| 402 | Payment Required | Quota exceeded, payment failed |
| 403 | Forbidden | Admin endpoint, insufficient permissions |
| 404 | Not Found | Customer doesn't exist |
| 429 | Rate Limited | Too many requests |
| 500 | Server Error | Database failure, internal error |

---

## Rate Limiting

- **Main API**: 1000 requests/minute
- **Admin API**: 500 requests/minute  
- **Analytics API**: 500 requests/minute

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 2024-01-31T14:00:00Z
```

---

## Performance Tips

1. **Pagination**: Always paginate customer lists (`limit` ≤ 500)
2. **Caching**: Admin endpoints include `Cache-Control: max-age=60` headers
3. **Batch Operations**: Use Admin API for bulk reporting instead of per-customer queries
4. **Date Filtering**: Specify date ranges to reduce response size
5. **Projection**: Request only needed fields (implement in v2)

---

## Documentation Files

- **openapi.json** - Machine-readable OpenAPI 3.0 specification
- **swagger-ui.html** - Interactive Swagger UI (local viewing)
- **BlackRoad_API_Postman.json** - Postman collection for testing
- **API_DOCUMENTATION.md** - This file (human-readable guide)

---

## Support

For API questions or issues:
1. Check this documentation
2. Review error messages and status codes
3. Check logs: `docker logs api`, `docker logs admin-dashboard`
4. Contact engineering@blackroad.com

---

**Version:** 1.0.0  
**Last Updated:** 2024-01-31  
**Status:** Production Ready ✅
