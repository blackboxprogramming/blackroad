"""
Metrics Collection & Log Aggregation
Prometheus metrics and centralized logging
"""

import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import logging


class LogLevel(Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEntry:
    """Represents a log entry."""
    
    def __init__(self, level: LogLevel, message: str, 
                 source: str = "unknown", correlation_id: str = None):
        self.id = str(int(time.time() * 1000))
        self.timestamp = datetime.utcnow()
        self.level = level
        self.message = message
        self.source = source
        self.correlation_id = correlation_id or ""
        self.context: Dict[str, Any] = {}
        self.stack_trace: Optional[str] = None
    
    def add_context(self, key: str, value: Any) -> None:
        """Add context to log."""
        self.context[key] = value
    
    def set_stack_trace(self, trace: str) -> None:
        """Set stack trace."""
        self.stack_trace = trace
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'message': self.message,
            'source': self.source,
            'correlation_id': self.correlation_id,
            'context': self.context,
            'stack_trace': self.stack_trace,
        }


class LogAggregator:
    """Centralized log aggregation."""
    
    def __init__(self, max_logs: int = 100000):
        self.logs: List[LogEntry] = []
        self.max_logs = max_logs
        self.logger = logging.getLogger(__name__)
    
    def log(self, level: LogLevel, message: str, source: str = "app",
            correlation_id: str = None) -> LogEntry:
        """Log entry."""
        entry = LogEntry(level, message, source, correlation_id)
        self.logs.append(entry)
        
        # Keep size bounded
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
        
        return entry
    
    def debug(self, message: str, source: str = "app") -> LogEntry:
        """Log debug."""
        return self.log(LogLevel.DEBUG, message, source)
    
    def info(self, message: str, source: str = "app") -> LogEntry:
        """Log info."""
        return self.log(LogLevel.INFO, message, source)
    
    def warning(self, message: str, source: str = "app") -> LogEntry:
        """Log warning."""
        return self.log(LogLevel.WARNING, message, source)
    
    def error(self, message: str, source: str = "app") -> LogEntry:
        """Log error."""
        return self.log(LogLevel.ERROR, message, source)
    
    def critical(self, message: str, source: str = "app") -> LogEntry:
        """Log critical."""
        return self.log(LogLevel.CRITICAL, message, source)
    
    def search(self, query: str, level: Optional[LogLevel] = None,
              source: Optional[str] = None, limit: int = 100) -> List[LogEntry]:
        """Search logs."""
        results = []
        
        for log in reversed(self.logs):
            if query.lower() not in log.message.lower():
                continue
            
            if level and log.level != level:
                continue
            
            if source and log.source != source:
                continue
            
            results.append(log)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_logs_by_level(self, level: LogLevel, limit: int = 100) -> List[LogEntry]:
        """Get logs by level."""
        return [l for l in reversed(self.logs) if l.level == level][:limit]
    
    def get_logs_by_source(self, source: str, limit: int = 100) -> List[LogEntry]:
        """Get logs by source."""
        return [l for l in reversed(self.logs) if l.source == source][:limit]
    
    def get_logs_by_correlation_id(self, correlation_id: str) -> List[LogEntry]:
        """Get logs by correlation ID."""
        return [l for l in self.logs if l.correlation_id == correlation_id]
    
    def get_error_logs(self, hours: int = 1) -> List[LogEntry]:
        """Get error logs from last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        errors = [l for l in self.logs 
                 if l.level in [LogLevel.ERROR, LogLevel.CRITICAL]
                 and l.timestamp >= cutoff]
        return errors
    
    def get_statistics(self) -> Dict:
        """Get log statistics."""
        return {
            'total_logs': len(self.logs),
            'debug_count': sum(1 for l in self.logs if l.level == LogLevel.DEBUG),
            'info_count': sum(1 for l in self.logs if l.level == LogLevel.INFO),
            'warning_count': sum(1 for l in self.logs if l.level == LogLevel.WARNING),
            'error_count': sum(1 for l in self.logs if l.level == LogLevel.ERROR),
            'critical_count': sum(1 for l in self.logs if l.level == LogLevel.CRITICAL),
            'sources': list(set(l.source for l in self.logs)),
        }
    
    def export_json(self, limit: int = 1000) -> str:
        """Export logs as JSON."""
        logs_to_export = self.logs[-limit:]
        return json.dumps([l.to_dict() for l in logs_to_export], indent=2)
    
    def export_csv(self, limit: int = 1000) -> str:
        """Export logs as CSV."""
        logs_to_export = self.logs[-limit:]
        
        lines = ["timestamp,level,source,message,correlation_id"]
        for log in logs_to_export:
            escaped_msg = log.message.replace('"', '""')
            lines.append(
                f'{log.timestamp.isoformat()},"{log.level.value}","{log.source}",'
                f'"{escaped_msg}","{log.correlation_id}"'
            )
        
        return "\n".join(lines)


class MetricsCollector:
    """Collect and aggregate metrics."""
    
    def __init__(self):
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}
        self.timers: Dict[str, List[float]] = {}
        self.logger = logging.getLogger(__name__)
    
    def counter_increment(self, name: str, value: float = 1) -> None:
        """Increment counter."""
        if name not in self.counters:
            self.counters[name] = 0
        self.counters[name] += value
    
    def gauge_set(self, name: str, value: float) -> None:
        """Set gauge value."""
        self.gauges[name] = value
    
    def histogram_observe(self, name: str, value: float) -> None:
        """Record histogram observation."""
        if name not in self.histograms:
            self.histograms[name] = []
        self.histograms[name].append(value)
    
    def timer_start(self, name: str) -> float:
        """Start timer."""
        return time.time()
    
    def timer_end(self, name: str, start_time: float) -> None:
        """End timer."""
        duration = (time.time() - start_time) * 1000  # ms
        if name not in self.timers:
            self.timers[name] = []
        self.timers[name].append(duration)
    
    def get_counter(self, name: str) -> float:
        """Get counter value."""
        return self.counters.get(name, 0)
    
    def get_gauge(self, name: str) -> float:
        """Get gauge value."""
        return self.gauges.get(name, 0)
    
    def get_histogram_stats(self, name: str) -> Optional[Dict]:
        """Get histogram statistics."""
        if name not in self.histograms or not self.histograms[name]:
            return None
        
        values = sorted(self.histograms[name])
        n = len(values)
        
        return {
            'count': n,
            'min': values[0],
            'max': values[-1],
            'mean': sum(values) / n,
            'median': values[n // 2],
            'p95': values[int(n * 0.95)],
            'p99': values[int(n * 0.99)],
        }
    
    def get_timer_stats(self, name: str) -> Optional[Dict]:
        """Get timer statistics (in milliseconds)."""
        return self.get_histogram_stats(name)
    
    def export_prometheus(self) -> str:
        """Export in Prometheus format."""
        lines = []
        
        # Counters
        for name, value in self.counters.items():
            lines.append(f"# HELP {name} Counter metric")
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")
        
        # Gauges
        for name, value in self.gauges.items():
            lines.append(f"# HELP {name} Gauge metric")
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
        
        # Histograms
        for name, values in self.histograms.items():
            if values:
                stats = self.get_histogram_stats(name)
                lines.append(f"# HELP {name} Histogram metric")
                lines.append(f"# TYPE {name} histogram")
                lines.append(f'{name}_bucket{{le="1.0"}} {sum(1 for v in values if v <= 1.0)}')
                lines.append(f'{name}_bucket{{le="5.0"}} {sum(1 for v in values if v <= 5.0)}')
                lines.append(f'{name}_bucket{{le="10.0"}} {sum(1 for v in values if v <= 10.0)}')
                lines.append(f'{name}_count {len(values)}')
                lines.append(f'{name}_sum {sum(values)}')
        
        return "\n".join(lines)
    
    def get_all_metrics(self) -> Dict:
        """Get all metrics."""
        return {
            'counters': self.counters,
            'gauges': self.gauges,
            'histograms': {
                name: self.get_histogram_stats(name)
                for name in self.histograms.keys()
            },
            'timers': {
                name: self.get_timer_stats(name)
                for name in self.timers.keys()
            },
        }


class HealthCheck:
    """System health check."""
    
    def __init__(self):
        self.checks: Dict[str, bool] = {}
        self.last_check = datetime.utcnow()
    
    def register_check(self, name: str, status: bool, details: str = "") -> None:
        """Register health check."""
        self.checks[name] = status
        self.last_check = datetime.utcnow()
    
    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        return all(self.checks.values()) if self.checks else True
    
    def get_status(self) -> Dict:
        """Get health status."""
        return {
            'healthy': self.is_healthy(),
            'checks': self.checks,
            'last_check': self.last_check.isoformat(),
        }
