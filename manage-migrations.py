#!/usr/bin/env python3
"""
Database migration management for BlackRoad.

Usage:
    ./manage-migrations.py status              # Check current schema version
    ./manage-migrations.py upgrade             # Apply pending migrations
    ./manage-migrations.py downgrade <version> # Rollback to specific version
    ./manage-migrations.py create <message>    # Create new migration
    ./manage-migrations.py current             # Show current revision
"""

import os
import sys
import argparse
from sqlalchemy import create_engine, inspect
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.migration import MigrationContext
from alembic.operations import Operations
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://blackroad:dev-password@localhost/blackroad_dev'
)

def get_alembic_config():
    """Get Alembic configuration."""
    config = Config('alembic.ini')
    config.set_main_option('sqlalchemy.url', DATABASE_URL)
    return config

def get_current_revision():
    """Get current database revision."""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            return context.get_current_revision()
    except Exception as e:
        logger.error(f"Failed to get current revision: {e}")
        return None

def show_status():
    """Show current migration status."""
    current = get_current_revision()
    config = get_alembic_config()
    script = ScriptDirectory.from_config(config)
    
    print("╔════════════════════════════════════════════╗")
    print("║  Database Migration Status                 ║")
    print("╚════════════════════════════════════════════╝")
    print()
    
    if current:
        print(f"✅ Current revision: {current}")
    else:
        print("⚠️  No migrations applied yet")
    
    print()
    print("Available migrations:")
    for revision in script.walk_revisions(reverse=False):
        status = "✅" if revision.revision == current else "⏳"
        print(f"  {status} {revision.revision}: {revision.doc or 'No description'}")

def upgrade(revision=None):
    """Apply migrations."""
    from alembic.command import upgrade as alembic_upgrade
    
    config = get_alembic_config()
    target = revision or 'head'
    
    try:
        alembic_upgrade(config, target)
        logger.info(f"✅ Upgraded to {target}")
    except Exception as e:
        logger.error(f"❌ Upgrade failed: {e}")
        return False
    return True

def downgrade(revision):
    """Rollback to specific revision."""
    from alembic.command import downgrade as alembic_downgrade
    
    config = get_alembic_config()
    
    try:
        alembic_downgrade(config, revision)
        logger.info(f"✅ Downgraded to {revision}")
    except Exception as e:
        logger.error(f"❌ Downgrade failed: {e}")
        return False
    return True

def create_migration(message):
    """Create new migration."""
    from alembic.command import revision as alembic_revision
    
    config = get_alembic_config()
    
    try:
        alembic_revision(config, autogenerate=False, message=message)
        logger.info(f"✅ Migration created: {message}")
    except Exception as e:
        logger.error(f"❌ Failed to create migration: {e}")
        return False
    return True

def verify_schema():
    """Verify schema is correct."""
    try:
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = [
            'stripe_customers',
            'monthly_usage',
            'user_tiers',
            'charges',
            'invoices',
            'webhooks_log',
            'alembic_version'
        ]
        
        print("╔════════════════════════════════════════════╗")
        print("║  Database Schema Verification              ║")
        print("╚════════════════════════════════════════════╝")
        print()
        
        missing = [t for t in required_tables if t not in tables]
        
        if missing:
            print(f"❌ Missing tables: {', '.join(missing)}")
            return False
        else:
            print("✅ All required tables present:")
            for table in required_tables:
                columns = len(inspector.get_columns(table))
                print(f"   ✓ {table} ({columns} columns)")
            return True
    
    except Exception as e:
        logger.error(f"❌ Schema verification failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Database migration management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  ./manage-migrations.py status                 # Show migration status
  ./manage-migrations.py upgrade                # Apply all pending migrations
  ./manage-migrations.py upgrade 001_initial    # Apply up to specific version
  ./manage-migrations.py downgrade 001_initial  # Rollback to specific version
  ./manage-migrations.py create "Add new table" # Create new migration
  ./manage-migrations.py verify                 # Verify schema
        '''
    )
    
    parser.add_argument(
        'command',
        choices=['status', 'upgrade', 'downgrade', 'create', 'verify', 'current'],
        help='Migration command'
    )
    parser.add_argument(
        'target',
        nargs='?',
        help='Target revision or message'
    )
    
    args = parser.parse_args()
    
    if args.command == 'status':
        show_status()
    
    elif args.command == 'upgrade':
        target = args.target or 'head'
        upgrade(target)
    
    elif args.command == 'downgrade':
        if not args.target:
            logger.error("Downgrade requires target revision")
            sys.exit(1)
        downgrade(args.target)
    
    elif args.command == 'create':
        if not args.target:
            logger.error("Create requires migration message")
            sys.exit(1)
        create_migration(args.target)
    
    elif args.command == 'verify':
        success = verify_schema()
        sys.exit(0 if success else 1)
    
    elif args.command == 'current':
        revision = get_current_revision()
        if revision:
            print(f"Current revision: {revision}")
        else:
            print("No migrations applied")

if __name__ == '__main__':
    main()
