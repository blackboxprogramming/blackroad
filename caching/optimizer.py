"""Query optimization and execution planning."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class IndexType(Enum):
    """Index types."""
    PRIMARY = "primary"
    BTREE = "btree"
    HASH = "hash"
    COMPOSITE = "composite"


@dataclass
class QueryPlan:
    """Query execution plan."""
    query_id: str
    operations: List[str]
    estimated_cost: float
    actual_cost: Optional[float] = None
    indexes_used: List[str] = None


class QueryPlanner:
    """Query execution planner."""
    
    def __init__(self):
        self.indexes: Dict[str, IndexType] = {}
        self.table_stats: Dict[str, Dict[str, int]] = {}
    
    def add_index(self, index_name: str, table: str, columns: List[str], index_type: IndexType) -> bool:
        """Add index metadata."""
        self.indexes[index_name] = index_type
        return True
    
    def set_table_stats(self, table: str, row_count: int, avg_row_size: int) -> None:
        """Set table statistics."""
        self.table_stats[table] = {'row_count': row_count, 'avg_row_size': avg_row_size}
    
    def plan_query(self, query: str, tables: List[str]) -> QueryPlan:
        """Generate query execution plan."""
        operations = []
        cost = 0.0
        indexes_used = []
        
        for table in tables:
            if table in self.table_stats:
                row_count = self.table_stats[table]['row_count']
                # Full table scan cost estimation
                cost += row_count * 1.0
                operations.append(f"scan({table})")
            else:
                operations.append(f"scan({table})")
        
        # Check for applicable indexes
        for idx, idx_type in self.indexes.items():
            if idx_type in [IndexType.BTREE, IndexType.HASH]:
                cost *= 0.1  # 90% cost reduction with index
                indexes_used.append(idx)
                break
        
        return QueryPlan(
            query_id=hash(query) % 100000,
            operations=operations,
            estimated_cost=cost,
            indexes_used=indexes_used
        )


class PerformanceOptimizer:
    """Database performance optimizer."""
    
    def __init__(self):
        self.bottlenecks: List[Dict[str, Any]] = []
        self.recommendations: List[str] = []
    
    def analyze_slow_queries(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze slow-running queries."""
        slow = [q for q in queries if q.get('duration_ms', 0) > 100]
        self.bottlenecks = slow
        
        for query in slow:
            self.recommendations.append(f"Consider indexing: {query.get('table', 'unknown')}")
        
        return slow
    
    def get_recommendations(self) -> List[str]:
        """Get optimization recommendations."""
        return self.recommendations
    
    def estimate_improvement(self, plan: QueryPlan, optimization: str) -> float:
        """Estimate performance improvement percentage."""
        if 'index' in optimization.lower():
            return 0.85  # 85% improvement
        elif 'partition' in optimization.lower():
            return 0.70
        elif 'materialized_view' in optimization.lower():
            return 0.90
        return 0.0


class ConnectionPool:
    """Database connection pooling."""
    
    def __init__(self, max_connections: int = 50):
        self.max_connections = max_connections
        self.available_connections = max_connections
        self.total_connections = 0
        self.wait_time_ms = 0
    
    def get_connection(self) -> bool:
        """Get connection from pool."""
        if self.available_connections > 0:
            self.available_connections -= 1
            self.total_connections += 1
            return True
        return False
    
    def release_connection(self) -> bool:
        """Release connection back to pool."""
        if self.total_connections > 0:
            self.available_connections += 1
            self.total_connections -= 1
            return True
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get pool status."""
        return {
            'max_connections': self.max_connections,
            'available': self.available_connections,
            'in_use': self.max_connections - self.available_connections,
            'utilization_percent': ((self.max_connections - self.available_connections) / self.max_connections * 100),
        }
