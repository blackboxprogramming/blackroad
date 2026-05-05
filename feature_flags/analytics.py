"""Feature flag analytics."""

from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime


class FlagMetrics:
    """Tracks flag metrics."""
    
    def __init__(self, flag_id: str):
        self.flag_id = flag_id
        self.total_evaluations = 0
        self.enabled_count = 0
        self.disabled_count = 0
        self.variant_usage: Dict[str, int] = defaultdict(int)
        self.evaluations_by_user: Dict[str, int] = defaultdict(int)
        self.last_evaluated_at: Optional[datetime] = None
    
    def record_evaluation(self, result: bool, variant: Optional[str] = None, user_id: str = None) -> None:
        """Record evaluation."""
        self.total_evaluations += 1
        if result:
            self.enabled_count += 1
        else:
            self.disabled_count += 1
        
        if variant:
            self.variant_usage[variant] += 1
        
        if user_id:
            self.evaluations_by_user[user_id] += 1
        
        self.last_evaluated_at = datetime.utcnow()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics."""
        enabled_rate = (self.enabled_count / max(self.total_evaluations, 1)) * 100
        
        return {
            'flag_id': self.flag_id,
            'total_evaluations': self.total_evaluations,
            'enabled_count': self.enabled_count,
            'disabled_count': self.disabled_count,
            'enabled_rate_percent': enabled_rate,
            'unique_users': len(self.evaluations_by_user),
            'variants': dict(self.variant_usage),
            'last_evaluated': self.last_evaluated_at.isoformat() if self.last_evaluated_at else None,
        }


class AnalyticsCollector:
    """Collects flag analytics."""
    
    def __init__(self):
        self.metrics: Dict[str, FlagMetrics] = {}
        self.events: List[Dict[str, Any]] = []
    
    def record_evaluation(self, flag_id: str, result: bool, context: Dict[str, Any] = None) -> None:
        """Record flag evaluation."""
        if flag_id not in self.metrics:
            self.metrics[flag_id] = FlagMetrics(flag_id)
        
        variant = context.get('variant') if context else None
        user_id = context.get('user_id') if context else None
        
        self.metrics[flag_id].record_evaluation(result, variant, user_id)
        
        self.events.append({
            'flag_id': flag_id,
            'result': result,
            'user_id': user_id,
            'variant': variant,
            'timestamp': datetime.utcnow().isoformat(),
        })
    
    def get_flag_metrics(self, flag_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for flag."""
        if flag_id not in self.metrics:
            return None
        return self.metrics[flag_id].get_metrics()
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all flags."""
        return {flag_id: metrics.get_metrics() for flag_id, metrics in self.metrics.items()}
    
    def get_top_flags_by_usage(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top flags by evaluation count."""
        flags = sorted(
            [(fid, m.total_evaluations) for fid, m in self.metrics.items()],
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        return [{'flag_id': fid, 'evaluations': count} for fid, count in flags]
    
    def get_event_count(self) -> int:
        """Get total events recorded."""
        return len(self.events)
