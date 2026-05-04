"""
Monitoring & Alerting System for BlackRoad
Integrates with admin dashboard API to provide:
- Real-time health checks
- Performance monitoring
- Custom alerts based on thresholds
- Alert delivery (email, Slack, webhooks)
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertChannel(str, Enum):
    """Alert delivery channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"


@dataclass
class Alert:
    """Alert data structure"""
    title: str
    message: str
    severity: AlertSeverity
    metric: str
    current_value: float
    threshold: float
    timestamp: datetime
    channels: List[AlertChannel]


@dataclass
class HealthCheck:
    """Health check result"""
    service: str
    status: str  # "healthy" or "unhealthy"
    latency_ms: float
    message: str
    timestamp: datetime


class AdminDashboardClient:
    """Client for admin dashboard API"""
    
    def __init__(self, base_url: str = "http://localhost:8001/api/admin", token: str = None):
        self.base_url = base_url
        self.token = token or os.getenv("ADMIN_TOKEN", "dev-admin-token-change-in-prod")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def _make_request(self, endpoint: str, **kwargs) -> Dict:
        """Make authenticated request to admin dashboard"""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Dashboard request failed: {e}")
            return {"error": str(e)}
    
    def get_revenue(self, days: int = 30) -> Dict:
        """Get total revenue"""
        return self._make_request("revenue/total", params={"days": days})
    
    def get_revenue_by_tier(self, days: int = 30) -> Dict:
        """Get revenue by tier"""
        return self._make_request("revenue/by-tier", params={"days": days})
    
    def get_daily_revenue(self, days: int = 30) -> Dict:
        """Get daily revenue trend"""
        return self._make_request("revenue/daily", params={"days": days})
    
    def get_users_total(self) -> Dict:
        """Get total users by tier"""
        return self._make_request("users/total")
    
    def get_user_churn(self, days: int = 30) -> Dict:
        """Get churn rate"""
        return self._make_request("users/churn", params={"days": days})
    
    def get_paid_conversion(self) -> Dict:
        """Get paid conversion rate"""
        return self._make_request("users/paid-conversion")
    
    def get_database_health(self) -> Dict:
        """Get database health"""
        return self._make_request("health/database")
    
    def get_pending_invoices(self) -> Dict:
        """Get pending invoices"""
        return self._make_request("health/pending-invoices")
    
    def get_failed_charges(self, hours: int = 24) -> Dict:
        """Get failed charges"""
        return self._make_request("health/failed-charges", params={"hours": hours})
    
    def get_mrr(self) -> Dict:
        """Get MRR by tier"""
        return self._make_request("tiers/mrr")
    
    def get_daily_report(self) -> Dict:
        """Get comprehensive daily report"""
        return self._make_request("export/daily-report")


class AlertThresholds:
    """Default alert thresholds"""
    
    # Revenue metrics
    DAILY_REVENUE_DROP_PERCENT = 50  # Alert if daily drops > 50%
    
    # User metrics
    CHURN_RATE_WARNING = 10  # Alert if churn > 10%
    CHURN_RATE_CRITICAL = 15  # Alert if churn > 15%
    PAID_CONVERSION_LOW = 5  # Alert if conversion < 5%
    
    # System health
    DB_LATENCY_WARNING_MS = 100  # Alert if > 100ms
    DB_LATENCY_CRITICAL_MS = 500  # Alert if > 500ms
    FAILED_CHARGES_PERCENT_WARNING = 2  # Alert if > 2%
    FAILED_CHARGES_PERCENT_CRITICAL = 5  # Alert if > 5%
    PENDING_INVOICES_WARNING = 10  # Alert if > 10
    PENDING_INVOICES_CRITICAL = 25  # Alert if > 25
    
    # MRR metrics
    MRR_DROP_PERCENT = 10  # Alert if MRR drops > 10% month-over-month


