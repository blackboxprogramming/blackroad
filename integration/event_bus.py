"""
Cross-System Event Bus
Event-driven architecture connecting all 7 enterprise systems
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime
from enum import Enum
import json


class EventType(Enum):
    """System events that trigger cross-system workflows."""
    # Security Events
    SECURITY_ALERT = "security.alert"
    SECURITY_INCIDENT = "security.incident"
    VULNERABILITY_DETECTED = "security.vulnerability"
    
    # Deployment Events
    DEPLOYMENT_STARTED = "deployment.started"
    DEPLOYMENT_COMPLETED = "deployment.completed"
    DEPLOYMENT_FAILED = "deployment.failed"
    
    # API Events
    API_REQUEST = "api.request"
    API_ERROR = "api.error"
    API_RATE_LIMIT = "api.rate_limit"
    
    # Developer Events
    SDK_GENERATED = "developer.sdk_generated"
    API_KEY_CREATED = "developer.api_key_created"
    API_KEY_REVOKED = "developer.api_key_revoked"
    
    # Monitoring Events
    ALERT_TRIGGERED = "monitoring.alert_triggered"
    METRIC_ANOMALY = "monitoring.metric_anomaly"
    TRACE_ERROR = "monitoring.trace_error"
    
    # ML Events
    MODEL_TRAINED = "ml.model_trained"
    PREDICTION_MADE = "ml.prediction_made"
    ANOMALY_DETECTED = "ml.anomaly_detected"
    
    # Compliance Events
    CONTROL_FAILED = "compliance.control_failed"
    AUDIT_LOG_ENTRY = "compliance.audit_log_entry"
    RISK_ESCALATED = "compliance.risk_escalated"


class EventPriority(Enum):
    """Event priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class Event:
    """Unified event structure."""
    
    def __init__(self, event_type: EventType, source_system: str,
                 data: Dict, priority: EventPriority = EventPriority.NORMAL,
                 correlation_id: Optional[str] = None):
        self.id = f"event_{int(datetime.utcnow().timestamp() * 1000)}"
        self.type = event_type
        self.source_system = source_system
        self.data = data
        self.priority = priority
        self.correlation_id = correlation_id or self.id
        self.timestamp = datetime.utcnow().isoformat()
        self.processed = False
        self.handlers_called: List[str] = []
    
    def to_dict(self) -> Dict:
        """Export event."""
        return {
            'id': self.id,
            'type': self.type.value,
            'source_system': self.source_system,
            'data': self.data,
            'priority': self.priority.value,
            'correlation_id': self.correlation_id,
            'timestamp': self.timestamp,
            'processed': self.processed,
            'handlers_called': self.handlers_called,
        }


