"""Tests for message queue system."""

import pytest
from datetime import datetime, timedelta
from message_queue.queue import QueueEngine, QueueType, MessagePriority, MessageStatus
from message_queue.scheduler import TaskScheduler, ScheduleType
from message_queue.worker import WorkerPool, WorkerStatus


class TestQueue:
    """Test queue operations."""

    def test_create_queue(self):
        """Test queue creation."""
        engine = QueueEngine()
        queue = engine.create_queue('test-queue', QueueType.FIFO)
        assert queue.queue_name == 'test-queue'
        assert queue.queue_type == QueueType.FIFO

    def test_max_queues_limit(self):
        """Test max queues limit."""
        engine = QueueEngine(max_queues=2)
        engine.create_queue('q1', QueueType.FIFO)
        engine.create_queue('q2', QueueType.FIFO)
        
        with pytest.raises(RuntimeError):
            engine.create_queue('q3', QueueType.FIFO)

    def test_get_queue(self):
        """Test getting queue."""
        engine = QueueEngine()
        engine.create_queue('test', QueueType.FIFO)
        queue = engine.get_queue('test')
        assert queue is not None
        assert queue.queue_name == 'test'

    def test_enqueue_message(self):
        """Test enqueuing message."""
        engine = QueueEngine()
        engine.create_queue('test', QueueType.FIFO)
        
        msg = engine.enqueue('test', {'key': 'value'})
        assert msg.payload == {'key': 'value'}
        assert msg.status == MessageStatus.PENDING

    def test_enqueue_with_priority(self):
        """Test enqueuing with priority."""
        engine = QueueEngine()
        engine.create_queue('test', QueueType.PRIORITY)
        
        msg1 = engine.enqueue('test', {'id': 1}, priority=MessagePriority.LOW)
        msg2 = engine.enqueue('test', {'id': 2}, priority=MessagePriority.CRITICAL)
        msg3 = engine.enqueue('test', {'id': 3}, priority=MessagePriority.NORMAL)
        
        assert msg1.priority == MessagePriority.LOW
        assert msg2.priority == MessagePriority.CRITICAL

    def test_dequeue_fifo(self):
        """Test FIFO dequeue."""
        engine = QueueEngine()
        engine.create_queue('test', QueueType.FIFO)
        
        engine.enqueue('test', {'id': 1})
        engine.enqueue('test', {'id': 2})
        engine.enqueue('test', {'id': 3})
        
        msgs = engine.dequeue('test', batch_size=2)
        assert len(msgs) == 2
        assert msgs[0].payload['id'] == 1
        assert msgs[1].payload['id'] == 2

    def test_dequeue_priority(self):
        """Test priority dequeue."""
        engine = QueueEngine()
        engine.create_queue('test', QueueType.PRIORITY)
        
        engine.enqueue('test', {'id': 1}, priority=MessagePriority.LOW)
        engine.enqueue('test', {'id': 2}, priority=MessagePriority.CRITICAL)
        engine.enqueue('test', {'id': 3}, priority=MessagePriority.NORMAL)
        
        msgs = engine.dequeue('test', batch_size=1)
        assert len(msgs) == 1
        assert msgs[0].payload['id'] == 2  # CRITICAL first

    def test_complete_message(self):
        """Test completing message."""
        engine = QueueEngine()
        engine.create_queue('test', QueueType.FIFO)
        
        msg = engine.enqueue('test', {'id': 1})
        dequeued = engine.dequeue('test', batch_size=1)[0]
        completed = engine.complete_message('test', dequeued.message_id)
        
        assert completed.status == MessageStatus.COMPLETED
        assert completed.completed_at is not None

    def test_fail_message_retry(self):
        """Test failing message with retry."""
        engine = QueueEngine()
        engine.create_queue('test', QueueType.FIFO)
        
        msg = engine.enqueue('test', {'id': 1}, max_retries=3)
        dequeued = engine.dequeue('test', batch_size=1)[0]
        
        failed = engine.fail_message('test', dequeued.message_id, 'Test error')
        assert failed.retry_count == 1
        assert failed.status == MessageStatus.PENDING

    def test_fail_message_dead_letter(self):
        """Test message goes to dead letter after max retries."""
        engine = QueueEngine()
        engine.create_queue('test', QueueType.FIFO)
        
        msg = engine.enqueue('test', {'id': 1}, max_retries=1)
        
        # Retry 1 - should go to dead letter
        dequeued = engine.dequeue('test', batch_size=1)[0]
        failed = engine.fail_message('test', dequeued.message_id, 'Error 1')
        
        # Should be in dead letter now
        dead = engine.get_dead_letter_messages('test')
        assert len(dead) == 1
        assert dead[0].status == MessageStatus.DEAD_LETTER

    def test_queue_stats(self):
        """Test queue statistics."""
        engine = QueueEngine()
        engine.create_queue('test', QueueType.FIFO)
        
        engine.enqueue('test', {'id': 1})
        engine.enqueue('test', {'id': 2})
        
        stats = engine.get_queue_stats('test')
        assert stats['size'] == 2
        assert stats['utilization_percent'] == 0.02

    def test_register_handler(self):
        """Test handler registration."""
        engine = QueueEngine()
        engine.create_queue('test', QueueType.FIFO)
        
        def test_handler(payload):
            pass
        
        engine.register_handler('test', test_handler)
        assert 'test' in engine.handlers

    def test_process_queue_with_handler(self):
        """Test processing queue with handler."""
        engine = QueueEngine()
        engine.create_queue('test', QueueType.FIFO)
        
        processed_items = []
        
        def handler(payload):
            processed_items.append(payload)
        
        engine.register_handler('test', handler)
        engine.enqueue('test', {'id': 1})
        engine.enqueue('test', {'id': 2})
        
        result = engine.process_queue('test', batch_size=2)
        assert result['processed'] == 2
        assert len(processed_items) == 2

    def test_metrics(self):
        """Test engine metrics."""
        engine = QueueEngine()
        engine.create_queue('test', QueueType.FIFO)
        
        engine.enqueue('test', {'id': 1})
        engine.enqueue('test', {'id': 2})
        
        metrics = engine.get_metrics()
        assert metrics['total_enqueued'] == 2
        assert metrics['queue_count'] == 1


