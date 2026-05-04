# Database Migrations Guide

## Overview

This project uses **Alembic** for database schema versioning and migrations. Alembic tracks all schema changes, allowing you to upgrade and downgrade database versions safely.

## Quick Start

### View Migration Status
```bash
./manage-migrations.py status
```

### Apply All Pending Migrations
```bash
./manage-migrations.py upgrade
```

### Verify Schema
```bash
./manage-migrations.py verify
```

---

## Database Schema

The initial migration (`001_initial_schema`) creates these tables:

### stripe_customers
Stores mapping between BlackRoad customers and Stripe customers.

| Column | Type | Purpose |
|--------|------|---------|
| customer_id | VARCHAR | Primary identifier (unique) |
| stripe_id | VARCHAR | Stripe customer ID (unique) |
| email | VARCHAR | Customer email |
| tier | VARCHAR | Subscription tier (free, light, power, enterprise) |
| status | VARCHAR | Account status (active, suspended, deleted) |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |

Indexes:
- `customer_id` (fast lookups by customer)
- `stripe_id` (fast lookups by Stripe ID)

### monthly_usage
Tracks API usage per customer per month.

| Column | Type | Purpose |
|--------|------|---------|
| customer_id | VARCHAR | Customer identifier (indexed) |
| year_month | VARCHAR | Period in YYYY-MM format |
| total_calls | INTEGER | API calls this month |
| total_seconds | FLOAT | Total seconds of API time |
| total_cost | FLOAT | Total cost for month |
| free_hours_used | FLOAT | Free tier hours consumed |
| paid_hours | FLOAT | Paid tier hours consumed |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |

Unique Constraint: `(customer_id, year_month)` - one record per customer per month

Indexes:
- `customer_id, year_month` composite (fast period lookups)

### user_tiers
Current subscription tier for each customer.

| Column | Type | Purpose |
|--------|------|---------|
| customer_id | VARCHAR | Customer identifier (unique, indexed) |
| tier | VARCHAR | Current tier (free, light, power, enterprise) |
| status | VARCHAR | Tier status (active, pending, canceled) |
| stripe_subscription_id | VARCHAR | Stripe subscription ID |
| started_at | DATETIME | When tier became active |
| ended_at | DATETIME | When tier ends (NULL = active) |

### charges
Individual charge records for audit trail.

| Column | Type | Purpose |
|--------|------|---------|
| transaction_id | VARCHAR | Unique charge ID (indexed) |
| customer_id | VARCHAR | Customer who was charged (indexed) |
| amount | FLOAT | Charge amount in dollars |
| description | VARCHAR | What was charged for |
| stripe_event_id | VARCHAR | Stripe meter event ID |
| status | VARCHAR | pending, succeeded, failed |
| error_message | VARCHAR | Error details if failed |
| created_at | DATETIME | When charge occurred |

Indexes:
- `transaction_id` (lookup by charge)
- `customer_id` (all charges for customer)
- `status` (find failed charges)
- `created_at` (time-based queries)

### invoices
Generated invoices for customers.

| Column | Type | Purpose |
|--------|------|---------|
| invoice_id | VARCHAR | BlackRoad invoice ID (unique, indexed) |
| customer_id | VARCHAR | Customer (indexed) |
| stripe_invoice_id | VARCHAR | Stripe invoice ID |
| amount | FLOAT | Invoice total |
| period_start | DATE | Billing period start |
| period_end | DATE | Billing period end |
| status | VARCHAR | draft, open, paid, void, uncollectible |
| paid_at | DATETIME | When payment received |
| pdf_url | VARCHAR | URL to PDF invoice |

### webhooks_log
Tracks all webhook deliveries for debugging.

| Column | Type | Purpose |
|--------|------|---------|
| event_id | VARCHAR | Stripe event ID (unique, indexed) |
| event_type | VARCHAR | Event type (indexed, indexed for fast filtering) |
| customer_id | VARCHAR | Related customer (indexed) |
| payload | JSON | Full webhook payload |
| status | VARCHAR | received, processing, completed, failed |
| retries | INTEGER | Number of retry attempts |
| error_message | VARCHAR | Error if failed |

---

## Migrations Commands

### View Status
```bash
./manage-migrations.py status
```

Shows:
- Current database revision
- All available migrations
- Which migrations are applied

Example output:
```
Current revision: 001_initial_schema
Available migrations:
  ✅ 001_initial_schema: Initial database schema for BlackRoad monetization
```

### Apply Migrations
```bash
# Apply all pending migrations
./manage-migrations.py upgrade

# Apply up to specific revision
./manage-migrations.py upgrade 001_initial_schema
```

