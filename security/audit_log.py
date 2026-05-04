"""
Security Audit Logging - Track all security-relevant events
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum


class AuditEventType(Enum):
    """Types of security audit events."""
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGIN_BRUTEFORCE = "LOGIN_BRUTEFORCE"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    SENSITIVE_DATA_ACCESS = "SENSITIVE_DATA_ACCESS"
    ADMIN_ACTION = "ADMIN_ACTION"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    API_KEY_CREATED = "API_KEY_CREATED"
    API_KEY_REVOKED = "API_KEY_REVOKED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    MALICIOUS_PAYLOAD = "MALICIOUS_PAYLOAD"
    SECURITY_HEADER_MISSING = "SECURITY_HEADER_MISSING"
    CERTIFICATE_EXPIRY = "CERTIFICATE_EXPIRY"
    BACKUP_FAILED = "BACKUP_FAILED"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    DATA_EXPORT = "DATA_EXPORT"


class SecurityAuditLog:
    """Centralized security audit logging."""
    
    def __init__(self, db_connection=None, elasticsearch_client=None):
        self.db = db_connection
        self.es = elasticsearch_client
        self.memory_buffer = []
        self.alert_rules = self._init_alert_rules()
    
    def log_event(self, event_type: AuditEventType, user_id: str, 
                  ip_address: str, details: Dict,
                  severity: str = 'INFO') -> str:
        """
        Log a security event.
        
        Args:
            event_type: Type of security event
            user_id: User who triggered event
            ip_address: Client IP address
            details: Event-specific details
            severity: INFO, WARNING, CRITICAL
        
        Returns:
            Event ID
        """
        event_id = self._generate_event_id()
        timestamp = datetime.utcnow().isoformat()
        
        event = {
            'event_id': event_id,
            'event_type': event_type.value,
            'user_id': user_id,
            'ip_address': ip_address,
            'timestamp': timestamp,
            'severity': severity,
            'details': details,
            'environment': 'production',  # Can be parameterized
        }
        
        # Store in memory buffer
        self.memory_buffer.append(event)
        
        # Store in database if available
        if self.db:
            self._store_in_db(event)
        
        # Index in Elasticsearch for fast search
        if self.es:
            self._index_in_elasticsearch(event)
        
        # Check alert rules
        if self._should_alert(event):
            self._trigger_alert(event)
        
        return event_id
    
    def _init_alert_rules(self) -> List[Dict]:
        """Initialize alerting rules."""
        return [
            {
                'name': 'Brute Force Attack',
                'trigger': 'LOGIN_FAILED',
                'threshold': 5,
                'window': 300,  # 5 minutes
                'severity': 'CRITICAL'
            },
            {
                'name': 'Unauthorized Access Attempt',
                'trigger': 'UNAUTHORIZED_ACCESS',
                'threshold': 3,
                'window': 60,
                'severity': 'HIGH'
            },
            {
                'name': 'Rate Limit Exceeded',
                'trigger': 'RATE_LIMIT_EXCEEDED',
                'threshold': 10,
                'window': 300,
                'severity': 'MEDIUM'
            },
            {
                'name': 'Malicious Payload Detected',
                'trigger': 'MALICIOUS_PAYLOAD',
                'threshold': 1,
                'window': 3600,
                'severity': 'CRITICAL'
            },
            {
                'name': 'Privilege Escalation Attempt',
                'trigger': 'PRIVILEGE_ESCALATION',
                'threshold': 1,
                'window': 3600,
                'severity': 'CRITICAL'
            }
        ]
    
    def _should_alert(self, event: Dict) -> bool:
        """Check if event should trigger alert."""
        for rule in self.alert_rules:
            if rule['trigger'] == event['event_type']:
                if event['severity'] == rule['severity']:
                    return True
        return False
    
    def _trigger_alert(self, event: Dict) -> None:
        """Trigger security alert (send notifications, etc)."""
        # Would integrate with alerting system
        alert = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_id': event['event_id'],
            'message': f"Security Alert: {event['event_type']} from {event['ip_address']}",
            'severity': event['severity']
        }
        # Send to Slack, PagerDuty, etc.
        print(f"[ALERT] {alert['message']}")
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        import hashlib
        import time
        data = f"{time.time()}{len(self.memory_buffer)}".encode()
        return hashlib.sha256(data).hexdigest()[:16]
    
    def _store_in_db(self, event: Dict) -> bool:
        """Store event in database."""
        try:
            # SQL: INSERT INTO security_audit_log (...)
            # This is pseudo-code
            sql = """
            INSERT INTO security_audit_log 
            (event_id, event_type, user_id, ip_address, timestamp, severity, details)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            # self.db.execute(sql, (event['event_id'], ...))
            return True
        except Exception as e:
            print(f"Failed to store audit log: {e}")
            return False
    
    def _index_in_elasticsearch(self, event: Dict) -> bool:
        """Index event in Elasticsearch."""
        try:
            index_name = f"security_audit_{datetime.now().strftime('%Y.%m.%d')}"
            # self.es.index(index=index_name, doc_type='_doc', body=event)
            return True
        except Exception as e:
            print(f"Failed to index audit log: {e}")
            return False
    
    def get_events_for_user(self, user_id: str, 
                          limit: int = 100) -> List[Dict]:
        """Get all security events for user."""
        if self.db:
            # Query from database
            pass
        
        # Query from memory buffer (for demo)
        return [e for e in self.memory_buffer if e['user_id'] == user_id][-limit:]
    
    def get_events_by_ip(self, ip_address: str, 
                        limit: int = 100) -> List[Dict]:
        """Get all security events from IP address."""
        return [e for e in self.memory_buffer 
                if e['ip_address'] == ip_address][-limit:]
    
    def get_failed_logins(self, hours: int = 24) -> List[Dict]:
        """Get failed login attempts in last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [e for e in self.memory_buffer 
                if e['event_type'] == 'LOGIN_FAILED' 
                and datetime.fromisoformat(e['timestamp']) > cutoff]
    
    def detect_brute_force(self, ip_address: str, 
                          failed_login_threshold: int = 5) -> Dict:
        """Detect brute force attacks from IP."""
        failed_logins = [e for e in self.get_events_by_ip(ip_address) 
                        if e['event_type'] == 'LOGIN_FAILED']
        
        # Check if multiple failures in short time
        recent = [e for e in failed_logins 
                 if (datetime.utcnow() - datetime.fromisoformat(e['timestamp'])).seconds < 300]
        
        return {
            'ip_address': ip_address,
            'total_failed_logins': len(failed_logins),
            'recent_failures': len(recent),
            'is_brute_force': len(recent) >= failed_login_threshold,
            'recommended_action': 'BLOCK_IP' if len(recent) >= failed_login_threshold else 'MONITOR'
        }
    
    def get_audit_report(self, start_date: datetime, 
                        end_date: datetime) -> Dict:
        """Generate audit report for date range."""
        events_in_range = [e for e in self.memory_buffer 
                          if start_date <= datetime.fromisoformat(e['timestamp']) <= end_date]
        
        # Aggregate statistics
        event_types = {}
        severity_counts = {'INFO': 0, 'WARNING': 0, 'CRITICAL': 0}
        
        for event in events_in_range:
            event_type = event['event_type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
            severity_counts[event['severity']] += 1
        
        return {
            'report_period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_events': len(events_in_range),
            'event_types': event_types,
            'severity_breakdown': severity_counts,
            'unique_users': len(set(e['user_id'] for e in events_in_range)),
            'unique_ips': len(set(e['ip_address'] for e in events_in_range)),
        }
