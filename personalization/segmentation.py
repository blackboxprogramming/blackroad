"""User Segmentation Engine with RFM and clustering."""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import math


class SegmentationType(Enum):
    """Types of segmentation."""
    RFM = "rfm"
    BEHAVIORAL = "behavioral"
    LOOKALIKE = "lookalike"
    CHURN_RISK = "churn_risk"
    HIGH_VALUE = "high_value"


@dataclass
class UserSegment:
    """A user segment."""
    segment_id: str
    segment_type: SegmentationType
    name: str
    description: str
    user_ids: Set[str]
    created_at: datetime
    metrics: Dict[str, Any]


class SegmentationEngine:
    """User segmentation with RFM, clustering, and lookalike modeling."""
    
    def __init__(self, personalizer):
        """Initialize segmentation engine."""
        self.personalizer = personalizer
        self.segments: Dict[str, UserSegment] = {}
        self.user_to_segments: Dict[str, Set[str]] = defaultdict(set)
    
    def segment_by_rfm(self) -> UserSegment:
        """Create RFM-based segmentation."""
        segment_id = f"seg_rfm_{datetime.utcnow().timestamp()}"
        rfm_groups = defaultdict(set)
        
        for user_id, profile in self.personalizer.profiles.items():
            if profile.total_interactions == 0:
                continue
            
            # Calculate RFM scores (1-5 scale)
            recency_score = self._calculate_recency_score(profile)
            frequency_score = self._calculate_frequency_score(profile)
            monetary_score = self._calculate_monetary_score(profile)
            
            # Create RFM code
            rfm_code = f"R{recency_score}F{frequency_score}M{monetary_score}"
            rfm_groups[rfm_code].add(user_id)
        
        # Create subsegments for key RFM groups
        segments_created = []
        for rfm_code, user_ids in rfm_groups.items():
            if len(user_ids) >= 5:  # Only segments with 5+ users
                rfm_segment = UserSegment(
                    segment_id=f"{segment_id}_{rfm_code}",
                    segment_type=SegmentationType.RFM,
                    name=f"RFM {rfm_code}",
                    description=self._rfm_description(rfm_code),
                    user_ids=user_ids,
                    created_at=datetime.utcnow(),
                    metrics={
                        'rfm_code': rfm_code,
                        'user_count': len(user_ids),
                        'avg_value': sum(
                            self.personalizer.profiles[uid].total_revenue
                            for uid in user_ids
                        ) / len(user_ids),
                    }
                )
                segments_created.append(rfm_segment)
                self.segments[rfm_segment.segment_id] = rfm_segment
                
                for user_id in user_ids:
                    self.user_to_segments[user_id].add(rfm_segment.segment_id)
        
        return segments_created[0] if segments_created else None
    
    def identify_churn_risk(self, threshold_days: int = 30) -> UserSegment:
        """Identify users at risk of churn."""
        segment_id = f"seg_churn_{datetime.utcnow().timestamp()}"
        churn_users = set()
        
        cutoff = datetime.utcnow() - timedelta(days=threshold_days)
        
        for user_id, profile in self.personalizer.profiles.items():
            if profile.last_active and profile.last_active < cutoff:
                churn_users.add(user_id)
        
        segment = UserSegment(
            segment_id=segment_id,
            segment_type=SegmentationType.CHURN_RISK,
            name=f"Churn Risk (inactive {threshold_days}+ days)",
            description=f"Users inactive for more than {threshold_days} days",
            user_ids=churn_users,
            created_at=datetime.utcnow(),
            metrics={
                'user_count': len(churn_users),
                'avg_ltv': sum(
                    self.personalizer.profiles[uid].total_revenue
                    for uid in churn_users
                ) / len(churn_users) if churn_users else 0,
            }
        )
        
        self.segments[segment_id] = segment
        for user_id in churn_users:
            self.user_to_segments[user_id].add(segment_id)
        
        return segment
    
    def identify_high_value_customers(self, percentile: int = 80) -> UserSegment:
        """Identify high-value customers (top percentile by revenue)."""
        segment_id = f"seg_hvc_{datetime.utcnow().timestamp()}"
        
        revenues = [p.total_revenue for p in self.personalizer.profiles.values()]
        if not revenues:
            return None
        
        threshold = sorted(revenues)[int(len(revenues) * percentile / 100)]
        
        hvc_users = set(
            user_id for user_id, profile in self.personalizer.profiles.items()
            if profile.total_revenue >= threshold
        )
        
        segment = UserSegment(
            segment_id=segment_id,
            segment_type=SegmentationType.HIGH_VALUE,
            name=f"High-Value Customers (Top {100-percentile}%)",
            description=f"Users in top {100-percentile}% by revenue",
            user_ids=hvc_users,
            created_at=datetime.utcnow(),
            metrics={
                'user_count': len(hvc_users),
                'total_revenue': sum(
                    self.personalizer.profiles[uid].total_revenue
                    for uid in hvc_users
                ),
                'avg_revenue_per_user': sum(
                    self.personalizer.profiles[uid].total_revenue
                    for uid in hvc_users
                ) / len(hvc_users) if hvc_users else 0,
            }
        )
        
        self.segments[segment_id] = segment
        for user_id in hvc_users:
            self.user_to_segments[user_id].add(segment_id)
        
        return segment
    
    def find_lookalike_audience(
        self,
        seed_user_ids: List[str],
        target_size: int = 100
    ) -> UserSegment:
        """Find lookalike audience similar to seed users."""
        segment_id = f"seg_lookalike_{datetime.utcnow().timestamp()}"
        
        # Get characteristics of seed users
        seed_profiles = [
            self.personalizer.get_or_create_profile(uid)
            for uid in seed_user_ids
        ]
        
        avg_categories = defaultdict(float)
        avg_brands = defaultdict(float)
        
        for profile in seed_profiles:
            for cat, aff in profile.category_affinities.items():
                avg_categories[cat] += aff
            for brand, aff in profile.brand_affinities.items():
                avg_brands[brand] += aff
        
        # Normalize
        for cat in avg_categories:
            avg_categories[cat] /= len(seed_profiles)
        for brand in avg_brands:
            avg_brands[brand] /= len(seed_profiles)
        
        # Find similar users
        similarities = []
        for user_id, profile in self.personalizer.profiles.items():
            if user_id in seed_user_ids:
                continue
            
            similarity = 0.0
            shared_cats = sum(
                min(avg_categories.get(c, 0), profile.category_affinities.get(c, 0))
                for c in set(avg_categories.keys()) & set(profile.category_affinities.keys())
            )
            shared_brands = sum(
                min(avg_brands.get(b, 0), profile.brand_affinities.get(b, 0))
                for b in set(avg_brands.keys()) & set(profile.brand_affinities.keys())
            )
            
            similarity = shared_cats * 0.6 + shared_brands * 0.4
            similarities.append((user_id, similarity))
        
        # Get top target_size
        lookalike_users = set(
            uid for uid, _ in sorted(similarities, key=lambda x: x[1], reverse=True)[:target_size]
        )
        
        segment = UserSegment(
            segment_id=segment_id,
            segment_type=SegmentationType.LOOKALIKE,
            name=f"Lookalike Audience ({target_size} users)",
            description="Users similar to seed audience",
            user_ids=lookalike_users,
            created_at=datetime.utcnow(),
            metrics={
                'seed_users': len(seed_user_ids),
                'lookalike_users': len(lookalike_users),
                'avg_similarity': sum(s for _, s in similarities[:target_size]) / target_size if similarities else 0,
            }
        )
        
        self.segments[segment_id] = segment
        for user_id in lookalike_users:
            self.user_to_segments[user_id].add(segment_id)
        
        return segment
    
    def segment_by_behavior(self) -> List[UserSegment]:
        """Create behavioral segments."""
        segments = []
        
        # Define behavioral groups
        behaviors = {
            'browsers': self._find_browsers(),
            'converters': self._find_converters(),
            'repeat_buyers': self._find_repeat_buyers(),
        }
        
        for behavior_name, user_ids in behaviors.items():
            if len(user_ids) >= 5:
                segment = UserSegment(
                    segment_id=f"seg_behavior_{behavior_name}_{datetime.utcnow().timestamp()}",
                    segment_type=SegmentationType.BEHAVIORAL,
                    name=behavior_name.replace('_', ' ').title(),
                    description=f"Users exhibiting {behavior_name}",
                    user_ids=user_ids,
                    created_at=datetime.utcnow(),
                    metrics={
                        'user_count': len(user_ids),
                    }
                )
                segments.append(segment)
                self.segments[segment.segment_id] = segment
                
                for user_id in user_ids:
                    self.user_to_segments[user_id].add(segment.segment_id)
        
        return segments
    
    def _find_browsers(self) -> Set[str]:
        """Find users who browse but don't buy."""
        from personalizer import UserAction
        
        browsers = set()
        for user_id, profile in self.personalizer.profiles.items():
            if profile.total_views > 10 and profile.total_purchases == 0:
                browsers.add(user_id)
        return browsers
    
    def _find_converters(self) -> Set[str]:
        """Find high-conversion-rate users."""
        converters = set()
        for user_id, profile in self.personalizer.profiles.items():
            if profile.total_interactions > 0:
                conversion_rate = profile.total_purchases / profile.total_interactions
                if conversion_rate > 0.3:
                    converters.add(user_id)
        return converters
    
    def _find_repeat_buyers(self) -> Set[str]:
        """Find repeat customers."""
        repeat_buyers = set()
        for user_id, profile in self.personalizer.profiles.items():
            if profile.total_purchases >= 3:
                repeat_buyers.add(user_id)
        return repeat_buyers
    
    def _calculate_recency_score(self, profile) -> int:
        """Calculate recency score (1-5)."""
        if not profile.last_active:
            return 1
        
        days_inactive = (datetime.utcnow() - profile.last_active).days
        
        if days_inactive <= 7:
            return 5
        elif days_inactive <= 14:
            return 4
        elif days_inactive <= 30:
            return 3
        elif days_inactive <= 60:
            return 2
        else:
            return 1
    
    def _calculate_frequency_score(self, profile) -> int:
        """Calculate frequency score (1-5)."""
        if profile.total_interactions == 0:
            return 1
        elif profile.total_interactions <= 5:
            return 2
        elif profile.total_interactions <= 15:
            return 3
        elif profile.total_interactions <= 50:
            return 4
        else:
            return 5
    
    def _calculate_monetary_score(self, profile) -> int:
        """Calculate monetary score (1-5)."""
        if profile.total_revenue == 0:
            return 1
        elif profile.total_revenue <= 50:
            return 2
        elif profile.total_revenue <= 200:
            return 3
        elif profile.total_revenue <= 1000:
            return 4
        else:
            return 5
    
    def _rfm_description(self, rfm_code: str) -> str:
        """Generate description for RFM segment."""
        descriptions = {
            'R5F5M5': 'Champions - Best customers',
            'R5F5M4': 'Loyal Customers - High value',
            'R4F5M5': 'Can\'t Lose Them - High value at risk',
            'R5F1M5': 'Recent High Spenders',
            'R5F1M1': 'Recent Low Spenders',
            'R1F1M1': 'Lost - At Risk customers',
        }
        return descriptions.get(rfm_code, 'RFM Segment')
    
    def get_user_segments(self, user_id: str) -> List[UserSegment]:
        """Get all segments a user belongs to."""
        segment_ids = self.user_to_segments.get(user_id, set())
        return [self.segments[sid] for sid in segment_ids if sid in self.segments]
    
    def get_engine_metrics(self) -> Dict[str, Any]:
        """Get segmentation engine metrics."""
        return {
            'total_segments': len(self.segments),
            'segments_by_type': {
                st.value: len([s for s in self.segments.values() if s.segment_type == st])
                for st in SegmentationType
            },
            'avg_segment_size': sum(len(s.user_ids) for s in self.segments.values()) /
                len(self.segments) if self.segments else 0,
            'users_segmented': len(self.user_to_segments),
        }
