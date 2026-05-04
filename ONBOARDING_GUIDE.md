# Customer Onboarding Service - Production Guide

**Version:** 1.0  
**Service Port:** 8007  
**Status:** ✅ Production Ready  
**Features:** Multi-step signup, email verification, welcome sequence

---

## 🎯 Overview

Complete customer onboarding system with:
- ✅ Multi-step signup flow (email → profile → tier → completion)
- ✅ Email verification with token-based links
- ✅ Automated welcome email sequence (3 emails)
- ✅ Progress tracking & completion metrics
- ✅ Onboarding analytics & conversion tracking
- ✅ Resource recommendations (guides, tutorials, docs)
- ✅ Integration-ready (webhook events, email providers)

---

## 📊 Onboarding Steps

```
1. SIGNUP (0%)
   └─ Collect: email, first_name, last_name, company

2. EMAIL_VERIFICATION (25%)
   └─ Send verification email with 24-hour token link

3. PROFILE (50%)
   └─ Display onboarding dashboard
   └─ Show feature walkthrough

4. PLAN_SELECTION (50%)
   └─ Choose tier (free/starter/pro/enterprise)

5. PAYMENT (75%)
   └─ Add payment method (if paid tier)

6. FIRST_API_KEY (75%)
   └─ Generate API key
   └─ Show integration examples

7. FIRST_REQUEST (85%)
   └─ Make first API call
   └─ Celebrate success

8. COMPLETED (100%)
   └─ Full platform access
   └─ Send completion email
```

---

## 📧 Email Sequence

### Email 1: Verification Email
- **Trigger:** Signup
- **Content:** Verify email button, 24-hour expiry
- **Goal:** Confirm email ownership

### Email 2: Welcome Email
- **Trigger:** Email verification complete
- **Content:** Welcome to tier, quick start links
- **Goal:** Get user to dashboard

### Email 3: First Steps (Day 1)
- **Trigger:** 1 hour after signup
- **Content:** API basics, code examples, docs links
- **Goal:** Encourage first API call

### Optional: Day 3 Onboarding Email
- **Trigger:** 3 days after signup
- **Content:** Advanced features, best practices
- **Goal:** Reduce churn for inactive users

---

## 🔌 API Endpoints (5 new)

### 1. Start Signup
```bash
POST /api/onboarding/start
Content-Type: application/json

{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "company": "Acme Inc"
}
```

**Response:**
```json
{
  "status": "signup_started",
  "onboarding_id": "onb_123abc",
  "email": "user@example.com",
  "next_step": "email_verification",
  "message": "Verification email sent"
}
```

### 2. Verify Email
```bash
POST /api/onboarding/verify-email
Content-Type: application/json

{
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:**
```json
{
  "status": "email_verified",
  "onboarding_id": "onb_123abc",
  "email": "user@example.com",
  "name": "John Doe",
  "next_step": "profile",
  "progress": 25
}
```

### 3. Complete Profile
```bash
POST /api/onboarding/complete-profile
Authorization: Bearer API_KEY
Content-Type: application/json

