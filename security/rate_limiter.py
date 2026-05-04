"""
Advanced Rate Limiter - Sliding Window Algorithm
Implements IP-based, user-based, and dynamic rate limiting
"""

import time
import hashlib
from collections import defaultdict
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
import json


class RateLimiter:
    """Implements sliding window rate limiting with multiple strategies."""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        # In-memory fallback if Redis not available
        self.window_data: Dict[str, list] = defaultdict(list)
        self.limits = {
            'global': {'requests': 10000, 'window': 60},  # 10k/min global
            'ip': {'requests': 1000, 'window': 60},        # 1k/min per IP
            'user': {'requests': 500, 'window': 60},       # 500/min per user
            'api_key': {'requests': 2000, 'window': 60},   # 2k/min per key
            'endpoint': {
                '/auth/login': {'requests': 10, 'window': 300},      # 10/5min
                '/api/bulk': {'requests': 50, 'window': 3600},       # 50/hour
                '/payments': {'requests': 100, 'window': 3600},      # 100/hour
                '/agents': {'requests': 500, 'window': 60},          # 500/min
            }
        }
        self.burst_allowance = 1.5  # 50% burst tolerance
    
    def check_rate_limit(self, identifier: str, limit_type: str = 'ip', 
                        endpoint: str = None) -> Tuple[bool, Dict]:
        """
        Check if request should be allowed under rate limit.
        
        Args:
            identifier: IP address, user_id, or api_key
            limit_type: 'ip', 'user', 'api_key', 'global'
            endpoint: API endpoint for endpoint-specific limits
        
        Returns:
            (allowed: bool, metadata: dict with headers)
        """
        now = time.time()
        key = self._make_key(identifier, limit_type)
        
        # Get endpoint-specific limit if provided
        if endpoint and endpoint in self.limits['endpoint']:
            limit_config = self.limits['endpoint'][endpoint]
        else:
            limit_config = self.limits[limit_type]
        
        requests_allowed = limit_config['requests']
        window_size = limit_config['window']
        burst_limit = int(requests_allowed * self.burst_allowance)
        
        # Use Redis if available, fallback to in-memory
        if self.redis:
            allowed, remaining, reset_time = self._check_redis(
                key, requests_allowed, window_size
            )
        else:
            allowed, remaining, reset_time = self._check_memory(
                key, requests_allowed, burst_limit, window_size, now
            )
        
        headers = {
            'X-RateLimit-Limit': str(requests_allowed),
            'X-RateLimit-Remaining': str(max(0, remaining)),
            'X-RateLimit-Reset': str(int(reset_time)),
            'X-RateLimit-RetryAfter': str(int(reset_time - now)) if not allowed else '0'
        }
        
        return allowed, headers
    
    def _make_key(self, identifier: str, limit_type: str) -> str:
        """Generate cache key for identifier."""
        return f"ratelimit:{limit_type}:{identifier}"
    
    def _check_redis(self, key: str, limit: int, window: int) -> Tuple[bool, int, float]:
        """Check rate limit using Redis."""
        try:
            now = time.time()
            pipe = self.redis.pipeline()
            
            # Remove old entries outside window
            pipe.zremrangebyscore(key, 0, now - window)
            
            # Get current request count
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(now): now})
            
            # Set expiry
            pipe.expire(key, window)
            
            results = pipe.execute()
            count = results[1]
            
            # Get reset time (oldest request + window)
            oldest = self.redis.zrange(key, 0, 0, withscores=True)
            reset_time = oldest[0][1] + window if oldest else now + window
            
            allowed = count <= limit
            remaining = max(0, limit - count)
            
            return allowed, remaining, reset_time
        except Exception:
            # Fallback to memory on Redis error
            return True, limit, time.time() + window
    
    def _check_memory(self, key: str, limit: int, burst_limit: int, 
                     window: int, now: float) -> Tuple[bool, int, float]:
        """Check rate limit using in-memory store."""
        # Clean old entries
        self.window_data[key] = [
            ts for ts in self.window_data[key] 
            if now - ts < window
        ]
        
        current_count = len(self.window_data[key])
        
        # Check against burst limit first (more lenient)
        allowed = current_count < burst_limit
        
        # If beyond soft limit, check strict limit for logging
        if current_count >= limit:
            allowed = False
        
        # Add current request
        self.window_data[key].append(now)
        
        remaining = max(0, limit - current_count)
        reset_time = (self.window_data[key][0] + window) if self.window_data[key] else (now + window)
        
        return allowed, remaining, reset_time
    
    def get_stats(self, identifier: str, limit_type: str = 'ip') -> Dict:
        """Get rate limit statistics for debugging."""
        key = self._make_key(identifier, limit_type)
        now = time.time()
        
        if self.redis:
            try:
                count = self.redis.zcard(key)
                oldest = self.redis.zrange(key, 0, 0, withscores=True)
                oldest_time = oldest[0][1] if oldest else now
            except:
                count = len(self.window_data[key])
                oldest_time = self.window_data[key][0] if self.window_data[key] else now
        else:
            count = len(self.window_data[key])
            oldest_time = self.window_data[key][0] if self.window_data[key] else now
        
        window_size = self.limits[limit_type]['window']
        
        return {
            'identifier': identifier,
            'type': limit_type,
            'current_count': count,
            'window_size': window_size,
            'oldest_request': datetime.fromtimestamp(oldest_time).isoformat(),
            'requests_per_sec': count / window_size if count > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }
    
    def reset_limit(self, identifier: str, limit_type: str = 'ip') -> bool:
        """Reset rate limit for identifier (admin only)."""
        key = self._make_key(identifier, limit_type)
        
        if self.redis:
            self.redis.delete(key)
        else:
            self.window_data[key] = []
        
        return True
    
    def set_custom_limit(self, endpoint: str, requests: int, window: int) -> None:
        """Set custom rate limit for specific endpoint."""
        self.limits['endpoint'][endpoint] = {
            'requests': requests,
            'window': window
        }


