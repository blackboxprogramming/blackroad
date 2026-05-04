"""Advanced caching system with multi-layer strategies."""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import OrderedDict
import hashlib
import json


@dataclass
class CacheEntry:
    """A cache entry with metadata."""
    key: str
    value: Any
    ttl: int  # seconds
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    size_bytes: int = 0


class LRUCache:
    """Least Recently Used cache."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.hits = 0
        self.misses = 0
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set cache entry."""
        if key in self.cache:
            self.cache.move_to_end(key)
        
        size = len(json.dumps(value).encode('utf-8'))
        entry = CacheEntry(
            key=key,
            value=value,
            ttl=ttl,
            created_at=datetime.utcnow(),
            accessed_at=datetime.utcnow(),
            size_bytes=size
        )
        self.cache[key] = entry
        
        # Evict oldest if over capacity
        while len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
        
        return True
    
    def get(self, key: str) -> Optional[Any]:
        """Get cache entry."""
        if key not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[key]
        
        # Check TTL
        age = (datetime.utcnow() - entry.created_at).total_seconds()
        if age > entry.ttl:
            del self.cache[key]
            self.misses += 1
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        entry.accessed_at = datetime.utcnow()
        entry.access_count += 1
        self.hits += 1
        return entry.value
    
    def get_hit_rate(self) -> float:
        """Get cache hit rate."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.get_hit_rate(),
        }


class BloomFilter:
    """Probabilistic data structure for fast membership testing."""
    
    def __init__(self, size: int = 10000, num_hashes: int = 3):
        self.size = size
        self.num_hashes = num_hashes
        self.bits = [False] * size
    
    def _hash(self, item: str, seed: int) -> int:
        """Hash function with seed."""
        h = hashlib.md5(f"{item}{seed}".encode()).hexdigest()
        return int(h, 16) % self.size
    
    def add(self, item: str) -> None:
        """Add item to filter."""
        for i in range(self.num_hashes):
            idx = self._hash(item, i)
            self.bits[idx] = True
    
    def contains(self, item: str) -> bool:
        """Check if item might be in set."""
        for i in range(self.num_hashes):
            idx = self._hash(item, i)
            if not self.bits[idx]:
                return False
        return True


class QueryCache:
    """Cache for database query results."""
    
    def __init__(self, cache_size: int = 500):
        self.cache = LRUCache(max_size=cache_size)
        self.query_map: Dict[str, str] = {}  # key -> query mapping
        self.table_queries: Dict[str, List[str]] = {}  # table -> queries
    
    def set_query_result(self, query: str, result: Any, ttl: int = 300) -> bool:
        """Cache query result."""
        key = self._make_key(query)
        self.cache.set(key, result, ttl)
        self.query_map[key] = query
        
        # Track which tables this query uses
        for table in self._extract_tables(query):
            if table not in self.table_queries:
                self.table_queries[table] = []
            self.table_queries[table].append(key)
        
        return True
    
    def get_query_result(self, query: str) -> Optional[Any]:
        """Get cached query result."""
        key = self._make_key(query)
        return self.cache.get(key)
    
    def invalidate_by_table(self, table_name: str) -> int:
        """Invalidate queries touching a table."""
        count = 0
        table_upper = table_name.upper()
        keys_to_remove = self.table_queries.get(table_upper, [])
        
        for key in keys_to_remove:
            if key in self.cache.cache:
                del self.cache.cache[key]
                count += 1
        
        if table_upper in self.table_queries:
            del self.table_queries[table_upper]
        
        return count
    
    def _make_key(self, query: str) -> str:
        """Generate cache key from query."""
        return hashlib.md5(query.encode()).hexdigest()
    
    def _extract_tables(self, query: str) -> List[str]:
        """Extract table names from query."""
        tables = []
        query_upper = query.upper()
        if 'FROM' in query_upper:
            parts = query_upper.split('FROM')
            if len(parts) > 1:
                table_part = parts[1].split('WHERE')[0].strip()
                tables = [t.strip() for t in table_part.split(',')]
        return tables


class DistributedCache:
    """Distributed cache layer."""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.local_cache = LRUCache(max_size=1000)
        self.sync_log: List[Dict[str, Any]] = []
    
    def replicate(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Replicate cache entry."""
        self.local_cache.set(key, value, ttl)
        self.sync_log.append({
            'node': self.node_id,
            'action': 'set',
            'key': key,
            'timestamp': datetime.utcnow().isoformat(),
        })
        return True
    
    def invalidate_across_nodes(self, key: str) -> Dict[str, bool]:
        """Invalidate key on all nodes."""
        if key in self.local_cache.cache:
            del self.local_cache.cache[key]
        
        self.sync_log.append({
            'node': self.node_id,
            'action': 'invalidate',
            'key': key,
            'timestamp': datetime.utcnow().isoformat(),
        })
        
        return {'this_node': True}
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get replication status."""
        return {
            'node_id': self.node_id,
            'local_cache_size': len(self.local_cache.cache),
            'sync_events': len(self.sync_log),
            'last_sync': self.sync_log[-1] if self.sync_log else None,
        }


class CacheWarmer:
    """Pre-load cache with popular data."""
    
    def __init__(self, cache: LRUCache):
        self.cache = cache
        self.warm_strategies = {}
    
    def add_strategy(self, name: str, loader: Callable[[], Dict[str, Any]]) -> None:
        """Add warming strategy."""
        self.warm_strategies[name] = loader
    
    def warm_cache(self, strategy_name: str) -> Dict[str, int]:
        """Execute warming strategy."""
        if strategy_name not in self.warm_strategies:
            return {'error': 'Strategy not found'}
        
        loader = self.warm_strategies[strategy_name]
        data = loader()
        
        count = 0
        for key, value in data.items():
            self.cache.set(key, value, ttl=3600)
            count += 1
        
        return {'strategy': strategy_name, 'items_loaded': count}
    
    def warm_all(self) -> Dict[str, int]:
        """Warm all strategies."""
        results = {}
        for strategy_name in self.warm_strategies.keys():
            result = self.warm_cache(strategy_name)
            results[strategy_name] = result.get('items_loaded', 0)
        return results


class CacheMetrics:
    """Track cache performance metrics."""
    
    def __init__(self):
        self.metrics = {
            'total_hits': 0,
            'total_misses': 0,
            'total_evictions': 0,
            'total_invalidations': 0,
        }
    
    def record_hit(self) -> None:
        """Record cache hit."""
        self.metrics['total_hits'] += 1
    
    def record_miss(self) -> None:
        """Record cache miss."""
        self.metrics['total_misses'] += 1
    
    def record_eviction(self) -> None:
        """Record eviction."""
        self.metrics['total_evictions'] += 1
    
    def record_invalidation(self) -> None:
        """Record invalidation."""
        self.metrics['total_invalidations'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        total = self.metrics['total_hits'] + self.metrics['total_misses']
        hit_rate = (self.metrics['total_hits'] / total * 100) if total > 0 else 0
        
        return {
            **self.metrics,
            'hit_rate_percent': hit_rate,
            'total_requests': total,
        }
