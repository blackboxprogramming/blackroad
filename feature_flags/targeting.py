"""Feature flag targeting rules."""

from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum


class RuleOperator(Enum):
    """Rule comparison operators."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    NOT_IN = "not_in"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"


@dataclass
class TargetingRule:
    """Rule for targeting users."""
    rule_id: str
    attribute: str
    operator: RuleOperator
    value: Any
    priority: int = 0


class TargetingEngine:
    """Evaluates targeting rules."""
    
    def __init__(self):
        self.rules: Dict[str, List[TargetingRule]] = {}  # flag_id -> rules
    
    def add_rule(self, flag_id: str, rule: TargetingRule) -> bool:
        """Add targeting rule to flag."""
        if flag_id not in self.rules:
            self.rules[flag_id] = []
        
        self.rules[flag_id].append(rule)
        # Sort by priority
        self.rules[flag_id].sort(key=lambda r: r.priority, reverse=True)
        return True
    
    def evaluate_rules(self, flag_id: str, context: Dict[str, Any]) -> bool:
        """Evaluate all rules for flag."""
        if flag_id not in self.rules:
            return True  # No rules = allow all
        
        rules = self.rules[flag_id]
        for rule in rules:
            if not self._evaluate_rule(rule, context):
                return False
        
        return True
    
    def _evaluate_rule(self, rule: TargetingRule, context: Dict[str, Any]) -> bool:
        """Evaluate single rule."""
        attr_value = context.get(rule.attribute)
        
        if rule.operator == RuleOperator.EQUALS:
            return attr_value == rule.value
        elif rule.operator == RuleOperator.NOT_EQUALS:
            return attr_value != rule.value
        elif rule.operator == RuleOperator.IN:
            return attr_value in rule.value if isinstance(rule.value, list) else False
        elif rule.operator == RuleOperator.NOT_IN:
            return attr_value not in rule.value if isinstance(rule.value, list) else True
        elif rule.operator == RuleOperator.GREATER_THAN:
            return attr_value > rule.value if attr_value is not None else False
        elif rule.operator == RuleOperator.LESS_THAN:
            return attr_value < rule.value if attr_value is not None else False
        elif rule.operator == RuleOperator.CONTAINS:
            return rule.value in str(attr_value) if attr_value is not None else False
        
        return True
    
    def get_rules_for_flag(self, flag_id: str) -> List[TargetingRule]:
        """Get all rules for flag."""
        return self.rules.get(flag_id, [])
    
    def clear_rules(self, flag_id: str) -> bool:
        """Clear all rules for flag."""
        if flag_id in self.rules:
            self.rules[flag_id] = []
            return True
        return False


class Segment:
    """User segment definition."""
    
    def __init__(self, segment_id: str, name: str):
        self.segment_id = segment_id
        self.name = name
        self.rules: List[TargetingRule] = []
        self.user_count = 0
    
    def add_rule(self, rule: TargetingRule) -> bool:
        """Add rule to segment."""
        self.rules.append(rule)
        return True
    
    def matches_user(self, context: Dict[str, Any]) -> bool:
        """Check if user matches segment."""
        for rule in self.rules:
            engine = TargetingEngine()
            if not engine._evaluate_rule(rule, context):
                return False
        return True


class SegmentManager:
    """Manages user segments."""
    
    def __init__(self):
        self.segments: Dict[str, Segment] = {}
    
    def create_segment(self, segment_id: str, name: str) -> Segment:
        """Create segment."""
        segment = Segment(segment_id, name)
        self.segments[segment_id] = segment
        return segment
    
    def get_segment(self, segment_id: str) -> Optional[Segment]:
        """Get segment by ID."""
        return self.segments.get(segment_id)
    
    def get_segments_for_user(self, context: Dict[str, Any]) -> List[str]:
        """Get segments matching user."""
        matching = []
        for segment_id, segment in self.segments.items():
            if segment.matches_user(context):
                matching.append(segment_id)
        return matching
    
    def list_segments(self) -> List[Segment]:
        """List all segments."""
        return list(self.segments.values())