{
  "onboarding_id": "onb_123abc",
  "tier": "starter"
}
```

**Response:**
```json
{
  "status": "profile_completed",
  "onboarding_id": "onb_123abc",
  "tier": "starter",
  "next_step": "create_api_key",
  "progress": 50
}
```

### 4. Get Progress
```bash
GET /api/onboarding/progress?onboarding_id=onb_123abc
Authorization: Bearer API_KEY
```

**Response:**
```json
{
  "onboarding_id": "onb_123abc",
  "email": "user@example.com",
  "name": "John Doe",
  "tier": "starter",
  "current_step": "plan_selection",
  "progress": 50,
  "email_verified": true,
  "completed": false,
  "started_at": "2026-05-04T14:00:00Z",
  "completed_at": null
}
```

### 5. Get Resources
```bash
GET /api/onboarding/resources?step=profile
```

**Response:**
```json
{
  "resources": [
    {
      "id": "res_1",
      "title": "Getting Started",
      "description": "Learn the basics of BlackRoad",
      "type": "guide",
      "url": "https://docs.blackroad.io/getting-started",
      "step": "profile"
    }
  ],
  "count": 4
}
```

### 6. Get Analytics
```bash
GET /api/onboarding/analytics?days=30
Authorization: Bearer ADMIN_TOKEN
```

**Response:**
```json
{
  "period_days": 30,
  "signups": 145,
  "verified_emails": 132,
  "completed": 98,
  "verification_rate": 91.0,
  "completion_rate": 67.6
}
```

---

## 🗄️ Database Schema

### onboarding_profiles
```sql
CREATE TABLE onboarding_profiles (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    user_id TEXT,
    first_name TEXT,
    last_name TEXT,
    company TEXT,
    tier TEXT DEFAULT 'free',
    current_step TEXT,
    progress INT,
    email_verified BOOLEAN,
    email_verified_at TIMESTAMP,
    welcome_email_sent BOOLEAN,
    onboarding_email_1_sent BOOLEAN,
    onboarding_email_2_sent BOOLEAN,
    onboarding_email_3_sent BOOLEAN,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP
);
```

### email_verification_tokens
```sql
CREATE TABLE email_verification_tokens (
    id TEXT PRIMARY KEY,
    onboarding_id TEXT,
    token TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP,
    FOREIGN KEY (onboarding_id) REFERENCES onboarding_profiles(id)
);
```

### onboarding_steps
```sql
CREATE TABLE onboarding_steps (
    id TEXT PRIMARY KEY,
    onboarding_id TEXT,
    step TEXT NOT NULL,
    completed_at TIMESTAMP,
    data JSONB,
    UNIQUE(onboarding_id, step)
);
```

---

## 📈 Conversion Funnel

**Typical Metrics (30 days):**
- Signups: 100
- Email Verified: 91 (91%)
- Tier Selected: 85 (85%)
- API Key Created: 72 (72%)
- First API Call: 58 (58%)
- Completed Onboarding: 45 (45%)

**Optimization Targets:**
- Email verification: >90%
- Tier selection: >80%
- First API call: >60%
- Completion: >50%

---

## 🚀 Deployment

### Environment Variables
```bash
# .env
DATABASE_URL=postgresql://user:pass@host:5432/db
ADMIN_TOKEN=your-secure-token

# Email (optional - dry run mode if not set)
SEND_EMAILS=false  # Set to true in production
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.your_key
```

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY onboarding_service.py .
EXPOSE 8007

CMD ["python", "onboarding_service.py"]
```

### Docker Compose
```yaml
onboarding:
  build: .
  ports:
    - "8007:8007"
  environment:
    - DATABASE_URL=postgresql://blackroad:dev-password@postgres:5432/blackroad_dev
    - ADMIN_TOKEN=${ADMIN_TOKEN}
    - SEND_EMAILS=${SEND_EMAILS:-false}
  depends_on:
    - postgres
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8007/api/onboarding/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

---

## 📧 Email Templates

### Verification Email Template
```html
<h2>Welcome, {{first_name}}!</h2>

<p>Thanks for signing up to BlackRoad. Click the link below to verify your email:</p>

<a href="{{verify_link}}" style="background: #007bff; color: white; padding: 12px 30px; text-decoration: none;">
  Verify Email
</a>

<p>This link expires in 24 hours.</p>
```

### Welcome Email Template
```html
<h2>🎉 Welcome to BlackRoad {{tier}} Plan!</h2>

<p>You're all set. Here's what to do next:</p>

<ul>
  <li><a href="https://app.blackroad.io/dashboard">View your dashboard</a></li>
  <li><a href="https://docs.blackroad.io/getting-started">Read getting started guide</a></li>
  <li><a href="https://app.blackroad.io/settings/api">Create your first API key</a></li>
</ul>
```

---

## 🧪 Testing

### Manual Testing
```bash
# 1. Start signup
curl -X POST http://localhost:8007/api/onboarding/start \
  -d '{
    "email": "test@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "company": "Test Inc"
  }'

# 2. Get token from email (dry-run mode)
# Token will be in logs: "Verification email sent to test@example.com (token: ...)"

