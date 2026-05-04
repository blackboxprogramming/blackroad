"""Feature flag engine with evaluation."""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class FlagType(Enum):
    """Feature flag types."""
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    MULTI_VARIANT = "multi_variant"
    EXPERIMENT = "experiment"


class FlagStatus(Enum):
    """Feature flag status."""
    DEVELOPMENT = "development"
    STAGED = "staged"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"


@dataclass
class FeatureFlag:
    """Feature flag definition."""
    flag_id: str
    name: str
    description: str
    flag_type: FlagType
    status: FlagStatus
    enabled: bool = False
    percentage: float = 0.0  # 0-100 for percentage flags
    variants: Dict[str, Any] = field(default_factory=dict)  # multi_variant options
    created_at: datetime = None
    updated_at: datetime = None
    created_by: str = ""
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class Context:
    """Evaluation context."""
    user_id: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class FlagEvaluator:
    """Evaluates feature flags against context."""
    
    def __init__(self):
        self.evaluations: List[Dict[str, Any]] = []
    
    def evaluate(self, flag: FeatureFlag, context: Context) -> bool:
        """Evaluate flag for context."""
        result = self._do_evaluate(flag, context)
        
        # Log evaluation
        self.evaluations.append({
            'flag_id': flag.flag_id,
            'user_id': context.user_id,
            'result': result,
            'timestamp': datetime.utcnow().isoformat(),
        })
        
        return result
    
    def _do_evaluate(self, flag: FeatureFlag, context: Context) -> bool:
        """Internal evaluation logic."""
        if not flag.enabled:
            return False
        
        if flag.flag_type == FlagType.BOOLEAN:
            return True
        
        elif flag.flag_type == FlagType.PERCENTAGE:
            # Use user_id as seed for consistent bucketing
            hash_val = hash(f"{flag.flag_id}:{context.user_id}") % 100
            return hash_val < flag.percentage
        
        elif flag.flag_type == FlagType.MULTI_VARIANT:
            return True
        
        elif flag.flag_type == FlagType.EXPERIMENT:
            return hash(context.user_id) % 2 == 0
        
        return False
    
    def get_variant(self, flag: FeatureFlag, context: Context) -> Optional[str]:
        """Get variant for multi-variant flag."""
        if flag.flag_type != FlagType.MULTI_VARIANT or not flag.variants:
            return None
        
        variant_names = list(flag.variants.keys())
        if not variant_names:
            return None
        
        hash_val = hash(f"{flag.flag_id}:{context.user_id}") % len(variant_names)
        return variant_names[hash_val]
    
    def get_evaluation_count(self) -> int:
        """Get total evaluations."""
        return len(self.evaluations)


class FlagStore:
    """Stores feature flags."""
    
    def __init__(self):
        self.flags: Dict[str, FeatureFlag] = {}
    
    def create_flag(self, flag: FeatureFlag) -> bool:
        """Create feature flag."""
        if flag.flag_id in self.flags:
            return False
        self.flags[flag.flag_id] = flag
        return True
    
    def get_flag(self, flag_id: str) -> Optional[FeatureFlag]:
        """Get flag by ID."""
        return self.flags.get(flag_id)
    
    def update_flag(self, flag_id: str, updates: Dict[str, Any]) -> bool:
        """Update flag."""
        if flag_id not in self.flags:
            return False
        
        flag = self.flags[flag_id]
        for key, value in updates.items():
            if hasattr(flag, key):
                setattr(flag, key, value)
        flag.updated_at = datetime.utcnow()
        return True
    
    def delete_flag(self, flag_id: str) -> bool:
        """Delete flag."""
        if flag_id in self.flags:
            del self.flags[flag_id]
            return True
        return False
    
    def list_flags(self, status: FlagStatus = None) -> List[FeatureFlag]:
        """List flags."""
        flags = list(self.flags.values())
        if status:
            flags = [f for f in flags if f.status == status]
        return flags
    
    def enable_flag(self, flag_id: str) -> bool:
        """Enable flag."""
        return self.update_flag(flag_id, {'enabled': True})
    
    def disable_flag(self, flag_id: str) -> bool:
        """Disable flag."""
        return self.update_flag(flag_id, {'enabled': False})
    
    def get_flag_count(self) -> Dict[str, int]:
        """Get flag counts by status."""
        counts = {}
        for status in FlagStatus:
            counts[status.value] = sum(1 for f in self.flags.values() if f.status == status)
        return counts


class FlagEngine:
    """Main feature flag engine."""
    
    def __init__(self):
        self.store = FlagStore()
        self.evaluator = FlagEvaluator()
        self.cache: Dict[str, bool] = {}
        self.cache_ttl_seconds = 60
    
    def create_flag(
        self,
        flag_id: str,
        name: str,
        flag_type: FlagType,
        created_by: str = "system"
    ) -> FeatureFlag:
        """Create feature flag."""
        flag = FeatureFlag(
            flag_id=flag_id,
            name=name,
            description="",
            flag_type=flag_type,
            status=FlagStatus.DEVELOPMENT,
            created_by=created_by
        )
        self.store.create_flag(flag)
        return flag
    
    def is_enabled(self, flag_id: str, context: Context) -> bool:
        """Check if flag is enabled for context."""
        flag = self.store.get_flag(flag_id)
        if not flag:
            return False
        
        return self.evaluator.evaluate(flag, context)
    
    def get_variant(self, flag_id: str, context: Context) -> Optional[str]:
        """Get variant for flag."""
        flag = self.store.get_flag(flag_id)
        if not flag:
            return None
        
        return self.evaluator.get_variant(flag, context)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get engine metrics."""
        return {
            'total_flags': len(self.store.flags),
            'enabled_flags': sum(1 for f in self.store.flags.values() if f.enabled),
            'total_evaluations': self.evaluator.get_evaluation_count(),
            'flag_counts': self.store.get_flag_count(),
        }