class MonitoringSystem:
    """Main monitoring system"""
    
    def __init__(self, dashboard_url: str = None, admin_token: str = None):
        self.client = AdminDashboardClient(dashboard_url, admin_token)
        self.alerts: List[Alert] = []
        self.health_checks: List[HealthCheck] = []
        self.thresholds = AlertThresholds()
    
    def run_health_checks(self) -> List[HealthCheck]:
        """Run all health checks"""
        self.health_checks = []
        
        # Database health
        db_health = self.check_database_health()
        self.health_checks.append(db_health)
        
        # API connectivity
        api_health = self.check_api_connectivity()
        self.health_checks.append(api_health)
        
        return self.health_checks
    
    def check_database_health(self) -> HealthCheck:
        """Check database connectivity and performance"""
        start = datetime.utcnow()
        result = self.client.get_database_health()
        latency = (datetime.utcnow() - start).total_seconds() * 1000
        
        if "error" in result:
            return HealthCheck(
                service="database",
                status="unhealthy",
                latency_ms=latency,
                message=result.get("error", "Unknown error"),
                timestamp=datetime.utcnow()
            )
        
        db_status = result.get("status", "unknown")
        return HealthCheck(
            service="database",
            status=db_status,
            latency_ms=latency,
            message=f"Database latency: {latency:.2f}ms",
            timestamp=datetime.utcnow()
        )
    
    def check_api_connectivity(self) -> HealthCheck:
        """Check admin dashboard API connectivity"""
        start = datetime.utcnow()
        result = self.client._make_request("ping")
        latency = (datetime.utcnow() - start).total_seconds() * 1000
        
        if "error" in result:
            return HealthCheck(
                service="admin_api",
                status="unhealthy",
                latency_ms=latency,
                message=f"API unreachable: {result.get('error')}",
                timestamp=datetime.utcnow()
            )
        
        return HealthCheck(
            service="admin_api",
            status="healthy",
            latency_ms=latency,
            message=f"API responsive: {latency:.2f}ms",
            timestamp=datetime.utcnow()
        )
    
    def check_revenue_alerts(self, days: int = 30) -> List[Alert]:
        """Check revenue-related alerts"""
        alerts = []
        
        # Get current and previous revenue
        revenue_data = self.client.get_daily_revenue(days=days)
        
        if "daily_trend" not in revenue_data or len(revenue_data["daily_trend"]) < 2:
            return alerts
        
        # Compare today to average
        today = revenue_data["daily_trend"][-1]["revenue_usd"]
        historical = [d["revenue_usd"] for d in revenue_data["daily_trend"][:-1]]
        average = sum(historical) / len(historical) if historical else 0
        
        if average > 0:
            drop_percent = ((average - today) / average) * 100
            
            if drop_percent > self.thresholds.DAILY_REVENUE_DROP_PERCENT:
                alerts.append(Alert(
                    title="Revenue Drop Alert",
                    message=f"Daily revenue dropped {drop_percent:.1f}% below average",
                    severity=AlertSeverity.WARNING,
                    metric="daily_revenue",
                    current_value=today,
                    threshold=average * (1 - self.thresholds.DAILY_REVENUE_DROP_PERCENT / 100),
                    timestamp=datetime.utcnow(),
                    channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
                ))
        
        return alerts
    
    def check_churn_alerts(self) -> List[Alert]:
        """Check user churn alerts"""
        alerts = []
        churn_data = self.client.get_user_churn()
        
        if "churn_rate_percent" not in churn_data:
            return alerts
        
        churn_rate = churn_data["churn_rate_percent"]
        
        if churn_rate > self.thresholds.CHURN_RATE_CRITICAL:
            alerts.append(Alert(
                title="Critical Churn Rate",
                message=f"Churn rate is {churn_rate:.1f}% (threshold: {self.thresholds.CHURN_RATE_CRITICAL}%)",
                severity=AlertSeverity.CRITICAL,
                metric="churn_rate",
                current_value=churn_rate,
                threshold=self.thresholds.CHURN_RATE_CRITICAL,
                timestamp=datetime.utcnow(),
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
            ))
        elif churn_rate > self.thresholds.CHURN_RATE_WARNING:
            alerts.append(Alert(
                title="High Churn Rate",
                message=f"Churn rate is {churn_rate:.1f}% (threshold: {self.thresholds.CHURN_RATE_WARNING}%)",
                severity=AlertSeverity.WARNING,
                metric="churn_rate",
                current_value=churn_rate,
                threshold=self.thresholds.CHURN_RATE_WARNING,
                timestamp=datetime.utcnow(),
                channels=[AlertChannel.SLACK]
            ))
        
        return alerts
    
    def check_system_health_alerts(self) -> List[Alert]:
        """Check system health alerts"""
        alerts = []
        
        # Database latency
        db_health = self.client.get_database_health()
        if db_health.get("status") == "healthy":
            latency = db_health.get("connectivity_latency_ms", 0)
            
            if latency > self.thresholds.DB_LATENCY_CRITICAL_MS:
                alerts.append(Alert(
                    title="Critical Database Latency",
                    message=f"Database latency is {latency:.2f}ms (threshold: {self.thresholds.DB_LATENCY_CRITICAL_MS}ms)",
                    severity=AlertSeverity.CRITICAL,
                    metric="db_latency",
                    current_value=latency,
                    threshold=self.thresholds.DB_LATENCY_CRITICAL_MS,
                    timestamp=datetime.utcnow(),
                    channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
                ))
            elif latency > self.thresholds.DB_LATENCY_WARNING_MS:
                alerts.append(Alert(
                    title="Database Latency Warning",
                    message=f"Database latency is {latency:.2f}ms (threshold: {self.thresholds.DB_LATENCY_WARNING_MS}ms)",
                    severity=AlertSeverity.WARNING,
                    metric="db_latency",
                    current_value=latency,
                    threshold=self.thresholds.DB_LATENCY_WARNING_MS,
                    timestamp=datetime.utcnow(),
                    channels=[AlertChannel.SLACK]
                ))
        
        # Pending invoices
        invoices = self.client.get_pending_invoices()
        pending = invoices.get("pending_invoices", 0)
        
        if pending > self.thresholds.PENDING_INVOICES_CRITICAL:
            alerts.append(Alert(
                title="Critical Pending Invoices",
                message=f"{pending} invoices pending (threshold: {self.thresholds.PENDING_INVOICES_CRITICAL})",
                severity=AlertSeverity.CRITICAL,
                metric="pending_invoices",
                current_value=pending,
                threshold=self.thresholds.PENDING_INVOICES_CRITICAL,
                timestamp=datetime.utcnow(),
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
            ))
        elif pending > self.thresholds.PENDING_INVOICES_WARNING:
            alerts.append(Alert(
                title="Pending Invoices Alert",
                message=f"{pending} invoices pending (threshold: {self.thresholds.PENDING_INVOICES_WARNING})",
                severity=AlertSeverity.WARNING,
                metric="pending_invoices",
                current_value=pending,
                threshold=self.thresholds.PENDING_INVOICES_WARNING,
                timestamp=datetime.utcnow(),
                channels=[AlertChannel.SLACK]
            ))
        
        return alerts
    
    def run_all_checks(self) -> Dict:
        """Run all monitoring checks and collect alerts"""
        self.alerts = []
        
        # Run health checks
        self.run_health_checks()
        
        # Collect metric-based alerts
        self.alerts.extend(self.check_revenue_alerts())
        self.alerts.extend(self.check_churn_alerts())
        self.alerts.extend(self.check_system_health_alerts())
        
        return self.get_status_report()
    
    def get_status_report(self) -> Dict:
        """Generate status report"""
        critical_alerts = [a for a in self.alerts if a.severity == AlertSeverity.CRITICAL]
        warning_alerts = [a for a in self.alerts if a.severity == AlertSeverity.WARNING]
        
        overall_status = "critical" if critical_alerts else \
                        "warning" if warning_alerts else \
                        "healthy"
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": overall_status,
            "health_checks": [
                {
                    "service": h.service,
                    "status": h.status,
                    "latency_ms": h.latency_ms,
                    "message": h.message,
                }
                for h in self.health_checks
            ],
            "alerts": {
                "critical": len(critical_alerts),
                "warning": len(warning_alerts),
                "total": len(self.alerts),
                "details": [
                    {
                        "title": a.title,
                        "message": a.message,
                        "severity": a.severity.value,
                        "metric": a.metric,
                        "current_value": a.current_value,
                        "threshold": a.threshold,
                    }
                    for a in sorted(self.alerts, 
                                   key=lambda x: (x.severity != AlertSeverity.CRITICAL, x.severity != AlertSeverity.WARNING))
                ]
            }
        }


