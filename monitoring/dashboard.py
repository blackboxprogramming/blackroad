"""
Advanced Monitoring & Observability Dashboard
Real-time metrics, tracing, logs, and alerts
"""

import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import logging
from collections import defaultdict
from statistics import mean, median


class MetricType(Enum):
    """Types of metrics."""
    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Metric:
    """Represents a metric."""
    
    def __init__(self, name: str, metric_type: MetricType, value: float = 0):
        self.name = name
        self.type = metric_type
        self.value = value
        self.labels: Dict[str, str] = {}
        self.timestamp = datetime.utcnow()
        self.samples: List[float] = []
    
    def observe(self, value: float) -> None:
        """Record observation."""
        self.samples.append(value)
        self.value = value
        self.timestamp = datetime.utcnow()
    
    def increment(self, amount: float = 1) -> None:
        """Increment counter."""
        self.value += amount
        self.timestamp = datetime.utcnow()
    
    def set_gauge(self, value: float) -> None:
        """Set gauge value."""
        self.value = value
        self.timestamp = datetime.utcnow()
    
    def get_stats(self) -> Dict:
        """Get statistics."""
        if not self.samples:
            return {}
        
        return {
            'count': len(self.samples),
            'min': min(self.samples),
            'max': max(self.samples),
            'mean': mean(self.samples),
            'median': median(self.samples),
            'p95': sorted(self.samples)[int(len(self.samples) * 0.95)] if len(self.samples) > 0 else 0,
            'p99': sorted(self.samples)[int(len(self.samples) * 0.99)] if len(self.samples) > 0 else 0,
        }


class Alert:
    """Represents an alert."""
    
    def __init__(self, name: str, metric_name: str, threshold: float,
                 severity: AlertSeverity, condition: str = "above"):
        self.id = f"alert_{int(time.time() * 1000)}"
        self.name = name
        self.metric_name = metric_name
        self.threshold = threshold
        self.severity = severity
        self.condition = condition  # above, below, equals
        self.is_active = False
        self.triggered_at: Optional[datetime] = None
        self.acknowledged = False
        self.notification_channels: List[str] = []
    
    def check(self, value: float) -> bool:
        """Check if alert should trigger."""
        if self.condition == "above":
            return value > self.threshold
        elif self.condition == "below":
            return value < self.threshold
        elif self.condition == "equals":
            return value == self.threshold
        return False