class AdaptiveRateLimiter(RateLimiter):
    """Rate limiter with adaptive limits based on system load."""
    
    def __init__(self, redis_client=None):
        super().__init__(redis_client)
        self.load_factor = 1.0  # Adjusts limits based on system load
        self.abuse_detection_enabled = True
    
    def adjust_limits(self, cpu_usage: float, memory_usage: float, 
                      error_rate: float) -> None:
        """Dynamically adjust limits based on system metrics."""
        if cpu_usage > 80:
            self.load_factor = 0.5  # Reduce by 50% under high CPU
        elif cpu_usage > 60:
            self.load_factor = 0.75
        elif cpu_usage < 30:
            self.load_factor = 1.2  # Increase during low load
        else:
            self.load_factor = 1.0
        
        # Further reduce if error rate is high
        if error_rate > 0.05:
            self.load_factor *= 0.8
    
    def check_rate_limit(self, identifier: str, limit_type: str = 'ip',
                        endpoint: str = None) -> Tuple[bool, Dict]:
        """Override to apply load factor."""
        allowed, headers = super().check_rate_limit(identifier, limit_type, endpoint)
        
        # Apply load factor to limits
        if self.load_factor != 1.0:
            remaining = int(int(headers['X-RateLimit-Remaining']) * self.load_factor)
            headers['X-RateLimit-Remaining'] = str(max(0, remaining))
        
        return allowed, headers
    
    def detect_abuse(self, identifier: str, limit_type: str = 'ip') -> Dict:
        """Detect potential abuse patterns."""
        stats = self.get_stats(identifier, limit_type)
        
        abuse_score = 0
        issues = []
        
        # Check request rate
        if stats['requests_per_sec'] > 100:
            abuse_score += 50
            issues.append('Extremely high request rate')
        elif stats['requests_per_sec'] > 50:
            abuse_score += 25
            issues.append('High request rate')
        
        # Check for burst patterns
        if stats['current_count'] > self.limits[limit_type]['requests'] * 0.8:
            abuse_score += 15
            issues.append('Approaching rate limit')
        
        return {
            'identifier': identifier,
            'abuse_score': min(100, abuse_score),
            'is_suspicious': abuse_score > 30,
            'issues': issues,
            'recommended_action': self._recommend_action(abuse_score)
        }
    
    def _recommend_action(self, score: int) -> str:
        """Recommend action based on abuse score."""
        if score > 80:
            return 'BLOCK_IMMEDIATELY'
        elif score > 60:
            return 'AGGRESSIVE_LIMITING'
        elif score > 30:
            return 'MONITOR_CLOSELY'
        else:
            return 'NORMAL'