# 3. Verify email
curl -X POST http://localhost:8007/api/onboarding/verify-email \
  -d '{"token": "YOUR_TOKEN"}'

# 4. Complete profile
curl -X POST http://localhost:8007/api/onboarding/complete-profile \
  -H "Authorization: Bearer test-api-key" \
  -d '{
    "onboarding_id": "onb_123",
    "tier": "starter"
  }'

# 5. Check progress
curl http://localhost:8007/api/onboarding/progress?onboarding_id=onb_123 \
  -H "Authorization: Bearer test-api-key"
```

### Load Testing
```bash
# Simulate 100 concurrent signups
ab -n 100 -c 10 \
  -H "Content-Type: application/json" \
  -p signup_payload.json \
  http://localhost:8007/api/onboarding/start
```

---

## 📊 Monitoring

### Key Metrics
- **Signup rate** (per day)
- **Email verification rate** (should be >90%)
- **Tier selection rate** (should be >80%)
- **Completion rate** (goal: >50%)
- **Time to completion** (should be <24 hours)
- **Churn rate** (users who never complete)

### Alerts
- Email verification rate drops below 85%
- Completion rate drops below 40%
- More than 5 failed email sends in 1 hour
- Verification token expiry rate >10%

---

## 🔐 Security

- ✅ Email verification tokens are cryptographically secure (secrets.token_urlsafe)
- ✅ Tokens expire after 24 hours
- ✅ Tokens are one-time use (marked as used after verification)
- ✅ API endpoints require bearer token auth
- ✅ Passwords not stored during onboarding (delegated to auth provider)
- ✅ SMTP credentials stored in environment (not in code)

---

## 🐛 Troubleshooting

### Issue: Verification emails not sending
**Solution:**
- Check `SEND_EMAILS=true` in environment
- Verify SMTP credentials
- Check email provider logs (SendGrid, etc.)
- In development, use dry-run mode (default) - tokens logged to console

### Issue: High bounce rate on emails
**Solution:**
- Verify sender email domain is authenticated
- Check SPF/DKIM/DMARC records
- Use email provider's templates
- Test with real email addresses

### Issue: Users not completing onboarding
**Solution:**
- Analyze drop-off in funnel
- Check email delivery rate
- Review resources (docs/guides) quality
- Simplify signup form (fewer required fields)

---

## 🔄 Integration Examples

### Link to Onboarding in Auth Provider
```javascript
// After successful signup in Clerk/Auth0
const onboardingId = response.userId;
window.location.href = `/onboarding?id=${onboardingId}`;
```

### Trigger in Welcome Email
```python
# After tier selection
db.update_step(
    onboarding_id,
    "plan_selection",
    50,
    {"tier": "starter"}
)

# Send welcome email
email_service.send_welcome_email(email, first_name, tier)

# Fire webhook event (for CRM)
webhook_client.trigger("onboarding.tier_selected", {
    "onboarding_id": onboarding_id,
    "tier": tier
})
```

### Create User in Main DB
```python
# After onboarding completion
user = create_user(
    email=profile['email'],
    first_name=profile['first_name'],
    last_name=profile['last_name'],
    company=profile['company'],
    tier=profile['tier']
)

# Link onboarding to user
db.update_profile(onboarding_id, user_id=user.id)
```

---

## 📚 Next Steps

1. **Connect Email Provider**
   - Set up SendGrid/Mailgun account
   - Configure SMTP credentials
   - Set `SEND_EMAILS=true`

2. **Build Onboarding UI**
   - Create signup form (email, name)
   - Verify email page (token input)
   - Profile setup page (tier selection)
   - Success celebration page

3. **Setup Analytics Tracking**
   - Track page views
   - Track form submissions
   - Track completion events
   - Connect to Mixpanel/Segment

4. **Create Welcome Content**
   - Record video walkthrough
   - Create getting started guide
   - Prepare code examples
   - Build tutorial library

5. **Monitor Funnel**
   - Daily review of conversion rates
   - Identify drop-off points
   - A/B test email subject lines
   - Optimize based on data

---

**Status:** ✅ Production Ready  
**Last Updated:** 2026-05-04  
**Maintainer:** BlackRoad Onboarding Team
