"""Real-time event ingestion and stream processing."""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
from collections import defaultdict
import time


class EventType(Enum):
    """Types of events tracked."""
    PAGE_VIEW = "page_view"
    CLICK = "click"
    PURCHASE = "purchase"
    SIGNUP = "signup"
    LOGIN = "login"
    ERROR = "error"
    API_CALL = "api_call"
    SEARCH = "search"
    ADD_TO_CART = "add_to_cart"
    CHECKOUT = "checkout"
    REFUND = "refund"
    SUPPORT_TICKET = "support_ticket"


@dataclass
class Event:
    """An analytics event."""
    event_id: str
    event_type: EventType
    user_id: str
    timestamp: datetime
    properties: Dict[str, Any] = field(default_factory=dict)
    session_id: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat(),
            'properties': self.properties,
            'session_id': self.session_id,
            'context': self.context,
        }


class EventBatch:
    """A batch of events for processing."""
    
    def __init__(self, batch_id: str, max_size: int = 1000, max_age_sec: int = 60):
        self.batch_id = batch_id
        self.events: List[Event] = []
        self.max_size = max_size
        self.max_age_sec = max_age_sec
        self.created_at = datetime.utcnow()
    
    def add_event(self, event: Event) -> bool:
        """Add event to batch."""
        if len(self.events) >= self.max_size:
            return False
        self.events.append(event)
        return True
    
    def is_full(self) -> bool:
        """Check if batch is full."""
        return len(self.events) >= self.max_size
    
    def is_expired(self) -> bool:
        """Check if batch has aged out."""
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > self.max_age_sec
    
    def get_events(self) -> List[Event]:
        """Get all events in batch."""
        return self.events
    
    def get_size(self) -> int:
        """Get batch size."""
        return len(self.events)


class EventDeduplicator:
    """Deduplicates events based on event_id."""
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.seen_ids: Dict[str, datetime] = {}
    
    def is_duplicate(self, event_id: str) -> bool:
        """Check if event_id is duplicate."""
        if event_id in self.seen_ids:
            return True
        
        # Add to seen
        self.seen_ids[event_id] = datetime.utcnow()
        
        # Clean old entries
        cutoff = datetime.utcnow() - timedelta(hours=self.retention_hours)
        self.seen_ids = {
            eid: ts for eid, ts in self.seen_ids.items()
            if ts >= cutoff
        }
        
        return False


class EventIngestion:
    """Real-time event ingestion pipeline."""
    
    def __init__(self, batch_size: int = 1000, batch_timeout_sec: int = 60):
        """Initialize event ingestion."""
        self.batch_size = batch_size
        self.batch_timeout_sec = batch_timeout_sec
        self.current_batch = EventBatch(
            f"batch_{datetime.utcnow().timestamp()}",
            max_size=batch_size,
            max_age_sec=batch_timeout_sec
        )
        self.event_log: List[Event] = []
        self.deduplicator = EventDeduplicator()
        self.processors: List[Callable] = []
        self.metrics = {
            'total_events': 0,
            'deduplicated': 0,
            'batches_processed': 0,
            'errors': 0,
        }
    
    def ingest_event(
        self,
        event_type: EventType,
        user_id: str,
        properties: Optional[Dict[str, Any]] = None,
        session_id: str = "",
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Ingest a single event."""
        try:
            # Generate event ID
            event_id = self._generate_event_id(user_id, event_type)
            
            # Check for duplicates
            if self.deduplicator.is_duplicate(event_id):
                self.metrics['deduplicated'] += 1
                return False
            
            # Create event
            event = Event(
                event_id=event_id,
                event_type=event_type,
                user_id=user_id,
                timestamp=datetime.utcnow(),
                properties=properties or {},
                session_id=session_id,
                context=context or {}
            )
            
            # Add to log
            self.event_log.append(event)
            self.metrics['total_events'] += 1
            
            # Add to batch
            added = self.current_batch.add_event(event)
            
            # Check if batch is ready
            if self.current_batch.is_full() or self.current_batch.is_expired():
                self._flush_batch()
            
            return added
        except Exception as e:
            self.metrics['errors'] += 1
            return False
    
    def register_processor(self, processor: Callable) -> None:
        """Register event processor function."""
        self.processors.append(processor)
    
    def _flush_batch(self) -> Optional[List[Event]]:
        """Flush current batch for processing."""
        if self.current_batch.get_size() == 0:
            return None
        
        events = self.current_batch.get_events()
        
        # Process with registered processors
        for processor in self.processors:
            try:
                processor(events)
            except Exception as e:
                pass
        
        self.metrics['batches_processed'] += 1
        
        # Create new batch
        self.current_batch = EventBatch(
            f"batch_{datetime.utcnow().timestamp()}",
            max_size=self.batch_size,
            max_age_sec=self.batch_timeout_sec
        )
        
        return events
    
    def _generate_event_id(self, user_id: str, event_type: EventType) -> str:
        """Generate unique event ID."""
        timestamp = datetime.utcnow().timestamp()
        content = f"{user_id}_{event_type.value}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_pending_batch(self) -> Optional[EventBatch]:
        """Get current pending batch (for testing)."""
        return self.current_batch
    
    def force_flush(self) -> Optional[List[Event]]:
        """Force flush pending batch."""
        return self._flush_batch()
    
    def get_event_count(self, event_type: Optional[EventType] = None) -> int:
        """Get event count."""
        if not event_type:
            return len(self.event_log)
        return sum(1 for e in self.event_log if e.event_type == event_type)
    
    def get_recent_events(self, limit: int = 100) -> List[Event]:
        """Get recent events."""
        return self.event_log[-limit:]
    
    def get_ingestion_metrics(self) -> Dict[str, Any]:
        """Get ingestion metrics."""
        return {
            'total_events_ingested': self.metrics['total_events'],
            'deduplicated_events': self.metrics['deduplicated'],
            'batches_processed': self.metrics['batches_processed'],
            'errors': self.metrics['errors'],
            'pending_batch_size': self.current_batch.get_size(),
            'deduplication_rate': f"{(self.metrics['deduplicated'] / max(1, self.metrics['total_events'])) * 100:.2f}%",
            'throughput_eps': f"{self.metrics['total_events'] / max(1, (datetime.utcnow() - self.current_batch.created_at).total_seconds()):.0f}",
        }


class EventStream:
    """Manages multiple event streams."""
    
    def __init__(self):
        """Initialize event streams."""
        self.streams: Dict[str, EventIngestion] = {}
    
    def create_stream(self, stream_id: str, batch_size: int = 1000) -> EventIngestion:
        """Create a new stream."""
        stream = EventIngestion(batch_size=batch_size)
        self.streams[stream_id] = stream
        return stream
    
    def get_stream(self, stream_id: str) -> Optional[EventIngestion]:
        """Get a stream."""
        return self.streams.get(stream_id)
    
    def list_streams(self) -> List[str]:
        """List all streams."""
        return list(self.streams.keys())
    
    def get_total_events(self) -> int:
        """Get total events across all streams."""
        return sum(s.metrics['total_events'] for s in self.streams.values())
    
    def get_stream_metrics(self) -> Dict[str, Any]:
        """Get metrics for all streams."""
        return {
            'total_streams': len(self.streams),
            'total_events': self.get_total_events(),
            'streams': {
                sid: stream.get_ingestion_metrics()
                for sid, stream in self.streams.items()
            }
        }
