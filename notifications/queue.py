"""Notification queue and processing."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from collections import deque


@dataclass
class QueuedNotification:
    """Notification in queue."""
    notification_id: str
    recipient_id: str
    priority: int  # 1-10 (10 = highest)
    created_at: datetime
    scheduled_for: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3


class NotificationQueue:
    """Queue for notification processing."""
    
    def __init__(self, max_queue_size: int = 10000):
        self.queue: deque = deque()
        self.max_queue_size = max_queue_size
        self.processed_count = 0
        self.stats = {
            'total_enqueued': 0,
            'total_processed': 0,
            'total_retried': 0,
        }
    
    def enqueue(self, notification: QueuedNotification) -> bool:
        """Enqueue notification for processing."""
        if len(self.queue) >= self.max_queue_size:
            return False
        
        self.queue.append(notification)
        self.stats['total_enqueued'] += 1
        return True
    
    def dequeue(self) -> Optional[QueuedNotification]:
        """Dequeue highest priority notification."""
        if not self.queue:
            return None
        
        # Simple priority sorting
        max_priority = -1
        best_item = None
        best_index = -1
        
        for i, item in enumerate(self.queue):
            if item.priority > max_priority:
                max_priority = item.priority
                best_item = item
                best_index = i
        
        if best_index >= 0:
            self.queue[best_index] = None
            self.queue = deque([n for n in self.queue if n is not None])
        
        return best_item
    
    def process_batch(self, batch_size: int = 100) -> List[QueuedNotification]:
        """Process batch of notifications."""
        batch = []
        for _ in range(min(batch_size, len(self.queue))):
            item = self.dequeue()
            if item:
                batch.append(item)
                self.stats['total_processed'] += 1
        
        return batch
    
    def requeue(self, notification: QueuedNotification) -> bool:
        """Requeue notification for retry."""
        if notification.retry_count < notification.max_retries:
            notification.retry_count += 1
            self.stats['total_retried'] += 1
            return self.enqueue(notification)
        return False
    
    def get_queue_size(self) -> int:
        """Get current queue size."""
        return len(self.queue)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            **self.stats,
            'current_queue_size': len(self.queue),
            'queue_usage_percent': (len(self.queue) / self.max_queue_size * 100),
        }


class BatchProcessor:
    """Processes notifications in batches."""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.processed_batches = 0
        self.last_processed_at: Optional[datetime] = None
    
    def process(self, notifications: List[QueuedNotification]) -> Dict[str, Any]:
        """Process batch of notifications."""
        if not notifications:
            return {'processed': 0, 'failed': 0}
        
        processed = len(notifications)
        failed = 0
        
        # Simulate processing
        for notif in notifications:
            # In production, would call channel managers
            if notif.priority < 3:  # Simulate low priority failures
                failed += 1
        
        self.processed_batches += 1
        self.last_processed_at = datetime.utcnow()
        
        return {
            'processed': processed - failed,
            'failed': failed,
            'total_batches': self.processed_batches,
        }
    
    def get_processor_stats(self) -> Dict[str, Any]:
        """Get processor statistics."""
        return {
            'batches_processed': self.processed_batches,
            'batch_size': self.batch_size,
            'last_processed': self.last_processed_at.isoformat() if self.last_processed_at else None,
        }
