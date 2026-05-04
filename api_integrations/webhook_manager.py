"""Webhook manager for receiving and processing incoming events."""

from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from datetime import datetime
import hmac
import hashlib
import json
import uuid
from enum import Enum


class WebhookStatus(Enum):
    """Status of a webhook delivery."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class WebhookEndpoint:
    """A webhook endpoint for receiving events."""
    endpoint_id: str
    integration_id: str
    url: str
    events: List[str]  # event types to receive
    active: bool = True
    secret: str = ""
    delivery_count: int = 0
    failure_count: int = 0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class WebhookDelivery:
    """Record of a webhook delivery attempt."""
    delivery_id: str
    endpoint_id: str
    event_type: str
    payload: Dict[str, Any]
    status: WebhookStatus
    attempt: int = 1
    max_attempts: int = 5
    response_code: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime = None
    delivered_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class WebhookManager:
    """Manages webhook endpoints and deliveries."""
    
    def __init__(self):
        self.endpoints: Dict[str, WebhookEndpoint] = {}
        self.deliveries: Dict[str, WebhookDelivery] = {}
        self.delivery_history: List[WebhookDelivery] = []
    
    def create_endpoint(
        self,
        integration_id: str,
        url: str,
        events: List[str],
        secret: str = ""
    ) -> WebhookEndpoint:
        """Create a new webhook endpoint."""
        if not secret:
            secret = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:32]
        
        endpoint_id = f"wh_{uuid.uuid4().hex[:16]}"
        endpoint = WebhookEndpoint(
            endpoint_id=endpoint_id,
            integration_id=integration_id,
            url=url,
            events=events,
            secret=secret
        )
        self.endpoints[endpoint_id] = endpoint
        return endpoint
    
    def get_endpoint(self, endpoint_id: str) -> Optional[WebhookEndpoint]:
        """Get webhook endpoint."""
        return self.endpoints.get(endpoint_id)
    
    def list_endpoints(self, integration_id: str) -> List[WebhookEndpoint]:
        """List endpoints for an integration."""
        return [ep for ep in self.endpoints.values() if ep.integration_id == integration_id]
    
    def delete_endpoint(self, endpoint_id: str) -> bool:
        """Delete a webhook endpoint."""
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            return True
        return False
    
    def disable_endpoint(self, endpoint_id: str) -> bool:
        """Disable a webhook endpoint."""
        if endpoint_id not in self.endpoints:
            return False
        self.endpoints[endpoint_id].active = False
        return True
    
    def enable_endpoint(self, endpoint_id: str) -> bool:
        """Enable a webhook endpoint."""
        if endpoint_id not in self.endpoints:
            return False
        self.endpoints[endpoint_id].active = True
        return True
    
    def verify_webhook_signature(
        self,
        endpoint_id: str,
        payload: bytes,
        signature: str
    ) -> bool:
        """Verify webhook signature."""
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint or not endpoint.secret:
            return False
        
        expected = hmac.new(
            endpoint.secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)
    
    def queue_delivery(
        self,
        endpoint_id: str,
        event_type: str,
        payload: Dict[str, Any]
    ) -> Optional[WebhookDelivery]:
        """Queue a webhook delivery."""
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint or not endpoint.active:
            return None
        
        # Check if endpoint subscribes to this event
        if event_type not in endpoint.events and '*' not in endpoint.events:
            return None
        
        delivery_id = f"del_{uuid.uuid4().hex[:16]}"
        delivery = WebhookDelivery(
            delivery_id=delivery_id,
            endpoint_id=endpoint_id,
            event_type=event_type,
            payload=payload,
            status=WebhookStatus.PENDING
        )
        self.deliveries[delivery_id] = delivery
        return delivery
    
    def get_delivery(self, delivery_id: str) -> Optional[WebhookDelivery]:
        """Get delivery record."""
        return self.deliveries.get(delivery_id)
    
    def mark_delivery_success(
        self,
        delivery_id: str,
        response_code: int = 200
    ) -> bool:
        """Mark delivery as successful."""
        if delivery_id not in self.deliveries:
            return False
        
        delivery = self.deliveries[delivery_id]
        delivery.status = WebhookStatus.DELIVERED
        delivery.response_code = response_code
        delivery.delivered_at = datetime.utcnow()
        
        # Update endpoint metrics
        endpoint = self.get_endpoint(delivery.endpoint_id)
        if endpoint:
            endpoint.delivery_count += 1
        
        self.delivery_history.append(delivery)
        return True
    
    def mark_delivery_failure(
        self,
        delivery_id: str,
        error_message: str,
        response_code: Optional[int] = None
    ) -> bool:
        """Mark delivery as failed."""
        if delivery_id not in self.deliveries:
            return False
        
        delivery = self.deliveries[delivery_id]
        delivery.attempt += 1
        delivery.error_message = error_message
        delivery.response_code = response_code
        
        if delivery.attempt >= delivery.max_attempts:
            delivery.status = WebhookStatus.FAILED
            
            # Update endpoint metrics
            endpoint = self.get_endpoint(delivery.endpoint_id)
            if endpoint:
                endpoint.failure_count += 1
        else:
            delivery.status = WebhookStatus.RETRYING
        
        return True
    
    def get_pending_deliveries(self, limit: int = 100) -> List[WebhookDelivery]:
        """Get pending deliveries for processing."""
        pending = [
            d for d in self.deliveries.values()
            if d.status in [WebhookStatus.PENDING, WebhookStatus.RETRYING]
        ]
        return pending[:limit]
    
    def get_delivery_history(
        self,
        endpoint_id: Optional[str] = None,
        status: Optional[WebhookStatus] = None,
        limit: int = 100
    ) -> List[WebhookDelivery]:
        """Get delivery history."""
        history = self.delivery_history
        
        if endpoint_id:
            history = [d for d in history if d.endpoint_id == endpoint_id]
        
        if status:
            history = [d for d in history if d.status == status]
        
        return history[-limit:]
    
    def get_endpoint_stats(self, endpoint_id: str) -> Dict[str, Any]:
        """Get statistics for an endpoint."""
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint:
            return {}
        
        history = self.get_delivery_history(endpoint_id=endpoint_id)
        
        success_count = sum(1 for d in history if d.status == WebhookStatus.DELIVERED)
        failure_count = sum(1 for d in history if d.status == WebhookStatus.FAILED)
        
        return {
            'endpoint_id': endpoint_id,
            'url': endpoint.url,
            'active': endpoint.active,
            'events_subscribed': endpoint.events,
            'total_deliveries': len(history),
            'successful': success_count,
            'failed': failure_count,
            'success_rate': f"{(success_count / len(history) * 100):.1f}%" if history else "N/A",
            'created_at': endpoint.created_at.isoformat(),
        }
    
    def simulate_webhook(
        self,
        endpoint_id: str,
        event_type: str,
        test_payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Simulate sending a test webhook."""
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint:
            return {'success': False, 'error': 'Endpoint not found'}
        
        if not test_payload:
            test_payload = {
                'event': event_type,
                'test': True,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        delivery = self.queue_delivery(endpoint_id, event_type, test_payload)
        if not delivery:
            return {'success': False, 'error': 'Failed to queue delivery'}
        
        # Simulate successful delivery
        self.mark_delivery_success(delivery.delivery_id, 200)
        
        return {
            'success': True,
            'delivery_id': delivery.delivery_id,
            'endpoint_url': endpoint.url,
            'event_type': event_type,
            'payload': test_payload,
        }
    
    def replay_failed_webhooks(self, endpoint_id: str, hours: int = 24) -> Dict[str, Any]:
        """Replay failed webhooks from the past N hours."""
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        failed_deliveries = [
            d for d in self.delivery_history
            if d.endpoint_id == endpoint_id
            and d.status == WebhookStatus.FAILED
            and d.created_at >= cutoff
        ]
        
        replayed = 0
        for delivery in failed_deliveries:
            new_delivery = self.queue_delivery(
                delivery.endpoint_id,
                delivery.event_type,
                delivery.payload
            )
            if new_delivery:
                replayed += 1
        
        return {
            'endpoint_id': endpoint_id,
            'failed_found': len(failed_deliveries),
            'replayed': replayed,
            'timeframe_hours': hours,
        }
    
    def get_hub_stats(self) -> Dict[str, Any]:
        """Get overall webhook statistics."""
        all_deliveries = self.delivery_history
        
        successful = sum(1 for d in all_deliveries if d.status == WebhookStatus.DELIVERED)
        failed = sum(1 for d in all_deliveries if d.status == WebhookStatus.FAILED)
        pending = sum(1 for d in self.deliveries.values() if d.status in [WebhookStatus.PENDING, WebhookStatus.RETRYING])
        
        return {
            'total_endpoints': len(self.endpoints),
            'active_endpoints': sum(1 for ep in self.endpoints.values() if ep.active),
            'total_deliveries_completed': len(all_deliveries),
            'successful_deliveries': successful,
            'failed_deliveries': failed,
            'pending_deliveries': pending,
            'overall_success_rate': f"{(successful / len(all_deliveries) * 100):.1f}%" if all_deliveries else "N/A",
        }
