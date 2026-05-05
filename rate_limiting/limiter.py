"""Rate limiting engine with multiple algorithms."""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib


class LimitStrategy(Enum):
    """Rate limiting strategies."""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    LEAKY_BUCKET = "leaky_bucket"
    FIXED_WINDOW = "fixed_window"


class RequestStatus(Enum):
    """Request status."""
    ALLOWED = "allowed"
    REJECTED = "rejected"
    THROTTLED = "throttled"


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    max_requests: int
    window_size_seconds: int
    strategy: LimitStrategy = LimitStrategy.TOKEN_BUCKET
    burst_size: int = 0
    penalty_duration_seconds: int = 60
    
    def __post_init__(self):
        if self.burst_size == 0:
            self.burst_size = self.max_requests


@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""
    tokens: float
    max_tokens: float
    refill_rate: float
    last_refill: datetime
    
    def refill(self):
        """Refill tokens based on time elapsed."""
        now = datetime.utcnow()
        time_elapsed = (now - self.last_refill).total_seconds()
        tokens_to_add = time_elapsed * self.refill_rate
        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def consume(self, amount: float = 1.0) -> bool:
        """Attempt to consume tokens."""
        self.refill()
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False
    
    def reset(self):
        """Reset bucket."""
        self.tokens = self.max_tokens
        self.last_refill = datetime.utcnow()


@dataclass
class SlidingWindowCounter:
    """Sliding window counter for rate limiting."""
    window_size: int
    max_requests: int
    requests: list = field(default_factory=list)
    
    def add_request(self):
        """Add a request to the window."""
        now = datetime.utcnow()
        self.requests.append(now)
        self._cleanup()
    
    def _cleanup(self):
        """Remove old requests outside window."""
        cutoff = datetime.utcnow() - timedelta(seconds=self.window_size)
        self.requests = [r for r in self.requests if r > cutoff]
    
    def is_allowed(self) -> bool:
        """Check if request is allowed."""
        self._cleanup()
        return len(self.requests) < self.max_requests
    
    def get_request_count(self) -> int:
        """Get current request count."""
        self._cleanup()
        return len(self.requests)
    
    def reset(self):
        """Reset counter."""
        self.requests = []


@dataclass
class LeakyBucket:
    """Leaky bucket for rate limiting."""
    capacity: int
    leak_rate: float
    queue: list = field(default_factory=list)
    last_leak: datetime = field(default_factory=datetime.utcnow)
    
    def leak(self):
        """Leak requests from bucket."""
        now = datetime.utcnow()
        time_elapsed = (now - self.last_leak).total_seconds()
        requests_to_leak = int(time_elapsed * self.leak_rate)
        
        for _ in range(requests_to_leak):
            if self.queue:
                self.queue.pop(0)
        
        if requests_to_leak > 0:
            self.last_leak = now
    
    def add_request(self) -> bool:
        """Add request to bucket."""
        self.leak()
        if len(self.queue) < self.capacity:
            self.queue.append(datetime.utcnow())
            return True
        return False
    
    def get_queue_size(self) -> int:
        """Get current queue size."""
        self.leak()
        return len(self.queue)
    
    def reset(self):
        """Reset bucket."""
        self.queue = []
        self.last_leak = datetime.utcnow()


@dataclass
class FixedWindowCounter:
    """Fixed window counter for rate limiting."""
    window_size: int
    max_requests: int
    requests: int = 0
    window_start: datetime = field(default_factory=datetime.utcnow)
    
    def is_window_expired(self) -> bool:
        """Check if current window has expired."""
        window_end = self.window_start + timedelta(seconds=self.window_size)
        return datetime.utcnow() > window_end
    
    def reset_window(self):
        """Reset window counter."""
        self.requests = 0
        self.window_start = datetime.utcnow()
    
    def is_allowed(self) -> bool:
        """Check if request is allowed."""
        if self.is_window_expired():
            self.reset_window()
        return self.requests < self.max_requests
    
    def add_request(self) -> bool:
        """Add request to counter."""
        if self.is_allowed():
            self.requests += 1
            return True
        return False
    
    def get_request_count(self) -> int:
        """Get request count in current window."""
        if self.is_window_expired():
            self.reset_window()
        return self.requests


@dataclass
class RateLimitResult:
    """Rate limit check result."""
    allowed: bool
    status: RequestStatus
    requests_remaining: int
    reset_after_seconds: int
    retry_after_seconds: int = 0
    limit_exceeded: bool = False


