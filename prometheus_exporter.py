"""
Prometheus Metrics Exporter
Exposes BlackRoad metrics in Prometheus format for scraping
"""

from prometheus_client import Counter, Gauge, Histogram, start_http_server
from monitoring_system import MonitoringSystem, AlertSeverity
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# REVENUE METRICS
# ============================================================================

revenue_total = Gauge(
    'blackroad_revenue_total_usd',
    'Total revenue in USD',
    labelnames=['period']
)

revenue_by_tier = Gauge(
    'blackroad_revenue_by_tier_usd',
    'Revenue by tier in USD',
    labelnames=['tier']
)

daily_revenue = Gauge(
    'blackroad_daily_revenue_usd',
    'Daily revenue in USD',
    labelnames=['date']
)

revenue_projection_annual = Gauge(
    'blackroad_revenue_projection_annual_usd',
    'Projected annual revenue in USD'
)


# ============================================================================
# USER METRICS
# ============================================================================

total_users = Gauge(
    'blackroad_total_users',
    'Total users',
    labelnames=['tier']
)

daily_signups = Gauge(
    'blackroad_daily_signups',
    'Daily signups',
    labelnames=['date']
)

churn_rate = Gauge(
    'blackroad_churn_rate_percent',
    'Monthly churn rate in percent'
)

paid_conversion_rate = Gauge(
    'blackroad_paid_conversion_rate_percent',
    'Paid conversion rate in percent'
)


# ============================================================================
# SYSTEM HEALTH METRICS
# ============================================================================

database_latency_ms = Gauge(
    'blackroad_database_latency_ms',
    'Database latency in milliseconds'
)

pending_invoices = Gauge(
    'blackroad_pending_invoices',
    'Number of pending invoices'
)

failed_invoices = Gauge(
    'blackroad_failed_invoices',
    'Number of failed invoices'
)

failed_charges_total = Gauge(
    'blackroad_failed_charges_total',
    'Total failed charges in last 24 hours'
)


# ============================================================================
# SUBSCRIPTION & TIER METRICS
# ============================================================================

mrr_total = Gauge(
    'blackroad_mrr_total_usd',
    'Monthly Recurring Revenue in USD'
)

mrr_by_tier = Gauge(
    'blackroad_mrr_by_tier_usd',
    'MRR by tier in USD',
    labelnames=['tier']
)

arr_total = Gauge(
    'blackroad_arr_total_usd',
    'Annual Recurring Revenue in USD'
)


# ============================================================================
# ALERT METRICS
# ============================================================================

active_alerts = Gauge(
    'blackroad_alerts_active',
    'Number of active alerts',
    labelnames=['severity']
)

alert_total = Counter(
    'blackroad_alerts_total',
    'Total alerts triggered',
    labelnames=['severity', 'metric']
)


# ============================================================================
# HEALTH CHECK METRICS
# ============================================================================

health_check_status = Gauge(
    'blackroad_health_check_status',
    'Health check status (1=healthy, 0=unhealthy)',
    labelnames=['service']
)

health_check_latency = Gauge(
    'blackroad_health_check_latency_ms',
    'Health check latency in milliseconds',
    labelnames=['service']
)


class PrometheusExporter:
    """Exports BlackRoad metrics to Prometheus"""
    
    def __init__(self, port: int = 8002):
        self.monitoring = MonitoringSystem()
        self.port = port
        self.last_alert_count = {}
    
    def update_metrics(self):
        """Fetch data from admin dashboard and update Prometheus metrics"""
        try:
            # Revenue metrics
            revenue = self.monitoring.client.get_revenue(days=30)
            if "total_revenue_usd" in revenue:
                revenue_total.labels(period='30d').set(revenue["total_revenue_usd"])
            
            revenue_by_tier_data = self.monitoring.client.get_revenue_by_tier(days=30)
            if "by_tier" in revenue_by_tier_data:
                for tier_data in revenue_by_tier_data["by_tier"]:
                    revenue_by_tier.labels(tier=tier_data["tier"]).set(
                        tier_data.get("total_revenue_usd", 0)
                    )
            
            # Revenue projection
            projection = self.monitoring.client.get_revenue(days=30)
            revenue_projection = self.monitoring.client.get_revenue(days=30)
            
            # User metrics
            users = self.monitoring.client.get_users_total()
            if "by_tier" in users:
                for tier_data in users["by_tier"]:
                    total_users.labels(tier=tier_data["tier"]).set(
                        tier_data.get("user_count", 0)
                    )
            
            # Churn rate
            churn = self.monitoring.client.get_user_churn()
            if "churn_rate_percent" in churn:
                churn_rate.set(churn["churn_rate_percent"])
            
            # Paid conversion
            conversion = self.monitoring.client.get_paid_conversion()
            if "paid_conversion_rate_percent" in conversion:
                paid_conversion_rate.set(conversion["paid_conversion_rate_percent"])
            
            # System health
            db_health = self.monitoring.client.get_database_health()
            if "connectivity_latency_ms" in db_health:
                database_latency_ms.set(db_health["connectivity_latency_ms"])
                health_check_status.labels(service='database').set(
                    1 if db_health.get("status") == "healthy" else 0
                )
                health_check_latency.labels(service='database').set(
                    db_health["connectivity_latency_ms"]
                )
            
            # Invoices
            invoices = self.monitoring.client.get_pending_invoices()
            if "pending_invoices" in invoices:
                pending_invoices.set(invoices["pending_invoices"])
            if "failed_invoices" in invoices:
                failed_invoices.set(invoices["failed_invoices"])
            
            # Failed charges
            failed_charges = self.monitoring.client.get_failed_charges(hours=24)
            if "failed_charge_count" in failed_charges:
                failed_charges_total.set(failed_charges["failed_charge_count"])
            
            # MRR metrics
            mrr_data = self.monitoring.client.get_mrr()
            if "monthly_recurring_revenue_usd" in mrr_data:
                mrr_total.set(mrr_data["monthly_recurring_revenue_usd"])
                arr_total.set(mrr_data.get("annual_run_rate_usd", 0))
            
            if "by_tier" in mrr_data:
                for tier_data in mrr_data["by_tier"]:
                    mrr_by_tier.labels(tier=tier_data["tier"]).set(
                        tier_data.get("tier_mrr_usd", 0)
                    )
            
            # Run monitoring checks and update alert metrics
            report = self.monitoring.run_all_checks()
            alert_counts = report.get("alerts", {})
            
            for severity in ["critical", "warning"]:
                count = alert_counts.get(severity, 0)
                active_alerts.labels(severity=severity).set(count)
                
                # Track new alerts
                if severity not in self.last_alert_count or \
                   count > self.last_alert_count[severity]:
                    increase = max(0, count - self.last_alert_count.get(severity, 0))
                    for _ in range(increase):
                        alert_total.labels(severity=severity, metric='various').inc()
                
                self.last_alert_count[severity] = count
            
            logger.info("Metrics updated successfully")
        
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
    
    def start(self, update_interval: int = 30):
        """Start Prometheus HTTP server and metrics update loop"""
        # Start HTTP server
        start_http_server(self.port)
        logger.info(f"Prometheus exporter started on port {self.port}")
        logger.info(f"Metrics available at http://localhost:{self.port}/metrics")
        
        # Update metrics periodically
        try:
            while True:
                self.update_metrics()
                time.sleep(update_interval)
        except KeyboardInterrupt:
            logger.info("Exporter stopped")


if __name__ == "__main__":
    import sys
    
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8002
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    exporter = PrometheusExporter(port=port)
    exporter.start(update_interval=interval)
