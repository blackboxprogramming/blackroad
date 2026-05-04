"""Worker pool for processing messages from queues."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set
import time


class WorkerStatus(Enum):
    """Worker status states."""
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class WorkerMetrics:
    """Metrics for a worker."""
    worker_id: str
    status: WorkerStatus = WorkerStatus.IDLE
    messages_processed: int = 0
    messages_failed: int = 0
    total_processing_time: float = 0.0
    last_processed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    uptime_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        avg_time = (
            self.total_processing_time / self.messages_processed
            if self.messages_processed > 0 else 0
        )

        return {
            'worker_id': self.worker_id,
            'status': self.status.value,
            'messages_processed': self.messages_processed,
            'messages_failed': self.messages_failed,
            'average_processing_time_ms': avg_time * 1000,
            'last_processed_at': self.last_processed_at.isoformat() if self.last_processed_at else None,
            'uptime_seconds': self.uptime_seconds
        }


@dataclass
class Worker:
    """Individual worker for processing messages."""
    worker_id: str
    queue_engine: Any  # Reference to QueueEngine
    handler_registry: Dict[str, Callable] = field(default_factory=dict)
    metrics: WorkerMetrics = field(default_factory=lambda: WorkerMetrics(''))

    def __post_init__(self):
        """Initialize metrics with worker_id."""
        self.metrics = WorkerMetrics(worker_id=self.worker_id)

    def process_message(self, queue_name: str) -> Dict[str, Any]:
        """Process single message from queue."""
        try:
            self.metrics.status = WorkerStatus.PROCESSING

            # Get message
            messages = self.queue_engine.dequeue(queue_name, batch_size=1)

            if not messages:
                self.metrics.status = WorkerStatus.IDLE
                return {'status': 'no_messages', 'worker_id': self.worker_id}

            msg = messages[0]
            start_time = time.time()

            # Get handler
            if queue_name not in self.handler_registry:
                raise ValueError(f"No handler for queue '{queue_name}'")

            handler = self.handler_registry[queue_name]

            # Process
            handler(msg.payload)
            self.queue_engine.complete_message(queue_name, msg.message_id)

            # Update metrics
            processing_time = time.time() - start_time
            self.metrics.messages_processed += 1
            self.metrics.total_processing_time += processing_time
            self.metrics.last_processed_at = datetime.utcnow()

            self.metrics.status = WorkerStatus.IDLE

            return {
                'status': 'completed',
                'worker_id': self.worker_id,
                'message_id': msg.message_id,
                'queue_name': queue_name,
                'processing_time_ms': processing_time * 1000
            }

        except Exception as e:
            self.metrics.status = WorkerStatus.ERROR
            self.metrics.messages_failed += 1

            if messages:
                self.queue_engine.fail_message(queue_name, msg.message_id, str(e))

            return {
                'status': 'failed',
                'worker_id': self.worker_id,
                'error': str(e)
            }

    def register_handler(self, queue_name: str, handler: Callable) -> None:
        """Register handler for queue."""
        self.handler_registry[queue_name] = handler

    def get_metrics(self) -> Dict[str, Any]:
        """Get worker metrics."""
        uptime = (datetime.utcnow() - self.metrics.created_at).total_seconds()
        self.metrics.uptime_seconds = uptime
        return self.metrics.to_dict()


class WorkerPool:
    """Pool of workers for distributed message processing."""

    def __init__(self, queue_engine: Any, pool_size: int = 4):
        self.queue_engine = queue_engine
        self.pool_size = pool_size
        self.workers: Dict[str, Worker] = {}
        self.active_workers: Set[str] = set()
        self.metrics = {
            'total_processed': 0,
            'total_failed': 0,
            'worker_utilization_percent': 0.0
        }

        # Create workers
        for i in range(pool_size):
            worker_id = f"worker-{i:03d}"
            worker = Worker(
                worker_id=worker_id,
                queue_engine=queue_engine
            )
            self.workers[worker_id] = worker

    def register_handler(self, queue_name: str, handler: Callable) -> None:
        """Register handler for all workers."""
        for worker in self.workers.values():
            worker.register_handler(queue_name, handler)

    def process_batch(self, queue_name: str, batch_size: int = 10) -> Dict[str, Any]:
        """Process batch of messages with available workers."""
        results = []
        workers_used = 0

        for worker in self.workers.values():
            if workers_used >= batch_size:
                break

            if worker.metrics.status == WorkerStatus.IDLE:
                result = worker.process_message(queue_name)
                results.append(result)

                if result['status'] == 'completed':
                    self.metrics['total_processed'] += 1
                    workers_used += 1
                elif result['status'] == 'failed':
                    self.metrics['total_failed'] += 1
                    workers_used += 1

        # Update utilization
        active = sum(1 for w in self.workers.values() if w.metrics.status != WorkerStatus.IDLE)
        self.metrics['worker_utilization_percent'] = (active / self.pool_size) * 100

        return {
            'queue_name': queue_name,
            'batch_size': batch_size,
            'processed': sum(1 for r in results if r['status'] == 'completed'),
            'failed': sum(1 for r in results if r['status'] == 'failed'),
            'workers_used': workers_used,
            'results': results
        }

    def get_worker_stats(self, worker_id: str) -> Dict[str, Any]:
        """Get individual worker statistics."""
        worker = self.workers.get(worker_id)
        if not worker:
            raise ValueError(f"Worker '{worker_id}' not found")

        return worker.get_metrics()

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get worker pool statistics."""
        worker_stats = [w.get_metrics() for w in self.workers.values()]

        total_processed = sum(w['messages_processed'] for w in worker_stats)
        total_failed = sum(w['messages_failed'] for w in worker_stats)
        avg_processing_time = sum(
            w['average_processing_time_ms'] for w in worker_stats
        ) / len(worker_stats) if worker_stats else 0

        return {
            'pool_size': self.pool_size,
            'workers': worker_stats,
            'total_messages_processed': total_processed,
            'total_messages_failed': total_failed,
            'average_processing_time_ms': avg_processing_time,
            'success_rate': (
                total_processed / max(1, total_processed + total_failed) * 100
                if (total_processed + total_failed) > 0 else 0
            ),
            'utilization_percent': self.metrics['worker_utilization_percent']
        }

    def shutdown(self) -> None:
        """Shutdown all workers."""
        for worker in self.workers.values():
            worker.metrics.status = WorkerStatus.SHUTDOWN

    def list_workers(self) -> List[Dict[str, Any]]:
        """List all workers with status."""
        return [
            {
                'worker_id': w.worker_id,
                'status': w.metrics.status.value,
                'messages_processed': w.metrics.messages_processed,
                'messages_failed': w.metrics.messages_failed
            }
            for w in self.workers.values()
        ]
