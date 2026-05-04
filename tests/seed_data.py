"""
Sample Data Loader for BlackRoad Platform

This script populates the database with sample data for testing and demo purposes.
Run with: python tests/seed_data.py
"""

import psycopg2
from datetime import datetime, timedelta
import random
from typing import List, Dict

DB_CONN = {
    "host": "localhost",
    "port": 5432,
    "user": "blackroad",
    "password": "prod_secure_pass_12345",
    "database": "blackroad_prod",
}

SAMPLE_USERS = [
    {
        "email": "alice@acmecorp.com",
        "name": "Alice Johnson",
        "company": "Acme Corp",
        "plan": "enterprise",
    },
    {
        "email": "bob@techstartup.io",
        "name": "Bob Smith",
        "company": "TechStartup",
        "plan": "pro",
    },
    {
        "email": "carol@smallbiz.com",
        "name": "Carol White",
        "company": "Small Biz LLC",
        "plan": "starter",
    },
    {
        "email": "david@consulting.co",
        "name": "David Brown",
        "company": "Consulting Co",
        "plan": "pro",
    },
    {
        "email": "eve@retail.shop",
        "name": "Eve Davis",
        "company": "Retail Shop",
        "plan": "starter",
    },
]

PLANS = {
    "starter": {"price": 29.99, "requests": 10000},
    "pro": {"price": 99.99, "requests": 100000},
    "enterprise": {"price": 299.99, "requests": 1000000},
}


def seed_users(cursor):
    """Seed sample users"""
    print("Seeding users...")
    
    for user in SAMPLE_USERS:
        try:
            cursor.execute(
                """
                INSERT INTO users (email, name, created_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (email) DO NOTHING
                """,
                (user["email"], user["name"], datetime.utcnow())
            )
        except Exception as e:
            print(f"  Error inserting user {user['email']}: {e}")
    
    print(f"✓ Seeded {len(SAMPLE_USERS)} users")


def seed_customers(cursor):
    """Seed sample customers"""
    print("Seeding customers...")
    
    for user in SAMPLE_USERS:
        try:
            cursor.execute(
                """
                INSERT INTO customers (email, company, plan, created_at, status)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
                """,
                (user["email"], user["company"], user["plan"], datetime.utcnow(), "active")
            )
        except Exception as e:
            print(f"  Error inserting customer {user['email']}: {e}")
    
    print(f"✓ Seeded {len(SAMPLE_USERS)} customers")


def seed_subscriptions(cursor):
    """Seed sample subscriptions"""
    print("Seeding subscriptions...")
    
    count = 0
    for user in SAMPLE_USERS:
        try:
            plan = user["plan"]
            plan_data = PLANS[plan]
            
            cursor.execute(
                """
                INSERT INTO subscriptions (customer_email, plan, amount, status, created_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user["email"], plan, plan_data["price"], "active", datetime.utcnow())
            )
            count += 1
        except Exception as e:
            print(f"  Error creating subscription for {user['email']}: {e}")
    
    print(f"✓ Seeded {count} subscriptions")


def seed_transactions(cursor):
    """Seed sample transactions"""
    print("Seeding transactions...")
    
    count = 0
    for user in SAMPLE_USERS:
        try:
            plan_data = PLANS[user["plan"]]
            amount = plan_data["price"]
            
            # Create transactions for last 3 months
            for days_ago in [0, 30, 60]:
                cursor.execute(
                    """
                    INSERT INTO transactions (customer_email, amount, status, created_at)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (user["email"], amount, "completed", datetime.utcnow() - timedelta(days=days_ago))
                )
                count += 1
        except Exception as e:
            print(f"  Error creating transactions for {user['email']}: {e}")
    
    print(f"✓ Seeded {count} transactions")


def seed_analytics(cursor):
    """Seed sample analytics data"""
    print("Seeding analytics...")
    
    count = 0
    for user in SAMPLE_USERS:
        try:
            # Simulate usage data
            requests_per_day = random.randint(100, 5000)
            errors_per_day = random.randint(0, 50)
            latency_avg = random.uniform(100, 500)
            
            cursor.execute(
                """
                INSERT INTO analytics (customer_email, date, requests, errors, avg_latency)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user["email"], datetime.utcnow().date(), requests_per_day, errors_per_day, latency_avg)
            )
            count += 1
        except Exception as e:
            print(f"  Error creating analytics for {user['email']}: {e}")
    
    print(f"✓ Seeded {count} analytics records")


def main():
    """Main seed function"""
    print("\n╔════════════════════════════════════════════════════════╗")
    print("║  BlackRoad Sample Data Loader                          ║")
    print("╚════════════════════════════════════════════════════════╝\n")
    
    try:
        conn = psycopg2.connect(**DB_CONN)
        cursor = conn.cursor()
        
        print("Connected to database\n")
        
        # Seed data
        seed_users(cursor)
        seed_customers(cursor)
        seed_subscriptions(cursor)
        seed_transactions(cursor)
        seed_analytics(cursor)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n✓ Sample data loaded successfully!")
        print("\nYou can now test the platform with real data.")
        print("Try: curl http://localhost:3000 (Grafana dashboards)")
        
    except Exception as e:
        print(f"\n✗ Error loading sample data: {e}")
        exit(1)


if __name__ == "__main__":
    main()
