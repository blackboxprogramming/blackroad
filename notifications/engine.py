"""Notification engine with templates and tracking."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import uuid


class NotificationType(Enum):
    """Notification types."""
    WELCOME = "welcome"
    ORDER_CONFIRMATION = "order_confirmation"
    PAYMENT_REMINDER = "payment_reminder"
    PROMOTIONAL = "promotional"
    ALERT = "alert"
    SYSTEM = "system"


class NotificationStatus(Enum):
    """Notification delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


@dataclass
class NotificationTemplate:
    """Notification template."""
    template_id: str
    name: str
    subject: str
    body: str
    notification_type: NotificationType
    variables: List[str]  # template variables like {user_name}, {order_id}
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class Notification:
    """A notification instance."""
    notification_id: str
    recipient_id: str
    template_id: str
    subject: str
    body: str
    status: NotificationStatus
    channels: List[str]  # email, sms, push, in_app
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None


class TemplateEngine:
    """Manages notification templates."""
    
    def __init__(self):
        self.templates: Dict[str, NotificationTemplate] = {}
    
    def register_template(self, template: NotificationTemplate) -> bool:
        """Register a notification template."""
        self.templates[template.template_id] = template
        return True
    
    def get_template(self, template_id: str) -> Optional[NotificationTemplate]:
        """Get template by ID."""
        return self.templates.get(template_id)
    
    def render(self, template_id: str, variables: Dict[str, str]) -> Dict[str, str]:
        """Render template with variables."""
        template = self.templates.get(template_id)
        if not template:
            return {}
        
        subject = template.subject
        body = template.body
        
        # Replace variables
        for key, value in variables.items():
            subject = subject.replace(f"{{{key}}}", str(value))
            body = body.replace(f"{{{key}}}", str(value))
        
        return {'subject': subject, 'body': body}
    
    def list_templates(self, notification_type: NotificationType = None) -> List[NotificationTemplate]:
        """List templates."""
        templates = list(self.templates.values())
        if notification_type:
            templates = [t for t in templates if t.notification_type == notification_type]
        return templates


class NotificationStore:
    """Stores notification history."""
    
    def __init__(self, max_history: int = 10000):
        self.notifications: Dict[str, Notification] = {}
        self.max_history = max_history
        self.stats = {
            'total_sent': 0,
            'total_delivered': 0,
            'total_failed': 0,
        }
    
    def store(self, notification: Notification) -> bool:
        """Store notification."""
        self.notifications[notification.notification_id] = notification
        
        # Trim history if needed
        if len(self.notifications) > self.max_history:
            oldest_id = min(self.notifications.keys(), 
                           key=lambda k: self.notifications[k].sent_at or datetime.utcnow())
            del self.notifications[oldest_id]
        
        return True
    
    def get_notification(self, notification_id: str) -> Optional[Notification]:
        """Get notification by ID."""
        return self.notifications.get(notification_id)
    
    def get_user_notifications(self, recipient_id: str, limit: int = 50) -> List[Notification]:
        """Get notifications for user."""
        user_notifications = [
            n for n in self.notifications.values()
            if n.recipient_id == recipient_id
        ]
        return sorted(user_notifications, 
                     key=lambda n: n.sent_at or datetime.utcnow(), 
                     reverse=True)[:limit]
    
    def mark_delivered(self, notification_id: str) -> bool:
        """Mark notification as delivered."""
        if notification_id in self.notifications:
            notif = self.notifications[notification_id]
            notif.status = NotificationStatus.DELIVERED
            notif.delivered_at = datetime.utcnow()
            self.stats['total_delivered'] += 1
            return True
        return False
    
    def mark_read(self, notification_id: str) -> bool:
        """Mark notification as read."""
        if notification_id in self.notifications:
            self.notifications[notification_id].read_at = datetime.utcnow()
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get notification statistics."""
        total = len(self.notifications)
        pending = sum(1 for n in self.notifications.values() if n.status == NotificationStatus.PENDING)
        sent = sum(1 for n in self.notifications.values() if n.status == NotificationStatus.SENT)
        delivered = sum(1 for n in self.notifications.values() if n.status == NotificationStatus.DELIVERED)
        failed = sum(1 for n in self.notifications.values() if n.status == NotificationStatus.FAILED)
        
        return {
            'total': total,
            'pending': pending,
            'sent': sent,
            'delivered': delivered,
            'failed': failed,
            'success_rate': (delivered / max(sent, 1) * 100) if sent > 0 else 0,
        }


class NotificationEngine:
    """Main notification engine."""
    
    def __init__(self):
        self.template_engine = TemplateEngine()
        self.store = NotificationStore()
        self.sent_count = 0
    
    def create_notification(
        self,
        recipient_id: str,
        template_id: str,
        variables: Dict[str, str],
        channels: List[str],
    ) -> Optional[str]:
        """Create and queue notification."""
        # Render template
        rendered = self.template_engine.render(template_id, variables)
        if not rendered:
            return None
        
        # Create notification
        notification_id = str(uuid.uuid4())
        notification = Notification(
            notification_id=notification_id,
            recipient_id=recipient_id,
            template_id=template_id,
            subject=rendered['subject'],
            body=rendered['body'],
            status=NotificationStatus.PENDING,
            channels=channels,
            metadata={'variables': variables}
        )
        
        # Store
        self.store.store(notification)
        return notification_id
    
    def send_notification(self, notification_id: str) -> bool:
        """Send notification through channels."""
        notif = self.store.get_notification(notification_id)
        if not notif:
            return False
        
        notif.status = NotificationStatus.SENT
        notif.sent_at = datetime.utcnow()
        self.sent_count += 1
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get engine metrics."""
        return {
            'sent_count': self.sent_count,
            **self.store.get_stats()
        }
