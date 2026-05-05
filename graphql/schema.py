"""GraphQL schema and query engine."""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json


class FieldType(Enum):
    """GraphQL field types."""
    STRING = "String"
    INT = "Int"
    FLOAT = "Float"
    BOOLEAN = "Boolean"
    ID = "ID"
    LIST = "List"
    OBJECT = "Object"


@dataclass
class Field:
    """GraphQL field definition."""
    name: str
    field_type: FieldType
    resolver: Optional[Callable] = None
    required: bool = False
    description: str = ""


@dataclass
class Type:
    """GraphQL type definition."""
    name: str
    fields: Dict[str, Field]
    description: str = ""


class SchemaBuilder:
    """Builds GraphQL schema."""
    
    def __init__(self):
        self.types: Dict[str, Type] = {}
        self.queries: Dict[str, Field] = {}
        self.mutations: Dict[str, Field] = {}
    
    def add_type(self, name: str, fields: Dict[str, Field], description: str = "") -> None:
        """Add type to schema."""
        self.types[name] = Type(name, fields, description)
    
    def add_query(self, name: str, field_type: FieldType, resolver: Callable, required: bool = False) -> None:
        """Add query root field."""
        self.queries[name] = Field(name, field_type, resolver, required)
    
    def add_mutation(self, name: str, field_type: FieldType, resolver: Callable, required: bool = False) -> None:
        """Add mutation root field."""
        self.mutations[name] = Field(name, field_type, resolver, required)
    
    def build(self) -> Dict[str, Any]:
        """Build schema definition."""
        return {
            'types': list(self.types.keys()),
            'queries': list(self.queries.keys()),
            'mutations': list(self.mutations.keys()),
            'type_count': len(self.types),
            'query_count': len(self.queries),
            'mutation_count': len(self.mutations),
        }
    
    def get_type(self, name: str) -> Optional[Type]:
        """Get type by name."""
        return self.types.get(name)
    
    def get_schema_sdl(self) -> str:
        """Get schema as SDL."""
        sdl = "type Query {\n"
        for name, field in self.queries.items():
            sdl += f"  {name}: {field.field_type.value}\n"
        sdl += "}\n"
        
        sdl += "\ntype Mutation {\n"
        for name, field in self.mutations.items():
            sdl += f"  {name}: {field.field_type.value}\n"
        sdl += "}\n"
        
        return sdl


class QueryExecutor:
    """Executes GraphQL queries."""
    
    def __init__(self, schema: SchemaBuilder):
        self.schema = schema
        self.execution_time_ms = 0
    
    def execute(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute GraphQL query."""
        import time
        start = time.time()
        
        # Parse query (simplified)
        if not query or len(query) == 0:
            return {'errors': ['Empty query']}
        
        # Extract field names (simple parsing)
        fields = self._extract_fields(query)
        result = {}
        
        for field in fields:
            if field in self.schema.queries:
                resolver = self.schema.queries[field].resolver
                if resolver:
                    result[field] = resolver(variables or {})
                else:
                    result[field] = None
        
        self.execution_time_ms = (time.time() - start) * 1000
        
        return {
            'data': result,
            'execution_time_ms': self.execution_time_ms,
        }
    
    def _extract_fields(self, query: str) -> List[str]:
        """Extract field names from query."""
        # Simple field extraction
        fields = []
        lines = query.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('{') and not line.startswith('}'):
                field = line.split('(')[0].strip()
                if field and field != 'query' and field != 'Query':
                    fields.append(field)
        return fields


class QueryPlan:
    """Query execution plan."""
    
    def __init__(self, query: str):
        self.query = query
        self.fields: List[str] = []
        self.depth = 0
        self.estimated_cost = 0.0
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze query complexity."""
        self.depth = self._calculate_depth()
        self.estimated_cost = self.depth * 10.0
        
        return {
            'depth': self.depth,
            'fields': len(self.fields),
            'estimated_cost': self.estimated_cost,
            'complexity_level': 'low' if self.estimated_cost < 50 else 'medium' if self.estimated_cost < 100 else 'high',
        }
    
    def _calculate_depth(self) -> int:
        """Calculate query depth."""
        count = 0
        for char in self.query:
            if char == '{':
                count += 1
        return count


class ValidationEngine:
    """Validates GraphQL queries."""
    
    def __init__(self, schema: SchemaBuilder):
        self.schema = schema
        self.errors: List[str] = []
    
    def validate(self, query: str) -> bool:
        """Validate query against schema."""
        self.errors = []
        
        # Check query syntax
        if not query or len(query) == 0:
            self.errors.append("Query is empty")
            return False
        
        if query.count('{') != query.count('}'):
            self.errors.append("Query has unmatched braces")
            return False
        
        # Check fields exist in schema
        fields = self._extract_fields(query)
        if not fields:
            # No fields extracted, query is valid structure but no content
            return True
            
        for field in fields:
            # Only validate if schema has queries/mutations defined
            if self.schema.queries or self.schema.mutations:
                if field not in self.schema.queries and field not in self.schema.mutations:
                    self.errors.append(f"Field '{field}' not found in schema")
        
        return len(self.errors) == 0
    
    def _extract_fields(self, query: str) -> List[str]:
        """Extract field names from query."""
        fields = []
        # Remove brackets and split into tokens
        clean_query = query.replace('{', ' ').replace('}', ' ')
        tokens = clean_query.split()
        for token in tokens:
            token = token.strip()
            if token and token != 'query' and token != 'Query':
                field = token.split('(')[0]
                if field:
                    fields.append(field)
        return fields
    
    def get_errors(self) -> List[str]:
        """Get validation errors."""
        return self.errors
