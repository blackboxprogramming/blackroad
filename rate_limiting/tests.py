"""Tests for rate limiting system."""

import pytest
import time
from datetime import datetime, timedelta
from rate_limiting.limiter import (
    RateLimiter, RateLimitConfig, LimitStrategy, RequestStatus,
    TokenBucket, SlidingWindowCounter, LeakyBucket, FixedWindowCounter
)
from rate_limiting.analytics import RateLimitAnalytics, RateLimitMetrics


class TestTokenBucket:
    """Test token bucket algorithm."""

    def test_create_bucket(self):
        """Test creating token bucket."""
        bucket = TokenBucket(
            tokens=10.0,
            max_tokens=10.0,
            refill_rate=1.0,
            last_refill=datetime.utcnow()
        )
        assert bucket.tokens == 10.0
        assert bucket.max_tokens == 10.0

    def test_consume_tokens(self):
        """Test consuming tokens."""
        bucket = TokenBucket(
            tokens=10.0,
            max_tokens=10.0,
            refill_rate=1.0,
            last_refill=datetime.utcnow()
        )
        
        assert bucket.consume(5.0) == True
        assert bucket.tokens == 5.0
        assert bucket.consume(10.0) == False

    def test_refill_tokens(self):
        """Test token refilling."""
        bucket = TokenBucket(
            tokens=0.0,
            max_tokens=10.0,
            refill_rate=2.0,
            last_refill=datetime.utcnow() - timedelta(seconds=5)
        )
        
        bucket.refill()
        assert bucket.tokens >= 9.0  # 5 seconds * 2.0 refill_rate

    def test_bucket_reset(self):
        """Test resetting bucket."""
        bucket = TokenBucket(
            tokens=2.0,
            max_tokens=10.0,
            refill_rate=1.0,
            last_refill=datetime.utcnow()
        )
        
        bucket.reset()
        assert bucket.tokens == 10.0


class TestSlidingWindowCounter:
    """Test sliding window counter algorithm."""

    def test_create_counter(self):
        """Test creating counter."""
        counter = SlidingWindowCounter(window_size=60, max_requests=10)
        assert counter.max_requests == 10
        assert len(counter.requests) == 0

    def test_add_request(self):
        """Test adding request."""
        counter = SlidingWindowCounter(window_size=60, max_requests=10)
        counter.add_request()
        assert counter.get_request_count() == 1

    def test_sliding_window_limit(self):
        """Test sliding window limit enforcement."""
        counter = SlidingWindowCounter(window_size=60, max_requests=5)
        
        for i in range(5):
            assert counter.is_allowed() == True
            counter.add_request()
        
        assert counter.is_allowed() == False

    def test_window_cleanup(self):
        """Test old requests cleanup."""
        counter = SlidingWindowCounter(window_size=1, max_requests=10)
        counter.requests.append(datetime.utcnow() - timedelta(seconds=2))
        
        counter._cleanup()
        assert len(counter.requests) == 0

    def test_counter_reset(self):
        """Test resetting counter."""
        counter = SlidingWindowCounter(window_size=60, max_requests=10)
        counter.add_request()
        
        counter.reset()
        assert counter.get_request_count() == 0


class TestLeakyBucket:
    """Test leaky bucket algorithm."""

    def test_create_bucket(self):
        """Test creating leaky bucket."""
        bucket = LeakyBucket(capacity=10, leak_rate=1.0)
        assert bucket.capacity == 10
        assert len(bucket.queue) == 0

    def test_add_request(self):
        """Test adding request."""
        bucket = LeakyBucket(capacity=10, leak_rate=1.0)
        assert bucket.add_request() == True
        assert bucket.get_queue_size() == 1

    def test_capacity_exceeded(self):
        """Test capacity exceeded."""
        bucket = LeakyBucket(capacity=2, leak_rate=1.0)
        
        assert bucket.add_request() == True
        assert bucket.add_request() == True
        assert bucket.add_request() == False

    def test_leak_requests(self):
        """Test leaking requests."""
        bucket = LeakyBucket(
            capacity=10,
            leak_rate=2.0,
            last_leak=datetime.utcnow() - timedelta(seconds=2)
        )
        bucket.queue.append(datetime.utcnow())
        bucket.queue.append(datetime.utcnow())
        
        bucket.leak()
        assert bucket.get_queue_size() <= 2

    def test_bucket_reset(self):
        """Test resetting bucket."""
        bucket = LeakyBucket(capacity=10, leak_rate=1.0)
        bucket.queue.append(datetime.utcnow())
        
        bucket.reset()
        assert bucket.get_queue_size() == 0


