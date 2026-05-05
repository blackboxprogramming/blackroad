"""Multi-channel notification delivery."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ChannelType(Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


@dataclass
class ChannelResult:
    """Result of channel delivery attempt."""
    channel: ChannelType
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class EmailChannel:
    """Email delivery channel."""
    
    def __init__(self, provider: str = "sendgrid"):
        self.provider = provider
        self.sent_count = 0
        self.failed_count = 0
    
    def send(self, recipient: str, subject: str, body: str) -> ChannelResult:
        """Send email."""
        if not recipient or '@' not in recipient:
            self.failed_count += 1
            return ChannelResult(
                channel=ChannelType.EMAIL,
                success=False,
                error="Invalid email address"
            )
        
        # Simulate sending
        message_id = f"email_{self.sent_count}_{int(datetime.utcnow().timestamp())}"
        self.sent_count += 1
        
        return ChannelResult(
            channel=ChannelType.EMAIL,
            success=True,
            message_id=message_id
        )


class SMSChannel:
    """SMS delivery channel."""
    
    def __init__(self, provider: str = "twilio"):
        self.provider = provider
        self.sent_count = 0
        self.failed_count = 0
    
    def send(self, recipient: str, body: str) -> ChannelResult:
        """Send SMS."""
        # Validate phone (simplified)
        if not recipient or len(recipient) < 10:
            self.failed_count += 1
            return ChannelResult(
                channel=ChannelType.SMS,
                success=False,
                error="Invalid phone number"
            )
        
        # Limit body length (SMS constraint)
        if len(body) > 160:
            body = body[:157] + "..."
        
        message_id = f"sms_{self.sent_count}_{int(datetime.utcnow().timestamp())}"
        self.sent_count += 1
        
        return ChannelResult(
            channel=ChannelType.SMS,
            success=True,
            message_id=message_id
        )


class PushChannel:
    """Push notification delivery channel."""
    
    def __init__(self, provider: str = "firebase"):
        self.provider = provider
        self.sent_count = 0
        self.failed_count = 0
    
    def send(self, device_token: str, title: str, body: str) -> ChannelResult:
        """Send push notification."""
        if not device_token:
            self.failed_count += 1
            return ChannelResult(
                channel=ChannelType.PUSH,
                success=False,
                error="No device token"
            )
        
        message_id = f"push_{self.sent_count}_{int(datetime.utcnow().timestamp())}"
        self.sent_count += 1
        
        return ChannelResult(
            channel=ChannelType.PUSH,
            success=True,
            message_id=message_id
        )


class InAppChannel:
    """In-app notification channel."""
    
    def __init__(self):
        self.notifications: List[Dict[str, Any]] = []
        self.sent_count = 0
    
    def send(self, recipient_id: str, title: str, body: str, data: Dict[str, Any] = None) -> ChannelResult:
        """Store in-app notification."""
        self.notifications.append({
            'recipient_id': recipient_id,
            'title': title,
            'body': body,
            'data': data or {},
            'timestamp': datetime.utcnow().isoformat(),
        })
        
        message_id = f"inapp_{self.sent_count}"
        self.sent_count += 1
        
        return ChannelResult(
            channel=ChannelType.IN_APP,
            success=True,
            message_id=message_id
        )


class ChannelManager:
    """Manages multi-channel delivery."""
    
    def __init__(self):
        self.email = EmailChannel()
        self.sms = SMSChannel()
        self.push = PushChannel()
        self.in_app = InAppChannel()
        self.delivery_log: List[ChannelResult] = []
    
    def send_multi_channel(
        self,
        recipient_id: str,
        channels: List[str],
        subject: str,
        body: str,
        recipient_email: str = None,
        recipient_phone: str = None,
        device_token: str = None,
    ) -> Dict[str, ChannelResult]:
        """Send through multiple channels."""
        results = {}
        
        for channel in channels:
            if channel == 'email' and recipient_email:
                result = self.email.send(recipient_email, subject, body)
                results['email'] = result
                self.delivery_log.append(result)
            
            elif channel == 'sms' and recipient_phone:
                result = self.sms.send(recipient_phone, body)
                results['sms'] = result
                self.delivery_log.append(result)
            
            elif channel == 'push' and device_token:
                result = self.push.send(device_token, subject, body)
                results['push'] = result
                self.delivery_log.append(result)
            
            elif channel == 'in_app':
                result = self.in_app.send(recipient_id, subject, body)
                results['in_app'] = result
                self.delivery_log.append(result)
        
        return results
    
    def get_channel_stats(self) -> Dict[str, Dict[str, int]]:
        """Get statistics per channel."""
        return {
            'email': {'sent': self.email.sent_count, 'failed': self.email.failed_count},
            'sms': {'sent': self.sms.sent_count, 'failed': self.sms.failed_count},
            'push': {'sent': self.push.sent_count, 'failed': self.push.failed_count},
            'in_app': {'sent': self.in_app.sent_count},
        }
