"""
Redis Caching Layer for BlackRoad
Implements cache-aside pattern with automatic invalidation
"""

import json
import redis
from functools import wraps
from datetime import timedelta
from typing import Any, Callable, Optional

class CachingLayer:
    """Centralized caching layer for the application"""
    
    # Cache TTL configuration (in seconds)
    TTL_CONFIG = {
        'customer_revenue': 3600,      # 1 hour
        'tier_statistics': 7200,       # 2 hours
        'daily_metrics': 86400,        # 24 hours
        'user_list': 600,              # 10 minutes
        'api_response': 300,           # 5 minutes
    }
    
    def __init__(self, redis_host='localhost', redis_port=6379, db=0):
        """Initialize Redis connection pool"""
        self.redis_pool = redis.ConnectionPool(
            host=redis_host,
            port=redis_port,
            db=db,
            max_connections=50,
            retry_on_timeout=True,
            decode_responses=True
        )
        self.redis_client = redis.Redis(connection_pool=self.redis_pool)
        
        # Verify connection
        try:
            self.redis_client.ping()
            print("✅ Redis connected successfully")
        except redis.ConnectionError:
            print("⚠️  Redis connection failed - caching disabled")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL"""
        try:
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
        except Exception as e:
            print(f"Cache set error: {e}")
    
    def delete(self, *keys: str):
        """Delete one or more cache keys"""
        try:
            if keys:
                self.redis_client.delete(*keys)
        except Exception as e:
            print(f"Cache delete error: {e}")
    
    def invalidate_customer_cache(self, customer_id: str):
        """Invalidate all cache keys for a customer"""
        patterns = [
            f"revenue:{customer_id}",
            f"usage:{customer_id}",
            f"profile:{customer_id}",
            f"tier:{customer_id}",
        ]
        self.delete(*patterns)
    
    def invalidate_aggregates(self):
        """Invalidate aggregate statistics"""
        patterns = [
            "revenue_by_tier:*",
            "daily_revenue:*",
            "user_stats:*",
        ]
        for pattern in patterns:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.delete(*keys)
            except Exception as e:
                print(f"Error invalidating {pattern}: {e}")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        try:
            info = self.redis_client.info('stats')
            
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            
            if hits + misses == 0:
                hitrate = 0
            else:
                hitrate = (hits / (hits + misses)) * 100
            
            return {
                'connected_clients': info.get('connected_clients'),
                'used_memory_mb': round(info.get('used_memory', 0) / (1024 * 1024), 2),
                'used_memory_human': info.get('used_memory_human'),
                'evicted_keys': info.get('evicted_keys'),
                'total_commands': info.get('total_commands_processed'),
                'cache_hits': hits,
                'cache_misses': misses,
                'hitrate_percent': round(hitrate, 2),
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}


# Decorator for automatic caching
def cached(ttl_key: str = 'api_response'):
    """
    Decorator for caching function results
    
    Usage:
        @cached(ttl_key='tier_statistics')
        def get_tier_stats():
            return expensive_computation()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = CachingLayer()
            
            # Build cache key from function name and args
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # Try cache first
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Cache miss - call function
            result = func(*args, **kwargs)
            
            # Cache the result
            ttl = CachingLayer.TTL_CONFIG.get(ttl_key, 3600)
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator


# Example usage
if __name__ == '__main__':
    cache = CachingLayer()
    
    # Example: Store customer revenue
    cache.set('revenue:cust_123', {'total': 1500, 'currency': 'USD'}, ttl=3600)
    
    # Retrieve it
    revenue = cache.get('revenue:cust_123')
    print(f"Customer revenue: {revenue}")
    
    # Get cache stats
    stats = cache.get_stats()
    print(f"Cache stats: {stats}")
    
    # Invalidate customer cache
    cache.invalidate_customer_cache('cust_123')
    
    print("Cache layer demo completed")