class TestFixedWindowCounter:
    """Test fixed window counter algorithm."""

    def test_create_counter(self):
        """Test creating counter."""
        counter = FixedWindowCounter(window_size=60, max_requests=10)
        assert counter.window_size == 60
        assert counter.requests == 0

    def test_add_request(self):
        """Test adding request."""
        counter = FixedWindowCounter(window_size=60, max_requests=10)
        assert counter.add_request() == True
        assert counter.get_request_count() == 1

    def test_window_limit(self):
        """Test window limit enforcement."""
        counter = FixedWindowCounter(window_size=60, max_requests=3)
        
        for i in range(3):
            assert counter.add_request() == True
        
        assert counter.add_request() == False

    def test_window_reset(self):
        """Test window reset on expiration."""
        counter = FixedWindowCounter(window_size=1, max_requests=3)
        counter.window_start = datetime.utcnow() - timedelta(seconds=2)
        
        assert counter.is_window_expired() == True
        assert counter.add_request() == True

    def test_counter_reset(self):
        """Test resetting counter."""
        counter = FixedWindowCounter(window_size=60, max_requests=10)
        counter.add_request()
        
        counter.reset_window()
        assert counter.requests == 0


class TestRateLimiter:
    """Test rate limiter."""

    def test_create_limiter(self):
        """Test creating limiter."""
        limiter = RateLimiter()
        assert len(limiter.limiters) == 0

    def test_token_bucket_strategy(self):
        """Test token bucket rate limiting."""
        limiter = RateLimiter()
        config = RateLimitConfig(
            max_requests=5,
            window_size_seconds=60,
            strategy=LimitStrategy.TOKEN_BUCKET
        )
        
        for i in range(5):
            result = limiter.check_rate_limit('user1', config)
            assert result.allowed == True
        
        result = limiter.check_rate_limit('user1', config)
        assert result.allowed == False

    def test_sliding_window_strategy(self):
        """Test sliding window rate limiting."""
        limiter = RateLimiter()
        config = RateLimitConfig(
            max_requests=3,
            window_size_seconds=60,
            strategy=LimitStrategy.SLIDING_WINDOW
        )
        
        for i in range(3):
            result = limiter.check_rate_limit('user2', config)
            assert result.allowed == True
        
        result = limiter.check_rate_limit('user2', config)
        assert result.allowed == False

    def test_fixed_window_strategy(self):
        """Test fixed window rate limiting."""
        limiter = RateLimiter()
        config = RateLimitConfig(
            max_requests=2,
            window_size_seconds=60,
            strategy=LimitStrategy.FIXED_WINDOW
        )
        
        for i in range(2):
            result = limiter.check_rate_limit('user3', config)
            assert result.allowed == True
        
        result = limiter.check_rate_limit('user3', config)
        assert result.allowed == False

    def test_leaky_bucket_strategy(self):
        """Test leaky bucket rate limiting."""
        limiter = RateLimiter()
        config = RateLimitConfig(
            max_requests=2,
            window_size_seconds=60,
            strategy=LimitStrategy.LEAKY_BUCKET
        )
        
        for i in range(2):
            result = limiter.check_rate_limit('user4', config)
            assert result.allowed == True
        
        result = limiter.check_rate_limit('user4', config)
        assert result.allowed == False

    def test_burst_size(self):
        """Test burst size configuration."""
        limiter = RateLimiter()
        config = RateLimitConfig(
            max_requests=5,
            window_size_seconds=60,
            strategy=LimitStrategy.TOKEN_BUCKET,
            burst_size=20
        )
        
        for i in range(20):
            result = limiter.check_rate_limit('burst_user', config)
            assert result.allowed == True
        
        result = limiter.check_rate_limit('burst_user', config)
        assert result.allowed == False

    def test_penalty_duration(self):
        """Test penalty duration."""
        limiter = RateLimiter()
        config = RateLimitConfig(
            max_requests=1,
            window_size_seconds=60,
            penalty_duration_seconds=2
        )
        
        limiter.check_rate_limit('penalized', config)
        result = limiter.check_rate_limit('penalized', config)
        assert result.allowed == False
        assert result.retry_after_seconds == 2

    def test_rate_limit_result(self):
        """Test rate limit result."""
        limiter = RateLimiter()
        config = RateLimitConfig(max_requests=5, window_size_seconds=60)
        
        result = limiter.check_rate_limit('user', config)
        assert result.allowed == True
        assert result.status == RequestStatus.ALLOWED
        assert result.reset_after_seconds == 60
        assert result.limit_exceeded == False

    def test_reset_limiter(self):
        """Test resetting limiter."""
        limiter = RateLimiter()
        config = RateLimitConfig(max_requests=1, window_size_seconds=60)
        
        limiter.check_rate_limit('reset_user', config)
        limiter.check_rate_limit('reset_user', config)
        
        limiter.reset_limiter('reset_user')
        result = limiter.check_rate_limit('reset_user', config)
        assert result.allowed == True

    def test_get_stats(self):
        """Test getting statistics."""
        limiter = RateLimiter()
        config = RateLimitConfig(max_requests=5, window_size_seconds=60)
        
        for i in range(10):
            limiter.check_rate_limit('stats_user', config)
        
        stats = limiter.get_stats()
        assert stats['total_checks'] >= 10
        assert stats['allowed'] >= 5
        assert stats['rejected'] > 0

    def test_penalty_info(self):
        """Test penalty information."""
        limiter = RateLimiter()
        config = RateLimitConfig(max_requests=1, window_size_seconds=60, penalty_duration_seconds=5)
        
        limiter.check_rate_limit('penalty_check', config)
        limiter.check_rate_limit('penalty_check', config)
        
        info = limiter.get_penalty_info('penalty_check')
        assert info['penalized'] == True
        assert info['seconds_remaining'] > 0

    def test_clear_all(self):
        """Test clearing all limiters."""
        limiter = RateLimiter()
        config = RateLimitConfig(max_requests=5, window_size_seconds=60)
        
        limiter.check_rate_limit('user1', config)
        limiter.check_rate_limit('user2', config)
        
        limiter.clear_all()
        assert len(limiter.limiters) == 0

    def test_max_size_limit(self):
        """Test max size limit."""
        limiter = RateLimiter(max_size=2)
        config = RateLimitConfig(max_requests=5, window_size_seconds=60)
        
        limiter.check_rate_limit('user1', config)
        limiter.check_rate_limit('user2', config)
        
        with pytest.raises(RuntimeError):
            limiter.check_rate_limit('user3', config)


