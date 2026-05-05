"""Core personalization engine with user profiling and preference learning."""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
from collections import defaultdict
import math


class UserAction(Enum):
    """Types of user actions tracked."""
    VIEWED = "viewed"
    CLICKED = "clicked"
    PURCHASED = "purchased"
    BOOKMARKED = "bookmarked"
    SHARED = "shared"
    SEARCHED = "searched"
    ADDED_TO_CART = "added_to_cart"
    DOWNLOADED = "downloaded"
    RATED = "rated"
    COMMENTED = "commented"
    FOLLOWED = "followed"
    UNLIKED = "unliked"


class UserTier(Enum):
    """User engagement tiers."""
    INACTIVE = "inactive"
    ACTIVE = "active"
    ENGAGED = "engaged"
    VIP = "vip"


@dataclass
class ContentInteraction:
    """Record of user-content interaction."""
    content_id: str
    action: UserAction
    value: float = 1.0  # Weight/rating
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: str = ""
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserProfile:
    """User profile with preferences and behavior."""
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    # Behavior metrics
    total_interactions: int = 0
    total_views: int = 0
    total_clicks: int = 0
    total_purchases: int = 0
    total_revenue: float = 0.0
    
    # Engagement
    last_active: Optional[datetime] = None
    tier: UserTier = UserTier.INACTIVE
    engagement_score: float = 0.0
    
    # Preferences
    category_affinities: Dict[str, float] = field(default_factory=dict)
    brand_affinities: Dict[str, float] = field(default_factory=dict)
    content_type_preferences: Dict[str, float] = field(default_factory=dict)
    price_sensitivity: float = 0.5
    
    # Interactions
    interaction_history: List[ContentInteraction] = field(default_factory=list)
    
    # Segments
    segments: Set[str] = field(default_factory=set)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PersonalizationConfig:
    """Configuration for personalization engine."""
    engagement_window_days: int = 90
    interaction_decay_rate: float = 0.95
    min_interactions_for_profile: int = 5
    cold_start_threshold: int = 3
    category_weight: float = 0.4
    brand_weight: float = 0.3
    type_weight: float = 0.3
    engagement_threshold: float = 0.3


class InteractionDecay:
    """Time-based decay for interactions."""
    
    def __init__(self, decay_rate: float = 0.95, days: int = 90):
        self.decay_rate = decay_rate
        self.days = days
    
    def apply_decay(self, value: float, timestamp: datetime) -> float:
        """Apply exponential decay based on age."""
        age_days = (datetime.utcnow() - timestamp).days
        if age_days > self.days:
            return 0.0
        
        decay_factor = self.decay_rate ** (age_days / 30.0)
        return value * decay_factor