class TestScheduler:
    """Test task scheduler."""

    def test_schedule_task(self):
        """Test scheduling task."""
        scheduler = TaskScheduler()
        future = datetime.utcnow() + timedelta(seconds=5)
        
        task = scheduler.schedule_task(
            'queue',
            {'data': 'test'},
            future
        )
        assert task.queue_name == 'queue'
        assert task.schedule_type == ScheduleType.ONCE

    def test_schedule_recurring_task(self):
        """Test scheduling recurring task."""
        scheduler = TaskScheduler()
        future = datetime.utcnow()
        
        task = scheduler.schedule_task(
            'queue',
            {'data': 'test'},
            future,
            schedule_type=ScheduleType.RECURRING,
            interval_seconds=60
        )
        assert task.schedule_type == ScheduleType.RECURRING
        assert task.interval_seconds == 60

    def test_get_ready_tasks(self):
        """Test getting ready tasks."""
        scheduler = TaskScheduler()
        
        # Past task (ready)
        past = datetime.utcnow() - timedelta(seconds=1)
        scheduler.schedule_task('q1', {'id': 1}, past)
        
        # Future task (not ready)
        future = datetime.utcnow() + timedelta(seconds=10)
        scheduler.schedule_task('q2', {'id': 2}, future)
        
        ready = scheduler.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].payload['id'] == 1

    def test_mark_executed(self):
        """Test marking task as executed."""
        scheduler = TaskScheduler()
        past = datetime.utcnow() - timedelta(seconds=1)
        
        task = scheduler.schedule_task('queue', {'id': 1}, past)
        executed = scheduler.mark_executed(task.task_id)
        
        assert executed.execution_count == 1
        assert executed.last_executed_at is not None

    def test_recurring_task_reschedule(self):
        """Test recurring task is rescheduled."""
        scheduler = TaskScheduler()
        past = datetime.utcnow() - timedelta(seconds=1)
        
        task = scheduler.schedule_task(
            'queue',
            {'id': 1},
            past,
            schedule_type=ScheduleType.RECURRING,
            interval_seconds=60
        )
        
        old_next = task.next_execution_at
        scheduler.mark_executed(task.task_id)
        
        # Next execution should be in future
        assert task.next_execution_at > old_next

    def test_max_executions(self):
        """Test max executions limit."""
        scheduler = TaskScheduler()
        past = datetime.utcnow() - timedelta(seconds=1)
        
        task = scheduler.schedule_task(
            'queue',
            {'id': 1},
            past,
            schedule_type=ScheduleType.RECURRING,
            interval_seconds=10,
            max_executions=3
        )
        
        for i in range(3):
            ready = scheduler.get_ready_tasks()
            assert len(ready) == 1, f"Should have ready task on iteration {i}"
            scheduler.mark_executed(ready[0].task_id)
            # Reset next_execution_at to past for next iteration
            task.next_execution_at = datetime.utcnow() - timedelta(seconds=1)
        
        assert task.execution_count == 3
        assert task.enabled == False

    def test_scheduler_metrics(self):
        """Test scheduler metrics."""
        scheduler = TaskScheduler()
        past = datetime.utcnow() - timedelta(seconds=1)
        
        scheduler.schedule_task('q1', {'id': 1}, past)
        scheduler.schedule_task('q2', {'id': 2}, past)
        
        metrics = scheduler.get_metrics()
        assert metrics['total_scheduled'] == 2
        assert metrics['active_tasks'] == 2


