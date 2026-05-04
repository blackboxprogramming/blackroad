"""Notification rules and triggers."""

from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum


class TriggerType(Enum):
    """Notification trigger types."""
    USER_SIGNUP = "user_signup"
    ORDER_PLACED = "order_placed"
    PAYMENT_RECEIVED = "payment_received"
    DELIVERY_UPDATE = "delivery_update"
    PROMOTION = "promotion"
    ALERT = "alert"


@dataclass
class Rule:
    """Notification rule."""
    rule_id: str
    name: str
    trigger: TriggerType
    template_id: str
    channels: List[str]
    enabled: bool = True
    conditions: Dict[str, Any] = None


class RulesEngine:
    """Manages notification rules."""
    
    def __init__(self):
        self.rules: Dict[str, Rule] = {}
        self.triggers: Dict[TriggerType, List[str]] = {}  # trigger -> rule_ids
        self.execution_log: List[Dict[str, Any]] = []
    
    def register_rule(self, rule: Rule) -> bool:
        """Register notification rule."""
        self.rules[rule.rule_id] = rule
        
        if rule.trigger not in self.triggers:
            self.triggers[rule.trigger] = []
        
        self.triggers[rule.trigger].append(rule.rule_id)
        return True
    
    def get_rules_for_trigger(self, trigger: TriggerType) -> List[Rule]:
        """Get applicable rules for trigger."""
        rule_ids = self.triggers.get(trigger, [])
        rules = []
        for rule_id in rule_ids:
            rule = self.rules.get(rule_id)
            if rule and rule.enabled:
                rules.append(rule)
        return rules
    
    def execute_trigger(self, trigger: TriggerType, context: Dict[str, Any]) -> List[str]:
        """Execute rules for trigger."""
        applicable_rules = self.get_rules_for_trigger(trigger)
        notification_ids = []
        
        for rule in applicable_rules:
            # Check conditions
            if self._check_conditions(rule.conditions, context):
                # Would create notification here
                notif_id = f"notif_{rule.rule_id}_{len(notification_ids)}"
                notification_ids.append(notif_id)
                
                self.execution_log.append({
                    'rule_id': rule.rule_id,
                    'trigger': trigger.value,
                    'notification_id': notif_id,
                    'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
                })
        
        return notification_ids
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable rule."""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            return True
        return False
    
    def _check_conditions(self, conditions: Optional[Dict[str, Any]], context: Dict[str, Any]) -> bool:
        """Check if conditions match context."""
        if not conditions:
            return True
        
        for key, value in conditions.items():
            if key not in context or context[key] != value:
                return False
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get rules statistics."""
        return {
            'total_rules': len(self.rules),
            'enabled_rules': sum(1 for r in self.rules.values() if r.enabled),
            'disabled_rules': sum(1 for r in self.rules.values() if not r.enabled),
            'execution_count': len(self.execution_log),
            'triggers_configured': len(self.triggers),
        }


class EventListener:
    """Listens for events to trigger notifications."""
    
    def __init__(self, rules_engine: RulesEngine):
        self.rules_engine = rules_engine
        self.listeners: Dict[TriggerType, List[Callable]] = {}
        self.event_count = 0
    
    def on(self, trigger: TriggerType, callback: Callable) -> None:
        """Register event listener."""
        if trigger not in self.listeners:
            self.listeners[trigger] = []
        self.listeners[trigger].append(callback)
    
    def emit(self, trigger: TriggerType, context: Dict[str, Any]) -> List[str]:
        """Emit event and execute rules."""
        self.event_count += 1
        notification_ids = self.rules_engine.execute_trigger(trigger, context)
        
        # Call registered listeners
        callbacks = self.listeners.get(trigger, [])
        for callback in callbacks:
            try:
                callback(context)
            except Exception as e:
                print(f"Error in listener: {e}")
        
        return notification_ids
    
    def get_listener_stats(self) -> Dict[str, Any]:
        """Get listener statistics."""
        return {
            'total_events_emitted': self.event_count,
            'listeners_registered': sum(len(cbs) for cbs in self.listeners.values()),
            'trigger_types': len(self.listeners),
        }