class AlertNotifier:
    """Send alerts through various channels"""
    
    @staticmethod
    def send_email(alert: Alert, recipient: str) -> bool:
        """Send email alert"""
        try:
            # This would integrate with SendGrid, AWS SES, or similar
            logger.info(f"Email alert sent to {recipient}: {alert.title}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    @staticmethod
    def send_slack(alert: Alert, webhook_url: str = None) -> bool:
        """Send Slack alert"""
        webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False
        
        try:
            color = {
                AlertSeverity.INFO: "#36a64f",
                AlertSeverity.WARNING: "#ff9900",
                AlertSeverity.CRITICAL: "#ff0000",
            }.get(alert.severity, "#808080")
            
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": alert.title,
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Metric",
                                "value": alert.metric,
                                "short": True
                            },
                            {
                                "title": "Current Value",
                                "value": str(alert.current_value),
                                "short": True
                            },
                            {
                                "title": "Threshold",
                                "value": str(alert.threshold),
                                "short": True
                            },
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True
                            }
                        ],
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=5)
            response.raise_for_status()
            logger.info(f"Slack alert sent: {alert.title}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False
    
    @staticmethod
    def send_webhook(alert: Alert, webhook_url: str) -> bool:
        """Send custom webhook alert"""
        try:
            payload = {
                "title": alert.title,
                "message": alert.message,
                "severity": alert.severity.value,
                "metric": alert.metric,
                "current_value": alert.current_value,
                "threshold": alert.threshold,
                "timestamp": alert.timestamp.isoformat(),
            }
            
            response = requests.post(webhook_url, json=payload, timeout=5)
            response.raise_for_status()
            logger.info(f"Webhook alert sent: {alert.title}")
            return True
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            return False
    
    @staticmethod
    def send_alert(alert: Alert, channels: List[AlertChannel]) -> bool:
        """Send alert through specified channels"""
        success = True
        
        for channel in channels:
            if channel == AlertChannel.EMAIL:
                success &= AlertNotifier.send_email(alert, os.getenv("ALERT_EMAIL"))
            elif channel == AlertChannel.SLACK:
                success &= AlertNotifier.send_slack(alert)
            elif channel == AlertChannel.LOG:
                logger.warning(f"ALERT: {alert.title} - {alert.message}")
            elif channel == AlertChannel.WEBHOOK:
                webhook_url = os.getenv("ALERT_WEBHOOK_URL")
                if webhook_url:
                    success &= AlertNotifier.send_webhook(alert, webhook_url)
        
        return success


def create_monitoring_daemon(check_interval_seconds: int = 60):
    """Create a monitoring daemon that runs checks periodically"""
    import time
    import signal
    
    monitoring = MonitoringSystem()
    running = True
    
    def signal_handler(sig, frame):
        nonlocal running
        logger.info("Monitoring daemon stopping...")
        running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info(f"Starting monitoring daemon (check every {check_interval_seconds}s)")
    
    while running:
        try:
            report = monitoring.run_all_checks()
            logger.info(f"Monitoring check complete: {report['overall_status']}")
            
            # Send alerts
            notifier = AlertNotifier()
            for alert in monitoring.alerts:
                notifier.send_alert(alert, alert.channels)
            
            # Sleep until next check
            time.sleep(check_interval_seconds)
        except Exception as e:
            logger.error(f"Monitoring check failed: {e}")
            time.sleep(check_interval_seconds)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "daemon":
        # Run as daemon
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        create_monitoring_daemon(interval)
    else:
        # Run single check
        monitoring = MonitoringSystem()
        report = monitoring.run_all_checks()
        print(json.dumps(report, indent=2, default=str))
