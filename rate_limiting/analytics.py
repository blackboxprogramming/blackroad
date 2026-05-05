"""Rate limiting analytics and metrics."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict


class MetricType(Enum):
    """Metric types."""
    TOTAL_REQUESTS = "total_requests"
    ALLOWED_REQUESTS = "allowed_requests"
    REJECTED_REQUESTS = "rejected_requests"
    AVERAGE_WAIT_TIME = "average_wait_time"
    PEAK_REQUESTS = "peak_requests"


@dataclass
class RateLimitMetrics:
    """Rate limit metrics."""
    identifier: str
    total_requests: int = 0
    allowed_requests: int = 0
    rejected_requests: int = 0
    total_wait_time: float = 0.0
    peak_requests_per_second: float = 0.0
    current_penalty_count: int = 0
    last_check_time: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'identifier': self.identifier,
            'total_requests': self.total_requests,
            'allowed_requests': self.allowed_requests,
            'rejected_requests': self.rejected_requests,
            'rejection_rate': self.rejection_rate,
            'average_wait_time': self.average_wait_time,
            'peak_requests_per_second': self.peak_requests_per_second,
            'current_penalty_count': self.current_penalty_count,
            'created_at': self.created_at.isoformat()
        }
    
    @property
    def rejection_rate(self) -> float:
        """Get rejection rate."""
        if self.total_requests == 0:
            return 0.0
        return self.rejected_requests / self.total_requests
    
    @property
    def average_wait_time(self) -> float:
        """Get average wait time."""
        if self.rejected_requests == 0:
            return 0.0
        return self.total_wait_time / self.rejected_requests


class RateLimitAnalytics:
    """Rate limiting analytics engine."""
    
    def __init__(self, max_entries: int = 10000):
        """Initialize analytics."""
        self.max_entries = max_entries
        self.metrics: dict = {}
        self.time_series: dict = defaultdict(list)
        self.hourly_stats: dict = defaultdict(lambda: {
            'requests': 0,
            'rejections': 0,
            'hour': None
        })
    
    def record_request(self, identifier: str, allowed: bool, wait_time: float = 0.0):
        """Record a rate limit check."""
        if len(self.metrics) > self.max_entries:
            raise RuntimeError(f"Analytics entries limit exceeded: {self.max_entries}")
        
        if identifier not in self.metrics:
            self.metrics[identifier] = RateLimitMetrics(identifier=identifier)
        
        metrics = self.metrics[identifier]
        metrics.total_requests += 1
        metrics.last_check_time = datetime.utcnow()
        
        if allowed:
            metrics.allowed_requests += 1
        else:
            metrics.rejected_requests += 1
            metrics.total_wait_time += wait_time
        
        # Record time series
        now = datetime.utcnow()
        self.time_series[identifier].append({
            'timestamp': now,
            'allowed': allowed,
            'wait_time': wait_time
        })
        
        # Update hourly stats
        hour_key = now.strftime('%Y-%m-%d %H:00')
        self.hourly_stats[hour_key]['requests'] += 1
        if not allowed:
            self.hourly_stats[hour_key]['rejections'] += 1
    
    def get_metrics(self, identifier: str = None) -> dict:
        """Get metrics for identifier or all."""
        if identifier:
            if identifier in self.metrics:
                return self.metrics[identifier].to_dict()
            return None
        
        return {
            'total_identifiers': len(self.metrics),
            'total_requests': sum(m.total_requests for m in self.metrics.values()),
            'total_allowed': sum(m.allowed_requests for m in self.metrics.values()),
            'total_rejected': sum(m.rejected_requests for m in self.metrics.values()),
            'average_rejection_rate': sum(m.rejection_rate for m in self.metrics.values()) / max(1, len(self.metrics))
        }
    
    def get_top_rejected(self, limit: int = 10) -> list:
        """Get top rejected identifiers."""
        sorted_metrics = sorted(
            self.metrics.values(),
            key=lambda m: m.rejected_requests,
            reverse=True
        )
        return [m.to_dict() for m in sorted_metrics[:limit]]
    
    def get_top_requested(self, limit: int = 10) -> list:
        """Get top requested identifiers."""
        sorted_metrics = sorted(
            self.metrics.values(),
            key=lambda m: m.total_requests,
            reverse=True
        )
        return [m.to_dict() for m in sorted_metrics[:limit]]
    
    def get_hourly_stats(self, hours: int = 24) -> list:
        """Get hourly statistics."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        stats = []
        for hour_key, data in sorted(self.hourly_stats.items()):
            try:
                hour_time = datetime.strptime(hour_key, '%Y-%m-%d %H:%M')
                if hour_time > cutoff:
                    stats.append({
                        'hour': hour_key,
                        'requests': data['requests'],
                        'rejections': data['rejections'],
                        'rejection_rate': data['rejections'] / max(1, data['requests'])
                    })
            except ValueError:
                continue
        
        return stats
    
    def get_percentile_rejection_rate(self, percentile: int = 95) -> float:
        """Get percentile rejection rate across identifiers."""
        if not self.metrics:
            return 0.0
        
        rates = sorted(m.rejection_rate for m in self.metrics.values())
        idx = int(len(rates) * (percentile / 100))
        return rates[min(idx, len(rates) - 1)]
    
    def reset_metrics(self, identifier: str = None):
        """Reset metrics."""
        if identifier:
            if identifier in self.metrics:
                del self.metrics[identifier]
            if identifier in self.time_series:
                del self.time_series[identifier]
        else:
            self.metrics.clear()
            self.time_series.clear()
            self.hourly_stats.clear()
    
    def export_metrics(self, identifier: str = None) -> list:
        """Export metrics to list."""
        if identifier:
            if identifier in self.metrics:
                return [self.metrics[identifier].to_dict()]
            return []
        
        return [m.to_dict() for m in self.metrics.values()]