class TestWorkerPool:
    """Test worker pool."""

    def test_create_worker_pool(self):
        """Test creating worker pool."""
        engine = QueueEngine()
        pool = WorkerPool(engine, pool_size=4)
        
        assert len(pool.workers) == 4
        assert pool.pool_size == 4

    def test_register_handler_all_workers(self):
        """Test registering handler on all workers."""
        engine = QueueEngine()
        pool = WorkerPool(engine, pool_size=4)
        
        def handler(payload):
            pass
        
        pool.register_handler('test', handler)
        
        for worker in pool.workers.values():
            assert 'test' in worker.handler_registry

    def test_worker_stats(self):
        """Test getting worker statistics."""
        engine = QueueEngine()
        engine.create_queue('test', QueueType.FIFO)
        pool = WorkerPool(engine, pool_size=2)
        
        def handler(payload):
            pass
        
        pool.register_handler('test', handler)
        engine.register_handler('test', handler)
        
        engine.enqueue('test', {'id': 1})
        
        result = pool.process_batch('test', batch_size=1)
        assert result['processed'] == 1

    def test_pool_stats(self):
        """Test getting pool statistics."""
        engine = QueueEngine()
        engine.create_queue('test', QueueType.FIFO)
        pool = WorkerPool(engine, pool_size=4)
        
        stats = pool.get_pool_stats()
        assert stats['pool_size'] == 4
        assert len(stats['workers']) == 4

    def test_worker_list(self):
        """Test listing workers."""
        engine = QueueEngine()
        pool = WorkerPool(engine, pool_size=3)
        
        workers = pool.list_workers()
        assert len(workers) == 3
        assert all(w['status'] == 'idle' for w in workers)

    def test_multiple_message_processing(self):
        """Test processing multiple messages."""
        engine = QueueEngine()
        engine.create_queue('test', QueueType.FIFO)
        pool = WorkerPool(engine, pool_size=4)
        
        processed = []
        
        def handler(payload):
            processed.append(payload)
        
        pool.register_handler('test', handler)
        engine.register_handler('test', handler)
        
        for i in range(5):
            engine.enqueue('test', {'id': i})
        
        result = pool.process_batch('test', batch_size=5)
        assert result['processed'] >= 1

    def test_worker_shutdown(self):
        """Test shutting down worker pool."""
        engine = QueueEngine()
        pool = WorkerPool(engine, pool_size=2)
        
        pool.shutdown()
        
        for worker in pool.workers.values():
            assert worker.metrics.status == WorkerStatus.SHUTDOWN


# Run tests if executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