### Rollback Migrations
```bash
# Downgrade to specific revision (removes all changes after it)
./manage-migrations.py downgrade 001_initial_schema
```

⚠️ **Warning:** Downgrading deletes table data! Only use in development.

### Create New Migration
```bash
./manage-migrations.py create "Add price history table"
```

Creates new migration file in `alembic/versions/` with timestamp.

Then edit the migration file to define:
- `upgrade()` - what to do when applying
- `downgrade()` - how to undo

### Verify Schema
```bash
./manage-migrations.py verify
```

Checks all required tables exist and have correct columns.

---

## Deployment Flow

### Local Development
```bash
# Start database
docker-compose up -d postgres redis

# Apply migrations
./manage-migrations.py upgrade

# Start API
docker-compose up -d api
```

### Staging
```bash
# SSH to staging server
ssh deploy@staging.example.com

# Clone repo and navigate
cd /app/blackroad

# Apply migrations to staging DB
docker-compose exec api python manage-migrations.py upgrade

# Start services
docker-compose up -d
```

### Production
```bash
# In deployment pipeline:
docker-compose exec api python manage-migrations.py upgrade head

# Then start all services
docker-compose up -d
```

---

## Creating New Migrations

### Example: Add audit logging table

1. Create migration:
```bash
./manage-migrations.py create "Add audit logging table"
```

2. Edit `alembic/versions/002_audit_logging.py`:
```python
from alembic import op
import sqlalchemy as sa

revision = '002_audit_logging'
down_revision = '001_initial_schema'

def upgrade() -> None:
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('customer_id', sa.String(255), index=True),
        sa.Column('details', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('idx_audit_log_action', 'audit_log', ['action'])

def downgrade() -> None:
    op.drop_index('idx_audit_log_action')
    op.drop_table('audit_log')
```

3. Test upgrade:
```bash
./manage-migrations.py upgrade
```

4. Test downgrade:
```bash
./manage-migrations.py downgrade 001_initial_schema
```

5. Test upgrade again:
```bash
./manage-migrations.py upgrade
```

---

## Troubleshooting

### "Alembic version table not found"
This means migrations have never been applied.

```bash
./manage-migrations.py upgrade
```

### "Current revision is not available"
Database is out of sync.

```bash
# Reset database (WARNING: loses data)
docker-compose down -v
docker-compose up -d postgres
./manage-migrations.py upgrade
```

### "Cannot downgrade, would lose data"
Some migrations can't be downgraded without data loss.

In development, safest to reset:
```bash
docker-compose down -v
docker-compose up -d postgres
./manage-migrations.py upgrade
```

### "Migration dependency error"
A migration is missing or out of order.

View current state:
```bash
./manage-migrations.py status
```

Check `alembic/versions/` directory for missing files.

---

## Best Practices

### Before Making Schema Changes
1. **Backup production database**
   ```bash
   pg_dump $DATABASE_URL > backup.sql
   ```

2. **Test in staging first**
   ```bash
   ./manage-migrations.py upgrade
   ```

3. **Verify with queries**
   ```bash
   psql $DATABASE_URL -c "\d stripe_customers"
   ```

### Creating Migrations
1. **One change per migration**
   - ✅ Add one table
   - ✅ Add one index
   - ❌ Add table AND index in same migration (if you need to rollback table, index breaks)

2. **Always include downgrade**
   - Every `upgrade()` should have matching `downgrade()`
   - Test both directions

3. **Use descriptive names**
   - ✅ `002_add_audit_logging_table`
   - ❌ `002_updates`

4. **Add comments**
   ```python
   """Add audit logging for compliance.
   
   Tracks all customer actions for audit trail.
   Used by: compliance dashboard
   """
   ```

### Running Migrations
1. **Always in version control**
   - Never run raw SQL
   - Only use migrations

2. **Test before production**
   - Apply to staging first
   - Verify with queries
   - Then promote to production

3. **Monitor after deployment**
   - Check for slow queries
   - Monitor table sizes
   - Verify indexes working

---

## Monitoring

### Check Migration History
```bash
psql $DATABASE_URL -c "SELECT version, installed_on FROM alembic_version;"
```

### Monitor Slow Queries
```bash
# Find slow queries
psql $DATABASE_URL -c "SELECT query, calls, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

### Table Sizes
```bash
psql $DATABASE_URL -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

---

## References

- **Alembic Documentation**: https://alembic.sqlalchemy.org/
- **SQLAlchemy Types**: https://docs.sqlalchemy.org/en/20/core/types.html
- **PostgreSQL Types**: https://www.postgresql.org/docs/current/datatype.html
