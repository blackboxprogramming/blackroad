"""Advanced Personalization & AI-Powered Recommendations Engine."""

__version__ = "1.0.0"

from .personalizer import PersonalizationEngine, UserProfile, PersonalizationConfig
from .recommender import RecommendationEngine, Recommendation
from .segmentation import SegmentationEngine, UserSegment
from .content_optimizer import ContentOptimizer, ABTest

__all__ = [
    'PersonalizationEngine',
    'UserProfile',
    'PersonalizationConfig',
    'RecommendationEngine',
    'Recommendation',
    'SegmentationEngine',
    'UserSegment',
    'ContentOptimizer',
    'ABTest',
]