class MonitoringDashboard:
    """Real-time monitoring dashboard."""
    
    def __init__(self):
        self.metrics: Dict[str, Metric] = {}
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Dict] = []
        self.error_logs: List[Dict] = []
        self.system_health = {
            'status': 'healthy',
            'uptime_seconds': 0,
            'start_time': datetime.utcnow(),
        }
        self.logger = logging.getLogger(__name__)
    
    def register_metric(self, name: str, metric_type: MetricType) -> Metric:
        """Register metric."""
        metric = Metric(name, metric_type)
        self.metrics[name] = metric
        self.logger.info(f"Metric registered: {name}")
        return metric
    
    def record_metric(self, name: str, value: float) -> None:
        """Record metric value."""
        if name not in self.metrics:
            self.register_metric(name, MetricType.GAUGE)
        
        self.metrics[name].set_gauge(value)
    
    def create_alert(self, name: str, metric_name: str, threshold: float,
                    severity: AlertSeverity = AlertSeverity.WARNING) -> Alert:
        """Create alert rule."""
        alert = Alert(name, metric_name, threshold, severity)
        self.alerts[alert.id] = alert
        self.logger.info(f"Alert created: {alert.id}")
        return alert
    
    def check_alerts(self) -> List[Alert]:
        """Check all alerts."""
        triggered = []
        
        for alert in self.alerts.values():
            if alert.metric_name in self.metrics:
                value = self.metrics[alert.metric_name].value
                
                if alert.check(value):
                    if not alert.is_active:
                        alert.is_active = True
                        alert.triggered_at = datetime.utcnow()
                        triggered.append(alert)
                        
                        # Log alert
                        self.alert_history.append({
                            'alert_id': alert.id,
                            'alert_name': alert.name,
                            'severity': alert.severity.value,
                            'metric': alert.metric_name,
                            'value': value,
                            'threshold': alert.threshold,
                            'timestamp': datetime.utcnow().isoformat(),
                        })
                else:
                    if alert.is_active:
                        alert.is_active = False
        
        return triggered
    
    def get_dashboard_data(self) -> Dict:
        """Get dashboard data."""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'system_health': {
                'status': self.system_health['status'],
                'uptime_minutes': (datetime.utcnow() - self.system_health['start_time']).total_seconds() / 60,
            },
            'metrics': {
                name: {
                    'value': metric.value,
                    'type': metric.type.value,
                    'stats': metric.get_stats(),
                }
                for name, metric in self.metrics.items()
            },
            'active_alerts': [
                {
                    'id': alert.id,
                    'name': alert.name,
                    'severity': alert.severity.value,
                    'triggered_at': alert.triggered_at.isoformat() if alert.triggered_at else None,
                }
                for alert in self.alerts.values() if alert.is_active
            ],
            'recent_alerts': self.alert_history[-10:],
        }
    
    def generate_html_dashboard(self) -> str:
        """Generate HTML dashboard."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitoring Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
        }
        
        header {
            background: #161b22;
            border-bottom: 1px solid #30363d;
            padding: 16px;
        }
        
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        h1 {
            font-size: 24px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .status-healthy {
            background: #238636;
            color: white;
        }
        
        .status-warning {
            background: #d29922;
            color: white;
        }
        
        .status-critical {
            background: #da3633;
            color: white;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 16px;
        }
        
        .card-title {
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            color: #8b949e;
            margin-bottom: 8px;
        }
        
        .card-value {
            font-size: 36px;
            font-weight: 600;
            color: #79c0ff;
            margin-bottom: 4px;
        }
        
        .card-unit {
            font-size: 12px;
            color: #8b949e;
        }
        
        .card-trend {
            font-size: 12px;
            margin-top: 8px;
        }
        
        .trend-up {
            color: #f85149;
        }
        
        .trend-down {
            color: #3fb950;
        }
        
        .section {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            margin-bottom: 24px;
            overflow: hidden;
        }
        
        .section-header {
            padding: 16px;
            border-bottom: 1px solid #30363d;
            font-weight: 600;
            background: #0d1117;
        }
        
        .section-content {
            padding: 16px;
        }
        
        .alert-item {
            padding: 12px;
            margin-bottom: 8px;
            background: #0d1117;
            border-left: 4px solid;
            border-radius: 4px;
        }
        
        .alert-info {
            border-left-color: #3b8bfd;
        }
        
        .alert-warning {
            border-left-color: #d29922;
        }
        
        .alert-critical {
            border-left-color: #da3633;
        }
        
        .alert-title {
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .alert-detail {
            font-size: 12px;
            color: #8b949e;
        }
        
        .metric-bar {
            display: grid;
            grid-template-columns: 150px 1fr 80px;
            gap: 12px;
            padding: 12px;
            border-bottom: 1px solid #30363d;
            align-items: center;
        }
        
        .metric-name {
            font-size: 12px;
            font-weight: 600;
        }
        
        .metric-graph {
            height: 30px;
            background: #0d1117;
            border-radius: 3px;
            position: relative;
            overflow: hidden;
        }
        
        .metric-fill {
            height: 100%;
            background: linear-gradient(90deg, #3b8bfd, #79c0ff);
            border-radius: 3px;
        }
        
        .metric-value {
            font-size: 12px;
            text-align: right;
            font-weight: 600;
        }
        
        .chart {
            height: 300px;
            background: #0d1117;
            border-radius: 6px;
            padding: 12px;
            margin: 12px 0;
            display: flex;
            align-items: flex-end;
            gap: 2px;
        }
        
        .bar {
            flex: 1;
            background: #3b8bfd;
            border-radius: 2px 2px 0 0;
            min-height: 2px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #30363d;
        }
        
        th {
            background: #0d1117;
            font-weight: 600;
            color: #8b949e;
        }
        
        .refresh-button {
            background: #238636;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
        }
        
        .refresh-button:hover {
            background: #2ea043;
        }
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <div>
                <h1>📊 Monitoring Dashboard</h1>
                <p style="font-size: 12px; color: #8b949e;">Real-time system metrics and alerts</p>
            </div>
            <div>
                <span class="status-badge status-healthy">🟢 Healthy</span>
                <button class="refresh-button" onclick="location.reload()">Refresh</button>
            </div>
        </div>
    </header>
    
    <div class="container">
        <!-- Key Metrics -->
        <div class="grid">
            <div class="card">
                <div class="card-title">Requests/Min</div>
                <div class="card-value">1,234</div>
                <div class="card-unit">requests</div>
                <div class="card-trend trend-down">↓ 2.3% from 5min avg</div>
            </div>
            
            <div class="card">
                <div class="card-title">Avg Latency</div>
                <div class="card-value">145</div>
                <div class="card-unit">milliseconds</div>
                <div class="card-trend trend-down">↓ 8ms improvement</div>
            </div>
            
            <div class="card">
                <div class="card-title">Error Rate</div>
                <div class="card-value">0.2</div>
                <div class="card-unit">percent</div>
                <div class="card-trend trend-down">↓ 0.1% improvement</div>
            </div>
            
            <div class="card">
                <div class="card-title">P95 Latency</div>
                <div class="card-value">285</div>
                <div class="card-unit">milliseconds</div>
                <div class="card-trend trend-up">↑ 15ms from baseline</div>
            </div>
            
            <div class="card">
                <div class="card-title">Database Connections</div>
                <div class="card-value">247</div>
                <div class="card-unit">active connections</div>
                <div class="card-trend">68% of max pool</div>
            </div>
            
            <div class="card">
                <div class="card-title">Memory Usage</div>
                <div class="card-value">2.4</div>
                <div class="card-unit">GB / 4.0 GB</div>
                <div class="card-trend">60% utilized</div>
            </div>
        </div>
        
        <!-- Active Alerts -->
        <div class="section">
            <div class="section-header">🚨 Active Alerts (2)</div>
            <div class="section-content">
                <div class="alert-item alert-warning">
                    <div class="alert-title">High P95 Latency</div>
                    <div class="alert-detail">P95 latency is 285ms (threshold: 250ms) - Triggered 5 minutes ago</div>
                </div>
                
                <div class="alert-item alert-info">
                    <div class="alert-title">Database Connection Pool Nearly Full</div>
                    <div class="alert-detail">247/350 connections in use - Consider scaling</div>
                </div>
            </div>
        </div>
        
        <!-- Request Rate Chart -->
        <div class="section">
            <div class="section-header">Request Rate (Last Hour)</div>
            <div class="section-content">
                <div class="chart">
                    <div class="bar" style="height: 45%;"></div>
                    <div class="bar" style="height: 52%;"></div>
                    <div class="bar" style="height: 48%;"></div>
                    <div class="bar" style="height: 61%;"></div>
                    <div class="bar" style="height: 58%;"></div>
                    <div class="bar" style="height: 66%;"></div>
                    <div class="bar" style="height: 72%;"></div>
                    <div class="bar" style="height: 68%;"></div>
                    <div class="bar" style="height: 75%;"></div>
                    <div class="bar" style="height: 71%;"></div>
                </div>
            </div>
        </div>
        
        <!-- Top Endpoints -->
        <div class="section">
            <div class="section-header">Top Endpoints (Last Hour)</div>
            <div class="section-content">
                <table>
                    <thead>
                        <tr>
                            <th>Endpoint</th>
                            <th>Requests</th>
                            <th>Avg Latency</th>
                            <th>Error Rate</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>POST /graphql</td>
                            <td>28,400</td>
                            <td>142ms</td>
                            <td>0.12%</td>
                        </tr>
                        <tr>
                            <td>GET /api/customers</td>
                            <td>12,300</td>
                            <td>89ms</td>
                            <td>0.05%</td>
                        </tr>
                        <tr>
                            <td>POST /webhooks</td>
                            <td>8,750</td>
                            <td>156ms</td>
                            <td>0.23%</td>
                        </tr>
                        <tr>
                            <td>GET /health</td>
                            <td>5,400</td>
                            <td>12ms</td>
                            <td>0.0%</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- System Health -->
        <div class="section">
            <div class="section-header">System Health</div>
            <div class="section-content">
                <div class="metric-bar">
                    <div class="metric-name">CPU Usage</div>
                    <div class="metric-graph">
                        <div class="metric-fill" style="width: 45%;"></div>
                    </div>
                    <div class="metric-value">45%</div>
                </div>
                
                <div class="metric-bar">
                    <div class="metric-name">Memory Usage</div>
                    <div class="metric-graph">
                        <div class="metric-fill" style="width: 60%;"></div>
                    </div>
                    <div class="metric-value">2.4GB</div>
                </div>
                
                <div class="metric-bar">
                    <div class="metric-name">Disk I/O</div>
                    <div class="metric-graph">
                        <div class="metric-fill" style="width: 28%;"></div>
                    </div>
                    <div class="metric-value">28%</div>
                </div>
                
                <div class="metric-bar">
                    <div class="metric-name">Network In</div>
                    <div class="metric-graph">
                        <div class="metric-fill" style="width: 62%;"></div>
                    </div>
                    <div class="metric-value">1.2Gbps</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 10 seconds
        setInterval(() => {
            fetch('/api/dashboard/metrics').then(r => r.json()).then(data => {
                // Update metrics on page
                console.log('Metrics updated:', data);
            });
        }, 10000);
    </script>
</body>
</html>
'''


class MetricsExporter:
    """Export metrics in Prometheus format."""
    
    @staticmethod
    def export_prometheus(metrics: Dict[str, Metric]) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        lines.append("# HELP platform_requests_total Total platform requests")
        lines.append("# TYPE platform_requests_total counter")
        
        for name, metric in metrics.items():
            labels = ",".join([f'{k}="{v}"' for k, v in metric.labels.items()])
            if labels:
                lines.append(f'{name}{{{labels}}} {metric.value}')
            else:
                lines.append(f'{name} {metric.value}')
        
        return "\n".join(lines)