class EventBus:
    """Central event bus for cross-system communication."""
    
    def __init__(self):
        self.handlers: Dict[EventType, List[Callable]] = {}
        self.event_history: List[Event] = []
        self.subscriptions: Dict[str, List[EventType]] = {}
    
    def subscribe(self, event_type: EventType, handler: Callable,
                 system_id: Optional[str] = None) -> str:
        """Subscribe to event type."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        
        if system_id:
            if system_id not in self.subscriptions:
                self.subscriptions[system_id] = []
            self.subscriptions[system_id].append(event_type)
        
        return f"subscription_{event_type.value}_{len(self.handlers[event_type])}"
    
    def unsubscribe(self, event_type: EventType, handler: Callable) -> bool:
        """Unsubscribe from event type."""
        if event_type in self.handlers:
            try:
                self.handlers[event_type].remove(handler)
                return True
            except ValueError:
                return False
        return False
    
    def publish(self, event: Event) -> Dict:
        """Publish event to all subscribers."""
        self.event_history.append(event)
        
        results = {
            'event_id': event.id,
            'type': event.type.value,
            'handlers_executed': 0,
            'handlers_failed': 0,
            'handlers': [],
        }
        
        if event.type in self.handlers:
            for handler in self.handlers[event.type]:
                try:
                    handler(event)
                    event.handlers_called.append(handler.__name__)
                    results['handlers_executed'] += 1
                    results['handlers'].append({
                        'name': handler.__name__,
                        'status': 'success',
                    })
                except Exception as e:
                    results['handlers_failed'] += 1
                    results['handlers'].append({
                        'name': handler.__name__,
                        'status': 'failed',
                        'error': str(e),
                    })
        
        event.processed = True
        return results
    
    def get_event_history(self, event_type: Optional[EventType] = None,
                         source_system: Optional[str] = None,
                         limit: int = 100) -> List[Dict]:
        """Get event history."""
        history = self.event_history
        
        if event_type:
            history = [e for e in history if e.type == event_type]
        
        if source_system:
            history = [e for e in history if e.source_system == source_system]
        
        return [e.to_dict() for e in history[-limit:]]
    
    def get_correlation_chain(self, correlation_id: str) -> List[Dict]:
        """Get all events in a correlation chain."""
        chain = [e for e in self.event_history if e.correlation_id == correlation_id]
        return [e.to_dict() for e in chain]


class EventAggregator:
    """Aggregate events for cross-system dashboards."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.aggregations: Dict[str, Dict] = {}
    
    def aggregate_by_system(self) -> Dict[str, Dict]:
        """Aggregate events by source system."""
        aggregation = {}
        
        for event in self.event_bus.event_history:
            system = event.source_system
            if system not in aggregation:
                aggregation[system] = {
                    'total_events': 0,
                    'critical_events': 0,
                    'high_events': 0,
                    'last_event': None,
                }
            
            aggregation[system]['total_events'] += 1
            
            if event.priority == EventPriority.CRITICAL:
                aggregation[system]['critical_events'] += 1
            elif event.priority == EventPriority.HIGH:
                aggregation[system]['high_events'] += 1
            
            aggregation[system]['last_event'] = event.timestamp
        
        return aggregation
    
    def aggregate_by_type(self) -> Dict[str, int]:
        """Count events by type."""
        counts = {}
        for event in self.event_bus.event_history:
            event_type = event.type.value
            counts[event_type] = counts.get(event_type, 0) + 1
        
        return counts
    
    def get_critical_events(self, hours: int = 24) -> List[Dict]:
        """Get critical events from last N hours."""
        cutoff = datetime.utcnow().isoformat()
        critical = [
            e for e in self.event_bus.event_history
            if e.priority == EventPriority.CRITICAL
        ]
        
        return [e.to_dict() for e in critical]
    
    def get_system_health(self) -> Dict:
        """Calculate overall system health."""
        by_system = self.aggregate_by_system()
        
        health = {
            'overall_health': 100,
            'systems': {},
        }
        
        for system, stats in by_system.items():
            system_health = 100
            
            # Deduct points for critical events
            system_health -= stats['critical_events'] * 5
            
            # Deduct points for high events
            system_health -= stats['high_events'] * 2
            
            system_health = max(0, min(100, system_health))
            
            health['systems'][system] = {
                'health_score': system_health,
                'events': stats['total_events'],
                'critical': stats['critical_events'],
                'high': stats['high_events'],
            }
            
            # Update overall health (worst system drags down total)
            health['overall_health'] = min(health['overall_health'], system_health)
        
        return health


class CrossSystemWorkflow:
    """Define workflows triggered by events."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.workflows: Dict[str, Dict] = {}
    
    def register_workflow(self, workflow_id: str, trigger_event: EventType,
                         actions: List[Callable]) -> str:
        """Register event-triggered workflow."""
        self.workflows[workflow_id] = {
            'id': workflow_id,
            'trigger_event': trigger_event,
            'actions': actions,
            'created_at': datetime.utcnow().isoformat(),
            'executions': 0,
        }
        
        # Subscribe to trigger event
        def execute_workflow(event: Event):
            self._execute_workflow(workflow_id, event)
        
        self.event_bus.subscribe(trigger_event, execute_workflow)
        
        return workflow_id
    
    def _execute_workflow(self, workflow_id: str, event: Event) -> Dict:
        """Execute workflow actions."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {'error': 'Workflow not found'}
        
        results = {
            'workflow_id': workflow_id,
            'trigger_event': event.id,
            'actions_executed': 0,
            'actions_failed': 0,
            'execution_time': datetime.utcnow().isoformat(),
        }
        
        for action in workflow['actions']:
            try:
                action(event)
                results['actions_executed'] += 1
            except Exception as e:
                results['actions_failed'] += 1
        
        workflow['executions'] += 1
        
        return results
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get workflow status."""
        return self.workflows.get(workflow_id)


class IntegrationMiddleware:
    """Middleware for integrating auth and event bus."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
    
    def emit_auth_event(self, user_id: str, event_type: str,
                       system: str, details: Dict) -> str:
        """Emit authentication-related event."""
        event = Event(
            event_type=EventType.SECURITY_ALERT,
            source_system=system,
            data={
                'user_id': user_id,
                'auth_event': event_type,
                'details': details,
            },
            priority=EventPriority.HIGH if 'failure' in event_type else EventPriority.NORMAL
        )
        
        self.event_bus.publish(event)
        return event.id
    
    def emit_security_event(self, severity: str, description: str,
                           affected_systems: List[str]) -> str:
        """Emit security event."""
        priority = {
            'critical': EventPriority.CRITICAL,
            'high': EventPriority.HIGH,
            'medium': EventPriority.NORMAL,
            'low': EventPriority.LOW,
        }.get(severity, EventPriority.NORMAL)
        
        event = Event(
            event_type=EventType.SECURITY_INCIDENT,
            source_system='security',
            data={
                'severity': severity,
                'description': description,
                'affected_systems': affected_systems,
            },
            priority=priority
        )
        
        self.event_bus.publish(event)
        return event.id
