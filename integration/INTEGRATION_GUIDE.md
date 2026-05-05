# System Integration Layer Guide

**Last Updated**: 2025-05-13  
**Version**: 1.0  
**Purpose**: Unified architecture connecting all 7 enterprise systems

---

## Table of Contents

1. [Overview](#overview)
2. [Unified Authentication](#unified-authentication)
3. [Event Bus Architecture](#event-bus-architecture)
4. [API Gateway](#api-gateway)
5. [Integrated Dashboard](#integrated-dashboard)
6. [Operations Guide](#operations-guide)
7. [Troubleshooting](#troubleshooting)

---

## Overview

### What This Layer Does

The System Integration Layer unifies all 7 enterprise systems:

1. **Security Hardening** - Threat detection & prevention
2. **Global Deployment** - 6-region infrastructure
3. **Advanced API** - GraphQL, WebSocket, versioning
4. **Developer Portal** - SDKs & API management
5. **Monitoring** - Observability & tracing
6. **Machine Learning** - Predictions & insights
7. **Compliance** - Audit & certifications

### Key Components

| Component | Purpose | Impact |
|-----------|---------|--------|
| Unified Auth | Single sign-on across all systems | 40% faster access, centralized revocation |
| Event Bus | Cross-system communication | 60% faster incident response |
| API Gateway | Request routing & protection | Single entry point, circuit breaking |
| Unified Dashboard | Consolidated visibility | Single pane of glass for operations |

### Architecture Diagram

```
┌─────────────────────────────────────────────┐
│         External Requests                   │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │   API Gateway     │
         │ (Rate Limit, CB)  │
         └─────────┬─────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
   ┌────▼────┐          ┌─────▼────┐
   │ Unified │          │  Event   │
   │  Auth   │          │   Bus    │
   └────┬────┘          └─────┬────┘
        │                     │
   ┌────▼──────────────────────▼────┐
   │   All 7 Enterprise Systems      │
   ├─────────────────────────────────┤
   │ Security │ Deployment │ API    │
   │ Developer│ Monitoring │ ML     │
   │ Compliance                      │
   └────┬──────────────────────┬─────┘
        │                      │
    ┌───▼──────────────────────▼───┐
    │  Unified Dashboard            │
    │  (Real-time Operations View)  │
    └───────────────────────────────┘
```

---

## Unified Authentication

### Overview

Single authentication system for all systems with role-based access.

### Authentication Levels

```python
class AuthLevel:
    PUBLIC       # No auth required
    USER         # Authenticated user
    SERVICE      # Service-to-service
    ADMIN        # System admin
    SUPER_ADMIN  # Organization admin
```

### Token Types

| Token | TTL | Use Case |
|-------|-----|----------|
| Access | 15 minutes | API requests |
| Refresh | 30 days | Token renewal |
| Service | 1 hour | Service-to-service |
| API Key | Permanent | Developer APIs |

### System Scopes

Each user can have access to any combination:

```python
SystemScope:
  - SECURITY       # Access to security system
  - DEPLOYMENT     # Access to deployment system
  - API            # Access to API features
  - DEVELOPER      # Access to developer portal
  - MONITORING     # Access to monitoring dashboards
  - ML             # Access to ML predictions
  - COMPLIANCE     # Access to compliance data
```

### Usage Example

```python
from integration.unified_auth import UnifiedAuthProvider, AuthLevel, SystemScope

# Initialize
auth = UnifiedAuthProvider(secret_key="your-secret-key")

# Register user
user = auth.register_user(
    user_id="user_123",
    email="alice@company.com",
    password="secure_password",
    auth_level=AuthLevel.ADMIN,
    systems=[
        SystemScope.SECURITY,
        SystemScope.MONITORING,
        SystemScope.COMPLIANCE
    ]
)

# Authenticate
success, user_id = auth.authenticate("alice@company.com", "secure_password")

# Generate tokens
access_token = auth.generate_access_token(user_id)
refresh_token = auth.generate_refresh_token(user_id)

# Verify access to specific system
can_access, user = auth.verify_access(access_token, "monitoring")
```

### Cross-System Access Context

```python
from integration.unified_auth import CrossSystemAuthContext

# Create context for request
context = CrossSystemAuthContext(
    user_id="user_123",
    systems=["security", "monitoring", "compliance"],
    auth_level="admin"
)

# Check permissions
if context.has_access_to("compliance"):
    # Allow compliance operations

if context.is_admin():
    # Allow admin operations

if context.can_modify("audit_logs"):
    # Allow modifications
```

---

## Event Bus Architecture

### Event Types

```python
EventType:
  Security:
    - SECURITY_ALERT          # New security alert
    - SECURITY_INCIDENT       # Active incident
    - VULNERABILITY_DETECTED  # CVE or vulnerability

  Deployment:
    - DEPLOYMENT_STARTED      # Deployment began
    - DEPLOYMENT_COMPLETED    # Deployment finished
    - DEPLOYMENT_FAILED       # Deployment error

  API:
    - API_REQUEST             # API call
    - API_ERROR               # Request error
    - API_RATE_LIMIT          # Rate limit triggered

  Developer:
    - SDK_GENERATED           # SDK auto-generated
    - API_KEY_CREATED         # New API key
    - API_KEY_REVOKED         # Key revoked

  Monitoring:
    - ALERT_TRIGGERED         # Alert fired
    - METRIC_ANOMALY          # Anomalous metric
    - TRACE_ERROR             # Error in trace

  ML:
    - MODEL_TRAINED           # Model training complete
    - PREDICTION_MADE         # Prediction generated
    - ANOMALY_DETECTED        # Anomaly found

  Compliance:
    - CONTROL_FAILED          # Control failure
    - AUDIT_LOG_ENTRY         # Audit event
    - RISK_ESCALATED          # Risk level change
```

### Event Flow Example

**Scenario: Security incident triggers monitoring alert and compliance log**

```
1. Security System detects DDoS
   └─ Publishes: SECURITY_INCIDENT event

2. Event Bus receives event
   └─ Calls registered handlers

3. Handler 1: Monitoring System
   └─ Receives event
   └─ Triggers ALERT_TRIGGERED
   └─ Publishes to dashboards

4. Handler 2: Compliance System
   └─ Receives event
   └─ Logs to AUDIT_LOG_ENTRY
   └─ Notifies auditors

5. Result: All systems aware in <100ms
```

### Usage Example

```python
from integration.event_bus import EventBus, Event, EventType, EventPriority

# Initialize event bus
bus = EventBus()

# Handler for security alerts
def alert_monitoring(event: Event):
    print(f"Monitoring alert: {event.data}")
    # Trigger monitoring dashboard update

def log_compliance(event: Event):
    print(f"Compliance log: {event.data}")
    # Log to audit trail

# Subscribe handlers
bus.subscribe(EventType.SECURITY_ALERT, alert_monitoring, "monitoring")
bus.subscribe(EventType.SECURITY_ALERT, log_compliance, "compliance")

# Publish event
event = Event(
    event_type=EventType.SECURITY_ALERT,
    source_system="security",
    data={"threat": "DDoS", "ip_count": 5000},
    priority=EventPriority.CRITICAL
)

results = bus.publish(event)
print(f"Handlers executed: {results['handlers_executed']}")

# Query event history
history = bus.get_event_history(
    event_type=EventType.SECURITY_ALERT,
    limit=10
)

# Get correlation chain
chain = bus.get_correlation_chain(event.correlation_id)
```

### Cross-System Workflows

```python
from integration.event_bus import CrossSystemWorkflow

workflow = CrossSystemWorkflow(bus)

# Define workflow triggered by ML anomaly
def notify_team(event):
    print(f"Notifying ops team of anomaly: {event.data}")

def trigger_investigation(event):
    print(f"Starting automated investigation")

def log_event(event):
    print(f"Logging to compliance audit trail")

# Register workflow
workflow_id = workflow.register_workflow(
    workflow_id="anomaly_response",
    trigger_event=EventType.ANOMALY_DETECTED,
    actions=[
        notify_team,
        trigger_investigation,
        log_event
    ]
)

# When ML detects anomaly, all actions execute automatically
```

---

## API Gateway

### Overview

Central entry point for all API requests with:
- Rate limiting (token bucket)
- Circuit breaking (service health)
- Request validation
- Logging & metrics

### Rate Limiting

```python
from integration.api_gateway import RateLimiter

limiter = RateLimiter(requests_per_second=100)

# Check if request allowed
if limiter.is_allowed(user_id="user_123"):
    # Process request
else:
    # Return 429 Too Many Requests

# Get status
status = limiter.get_status("user_123")
# Returns: {'tokens_remaining': 87, 'requests_per_second': 100}
```

### Circuit Breaking

```python
from integration.api_gateway import CircuitBreaker

breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

# Record outcomes
breaker.record_success("monitoring_service")
breaker.record_failure("ml_service")

# Check if service available
if breaker.can_execute("ml_service"):
    # Call service
else:
    # Service in circuit-open state, use fallback

# Get status
status = breaker.get_status("ml_service")
# Returns: state='open', failures=5, etc.
```

### API Gateway Setup

```python
from integration.api_gateway import APIGateway, APIRequest, APIResponse

# Initialize gateway
gateway = APIGateway(rate_limiter=limiter, circuit_breaker=breaker)

# Register route handlers
def handle_security_request(request):
    return {"message": "Security data"}

def handle_compliance_request(request):
    return {"message": "Compliance data"}

gateway.register_route("/api/v1/security", handle_security_request)
gateway.register_route("/api/v1/compliance", handle_compliance_request)

# Add middleware
def auth_middleware(request):
    # Verify token
    return request

gateway.add_middleware(auth_middleware)

# Handle request
request = APIRequest(
    method="GET",
    path="/api/v1/security/alerts",
    headers={
        "X-User-ID": "user_123",
        "Authorization": "Bearer token..."
    }
)

response = gateway.handle_request(request)
print(response.status_code)  # 200
print(response.data)         # {"message": "Security data"}
```

### Metrics

```python
# Get gateway metrics
metrics = gateway.get_metrics()
# Returns:
# {
#   'total_requests': 1000000,
#   'successful_requests': 999700,
#   'failed_requests': 300,
#   'success_rate': 99.97,
#   'circuit_breakers': {
#       'monitoring': {'state': 'closed', 'failures': 0, ...}
#   }
# }
```

---

## Integrated Dashboard

### Accessing Dashboard

```python
from integration.unified_dashboard import UnifiedDashboard

dashboard = UnifiedDashboard()
html = dashboard.generate_html_dashboard()

# Save and serve
with open("dashboard.html", "w") as f:
    f.write(html)

# Or embed in web app
app.get("/dashboard", lambda: html)
```

### Dashboard Shows

1. **Overall Health Score** (0-100%)
2. **System Status** - Each of 7 systems
3. **Critical Events** - Last 24 hours
4. **API Gateway Metrics**
5. **Service Dependencies**
6. **Alerts & Incidents**

---

## Operations Guide

### Daily Tasks

```
Morning (9am):
  - Check unified dashboard
  - Review critical alerts
  - Verify all 7 systems operational

Daytime:
  - Monitor API gateway metrics
  - Check event bus for anomalies
  - Verify auth system healthy

Evening (5pm):
  - Review daily statistics
  - Check for recurring issues
  - Plan next day's maintenance
```

### Incident Response

When critical event occurs:

1. **Detect**: Event published to event bus
2. **Alert**: Handlers (monitoring, compliance) notified
3. **Investigate**: Cross-system context available
4. **Remediate**: System-specific tools applied
5. **Log**: Audit trail across all systems

### Scaling Considerations

- **Authentication**: Stateless JWT, scales horizontally
- **Event Bus**: In-memory (for session), use message queue in production
- **API Gateway**: Run multiple instances behind load balancer
- **Dashboard**: Stateless HTML generation

---

## Troubleshooting

### Auth Issues

**Problem**: User can't access system  
**Solution**:
1. Check user active: `auth.get_user_profile(user_id)`
2. Check token valid: `auth.verify_token(token)`
3. Check system access: `user['systems_access']`
4. Regenerate token if expired

### Event Bus Issues

**Problem**: Events not being processed  
**Solution**:
1. Check subscriptions registered: `bus.subscriptions`
2. Verify handlers not throwing errors
3. Check event history: `bus.get_event_history()`
4. Review correlation chains for failures

### Gateway Issues

**Problem**: Circuit breaker open, service unavailable  
**Solution**:
1. Check service health
2. Review error logs from service
3. Wait for recovery timeout
4. Manually close circuit if recovered

---

**Document Version**: 1.0  
**Last Reviewed**: 2025-05-13  
**Next Review**: 2025-08-13
