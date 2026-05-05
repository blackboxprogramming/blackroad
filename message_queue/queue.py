"""Message queue system for async job processing."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
import json
import hashlib
from collections import deque


class MessageStatus(Enum):
    """Message lifecycle status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class QueueType(Enum):
    """Queue types for different processing patterns."""
    FIFO = "fifo"
    PRIORITY = "priority"
    DELAYED = "delayed"
    FANOUT = "fanout"


@dataclass
class Message:
    """Individual message in queue."""
    message_id: str
    queue_name: str
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    status: MessageStatus = MessageStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    delay_seconds: int = 0
    dead_letter_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            'message_id': self.message_id,
            'queue_name': self.queue_name,
            'payload': self.payload,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'delay_seconds': self.delay_seconds,
            'dead_letter_reason': self.dead_letter_reason,
            'metadata': self.metadata
        }


@dataclass
class Queue:
    """Individual queue with messages."""
    queue_name: str
    queue_type: QueueType
    created_at: datetime = field(default_factory=datetime.utcnow)
    messages: deque = field(default_factory=deque)
    priority_messages: Dict[int, deque] = field(default_factory=lambda: {
        4: deque(),  # CRITICAL
        3: deque(),  # HIGH
        2: deque(),  # NORMAL
        1: deque(),  # LOW
    })
    dead_letter_queue: deque = field(default_factory=deque)
    max_size: int = 10000

    def is_full(self) -> bool:
        """Check if queue is at capacity."""
        total = len(self.messages) + sum(len(q) for q in self.priority_messages.values())
        return total >= self.max_size

    def get_size(self) -> int:
        """Get current queue size."""
        return len(self.messages) + sum(len(q) for q in self.priority_messages.values())


