"""Task scheduler and delayed message processing."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
import hashlib
from collections import deque


class ScheduleType(Enum):
    """Schedule types for tasks."""
    ONCE = "once"
    RECURRING = "recurring"
    CRON = "cron"


@dataclass
class ScheduledTask:
    """Scheduled task definition."""
    task_id: str
    queue_name: str
    payload: Dict[str, Any]
    schedule_type: ScheduleType
    scheduled_for: datetime
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    max_executions: Optional[int] = None
    execution_count: int = 0
    last_executed_at: Optional[datetime] = None
    next_execution_at: datetime = field(default_factory=datetime.utcnow)
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'task_id': self.task_id,
            'queue_name': self.queue_name,
            'payload': self.payload,
            'schedule_type': self.schedule_type.value,
            'scheduled_for': self.scheduled_for.isoformat(),
            'interval_seconds': self.interval_seconds,
            'cron_expression': self.cron_expression,
            'max_executions': self.max_executions,
            'execution_count': self.execution_count,
            'last_executed_at': self.last_executed_at.isoformat() if self.last_executed_at else None,
            'next_execution_at': self.next_execution_at.isoformat(),
            'enabled': self.enabled,
            'metadata': self.metadata
        }


class TaskScheduler:
    """Schedule and manage delayed/recurring tasks."""

    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.execution_queue: deque = deque()
        self.metrics = {
            'total_scheduled': 0,
            'total_executed': 0,
            'total_skipped': 0,
        }

    def schedule_task(
        self,
        queue_name: str,
        payload: Dict[str, Any],
        scheduled_for: datetime,
        schedule_type: ScheduleType = ScheduleType.ONCE,
        interval_seconds: Optional[int] = None,
        max_executions: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ScheduledTask:
        """Schedule a task for execution."""
        task_id = hashlib.md5(
            f"{queue_name}:{scheduled_for.isoformat()}".encode()
        ).hexdigest()[:12]

        task = ScheduledTask(
            task_id=task_id,
            queue_name=queue_name,
            payload=payload,
            schedule_type=schedule_type,
            scheduled_for=scheduled_for,
            interval_seconds=interval_seconds,
            max_executions=max_executions,
            next_execution_at=scheduled_for,
            metadata=metadata or {}
        )

        self.tasks[task_id] = task
        self.metrics['total_scheduled'] += 1
        return task

    def get_ready_tasks(self) -> List[ScheduledTask]:
        """Get tasks ready for execution."""
        now = datetime.utcnow()
        ready = []

        for task in self.tasks.values():
            if not task.enabled:
                continue

            if task.max_executions and task.execution_count >= task.max_executions:
                continue

            if task.next_execution_at <= now:
                ready.append(task)

        return ready

    def mark_executed(self, task_id: str) -> ScheduledTask:
        """Mark task as executed and schedule next."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task '{task_id}' not found")

        task.execution_count += 1
        task.last_executed_at = datetime.utcnow()
        self.metrics['total_executed'] += 1

        # Schedule next execution if recurring
        if task.schedule_type == ScheduleType.RECURRING and task.interval_seconds:
            task.next_execution_at = datetime.utcnow() + timedelta(seconds=task.interval_seconds)

            if task.max_executions and task.execution_count >= task.max_executions:
                task.enabled = False

        return task

    def update_task(self, task_id: str, **updates) -> ScheduledTask:
        """Update task configuration."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task '{task_id}' not found")

        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)

        return task

    def disable_task(self, task_id: str) -> ScheduledTask:
        """Disable a task."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task '{task_id}' not found")

        task.enabled = False
        return task

    def list_tasks(self, queue_name: Optional[str] = None) -> List[ScheduledTask]:
        """List all tasks, optionally filtered by queue."""
        tasks = self.tasks.values()

        if queue_name:
            tasks = [t for t in tasks if t.queue_name == queue_name]

        return list(tasks)

    def get_task_stats(self, task_id: str) -> Dict[str, Any]:
        """Get task statistics."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task '{task_id}' not found")

        return {
            'task_id': task_id,
            'queue_name': task.queue_name,
            'schedule_type': task.schedule_type.value,
            'enabled': task.enabled,
            'execution_count': task.execution_count,
            'max_executions': task.max_executions,
            'last_executed_at': task.last_executed_at.isoformat() if task.last_executed_at else None,
            'next_execution_at': task.next_execution_at.isoformat(),
            'interval_seconds': task.interval_seconds
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get scheduler metrics."""
        return {
            'total_scheduled': self.metrics['total_scheduled'],
            'total_executed': self.metrics['total_executed'],
            'active_tasks': sum(1 for t in self.tasks.values() if t.enabled),
            'tasks_at_capacity': sum(
                1 for t in self.tasks.values()
                if t.max_executions and t.execution_count >= t.max_executions
            )
        }
