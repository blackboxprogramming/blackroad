"""Core integration framework and management."""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
import hashlib
from abc import ABC, abstractmethod


class IntegrationStatus(Enum):
    """Status of an integration connection."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    EXPIRED = "expired"


class SyncDirection(Enum):
    """Direction of data synchronization."""
    INBOUND = "inbound"  # 3rd party -> us
    OUTBOUND = "outbound"  # us -> 3rd party
    BIDIRECTIONAL = "bidirectional"


@dataclass
class IntegrationConfig:
    """Configuration for a single integration."""
    integration_id: str  # salesforce, slack, stripe, etc.
    connector_name: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    oauth_token: Optional[str] = None
    oauth_refresh_token: Optional[str] = None
    webhook_secret: Optional[str] = None
    sync_direction: SyncDirection = SyncDirection.INBOUND
    rate_limit_rpm: int = 300
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrationEvent:
    """An event from a 3rd-party integration."""
    event_id: str
    integration_id: str
    connector_name: str
    event_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    source_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    status: str = "pending"
    processed_at: Optional[datetime] = None


@dataclass
class IntegrationMetrics:
    """Metrics for an integration."""
    integration_id: str
    total_events: int = 0
    successful_events: int = 0
    failed_events: int = 0
    skipped_events: int = 0
    avg_latency_ms: float = 0.0
    last_sync: Optional[datetime] = None
    rate_limit_hits: int = 0
    oauth_refresh_count: int = 0


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, rpm: int):
        self.rpm = rpm
        self.tokens = rpm
        self.last_refill = datetime.utcnow()
    
    def can_proceed(self) -> bool:
        """Check if request can proceed."""
        now = datetime.utcnow()
        elapsed = (now - self.last_refill).total_seconds()
        
        # Refill tokens (1 token per second / 60 = rpm)
        refill_rate = self.rpm / 60.0
        self.tokens = min(
            self.rpm,
            self.tokens + (elapsed * refill_rate)
        )
        self.last_refill = now
        
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
    
    def get_retry_after_seconds(self) -> int:
        """Seconds to wait before retrying."""
        return max(1, int(60 / self.rpm))


class RetryPolicy:
    """Exponential backoff retry policy."""
    
    def __init__(self, max_retries: int = 3, base_delay_ms: int = 100):
        self.max_retries = max_retries
        self.base_delay_ms = base_delay_ms
    
    def get_delay_ms(self, retry_count: int) -> int:
        """Exponential backoff: 100ms, 200ms, 400ms, 800ms..."""
        if retry_count >= self.max_retries:
            return -1
        return self.base_delay_ms * (2 ** retry_count)
    
    def should_retry(self, status_code: int, retry_count: int) -> bool:
        """Determine if we should retry."""
        if retry_count >= self.max_retries:
            return False
        # Retry on 429 (rate limit) and 5xx
        return status_code in [429, 500, 502, 503, 504]


class IntegrationHub:
    """Central hub for managing all integrations."""
    
    def __init__(self, master_key: str):
        """
        Initialize integration hub.
        
        Args:
            master_key: Master encryption key for credentials
        """
        self.master_key = master_key
        self.integrations: Dict[str, IntegrationConfig] = {}
        self.metrics: Dict[str, IntegrationMetrics] = {}
        self.event_queue: List[IntegrationEvent] = []
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.retry_policy = RetryPolicy()
        self.webhooks: Dict[str, Callable] = {}
        self.active_transforms: Dict[str, Callable] = {}
    
    def register_integration(self, config: IntegrationConfig) -> str:
        """Register a new integration."""
        integration_id = f"{config.connector_name}_{uuid.uuid4().hex[:8]}"
        self.integrations[integration_id] = config
        self.metrics[integration_id] = IntegrationMetrics(integration_id)
        self.rate_limiters[integration_id] = RateLimiter(config.rate_limit_rpm)
        return integration_id
    
    def get_integration(self, integration_id: str) -> Optional[IntegrationConfig]:
        """Get integration configuration."""
        return self.integrations.get(integration_id)
    
    def list_integrations(self, connector_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all integrations, optionally filtered by connector."""
        result = []
        for int_id, config in self.integrations.items():
            if connector_name and config.connector_name != connector_name:
                continue
            result.append({
                'integration_id': int_id,
                'connector': config.connector_name,
                'status': self._get_status(int_id),
                'enabled': config.enabled,
                'sync_direction': config.sync_direction.value,
                'metrics': self._get_metrics_summary(int_id),
            })
        return result
    
    def disable_integration(self, integration_id: str) -> bool:
        """Disable an integration."""
        if integration_id not in self.integrations:
            return False
        self.integrations[integration_id].enabled = False
        return True
    
    def enable_integration(self, integration_id: str) -> bool:
        """Enable an integration."""
        if integration_id not in self.integrations:
            return False
        self.integrations[integration_id].enabled = True
        return True
    
    def queue_event(self, event: IntegrationEvent) -> bool:
        """Queue an inbound event for processing."""
        if not self.integrations.get(event.integration_id):
            return False
        
        config = self.integrations[event.integration_id]
        if not config.enabled:
            return False
        
        self.event_queue.append(event)
        return True
    
    def can_call_api(self, integration_id: str) -> bool:
        """Check if API call is allowed (rate limiting)."""
        if integration_id not in self.rate_limiters:
            return False
        return self.rate_limiters[integration_id].can_proceed()
    
    def process_queue(self, batch_size: int = 100) -> Dict[str, int]:
        """Process queued events. Returns processing stats."""
        stats = {'processed': 0, 'failed': 0, 'retried': 0}
        
        for _ in range(min(batch_size, len(self.event_queue))):
            event = self.event_queue.pop(0)
            
            # Apply transformations if registered
            transform_key = f"{event.integration_id}_{event.event_type}"
            if transform_key in self.active_transforms:
                try:
                    event.payload = self.active_transforms[transform_key](event.payload)
                except Exception as e:
                    event.status = 'failed'
                    event.retry_count += 1
            
            # Determine if we should retry
            if event.status == 'failed':
                if event.retry_count < event.max_retries:
                    event.retry_count += 1
                    self.event_queue.append(event)
                    stats['retried'] += 1
                else:
                    stats['failed'] += 1
            else:
                event.status = 'processed'
                event.processed_at = datetime.utcnow()
                stats['processed'] += 1
            
            # Update metrics
            if event.integration_id in self.metrics:
                self.metrics[event.integration_id].total_events += 1
                if event.status == 'processed':
                    self.metrics[event.integration_id].successful_events += 1
                    self.metrics[event.integration_id].last_sync = datetime.utcnow()
                elif event.status == 'failed':
                    self.metrics[event.integration_id].failed_events += 1
        
        return stats
    
    def register_webhook_handler(self, integration_id: str, handler: Callable) -> bool:
        """Register incoming webhook handler."""
        if integration_id not in self.integrations:
            return False
        self.webhooks[integration_id] = handler
        return True
    
    def register_transform(
        self, 
        integration_id: str, 
        event_type: str, 
        transform_fn: Callable
    ) -> bool:
        """Register event transformation function."""
        if integration_id not in self.integrations:
            return False
        transform_key = f"{integration_id}_{event_type}"
        self.active_transforms[transform_key] = transform_fn
        return True
    
    def _get_status(self, integration_id: str) -> str:
        """Get current status of integration."""
        config = self.integrations.get(integration_id)
        if not config or not config.enabled:
            return IntegrationStatus.DISCONNECTED.value
        
        if config.oauth_token and (config.oauth_refresh_token or config.api_key):
            return IntegrationStatus.CONNECTED.value
        return IntegrationStatus.FAILED.value
    
    def _get_metrics_summary(self, integration_id: str) -> Dict[str, Any]:
        """Get summary metrics for integration."""
        if integration_id not in self.metrics:
            return {}
        
        m = self.metrics[integration_id]
        success_rate = (m.successful_events / m.total_events * 100) if m.total_events > 0 else 0
        
        return {
            'total_events': m.total_events,
            'success_rate': f"{success_rate:.1f}%",
            'failed_events': m.failed_events,
            'avg_latency_ms': f"{m.avg_latency_ms:.0f}",
            'last_sync': m.last_sync.isoformat() if m.last_sync else None,
        }
    
    def get_hub_metrics(self) -> Dict[str, Any]:
        """Get overall hub metrics."""
        total_events = sum(m.total_events for m in self.metrics.values())
        total_success = sum(m.successful_events for m in self.metrics.values())
        total_failed = sum(m.failed_events for m in self.metrics.values())
        
        success_rate = (total_success / total_events * 100) if total_events > 0 else 0
        
        return {
            'total_integrations': len(self.integrations),
            'enabled_integrations': sum(1 for c in self.integrations.values() if c.enabled),
            'total_events_processed': total_events,
            'successful_events': total_success,
            'failed_events': total_failed,
            'overall_success_rate': f"{success_rate:.1f}%",
            'queue_depth': len(self.event_queue),
            'unique_connectors': len(set(c.connector_name for c in self.integrations.values())),
        }
