"""Immutable audit logging system for compliance and tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Set
import hashlib
import json
from collections import defaultdict


class ActionType(Enum):
    """Type of action being audited."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    AUTHENTICATE = "authenticate"
    AUTHORIZE = "authorize"
    PAYMENT = "payment"
    EXPORT = "export"
    IMPORT = "import"
    MODIFY = "modify"
    ENABLE = "enable"
    DISABLE = "disable"


class ResourceType(Enum):
    """Type of resource being audited."""
    USER = "user"
    ACCOUNT = "account"
    PAYMENT = "payment"
    DOCUMENT = "document"
    CONFIG = "config"
    API_KEY = "api_key"
    ROLE = "role"
    PERMISSION = "permission"
    ORGANIZATION = "organization"
    DATA = "data"


@dataclass
class AuditEntry:
    """Single immutable audit log entry."""
    entry_id: str
    timestamp: datetime
    user_id: str
    action: ActionType
    resource_type: ResourceType
    resource_id: str
    changes: Dict[str, Any]  # before/after values
    status: str = "success"  # success or failure
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    hash_value: Optional[str] = None  # For tamper detection

    def calculate_hash(self) -> str:
        """Calculate SHA256 hash of entry for tamper detection."""
        entry_data = {
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'action': self.action.value,
            'resource_type': self.resource_type.value,
            'resource_id': self.resource_id,
            'changes': json.dumps(self.changes, sort_keys=True),
            'status': self.status
        }
        entry_json = json.dumps(entry_data, sort_keys=True)
        return hashlib.sha256(entry_json.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'entry_id': self.entry_id,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'action': self.action.value,
            'resource_type': self.resource_type.value,
            'resource_id': self.resource_id,
            'changes': self.changes,
            'status': self.status,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'details': self.details,
            'hash_value': self.hash_value
        }


