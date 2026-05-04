"""GraphQL subscriptions and real-time updates."""

from typing import Dict, List, Any, Callable, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import uuid


class SubscriptionEvent(Enum):
    """Subscription event types."""
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    ORDER_PLACED = "order_placed"
    ORDER_UPDATED = "order_updated"
    MESSAGE_SENT = "message_sent"


@dataclass
class Subscriber:
    """GraphQL subscriber."""
    id: str
    event_types: Set[SubscriptionEvent]
    callback: Callable
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class SubscriptionManager:
    """Manages GraphQL subscriptions."""
    
    def __init__(self):
        self.subscribers: Dict[str, Subscriber] = {}
        self.event_history: List[Dict[str, Any]] = []
        self.max_history = 1000
    
    def subscribe(self, event_types: List[SubscriptionEvent], callback: Callable) -> str:
        """Subscribe to events."""
        subscriber_id = str(uuid.uuid4())
        subscriber = Subscriber(
            id=subscriber_id,
            event_types=set(event_types),
            callback=callback,
        )
        self.subscribers[subscriber_id] = subscriber
        return subscriber_id
    
    def unsubscribe(self, subscriber_id: str) -> bool:
        """Unsubscribe from events."""
        if subscriber_id in self.subscribers:
            del self.subscribers[subscriber_id]
            return True
        return False
    
    def emit(self, event_type: SubscriptionEvent, data: Dict[str, Any]) -> int:
        """Emit event to subscribers."""
        count = 0
        
        # Record event
        self.event_history.append({
            'event_type': event_type.value,
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
        })
        
        # Trim history
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        # Notify subscribers
        for subscriber in self.subscribers.values():
            if event_type in subscriber.event_types:
                try:
                    subscriber.callback({
                        'event': event_type.value,
                        'data': data,
                        'timestamp': datetime.utcnow().isoformat(),
                    })
                    count += 1
                except Exception as e:
                    print(f"Error notifying subscriber {subscriber.id}: {e}")
        
        return count
    
    def get_subscriber_count(self, event_type: SubscriptionEvent = None) -> int:
        """Get subscriber count."""
        if event_type is None:
            return len(self.subscribers)
        
        count = 0
        for subscriber in self.subscribers.values():
            if event_type in subscriber.event_types:
                count += 1
        return count
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get subscription metrics."""
        return {
            'total_subscribers': len(self.subscribers),
            'event_types_count': len(SubscriptionEvent),
            'event_history_size': len(self.event_history),
            'unique_event_types': len(set(e['event_type'] for e in self.event_history)),
        }


class RealtimeSync:
    """Real-time synchronization."""
    
    def __init__(self):
        self.sync_queue: List[Dict[str, Any]] = []
        self.synced_count = 0
    
    def queue_sync(self, entity_type: str, entity_id: str, action: str, data: Dict[str, Any]) -> bool:
        """Queue entity for sync."""
        self.sync_queue.append({
            'entity_type': entity_type,
            'entity_id': entity_id,
            'action': action,  # created, updated, deleted
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
        })
        return True
    
    def process_sync_queue(self) -> Dict[str, Any]:
        """Process sync queue."""
        if not self.sync_queue:
            return {'synced': 0}
        
        # In production, this would persist to database
        synced = len(self.sync_queue)
        self.synced_count += synced
        self.sync_queue = []
        
        return {
            'synced': synced,
            'total_synced': self.synced_count,
        }
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status."""
        return {
            'queue_size': len(self.sync_queue),
            'total_synced': self.synced_count,
        }