class RateLimiter:
    """Main rate limiter engine."""
    
    def __init__(self, max_size: int = 10000):
        """Initialize rate limiter."""
        self.max_size = max_size
        self.limiters: dict = {}
        self.penalties: dict = {}
        self.stats: dict = {
            'total_checks': 0,
            'allowed': 0,
            'rejected': 0,
            'throttled': 0
        }
    
    def get_limiter(self, identifier: str, config: RateLimitConfig):
        """Get or create limiter for identifier."""
        if identifier not in self.limiters and len(self.limiters) >= self.max_size:
            raise RuntimeError(f"Rate limiter limit exceeded: {self.max_size}")
        
        if identifier not in self.limiters:
            if config.strategy == LimitStrategy.TOKEN_BUCKET:
                refill_rate = config.max_requests / config.window_size_seconds
                self.limiters[identifier] = {
                    'config': config,
                    'limiter': TokenBucket(
                        tokens=float(config.burst_size),
                        max_tokens=float(config.burst_size),
                        refill_rate=refill_rate,
                        last_refill=datetime.utcnow()
                    )
                }
            elif config.strategy == LimitStrategy.SLIDING_WINDOW:
                self.limiters[identifier] = {
                    'config': config,
                    'limiter': SlidingWindowCounter(
                        window_size=config.window_size_seconds,
                        max_requests=config.max_requests
                    )
                }
            elif config.strategy == LimitStrategy.LEAKY_BUCKET:
                leak_rate = config.max_requests / config.window_size_seconds
                self.limiters[identifier] = {
                    'config': config,
                    'limiter': LeakyBucket(
                        capacity=config.max_requests,
                        leak_rate=leak_rate
                    )
                }
            elif config.strategy == LimitStrategy.FIXED_WINDOW:
                self.limiters[identifier] = {
                    'config': config,
                    'limiter': FixedWindowCounter(
                        window_size=config.window_size_seconds,
                        max_requests=config.max_requests
                    )
                }
        
        return self.limiters[identifier]
    
    def check_rate_limit(self, identifier: str, config: RateLimitConfig) -> RateLimitResult:
        """Check if request is allowed under rate limit."""
        self.stats['total_checks'] += 1
        
        # Check if under penalty
        if identifier in self.penalties:
            penalty_end = self.penalties[identifier]
            if datetime.utcnow() < penalty_end:
                self.stats['rejected'] += 1
                retry_after = int((penalty_end - datetime.utcnow()).total_seconds())
                return RateLimitResult(
                    allowed=False,
                    status=RequestStatus.REJECTED,
                    requests_remaining=0,
                    reset_after_seconds=config.window_size_seconds,
                    retry_after_seconds=retry_after,
                    limit_exceeded=True
                )
            else:
                del self.penalties[identifier]
        
        limiter_data = self.get_limiter(identifier, config)
        limiter = limiter_data['limiter']
        
        allowed = False
        requests_remaining = 0
        
        if config.strategy == LimitStrategy.TOKEN_BUCKET:
            allowed = limiter.consume(1.0)
            limiter.refill()
            requests_remaining = int(limiter.tokens)
        elif config.strategy == LimitStrategy.SLIDING_WINDOW:
            allowed = limiter.is_allowed()
            if allowed:
                limiter.add_request()
            requests_remaining = config.max_requests - limiter.get_request_count()
        elif config.strategy == LimitStrategy.LEAKY_BUCKET:
            allowed = limiter.add_request()
            requests_remaining = config.max_requests - limiter.get_queue_size()
        elif config.strategy == LimitStrategy.FIXED_WINDOW:
            allowed = limiter.add_request()
            requests_remaining = config.max_requests - limiter.get_request_count()
        
        if not allowed:
            self.stats['rejected'] += 1
            self.penalties[identifier] = datetime.utcnow() + timedelta(seconds=config.penalty_duration_seconds)
            return RateLimitResult(
                allowed=False,
                status=RequestStatus.REJECTED,
                requests_remaining=0,
                reset_after_seconds=config.window_size_seconds,
                retry_after_seconds=config.penalty_duration_seconds,
                limit_exceeded=True
            )
        
        self.stats['allowed'] += 1
        return RateLimitResult(
            allowed=True,
            status=RequestStatus.ALLOWED,
            requests_remaining=requests_remaining,
            reset_after_seconds=config.window_size_seconds,
            retry_after_seconds=0,
            limit_exceeded=False
        )
    
    def reset_limiter(self, identifier: str):
        """Reset rate limiter for identifier."""
        if identifier in self.limiters:
            limiter = self.limiters[identifier]['limiter']
            limiter.reset()
        if identifier in self.penalties:
            del self.penalties[identifier]
    
    def get_stats(self, identifier: str = None) -> dict:
        """Get rate limiter statistics."""
        if identifier and identifier in self.limiters:
            limiter_data = self.limiters[identifier]
            limiter = limiter_data['limiter']
            
            if isinstance(limiter, TokenBucket):
                return {
                    'strategy': 'token_bucket',
                    'tokens': limiter.tokens,
                    'max_tokens': limiter.max_tokens,
                    'refill_rate': limiter.refill_rate
                }
            elif isinstance(limiter, SlidingWindowCounter):
                return {
                    'strategy': 'sliding_window',
                    'request_count': limiter.get_request_count(),
                    'max_requests': limiter.max_requests
                }
            elif isinstance(limiter, LeakyBucket):
                return {
                    'strategy': 'leaky_bucket',
                    'queue_size': limiter.get_queue_size(),
                    'capacity': limiter.capacity
                }
            elif isinstance(limiter, FixedWindowCounter):
                return {
                    'strategy': 'fixed_window',
                    'request_count': limiter.get_request_count(),
                    'max_requests': limiter.max_requests
                }
        
        return {
            'total_checks': self.stats['total_checks'],
            'allowed': self.stats['allowed'],
            'rejected': self.stats['rejected'],
            'active_limiters': len(self.limiters),
            'active_penalties': len(self.penalties)
        }
    
    def clear_all(self):
        """Clear all limiters."""
        self.limiters.clear()
        self.penalties.clear()
    
    def get_penalty_info(self, identifier: str) -> dict:
        """Get penalty information."""
        if identifier in self.penalties:
            penalty_end = self.penalties[identifier]
            remaining = int((penalty_end - datetime.utcnow()).total_seconds())
            return {
                'penalized': True,
                'penalty_end': penalty_end.isoformat(),
                'seconds_remaining': max(0, remaining)
            }
        return {'penalized': False}