class AuditLogger:
    """Central audit logging system."""

    def __init__(self, max_entries: int = 1000000):
        self.max_entries = max_entries
        self.entries: List[AuditEntry] = []
        self.entry_map: Dict[str, AuditEntry] = {}  # entry_id -> entry
        self.user_activities: Dict[str, List[str]] = defaultdict(list)  # user_id -> entry_ids
        self.resource_activities: Dict[str, List[str]] = defaultdict(list)  # resource_id -> entry_ids
        self.metrics = {
            'total_entries': 0,
            'entries_by_action': defaultdict(int),
            'entries_by_resource': defaultdict(int),
            'successful_actions': 0,
            'failed_actions': 0,
        }

    def log(
        self,
        user_id: str,
        action: ActionType,
        resource_type: ResourceType,
        resource_id: str,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEntry:
        """Log an action (immutable)."""
        if len(self.entries) >= self.max_entries:
            raise RuntimeError(f"Audit log capacity ({self.max_entries}) reached")

        timestamp = datetime.utcnow()

        # Generate entry ID
        entry_id = hashlib.md5(
            f"{user_id}:{resource_id}:{timestamp.isoformat()}".encode()
        ).hexdigest()[:16]

        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=timestamp,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes or {},
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {}
        )

        # Calculate hash for tamper detection
        entry.hash_value = entry.calculate_hash()

        # Append to immutable log
        self.entries.append(entry)
        self.entry_map[entry_id] = entry

        # Index by user and resource
        self.user_activities[user_id].append(entry_id)
        self.resource_activities[resource_id].append(entry_id)

        # Update metrics
        self.metrics['total_entries'] += 1
        self.metrics['entries_by_action'][action.value] += 1
        self.metrics['entries_by_resource'][resource_type.value] += 1

        if status == "success":
            self.metrics['successful_actions'] += 1
        else:
            self.metrics['failed_actions'] += 1

        return entry

    def get_entry(self, entry_id: str) -> Optional[AuditEntry]:
        """Get audit entry by ID."""
        return self.entry_map.get(entry_id)

    def verify_integrity(self, entry_id: str) -> bool:
        """Verify entry hasn't been tampered with."""
        entry = self.entry_map.get(entry_id)
        if not entry:
            return False

        if not entry.hash_value:
            return False

        # Recalculate hash
        current_hash = entry.calculate_hash()
        return current_hash == entry.hash_value

    def get_user_activity(self, user_id: str, limit: int = 100) -> List[AuditEntry]:
        """Get all activities by user."""
        entry_ids = self.user_activities.get(user_id, [])
        # Return most recent first
        return [self.entry_map[eid] for eid in entry_ids[-limit:]][::-1]

    def get_resource_activity(self, resource_id: str, limit: int = 100) -> List[AuditEntry]:
        """Get all activities on resource."""
        entry_ids = self.resource_activities.get(resource_id, [])
        # Return most recent first
        return [self.entry_map[eid] for eid in entry_ids[-limit:]][::-1]

    def get_entries_by_action(self, action: ActionType, limit: int = 100) -> List[AuditEntry]:
        """Get entries by action type."""
        matching = [e for e in self.entries if e.action == action]
        return matching[-limit:][::-1]

    def get_entries_by_resource_type(self, resource_type: ResourceType, limit: int = 100) -> List[AuditEntry]:
        """Get entries by resource type."""
        matching = [e for e in self.entries if e.resource_type == resource_type]
        return matching[-limit:][::-1]

    def get_entries_by_user_and_action(
        self, user_id: str, action: ActionType, limit: int = 100
    ) -> List[AuditEntry]:
        """Get entries for specific user and action."""
        entry_ids = self.user_activities.get(user_id, [])
        matching = [self.entry_map[eid] for eid in entry_ids if self.entry_map[eid].action == action]
        return matching[-limit:][::-1]

    def get_failed_actions(self, limit: int = 100) -> List[AuditEntry]:
        """Get all failed actions."""
        matching = [e for e in self.entries if e.status != "success"]
        return matching[-limit:][::-1]

    def get_recent_entries(self, limit: int = 100) -> List[AuditEntry]:
        """Get most recent entries."""
        return self.entries[-limit:][::-1]

    def search_entries(
        self,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[ActionType] = None,
        resource_type: Optional[ResourceType] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Search audit entries by criteria."""
        results = self.entries

        if user_id:
            entry_ids = self.user_activities.get(user_id, [])
            results = [self.entry_map[eid] for eid in entry_ids]

        results = [e for e in results if resource_id is None or e.resource_id == resource_id]
        results = [e for e in results if action is None or e.action == action]
        results = [e for e in results if resource_type is None or e.resource_type == resource_type]
        results = [e for e in results if status is None or e.status == status]

        return results[-limit:][::-1]

    def get_stats(self) -> Dict[str, Any]:
        """Get audit logging statistics."""
        return {
            'total_entries': self.metrics['total_entries'],
            'successful_actions': self.metrics['successful_actions'],
            'failed_actions': self.metrics['failed_actions'],
            'success_rate': (
                self.metrics['successful_actions'] / self.metrics['total_entries'] * 100
                if self.metrics['total_entries'] > 0 else 0
            ),
            'entries_by_action': dict(self.metrics['entries_by_action']),
            'entries_by_resource': dict(self.metrics['entries_by_resource']),
            'unique_users': len(self.user_activities),
            'unique_resources': len(self.resource_activities),
            'capacity_percent': (len(self.entries) / self.max_entries * 100)
        }

    def export_entries(
        self, user_id: Optional[str] = None, start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Export entries for compliance."""
        results = self.entries

        if user_id:
            entry_ids = self.user_activities.get(user_id, [])
            results = [self.entry_map[eid] for eid in entry_ids]

        if start_date:
            results = [e for e in results if e.timestamp >= start_date]

        if end_date:
            results = [e for e in results if e.timestamp <= end_date]

        return [e.to_dict() for e in results]

    def get_retention_period_entries(self, days: int) -> List[AuditEntry]:
        """Get entries older than retention period (for cleanup)."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [e for e in self.entries if e.timestamp < cutoff]


from datetime import timedelta
