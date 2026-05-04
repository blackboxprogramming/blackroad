"""Search analytics and metrics collection."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict, Counter


@dataclass
class SearchQuery:
    """Recorded search query."""
    query: str
    result_count: int
    exec_time_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    query_type: str = "normal"  # normal, phrase, suggest

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'query': self.query,
            'result_count': self.result_count,
            'exec_time_ms': round(self.exec_time_ms, 2),
            'timestamp': self.timestamp.isoformat(),
            'query_type': self.query_type
        }


class SearchAnalytics:
    """Track search metrics and analytics."""

    def __init__(self, max_queries: int = 10000):
        self.max_queries = max_queries
        self.queries: List[SearchQuery] = []
        self.metrics = {
            'total_searches': 0,
            'zero_result_searches': 0,
            'avg_exec_time_ms': 0.0,
            'avg_result_count': 0.0,
        }

    def record_search(self, query: str, result_count: int, exec_time_ms: float,
                     query_type: str = "normal") -> SearchQuery:
        """Record search query."""
        search_query = SearchQuery(
            query=query,
            result_count=result_count,
            exec_time_ms=exec_time_ms,
            query_type=query_type
        )

        if len(self.queries) < self.max_queries:
            self.queries.append(search_query)
        else:
            # Remove oldest if at capacity
            self.queries.pop(0)
            self.queries.append(search_query)

        # Update metrics
        self.metrics['total_searches'] += 1
        if result_count == 0:
            self.metrics['zero_result_searches'] += 1

        # Calculate averages
        if self.queries:
            self.metrics['avg_exec_time_ms'] = sum(q.exec_time_ms for q in self.queries) / len(self.queries)
            self.metrics['avg_result_count'] = sum(q.result_count for q in self.queries) / len(self.queries)

        return search_query

    def get_trending_queries(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get trending search queries."""
        query_counts = Counter(q.query for q in self.queries)
        return query_counts.most_common(limit)

    def get_zero_result_queries(self, limit: int = 10) -> List[str]:
        """Get queries with no results."""
        zero_queries = [q.query for q in self.queries if q.result_count == 0]
        counter = Counter(zero_queries)
        return [q for q, _ in counter.most_common(limit)]

    def get_query_performance(self) -> Dict[str, Any]:
        """Get query performance metrics."""
        if not self.queries:
            return {
                'total_searches': 0,
                'zero_result_searches': 0,
                'avg_exec_time_ms': 0.0,
                'avg_result_count': 0.0,
                'min_exec_time_ms': 0.0,
                'max_exec_time_ms': 0.0,
                'p95_exec_time_ms': 0.0,
            }

        exec_times = [q.exec_time_ms for q in self.queries]
        exec_times_sorted = sorted(exec_times)

        p95_index = int(len(exec_times_sorted) * 0.95)

        return {
            'total_searches': self.metrics['total_searches'],
            'zero_result_searches': self.metrics['zero_result_searches'],
            'zero_result_percent': (
                self.metrics['zero_result_searches'] / self.metrics['total_searches'] * 100
                if self.metrics['total_searches'] > 0 else 0
            ),
            'avg_exec_time_ms': round(self.metrics['avg_exec_time_ms'], 2),
            'avg_result_count': round(self.metrics['avg_result_count'], 2),
            'min_exec_time_ms': round(min(exec_times_sorted), 2),
            'max_exec_time_ms': round(max(exec_times_sorted), 2),
            'p95_exec_time_ms': round(exec_times_sorted[p95_index], 2) if exec_times_sorted else 0.0,
        }

    def get_query_types_breakdown(self) -> Dict[str, Any]:
        """Get breakdown by query type."""
        type_counts = defaultdict(int)
        type_times = defaultdict(float)

        for q in self.queries:
            type_counts[q.query_type] += 1
            type_times[q.query_type] += q.exec_time_ms

        breakdown = {}
        for query_type, count in type_counts.items():
            avg_time = type_times[query_type] / count
            breakdown[query_type] = {
                'count': count,
                'avg_time_ms': round(avg_time, 2),
                'percent': round(count / len(self.queries) * 100, 1) if self.queries else 0.0
            }

        return breakdown

    def get_recent_queries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent search queries."""
        recent = sorted(self.queries, key=lambda q: q.timestamp, reverse=True)[:limit]
        return [q.to_dict() for q in recent]

    def get_metrics(self) -> Dict[str, Any]:
        """Get all analytics metrics."""
        return {
            'queries_recorded': len(self.queries),
            'total_searches': self.metrics['total_searches'],
            'performance': self.get_query_performance(),
            'query_types': self.get_query_types_breakdown(),
            'trending': dict(self.get_trending_queries(10)),
            'zero_results': self.get_zero_result_queries(5),
        }
