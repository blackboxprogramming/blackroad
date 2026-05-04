"""
Webhook System - Reliable event delivery with retries
"""

import json
import hashlib
import hmac
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging


class WebhookEvent(Enum):
    """Types of events that trigger webhooks."""
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"
    CUSTOMER_DELETED = "customer.deleted"
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_UPDATED = "subscription.updated"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    INVOICE_GENERATED = "invoice.generated"
    INVOICE_PAID = "invoice.paid"
    PAYMENT_FAILED = "payment.failed"


class WebhookDeliveryStatus(Enum):
    """Webhook delivery status."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class Webhook:
    """Represents a webhook subscription."""
    
    def __init__(self, id: str, url: str, events: List[str],
                 api_key: str = None):
        self.id = id
        self.url = url
        self.events = events
        self.api_key = api_key or self._generate_key()
        self.is_active = True
        self.created_at = datetime.utcnow()
        self.last_triggered = None
        self.delivery_count = 0
        self.failure_count = 0


    def _generate_key(self) -> str:
        """Generate secret key for signing."""
        import secrets
        return secrets.token_urlsafe(32)
    
    def sign_payload(self, payload: str) -> str:
        """Sign payload for verification."""
        return hmac.new(
            self.api_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()


class WebhookEvent:
    """Represents a webhook event."""
    
    def __init__(self, event_type: str, data: Dict, 
                 resource_id: str = None):
        self.id = self._generate_id()
        self.event_type = event_type
        self.data = data
        self.resource_id = resource_id
        self.created_at = datetime.utcnow()
        self.attempts = 0
        self.last_attempt = None
    
    def _generate_id(self) -> str:
        """Generate unique event ID."""
        import uuid
        return uuid.uuid4().hex
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'event': self.event_type,
            'data': self.data,
            'timestamp': self.created_at.isoformat()
        }


class WebhookDelivery:
    """Represents a webhook delivery attempt."""
    
    def __init__(self, webhook_id: str, event_id: str):
        self.id = self._generate_id()
        self.webhook_id = webhook_id
        self.event_id = event_id
        self.status = WebhookDeliveryStatus.PENDING
        self.created_at = datetime.utcnow()
        self.last_attempt = None
        self.attempt_count = 0
        self.response_status = None
        self.response_body = None
        self.error_message = None
    
    def _generate_id(self) -> str:
        """Generate unique delivery ID."""
        import uuid
        return uuid.uuid4().hex


class WebhookManager:
    """Manages webhooks and deliveries."""
    
    def __init__(self):
        self.webhooks: Dict[str, Webhook] = {}
        self.events: Dict[str, WebhookEvent] = {}
        self.deliveries: List[WebhookDelivery] = []
        self.max_retries = 5
        self.retry_delay_seconds = 60
        self.logger = logging.getLogger(__name__)
    
    def register_webhook(self, url: str, events: List[str],
                        customer_id: str) -> Webhook:
        """Register new webhook."""
        import uuid
        webhook_id = f"wh_{uuid.uuid4().hex[:12]}"
        
        webhook = Webhook(webhook_id, url, events)
        self.webhooks[webhook_id] = webhook
        
        self.logger.info(f"Webhook registered: {webhook_id}")
        return webhook
    
    def trigger_event(self, event_type: str, data: Dict,
                     resource_id: str = None) -> int:
        """Trigger webhook event."""
        event = WebhookEvent(event_type, data, resource_id)
        self.events[event.id] = event
        
        # Find matching webhooks
        matching_webhooks = [
            w for w in self.webhooks.values()
            if w.is_active and event_type in w.events
        ]
        
        # Schedule delivery
        delivery_count = 0
        for webhook in matching_webhooks:
            delivery = WebhookDelivery(webhook.id, event.id)
            self.deliveries.append(delivery)
            delivery_count += 1
        
        self.logger.info(
            f"Event {event.id} queued for {delivery_count} webhooks"
        )
        
        return delivery_count
    
    def get_delivery_status(self, delivery_id: str) -> Optional[Dict]:
        """Get delivery status."""
        for delivery in self.deliveries:
            if delivery.id == delivery_id:
                return {
                    'id': delivery.id,
                    'status': delivery.status.value,
                    'attempts': delivery.attempt_count,
                    'created_at': delivery.created_at.isoformat(),
                    'last_attempt': delivery.last_attempt.isoformat() if delivery.last_attempt else None,
                    'response_status': delivery.response_status
                }
        return None
    
    def retry_failed_delivery(self, delivery_id: str,
                            max_retries: int = 5) -> bool:
        """Retry failed delivery."""
        for delivery in self.deliveries:
            if delivery.id == delivery_id and delivery.attempt_count < max_retries:
                delivery.status = WebhookDeliveryStatus.RETRYING
                delivery.attempt_count += 1
                self.logger.info(f"Retrying delivery {delivery_id}")
                return True
        return False
    
    def get_webhook_stats(self, webhook_id: str) -> Dict:
        """Get webhook statistics."""
        webhook = self.webhooks.get(webhook_id)
        if not webhook:
            return {}
        
        deliveries = [d for d in self.deliveries 
                     if d.webhook_id == webhook_id]
        
        successful = sum(1 for d in deliveries 
                        if d.status == WebhookDeliveryStatus.DELIVERED)
        failed = sum(1 for d in deliveries 
                    if d.status == WebhookDeliveryStatus.FAILED)
        
        return {
            'webhook_id': webhook_id,
            'url': webhook.url,
            'events': webhook.events,
            'total_deliveries': len(deliveries),
            'successful': successful,
            'failed': failed,
            'success_rate': successful / len(deliveries) * 100 if deliveries else 0,
            'last_triggered': webhook.last_triggered.isoformat() if webhook.last_triggered else None
        }
    
    def list_webhooks(self, customer_id: str = None) -> List[Webhook]:
        """List webhooks."""
        return list(self.webhooks.values())
    
    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete webhook."""
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            self.logger.info(f"Webhook deleted: {webhook_id}")
            return True
        return False


class WebhookRetryStrategy:
    """Implements retry strategy for failed deliveries."""
    
    def __init__(self):
        self.exponential_backoff = True
        self.base_delay = 60  # seconds
        self.max_delay = 3600  # 1 hour
        self.max_retries = 5
    
    def get_retry_delay(self, attempt_number: int) -> int:
        """Calculate delay for retry."""
        if self.exponential_backoff:
            delay = self.base_delay * (2 ** (attempt_number - 1))
            return min(delay, self.max_delay)
        else:
            return self.base_delay
    
    def should_retry(self, status_code: int, attempt_count: int) -> bool:
        """Determine if delivery should be retried."""
        if attempt_count >= self.max_retries:
            return False
        
        # Retry on transient errors
        retryable_codes = [408, 429, 500, 502, 503, 504]
        return status_code in retryable_codes
    
    def get_retry_schedule(self) -> List[int]:
        """Get full retry schedule (delays in seconds)."""
        schedule = []
        for i in range(1, self.max_retries + 1):
            schedule.append(self.get_retry_delay(i))
        return schedule


class WebhookSignatureVerifier:
    """Verifies webhook signatures."""
    
    @staticmethod
    def verify_signature(payload: str, signature: str,
                        secret: str) -> bool:
        """Verify webhook signature."""
        expected_signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected_signature)
    
    @staticmethod
    def generate_signature(payload: str, secret: str) -> str:
        """Generate signature for payload."""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