class TestAnalytics:
    """Test analytics."""

    def test_create_analytics(self):
        """Test creating analytics."""
        analytics = RateLimitAnalytics()
        assert len(analytics.metrics) == 0

    def test_record_request(self):
        """Test recording request."""
        analytics = RateLimitAnalytics()
        analytics.record_request('user1', allowed=True)
        
        assert 'user1' in analytics.metrics
        assert analytics.metrics['user1'].total_requests == 1
        assert analytics.metrics['user1'].allowed_requests == 1

    def test_rejection_metric(self):
        """Test rejection metric."""
        analytics = RateLimitAnalytics()
        analytics.record_request('user2', allowed=True)
        analytics.record_request('user2', allowed=False, wait_time=2.5)
        
        metrics = analytics.metrics['user2']
        assert metrics.rejected_requests == 1
        assert metrics.total_wait_time == 2.5

    def test_get_top_rejected(self):
        """Test getting top rejected identifiers."""
        analytics = RateLimitAnalytics()
        
        for i in range(5):
            analytics.record_request('user_a', allowed=False)
        for i in range(3):
            analytics.record_request('user_b', allowed=False)
        
        top = analytics.get_top_rejected(limit=2)
        assert len(top) == 2
        assert top[0]['identifier'] == 'user_a'

    def test_get_top_requested(self):
        """Test getting top requested identifiers."""
        analytics = RateLimitAnalytics()
        
        for i in range(10):
            analytics.record_request('user_x', allowed=True)
        for i in range(5):
            analytics.record_request('user_y', allowed=True)
        
        top = analytics.get_top_requested(limit=2)
        assert len(top) == 2
        assert top[0]['identifier'] == 'user_x'

    def test_hourly_stats(self):
        """Test hourly statistics."""
        analytics = RateLimitAnalytics()
        analytics.record_request('user', allowed=True)
        analytics.record_request('user', allowed=False)
        
        stats = analytics.get_hourly_stats(hours=24)
        assert len(stats) > 0

    def test_percentile_rejection_rate(self):
        """Test percentile rejection rate."""
        analytics = RateLimitAnalytics()
        
        for i in range(10):
            analytics.record_request('user_1', allowed=True)
        for i in range(5):
            analytics.record_request('user_2', allowed=False)
        
        percentile = analytics.get_percentile_rejection_rate(50)
        assert percentile >= 0 and percentile <= 1

    def test_export_metrics(self):
        """Test exporting metrics."""
        analytics = RateLimitAnalytics()
        analytics.record_request('user_export', allowed=True)
        
        exported = analytics.export_metrics()
        assert len(exported) == 1
        assert exported[0]['identifier'] == 'user_export'

    def test_reset_metrics(self):
        """Test resetting metrics."""
        analytics = RateLimitAnalytics()
        analytics.record_request('user_reset', allowed=True)
        
        analytics.reset_metrics('user_reset')
        assert 'user_reset' not in analytics.metrics


