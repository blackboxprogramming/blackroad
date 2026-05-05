"""Analytics engine with metrics and reporting."""

from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta


class AnalyticsEngine:
    """Analytics engine for metrics calculation."""
    
    def __init__(self, warehouse):
        """Initialize analytics engine."""
        self.warehouse = warehouse
        self.cache = {}
    
    def calculate_funnel(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate funnel metrics."""
        stages = []
        stage_users = defaultdict(set)
        
        for event in events:
            event_type = event.get('event_type')
            user_id = event.get('user_id')
            
            stages.append(event_type)
            stage_users[event_type].add(user_id)
        
        unique_stages = list(dict.fromkeys(stages))
        
        funnel = {}
        for i, stage in enumerate(unique_stages):
            users = len(stage_users[stage])
            funnel[stage] = users
            if i > 0:
                prev_stage = unique_stages[i-1]
                prev_users = len(stage_users[prev_stage])
                if prev_users > 0:
                    conversion = (users / prev_users) * 100
                else:
                    conversion = 0
                funnel[f"{stage}_conversion"] = f"{conversion:.1f}%"
        
        return funnel
    
    def calculate_retention(self, cohort_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate retention metrics."""
        retention = {}
        
        if not cohort_data:
            return retention
        
        values = list(cohort_data.values())
        if len(values) > 0:
            first_value = values[0]
            for period, value in enumerate(cohort_data.items()):
                key, val = value
                if first_value > 0:
                    retention_rate = (val / first_value) * 100
                else:
                    retention_rate = 0
                retention[f"period_{period}"] = retention_rate
        
        return retention
    
    def calculate_ltv(self, revenue: float, churn_rate: float, margin: float = 0.4) -> float:
        """Calculate lifetime value."""
        if churn_rate <= 0 or churn_rate >= 1:
            return 0
        monthly_churn = churn_rate / 12
        if monthly_churn >= 1:
            return 0
        return (revenue * margin) / monthly_churn
    
    def calculate_arpu(self, total_revenue: float, user_count: int) -> float:
        """Calculate average revenue per user."""
        if user_count == 0:
            return 0
        return total_revenue / user_count
    
    def get_metrics_report(self) -> Dict[str, Any]:
        """Get comprehensive metrics report."""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': {
                'total_events': self._count_total_events(),
                'unique_users': self._count_unique_users(),
                'total_revenue': self._sum_revenue(),
            }
        }
        return report
    
    def _count_total_events(self) -> int:
        """Count total events."""
        count = 0
        for table in self.warehouse.fact_tables.values():
            count += table.get_row_count()
        return count
    
    def _count_unique_users(self) -> int:
        """Count unique users."""
        users = set()
        for table in self.warehouse.fact_tables.values():
            for row in table.rows:
                users.add(row.user_id)
        return len(users)
    
    def _sum_revenue(self) -> float:
        """Sum all revenue."""
        total = 0.0
        for table in self.warehouse.fact_tables.values():
            for row in table.rows:
                total += row.revenue
        return total
