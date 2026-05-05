"""Data warehouse with star schema and aggregations."""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import json


@dataclass
class FactRow:
    """A fact table row."""
    fact_id: str
    date_id: int
    user_id: str
    event_type: str
    metric_value: float = 1.0
    revenue: float = 0.0
    quantity: int = 1
    properties: Dict[str, Any] = None


@dataclass
class DimensionRow:
    """A dimension table row."""
    dim_id: int
    name: str
    properties: Dict[str, Any]


class FactTable:
    """Fact table for events and metrics."""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.rows: List[FactRow] = []
        self.index = defaultdict(list)
    
    def insert(self, row: FactRow) -> bool:
        """Insert fact row."""
        self.rows.append(row)
        self.index[row.date_id].append(row)
        return True
    
    def query(self, date_range: Tuple[int, int], filters: Dict[str, Any] = None) -> List[FactRow]:
        """Query fact table."""
        results = []
        start_date, end_date = date_range
        
        for date_id in range(start_date, end_date + 1):
            results.extend(self.index.get(date_id, []))
        
        # Apply filters
        if filters:
            results = [
                r for r in results
                if all(getattr(r, k, None) == v for k, v in filters.items())
            ]
        
        return results
    
    def get_row_count(self) -> int:
        """Get row count."""
        return len(self.rows)


class DimensionTable:
    """Dimension table for attributes."""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.rows: Dict[int, DimensionRow] = {}
        self.next_id = 1
    
    def insert(self, name: str, properties: Dict[str, Any]) -> int:
        """Insert dimension row."""
        dim_id = self.next_id
        self.rows[dim_id] = DimensionRow(dim_id, name, properties or {})
        self.next_id += 1
        return dim_id
    
    def get(self, dim_id: int) -> Optional[DimensionRow]:
        """Get dimension row."""
        return self.rows.get(dim_id)
    
    def get_by_name(self, name: str) -> Optional[DimensionRow]:
        """Get dimension by name."""
        for row in self.rows.values():
            if row.name == name:
                return row
        return None
    
    def get_row_count(self) -> int:
        """Get row count."""
        return len(self.rows)


class DataWarehouse:
    """Star schema data warehouse."""
    
    def __init__(self):
        """Initialize warehouse."""
        self.fact_tables: Dict[str, FactTable] = {}
        self.dimension_tables: Dict[str, DimensionTable] = {}
        self.aggregations: Dict[str, Dict[str, Any]] = {}
        self.metrics = {
            'total_rows': 0,
            'fact_tables': 0,
            'dimension_tables': 0,
        }
    
    def create_fact_table(self, table_name: str) -> FactTable:
        """Create fact table."""
        table = FactTable(table_name)
        self.fact_tables[table_name] = table
        self.metrics['fact_tables'] += 1
        return table
    
    def create_dimension_table(self, table_name: str) -> DimensionTable:
        """Create dimension table."""
        table = DimensionTable(table_name)
        self.dimension_tables[table_name] = table
        self.metrics['dimension_tables'] += 1
        return table
    
    def get_fact_table(self, table_name: str) -> Optional[FactTable]:
        """Get fact table."""
        return self.fact_tables.get(table_name)
    
    def get_dimension_table(self, table_name: str) -> Optional[DimensionTable]:
        """Get dimension table."""
        return self.dimension_tables.get(table_name)
    
    def insert_fact(self, table_name: str, row: FactRow) -> bool:
        """Insert fact row."""
        table = self.fact_tables.get(table_name)
        if not table:
            return False
        table.insert(row)
        self.metrics['total_rows'] += 1
        return True
    
    def compute_rollup(
        self,
        fact_table: str,
        dimensions: List[str],
        measure: str = 'revenue'
    ) -> Dict[str, float]:
        """Compute rollup aggregation."""
        table = self.fact_tables.get(fact_table)
        if not table:
            return {}
        
        rollup = defaultdict(float)
        
        for row in table.rows:
            key = f"{row.event_type}"
            if measure == 'revenue':
                rollup[key] += row.revenue
            elif measure == 'count':
                rollup[key] += 1
            elif measure == 'quantity':
                rollup[key] += row.quantity
        
        return dict(rollup)
    
    def compute_daily_rollup(self, fact_table: str) -> Dict[int, float]:
        """Compute daily rollup."""
        table = self.fact_tables.get(fact_table)
        if not table:
            return {}
        
        daily = defaultdict(float)
        for row in table.rows:
            daily[row.date_id] += row.revenue
        
        return dict(daily)
    
    def compute_cohort_analysis(
        self,
        cohort_column: str,
        value_column: str
    ) -> Dict[str, float]:
        """Compute cohort analysis."""
        cohort_data = defaultdict(float)
        
        for table in self.fact_tables.values():
            for row in table.rows:
                cohort_key = getattr(row, cohort_column, 'unknown')
                value = getattr(row, value_column, 0)
                cohort_data[str(cohort_key)] += value
        
        return dict(cohort_data)
    
    def get_warehouse_metrics(self) -> Dict[str, Any]:
        """Get warehouse metrics."""
        return {
            'total_rows': self.metrics['total_rows'],
            'fact_tables': self.metrics['fact_tables'],
            'dimension_tables': self.metrics['dimension_tables'],
            'total_fact_rows': sum(
                t.get_row_count() for t in self.fact_tables.values()
            ),
            'total_dimension_rows': sum(
                t.get_row_count() for t in self.dimension_tables.values()
            ),
        }