class QueueEngine:
    """Central message queue engine."""

    def __init__(self, max_queues: int = 100):
        self.max_queues = max_queues
        self.queues: Dict[str, Queue] = {}
        self.handlers: Dict[str, Callable] = {}
        self.processing_messages: Dict[str, Message] = {}  # Track in-flight messages
        self.metrics = {
            'total_enqueued': 0,
            'total_processed': 0,
            'total_failed': 0,
            'total_retried': 0,
        }

    def create_queue(self, queue_name: str, queue_type: QueueType = QueueType.FIFO) -> Queue:
        """Create new queue."""
        if len(self.queues) >= self.max_queues:
            raise RuntimeError(f"Max queues ({self.max_queues}) reached")
        
        queue = Queue(queue_name=queue_name, queue_type=queue_type)
        self.queues[queue_name] = queue
        return queue

    def get_queue(self, queue_name: str) -> Optional[Queue]:
        """Get queue by name."""
        return self.queues.get(queue_name)

    def enqueue(
        self,
        queue_name: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        delay_seconds: int = 0,
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add message to queue."""
        queue = self.queues.get(queue_name)
        if not queue:
            raise ValueError(f"Queue '{queue_name}' not found")

        if queue.is_full():
            raise RuntimeError(f"Queue '{queue_name}' is full")

        # Generate message ID
        message_id = hashlib.md5(
            f"{queue_name}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:12]

        message = Message(
            message_id=message_id,
            queue_name=queue_name,
            payload=payload,
            priority=priority,
            delay_seconds=delay_seconds,
            max_retries=max_retries,
            metadata=metadata or {}
        )

        # Add to queue based on type
        if queue.queue_type == QueueType.PRIORITY:
            queue.priority_messages[priority.value].append(message)
        else:
            queue.messages.append(message)

        self.metrics['total_enqueued'] += 1
        return message

    def dequeue(self, queue_name: str, batch_size: int = 1) -> List[Message]:
        """Get messages from queue for processing."""
        queue = self.queues.get(queue_name)
        if not queue:
            raise ValueError(f"Queue '{queue_name}' not found")

        messages = []

        if queue.queue_type == QueueType.PRIORITY:
            # Get from highest priority first
            for priority_level in [4, 3, 2, 1]:  # CRITICAL to LOW
                pq = queue.priority_messages[priority_level]
                checked = 0
                max_check = len(pq) * 2  # Limit iterations to avoid infinite loop
                
                while messages.__len__() < batch_size and pq and checked < max_check:
                    checked += 1
                    msg = pq.popleft()
                    if msg.delay_seconds > 0:
                        # Requeue if delayed
                        queue.priority_messages[priority_level].append(msg)
                    else:
                        msg.status = MessageStatus.PROCESSING
                        msg.started_at = datetime.utcnow()
                        self.processing_messages[msg.message_id] = msg
                        messages.append(msg)
        else:
            # FIFO processing
            checked = 0
            max_check = len(queue.messages) * 2  # Limit iterations to avoid infinite loop
            
            while len(messages) < batch_size and queue.messages and checked < max_check:
                checked += 1
                msg = queue.messages.popleft()
                if msg.delay_seconds > 0:
                    # Requeue if delayed
                    queue.messages.append(msg)
                else:
                    msg.status = MessageStatus.PROCESSING
                    msg.started_at = datetime.utcnow()
                    self.processing_messages[msg.message_id] = msg
                    messages.append(msg)

        return messages

    def complete_message(self, queue_name: str, message_id: str) -> Message:
        """Mark message as completed."""
        if message_id not in self.processing_messages:
            raise ValueError(f"Message '{message_id}' not in processing")

        msg = self.processing_messages.pop(message_id)
        msg.status = MessageStatus.COMPLETED
        msg.completed_at = datetime.utcnow()
        self.metrics['total_processed'] += 1
        return msg

    def fail_message(self, queue_name: str, message_id: str, reason: str = "") -> Message:
        """Mark message as failed (with retry logic)."""
        queue = self.queues.get(queue_name)
        if not queue:
            raise ValueError(f"Queue '{queue_name}' not found")

        if message_id not in self.processing_messages:
            raise ValueError(f"Message '{message_id}' not in processing")

        msg = self.processing_messages.pop(message_id)
        msg.retry_count += 1

        if msg.retry_count >= msg.max_retries:
            # Move to dead letter queue
            msg.status = MessageStatus.DEAD_LETTER
            msg.dead_letter_reason = f"Max retries exceeded: {reason}"
            queue.dead_letter_queue.append(msg)
            self.metrics['total_failed'] += 1
        else:
            # Requeue for retry
            msg.status = MessageStatus.PENDING
            msg.delay_seconds = msg.retry_count * 2  # Exponential backoff
            if queue.queue_type == QueueType.PRIORITY:
                queue.priority_messages[msg.priority.value].append(msg)
            else:
                queue.messages.append(msg)
            self.metrics['total_retried'] += 1

        return msg

    def register_handler(self, queue_name: str, handler: Callable) -> None:
        """Register message handler for a queue."""
        self.handlers[queue_name] = handler

    def process_queue(self, queue_name: str, batch_size: int = 10) -> Dict[str, Any]:
        """Process messages from queue using registered handler."""
        if queue_name not in self.handlers:
            raise ValueError(f"No handler registered for queue '{queue_name}'")

        handler = self.handlers[queue_name]
        messages = self.dequeue(queue_name, batch_size)

        processed = 0
        failed = 0

        for msg in messages:
            try:
                handler(msg.payload)
                self.complete_message(queue_name, msg.message_id)
                processed += 1
            except Exception as e:
                self.fail_message(queue_name, msg.message_id, str(e))
                failed += 1

        return {
            'queue_name': queue_name,
            'processed': processed,
            'failed': failed,
            'messages': [m.to_dict() for m in messages]
        }

    def get_queue_stats(self, queue_name: str) -> Dict[str, Any]:
        """Get queue statistics."""
        queue = self.queues.get(queue_name)
        if not queue:
            raise ValueError(f"Queue '{queue_name}' not found")

        pending = sum(
            len(q) for q in queue.priority_messages.values()
        ) if queue.queue_type == QueueType.PRIORITY else len(queue.messages)

        return {
            'queue_name': queue_name,
            'queue_type': queue.queue_type.value,
            'size': pending,
            'max_size': queue.max_size,
            'dead_letter_count': len(queue.dead_letter_queue),
            'created_at': queue.created_at.isoformat(),
            'pending_messages': pending,
            'utilization_percent': (pending / queue.max_size * 100)
        }

    def get_dead_letter_messages(self, queue_name: str) -> List[Message]:
        """Get messages in dead letter queue."""
        queue = self.queues.get(queue_name)
        if not queue:
            raise ValueError(f"Queue '{queue_name}' not found")

        return list(queue.dead_letter_queue)

    def list_queues(self) -> List[Dict[str, Any]]:
        """List all queues with stats."""
        return [self.get_queue_stats(name) for name in self.queues.keys()]

    def get_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics."""
        return {
            'total_enqueued': self.metrics['total_enqueued'],
            'total_processed': self.metrics['total_processed'],
            'total_failed': self.metrics['total_failed'],
            'total_retried': self.metrics['total_retried'],
            'queue_count': len(self.queues),
            'success_rate': (
                self.metrics['total_processed'] / max(1, self.metrics['total_enqueued']) * 100
                if self.metrics['total_enqueued'] > 0 else 0
            )
        }