class PersonalizationEngine:
    """Core personalization and user profiling engine."""
    
    def __init__(self, config: Optional[PersonalizationConfig] = None):
        """Initialize personalization engine."""
        self.config = config or PersonalizationConfig()
        self.profiles: Dict[str, UserProfile] = {}
        self.interactions: Dict[str, List[ContentInteraction]] = defaultdict(list)
        self.decay = InteractionDecay(
            self.config.interaction_decay_rate,
            self.config.engagement_window_days
        )
    
    def get_or_create_profile(self, user_id: str) -> UserProfile:
        """Get or create user profile."""
        if user_id not in self.profiles:
            self.profiles[user_id] = UserProfile(
                user_id=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        return self.profiles[user_id]
    
    def track_interaction(
        self,
        user_id: str,
        content_id: str,
        action: UserAction,
        value: float = 1.0,
        context: Optional[Dict[str, Any]] = None
    ) -> UserProfile:
        """Track user-content interaction."""
        profile = self.get_or_create_profile(user_id)
        
        interaction = ContentInteraction(
            content_id=content_id,
            action=action,
            value=value,
            timestamp=datetime.utcnow(),
            context=context or {}
        )
        
        self.interactions[user_id].append(interaction)
        profile.interaction_history.append(interaction)
        profile.total_interactions += 1
        profile.last_active = datetime.utcnow()
        profile.updated_at = datetime.utcnow()
        
        # Update action-specific counters
        if action == UserAction.VIEWED:
            profile.total_views += 1
        elif action == UserAction.CLICKED:
            profile.total_clicks += 1
        elif action == UserAction.PURCHASED:
            profile.total_purchases += 1
            profile.total_revenue += value
        
        # Update tier based on engagement
        self._update_user_tier(profile)
        
        return profile
    
    def update_preferences(
        self,
        user_id: str,
        category_affinities: Optional[Dict[str, float]] = None,
        brand_affinities: Optional[Dict[str, float]] = None,
        content_preferences: Optional[Dict[str, float]] = None,
        price_sensitivity: Optional[float] = None
    ) -> UserProfile:
        """Update user preferences."""
        profile = self.get_or_create_profile(user_id)
        
        if category_affinities:
            profile.category_affinities.update(category_affinities)
        if brand_affinities:
            profile.brand_affinities.update(brand_affinities)
        if content_preferences:
            profile.content_type_preferences.update(content_preferences)
        if price_sensitivity is not None:
            profile.price_sensitivity = max(0.0, min(1.0, price_sensitivity))
        
        profile.updated_at = datetime.utcnow()
        return profile
    
    def infer_preferences(self, user_id: str) -> UserProfile:
        """Infer user preferences from interaction history."""
        profile = self.get_or_create_profile(user_id)
        
        if len(profile.interaction_history) < self.config.min_interactions_for_profile:
            return profile
        
        # Reset preferences
        category_aff = defaultdict(float)
        brand_aff = defaultdict(float)
        type_aff = defaultdict(float)
        
        total_weighted_value = 0.0
        
        for interaction in profile.interaction_history[-100:]:  # Last 100
            # Apply decay
            decayed_value = self.decay.apply_decay(interaction.value, interaction.timestamp)
            
            # Action type weighting
            action_weight = {
                UserAction.PURCHASED: 5.0,
                UserAction.BOOKMARKED: 3.0,
                UserAction.CLICKED: 2.0,
                UserAction.VIEWED: 1.0,
                UserAction.UNLIKED: -2.0,
            }.get(interaction.action, 1.0)
            
            weighted_value = decayed_value * action_weight
            total_weighted_value += weighted_value
            
            # Extract from context
            context = interaction.context
            if 'category' in context:
                category_aff[context['category']] += weighted_value
            if 'brand' in context:
                brand_aff[context['brand']] += weighted_value
            if 'content_type' in context:
                type_aff[context['content_type']] += weighted_value
        
        if total_weighted_value > 0:
            # Normalize
            category_aff = {k: v / total_weighted_value for k, v in category_aff.items()}
            brand_aff = {k: v / total_weighted_value for k, v in brand_aff.items()}
            type_aff = {k: v / total_weighted_value for k, v in type_aff.items()}
        
        profile.category_affinities = dict(category_aff)
        profile.brand_affinities = dict(brand_aff)
        profile.content_type_preferences = dict(type_aff)
        
        return profile
    
    def get_engagement_score(self, user_id: str) -> float:
        """Calculate engagement score (0-100)."""
        profile = self.get_or_create_profile(user_id)
        
        if profile.total_interactions == 0:
            return 0.0
        
        # Components
        recency = self._recency_score(profile)
        frequency = min(100.0, profile.total_interactions * 5)
        monetization = min(100.0, profile.total_revenue / 10)
        
        # Weighted average
        score = (recency * 0.4) + (frequency * 0.35) + (monetization * 0.25)
        
        profile.engagement_score = score
        return score
    
    def _recency_score(self, profile: UserProfile) -> float:
        """Calculate recency score."""
        if not profile.last_active:
            return 0.0
        
        days_since_active = (datetime.utcnow() - profile.last_active).days
        
        if days_since_active > self.config.engagement_window_days:
            return 0.0
        
        return 100.0 * (1.0 - (days_since_active / self.config.engagement_window_days))
    
    def _update_user_tier(self, profile: UserProfile) -> None:
        """Update user tier based on engagement."""
        engagement = self.get_engagement_score(profile.user_id)
        
        if engagement >= 80:
            profile.tier = UserTier.VIP
        elif engagement >= 50:
            profile.tier = UserTier.ENGAGED
        elif engagement >= 20:
            profile.tier = UserTier.ACTIVE
        else:
            profile.tier = UserTier.INACTIVE
    
    def get_profile_summary(self, user_id: str) -> Dict[str, Any]:
        """Get user profile summary."""
        profile = self.get_or_create_profile(user_id)
        self.infer_preferences(user_id)
        
        return {
            'user_id': user_id,
            'tier': profile.tier.value,
            'engagement_score': f"{profile.engagement_score:.1f}",
            'total_interactions': profile.total_interactions,
            'total_purchases': profile.total_purchases,
            'total_revenue': f"${profile.total_revenue:.2f}",
            'last_active': profile.last_active.isoformat() if profile.last_active else None,
            'top_categories': self._get_top_items(profile.category_affinities, 3),
            'top_brands': self._get_top_items(profile.brand_affinities, 3),
            'segments': list(profile.segments),
        }
    
    def _get_top_items(self, affinities: Dict[str, float], limit: int) -> List[str]:
        """Get top items by affinity."""
        return [
            item for item, _ in sorted(affinities.items(), key=lambda x: x[1], reverse=True)[:limit]
        ]
    
    def get_cohort_profiles(self, segment_id: str) -> List[Dict[str, Any]]:
        """Get profiles for users in a segment."""
        profiles = [
            self.get_profile_summary(pid)
            for profile in self.profiles.values()
            if segment_id in profile.segments
        ]
        return profiles
    
    def get_engine_metrics(self) -> Dict[str, Any]:
        """Get overall engine metrics."""
        if not self.profiles:
            return {}
        
        total_interactions = sum(p.total_interactions for p in self.profiles.values())
        total_revenue = sum(p.total_revenue for p in self.profiles.values())
        avg_engagement = sum(p.engagement_score for p in self.profiles.values()) / len(self.profiles)
        
        tier_distribution = defaultdict(int)
        for profile in self.profiles.values():
            tier_distribution[profile.tier.value] += 1
        
        return {
            'total_users': len(self.profiles),
            'total_interactions': total_interactions,
            'total_revenue': f"${total_revenue:.2f}",
            'average_engagement_score': f"{avg_engagement:.1f}",
            'tier_distribution': dict(tier_distribution),
            'active_users_24h': sum(
                1 for p in self.profiles.values()
                if p.last_active and (datetime.utcnow() - p.last_active).days < 1
            ),
        }