class TestIntegration:
    """Integration tests."""

    def test_end_to_end_rate_limiting(self):
        """Test end-to-end rate limiting."""
        limiter = RateLimiter()
        config = RateLimitConfig(
            max_requests=5,
            window_size_seconds=60,
            strategy=LimitStrategy.TOKEN_BUCKET
        )
        
        results = []
        for i in range(10):
            result = limiter.check_rate_limit('api_user', config)
            results.append(result)
        
        allowed_count = sum(1 for r in results if r.allowed)
        rejected_count = sum(1 for r in results if not r.allowed)
        
        assert allowed_count == 5
        assert rejected_count == 5

    def test_multiple_strategies(self):
        """Test multiple strategies."""
        limiter = RateLimiter()
        
        strategies = [
            LimitStrategy.TOKEN_BUCKET,
            LimitStrategy.SLIDING_WINDOW,
            LimitStrategy.FIXED_WINDOW,
            LimitStrategy.LEAKY_BUCKET
        ]
        
        for strategy in strategies:
            config = RateLimitConfig(
                max_requests=3,
                window_size_seconds=60,
                strategy=strategy
            )
            
            user_id = f'user_{strategy.value}'
            for i in range(5):
                result = limiter.check_rate_limit(user_id, config)
            
            stats = limiter.get_stats(user_id)
            assert stats is not None

    def test_analytics_integration(self):
        """Test analytics integration."""
        limiter = RateLimiter()
        analytics = RateLimitAnalytics()
        
        config = RateLimitConfig(max_requests=3, window_size_seconds=60)
        
        for i in range(5):
            result = limiter.check_rate_limit('tracked_user', config)
            analytics.record_request('tracked_user', allowed=result.allowed)
        
        metrics = analytics.get_metrics('tracked_user')
        assert metrics['total_requests'] == 5
        assert metrics['rejected_requests'] == 2


# Run tests if executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
