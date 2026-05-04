"""Initial database schema for BlackRoad monetization

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-05-04

Creates tables:
- stripe_customers: Stripe customer mappings
- monthly_usage: Monthly usage tracking per customer
- user_tiers: Customer subscription tiers
- charges: Individual charge records
- invoices: Generated invoices
- webhooks_log: Webhook delivery tracking
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Stripe customers mapping
    op.create_table(
        'stripe_customers',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('customer_id', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('stripe_id', sa.String(255), unique=True, nullable=False),
        sa.Column('email', sa.String(255)),
        sa.Column('tier', sa.String(50), default='free'),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_stripe_customers_customer_id', 'stripe_customers', ['customer_id'])
    op.create_index('idx_stripe_customers_stripe_id', 'stripe_customers', ['stripe_id'])

    # Monthly usage tracking
    op.create_table(
        'monthly_usage',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('customer_id', sa.String(255), nullable=False, index=True),
        sa.Column('year_month', sa.String(7), nullable=False),  # YYYY-MM format
        sa.Column('total_calls', sa.Integer, default=0),
        sa.Column('total_seconds', sa.Float, default=0),
        sa.Column('total_cost', sa.Float, default=0),
        sa.Column('free_hours_used', sa.Float, default=0),
        sa.Column('paid_hours', sa.Float, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('customer_id', 'year_month', name='uq_monthly_usage'),
    )
    op.create_index('idx_monthly_usage_customer', 'monthly_usage', ['customer_id'])
    op.create_index('idx_monthly_usage_year_month', 'monthly_usage', ['year_month'])

    # User tiers for subscription levels
    op.create_table(
        'user_tiers',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('customer_id', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('tier', sa.String(50), nullable=False),  # free, light, power, enterprise
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('stripe_subscription_id', sa.String(255)),
        sa.Column('started_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_user_tiers_customer', 'user_tiers', ['customer_id'])
    op.create_index('idx_user_tiers_tier', 'user_tiers', ['tier'])

    # Individual charges
    op.create_table(
        'charges',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('transaction_id', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('customer_id', sa.String(255), nullable=False, index=True),
        sa.Column('amount', sa.Float, nullable=False),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('description', sa.String(500)),
        sa.Column('stripe_event_id', sa.String(255)),
        sa.Column('status', sa.String(50), default='pending'),  # pending, succeeded, failed
        sa.Column('error_message', sa.String(500)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_charges_customer', 'charges', ['customer_id'])
    op.create_index('idx_charges_status', 'charges', ['status'])
    op.create_index('idx_charges_created', 'charges', ['created_at'])

    # Invoices
    op.create_table(
        'invoices',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('invoice_id', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('customer_id', sa.String(255), nullable=False, index=True),
        sa.Column('stripe_invoice_id', sa.String(255)),
        sa.Column('amount', sa.Float, nullable=False),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),
        sa.Column('status', sa.String(50), default='draft'),  # draft, open, paid, void, uncollectible
        sa.Column('paid_at', sa.DateTime),
        sa.Column('pdf_url', sa.String(500)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_invoices_customer', 'invoices', ['customer_id'])
    op.create_index('idx_invoices_period', 'invoices', ['period_start', 'period_end'])
    op.create_index('idx_invoices_status', 'invoices', ['status'])

    # Webhook delivery tracking
    op.create_table(
        'webhooks_log',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('event_id', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('customer_id', sa.String(255), index=True),
        sa.Column('payload', postgresql.JSON, nullable=False),
        sa.Column('status', sa.String(50), default='received'),  # received, processing, completed, failed
        sa.Column('retries', sa.Integer, default=0),
        sa.Column('error_message', sa.String(500)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_webhooks_event', 'webhooks_log', ['event_type'])
    op.create_index('idx_webhooks_customer', 'webhooks_log', ['customer_id'])
    op.create_index('idx_webhooks_status', 'webhooks_log', ['status'])

def downgrade() -> None:
    op.drop_index('idx_webhooks_status')
    op.drop_index('idx_webhooks_customer')
    op.drop_index('idx_webhooks_event')
    op.drop_table('webhooks_log')
    
    op.drop_index('idx_invoices_status')
    op.drop_index('idx_invoices_period')
    op.drop_index('idx_invoices_customer')
    op.drop_table('invoices')
    
    op.drop_index('idx_charges_created')
    op.drop_index('idx_charges_status')
    op.drop_index('idx_charges_customer')
    op.drop_table('charges')
    
    op.drop_index('idx_user_tiers_tier')
    op.drop_index('idx_user_tiers_customer')
    op.drop_table('user_tiers')
    
    op.drop_index('idx_monthly_usage_year_month')
    op.drop_index('idx_monthly_usage_customer')
    op.drop_table('monthly_usage')
    
    op.drop_index('idx_stripe_customers_stripe_id')
    op.drop_index('idx_stripe_customers_customer_id')
    op.drop_table('stripe_customers')
