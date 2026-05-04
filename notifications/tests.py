"""Notification system tests."""

import unittest
from datetime import datetime
from notifications.engine import (
    NotificationEngine, TemplateEngine, NotificationTemplate, 
    NotificationType, NotificationStatus, NotificationStore
)
from notifications.channels import (
    ChannelManager, EmailChannel, SMSChannel, PushChannel, 
    InAppChannel, ChannelType
)
from notifications.queue import NotificationQueue, QueuedNotification, BatchProcessor
from notifications.rules import RulesEngine, Rule, TriggerType, EventListener
from notifications.dashboard import generate_notification_dashboard


class TestTemplateEngine(unittest.TestCase):
    def setUp(self):
        self.engine = TemplateEngine()
    
    def test_register_template(self):
        template = NotificationTemplate(
            template_id='welcome',
            name='Welcome Email',
            subject='Welcome {name}!',
            body='Hello {name}, welcome to our platform!',
            notification_type=NotificationType.WELCOME,
            variables=['name']
        )
        result = self.engine.register_template(template)
        self.assertTrue(result)
    
    def test_render_template(self):
        template = NotificationTemplate(
            template_id='order',
            name='Order Confirmation',
            subject='Order {order_id} confirmed',
            body='Your order {order_id} for ${amount}',
            notification_type=NotificationType.ORDER_CONFIRMATION,
            variables=['order_id', 'amount']
        )
        self.engine.register_template(template)
        
        rendered = self.engine.render('order', {'order_id': '123', 'amount': '99.99'})
        self.assertIn('123', rendered['subject'])
        self.assertIn('99.99', rendered['body'])
    
    def test_list_templates(self):
        template = NotificationTemplate(
            template_id='alert',
            name='Alert',
            subject='Alert: {message}',
            body='{message}',
            notification_type=NotificationType.ALERT,
            variables=['message']
        )
        self.engine.register_template(template)
        templates = self.engine.list_templates(NotificationType.ALERT)
        self.assertEqual(len(templates), 1)


class TestNotificationStore(unittest.TestCase):
    def setUp(self):
        self.store = NotificationStore()
    
    def test_store_notification(self):
        from notifications.engine import Notification
        notif = Notification(
            notification_id='n1',
            recipient_id='user1',
            template_id='welcome',
            subject='Welcome',
            body='Welcome to platform',
            status=NotificationStatus.PENDING,
            channels=['email']
        )
        result = self.store.store(notif)
        self.assertTrue(result)
    
    def test_get_notification(self):
        from notifications.engine import Notification
        notif = Notification(
            notification_id='n1',
            recipient_id='user1',
            template_id='welcome',
            subject='Welcome',
            body='Welcome',
            status=NotificationStatus.PENDING,
            channels=['email']
        )
        self.store.store(notif)
        retrieved = self.store.get_notification('n1')
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.recipient_id, 'user1')


class TestChannelManager(unittest.TestCase):
    def setUp(self):
        self.manager = ChannelManager()
    
    def test_email_channel(self):
        result = self.manager.email.send('user@example.com', 'Subject', 'Body')
        self.assertTrue(result.success)
    
    def test_sms_channel(self):
        result = self.manager.sms.send('+1234567890', 'Body')
        self.assertTrue(result.success)
    
    def test_push_channel(self):
        result = self.manager.push.send('device_token_123', 'Title', 'Body')
        self.assertTrue(result.success)
    
    def test_in_app_channel(self):
        result = self.manager.in_app.send('user1', 'Title', 'Body')
        self.assertTrue(result.success)
    
    def test_multi_channel(self):
        results = self.manager.send_multi_channel(
            recipient_id='user1',
            channels=['email', 'in_app'],
            subject='Subject',
            body='Body',
            recipient_email='user@example.com'
        )
        self.assertEqual(len(results), 2)


