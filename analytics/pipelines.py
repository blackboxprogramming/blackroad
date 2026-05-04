"""ETL pipelines for data transformation."""

from typing import Dict, List, Any, Callable, Optional
from datetime import datetime
from collections import defaultdict


class ETLPipeline:
    """ETL pipeline for data transformation."""
    
    def __init__(self, pipeline_id: str):
        self.pipeline_id = pipeline_id
        self.transformations: List[Callable] = []
        self.loaded_rows = 0
    
    def add_transformation(self, transform_fn: Callable) -> None:
        """Add transformation step."""
        self.transformations.append(transform_fn)
    
    def extract(self, source_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract data."""
        return source_data
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply transformations."""
        for transform in self.transformations:
            data = [transform(row) for row in data]
        return data
    
    def load(self, data: List[Dict[str, Any]], warehouse) -> int:
        """Load data to warehouse."""
        from analytics.warehouse import FactRow
        for row in data:
            if isinstance(row, dict):
                fact_row = FactRow(
                    fact_id=row.get('fact_id', 'f1'),
                    date_id=row.get('date_id', 20240101),
                    user_id=row.get('user_id', 'unknown'),
                    event_type=row.get('event_type', 'click'),
                    revenue=row.get('revenue', 0.0),
                )
                warehouse.insert_fact('events_fact', fact_row)
            else:
                warehouse.insert_fact('events_fact', row)
        self.loaded_rows += len(data)
        return len(data)
    
    def run(self, source_data: List[Dict[str, Any]], warehouse) -> Dict[str, Any]:
        """Execute ETL pipeline."""
        extracted = self.extract(source_data)
        transformed = self.transform(extracted)
        loaded = self.load(transformed, warehouse)
        
        return {
            'pipeline_id': self.pipeline_id,
            'rows_extracted': len(extracted),
            'rows_transformed': len(transformed),
            'rows_loaded': loaded,
            'timestamp': datetime.utcnow().isoformat(),
        }


class DataValidator:
    """Validates data quality."""
    
    def __init__(self):
        self.validation_rules = {}
        self.error_log = []
    
    def add_rule(self, field: str, validator: Callable) -> None:
        """Add validation rule."""
        self.validation_rules[field] = validator
    
    def validate(self, row: Dict[str, Any]) -> bool:
        """Validate row."""
        for field, validator in self.validation_rules.items():
            if field not in row:
                self.error_log.append(f"Missing field: {field}")
                return False
            try:
                if not validator(row[field]):
                    self.error_log.append(f"Invalid {field}: {row[field]}")
                    return False
            except Exception as e:
                self.error_log.append(f"Validation error for {field}: {str(e)}")
                return False
        return True
    
    def validate_batch(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate batch."""
        valid = 0
        invalid = 0
        
        for row in rows:
            if self.validate(row):
                valid += 1
            else:
                invalid += 1
        
        return {
            'valid_rows': valid,
            'invalid_rows': invalid,
            'total_rows': len(rows),
            'error_count': len(self.error_log),
            'errors': self.error_log[-10:],  # Last 10
        }
