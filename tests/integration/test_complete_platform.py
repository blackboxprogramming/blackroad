"""
Complete Integration Test Suite for BlackRoad SaaS Platform

Tests all microservices, databases, caches, and workflows end-to-end.
Run with: pytest tests/integration/test_complete_platform.py -v
"""

import pytest
import requests
import os
from contextlib import closing
from uuid import uuid4
import psycopg2
import redis

# Configuration
BASE_URL = "http://localhost"
API_TIMEOUT = 10
SERVICES = {
    "billing": "http://localhost:8001",
    "admin": "http://localhost:8002",
    "analytics": "http://localhost:8003",
    "ml": "http://localhost:8004",
    "customer": "http://localhost:8005",
    "webhooks": "http://localhost:8006",
    "onboarding": "http://localhost:8007",
    "monitoring": "http://localhost:8008",
}

# Explicit URLs let CI use its disposable services instead of production examples.
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://blackroad:dev-password@localhost:5432/blackroad_dev"
)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")



class TestServiceHealth:
    """Test health endpoints of all services"""

    @pytest.mark.parametrize("service_name,url", SERVICES.items())
    def test_service_health(self, service_name, url):
        """Test that all services are healthy"""
        response = requests.get(f"{url}/health", timeout=API_TIMEOUT)
        assert response.status_code == 200, f"{service_name} health check failed"
        
        data = response.json()
        assert data["status"] == "healthy"

    def test_all_services_accessible(self):
        """Test that all services are accessible"""
        for service_name, url in SERVICES.items():
            try:
                response = requests.get(f"{url}/health", timeout=API_TIMEOUT)
                assert response.status_code == 200
            except requests.exceptions.ConnectionError:
                pytest.fail(f"{service_name} not accessible at {url}")


class TestDatabaseConnectivity:
    """Test PostgreSQL database connectivity"""

    def test_database_connection(self):
        """Test connection to PostgreSQL"""
        try:
            conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
            cursor.close()
            conn.close()
        except psycopg2.Error as e:
            pytest.fail(f"Database connection failed: {e}")

    def test_database_tables_exist(self):
        """Test that required tables exist"""
        required_tables = [
            "users",
            "customers",
            "subscriptions",
            "transactions",
        ]
        
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
        cursor = conn.cursor()
        
        for table in required_tables:
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name=%s)",
                (table,)
            )
            exists = cursor.fetchone()[0]
            assert exists, f"Table {table} missing"
        
        cursor.close()
        conn.close()


class TestCommittedMigration:
    """Verify the real monetization schema separately from the platform contract."""

    def test_revision_and_tables(self):
        with closing(psycopg2.connect(DATABASE_URL, connect_timeout=5)) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT version_num FROM alembic_version")
                assert cursor.fetchall() == [("001_initial_schema",)]
                cursor.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                )
                tables = {row[0] for row in cursor.fetchall()}
                assert {
                    "stripe_customers", "monthly_usage", "user_tiers",
                    "charges", "invoices", "webhooks_log",
                } <= tables

    def test_customer_mapping_enforces_unique_customer_id(self):
        # Transaction rollback keeps this check from retaining test records.
        with closing(psycopg2.connect(DATABASE_URL, connect_timeout=5)) as conn:
            try:
                with conn.cursor() as cursor:
                    customer_id = f"integration_{uuid4().hex}"
                    cursor.execute(
                        "INSERT INTO stripe_customers (customer_id, stripe_id) "
                        "VALUES (%s, %s)", (customer_id, f"stripe_{uuid4().hex}")
                    )
                    with pytest.raises(psycopg2.errors.UniqueViolation):
                        cursor.execute(
                            "INSERT INTO stripe_customers (customer_id, stripe_id) "
                            "VALUES (%s, %s)", (customer_id, f"stripe_{uuid4().hex}")
                        )
            finally:
                conn.rollback()


class TestCacheConnectivity:
    """Test Redis cache connectivity"""

    def test_redis_connection(self):
        """Test connection to Redis"""
        try:
            r = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=5, socket_timeout=5)
            r.ping()
        except redis.ConnectionError as e:
            pytest.fail(f"Redis connection failed: {e}")

    def test_redis_set_get(self):
        """Test Redis set/get operations"""
        r = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=5, socket_timeout=5)
        key = f"blackroad:integration:{uuid4().hex}"
        try:
            r.set(key, "test_value", ex=60)
            assert r.get(key) == b"test_value"
        finally:
            r.delete(key)
            r.close()


class TestBillingAPI:
    """Test Billing API endpoints"""

    def test_billing_api_accessible(self):
        """Test Billing API is accessible"""
        response = requests.get(f"{SERVICES['billing']}/health", timeout=API_TIMEOUT)
        assert response.status_code == 200

    def test_create_subscription(self):
        """Test creating a subscription"""
        data = {
            "customer_id": "cust_test",
            "plan": "pro",
            "amount": 29.99,
        }
        response = requests.post(
            f"{SERVICES['billing']}/api/subscriptions",
            json=data,
            timeout=API_TIMEOUT
        )
        assert response.status_code in [200, 201, 422]


class TestAnalyticsEngine:
    """Test Analytics Engine endpoints"""

    def test_analytics_api_accessible(self):
        """Test Analytics API is accessible"""
        response = requests.get(f"{SERVICES['analytics']}/health", timeout=API_TIMEOUT)
        assert response.status_code == 200


class TestMLAnalytics:
    """Test ML Analytics Engine"""

    def test_ml_api_accessible(self):
        """Test ML API is accessible"""
        response = requests.get(f"{SERVICES['ml']}/health", timeout=API_TIMEOUT)
        assert response.status_code == 200


class TestLoadBalancer:
    """Test Nginx Load Balancer"""

    def test_load_balancer_accessible(self):
        """Test load balancer is accessible"""
        response = requests.get(f"{BASE_URL}/health", timeout=API_TIMEOUT)
        assert response.status_code == 200

    def test_api_routing(self):
        """Test API routing works"""
        response = requests.get(f"{BASE_URL}/api/billing/health", timeout=API_TIMEOUT)
        assert response.status_code == 200


class TestPrometheus:
    """Test Prometheus metrics collection"""

    def test_prometheus_accessible(self):
        """Test Prometheus is accessible"""
        response = requests.get("http://localhost:9090", timeout=API_TIMEOUT)
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