class TestNotificationQueue(unittest.TestCase):
    def setUp(self):
        self.queue = NotificationQueue()
    
    def test_enqueue(self):
        notif = QueuedNotification(
            notification_id='n1',
            recipient_id='user1',
            priority=5,
            created_at=datetime.utcnow()
        )
        result = self.queue.enqueue(notif)
        self.assertTrue(result)
    
    def test_dequeue(self):
        notif = QueuedNotification(
            notification_id='n1',
            recipient_id='user1',
            priority=5,
            created_at=datetime.utcnow()
        )
        self.queue.enqueue(notif)
        dequeued = self.queue.dequeue()
        self.assertIsNotNone(dequeued)
        self.assertEqual(dequeued.notification_id, 'n1')
    
    def test_priority_ordering(self):
        low = QueuedNotification(
            notification_id='low',
            recipient_id='u1',
            priority=1,
            created_at=datetime.utcnow()
        )
        high = QueuedNotification(
            notification_id='high',
            recipient_id='u2',
            priority=10,
            created_at=datetime.utcnow()
        )
        self.queue.enqueue(low)
        self.queue.enqueue(high)
        
        first = self.queue.dequeue()
        self.assertEqual(first.notification_id, 'high')
    
    def test_batch_process(self):
        for i in range(5):
            notif = QueuedNotification(
                notification_id=f'n{i}',
                recipient_id=f'u{i}',
                priority=5,
                created_at=datetime.utcnow()
            )
            self.queue.enqueue(notif)
        
        batch = self.queue.process_batch(3)
        self.assertEqual(len(batch), 3)


class TestBatchProcessor(unittest.TestCase):
    def test_process_batch(self):
        processor = BatchProcessor(batch_size=10)
        notifications = [
            QueuedNotification(
                notification_id=f'n{i}',
                recipient_id=f'u{i}',
                priority=5,
                created_at=datetime.utcnow()
            )
            for i in range(5)
        ]
        result = processor.process(notifications)
        self.assertGreater(result['processed'], 0)


class TestRulesEngine(unittest.TestCase):
    def setUp(self):
        self.engine = RulesEngine()
    
    def test_register_rule(self):
        rule = Rule(
            rule_id='r1',
            name='Welcome Rule',
            trigger=TriggerType.USER_SIGNUP,
            template_id='welcome',
            channels=['email']
        )
        result = self.engine.register_rule(rule)
        self.assertTrue(result)
    
    def test_get_rules_for_trigger(self):
        rule = Rule(
            rule_id='r1',
            name='Welcome Rule',
            trigger=TriggerType.USER_SIGNUP,
            template_id='welcome',
            channels=['email']
        )
        self.engine.register_rule(rule)
        rules = self.engine.get_rules_for_trigger(TriggerType.USER_SIGNUP)
        self.assertEqual(len(rules), 1)
    
    def test_execute_trigger(self):
        rule = Rule(
            rule_id='r1',
            name='Welcome Rule',
            trigger=TriggerType.USER_SIGNUP,
            template_id='welcome',
            channels=['email']
        )
        self.engine.register_rule(rule)
        notif_ids = self.engine.execute_trigger(TriggerType.USER_SIGNUP, {})
        self.assertGreater(len(notif_ids), 0)


class TestEventListener(unittest.TestCase):
    def setUp(self):
        self.rules_engine = RulesEngine()
        self.listener = EventListener(self.rules_engine)
    
    def test_emit_event(self):
        rule = Rule(
            rule_id='r1',
            name='Alert Rule',
            trigger=TriggerType.ALERT,
            template_id='alert',
            channels=['email']
        )
        self.rules_engine.register_rule(rule)
        
        notif_ids = self.listener.emit(TriggerType.ALERT, {})
        self.assertGreater(len(notif_ids), 0)


class TestNotificationEngine(unittest.TestCase):
    def setUp(self):
        self.engine = NotificationEngine()
        template = NotificationTemplate(
            template_id='welcome',
            name='Welcome',
            subject='Welcome {name}',
            body='Welcome {name}',
            notification_type=NotificationType.WELCOME,
            variables=['name']
        )
        self.engine.template_engine.register_template(template)
    
    def test_create_notification(self):
        notif_id = self.engine.create_notification(
            recipient_id='user1',
            template_id='welcome',
            variables={'name': 'Alice'},
            channels=['email']
        )
        self.assertIsNotNone(notif_id)
    
    def test_send_notification(self):
        notif_id = self.engine.create_notification(
            recipient_id='user1',
            template_id='welcome',
            variables={'name': 'Alice'},
            channels=['email']
        )
        result = self.engine.send_notification(notif_id)
        self.assertTrue(result)


class TestDashboard(unittest.TestCase):
    def test_dashboard_generation(self):
        metrics = {
            'total': 1000,
            'delivered': 950,
            'failed': 50,
            'queue_size': 100,
            'enabled_rules': 25,
            'success_rate': 95.0
        }
        html = generate_notification_dashboard(metrics)
        self.assertIn('Notification System', html)
        self.assertIn('1,000', html)
        self.assertIn('95.0', html)


if __name__ == '__main__':
    unittest.main()
