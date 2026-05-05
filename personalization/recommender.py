"""AI-Powered Recommendation Engine with multiple algorithms."""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import math
from collections import defaultdict, Counter


@dataclass
class Recommendation:
    """A personalized recommendation."""
    content_id: str
    score: float
    algorithm: str
    explanation: str
    rank: int = 0
    context: Dict[str, Any] = None


class RecommendationEngine:
    """Recommendation engine with collaborative and content-based filtering."""
    
    def __init__(self, personalizer):
        """Initialize recommendation engine."""
        self.personalizer = personalizer
        self.user_similarities: Dict[Tuple[str, str], float] = {}
        self.item_similarities: Dict[Tuple[str, str], float] = {}
    
    def get_recommendations(
        self,
        user_id: str,
        limit: int = 10,
        algorithms: Optional[List[str]] = None
    ) -> List[Recommendation]:
        """Get personalized recommendations."""
        if algorithms is None:
            algorithms = ['collaborative', 'content_based', 'trending', 'diversity']
        
        recommendations = {}
        
        # Collaborative filtering
        if 'collaborative' in algorithms:
            collab_recs = self._collaborative_filtering(user_id, limit * 2)
            for rec in collab_recs:
                if rec.content_id not in recommendations:
                    recommendations[rec.content_id] = rec
                else:
                    recommendations[rec.content_id].score = (
                        recommendations[rec.content_id].score + rec.score
                    ) / 2
        
        # Content-based
        if 'content_based' in algorithms:
            content_recs = self._content_based_filtering(user_id, limit * 2)
            for rec in content_recs:
                if rec.content_id not in recommendations:
                    recommendations[rec.content_id] = rec
                else:
                    recommendations[rec.content_id].score = (
                        recommendations[rec.content_id].score + rec.score
                    ) / 2
        
        # Trending
        if 'trending' in algorithms:
            trending_recs = self._trending_recommendations(user_id, limit // 2)
            for rec in trending_recs:
                if rec.content_id not in recommendations:
                    recommendations[rec.content_id] = rec
        
        # Sort and diversify
        sorted_recs = sorted(
            recommendations.values(),
            key=lambda x: x.score,
            reverse=True
        )
        
        if 'diversity' in algorithms:
            sorted_recs = self._apply_diversity(sorted_recs, limit)
        else:
            sorted_recs = sorted_recs[:limit]
        
        # Add ranking
        for rank, rec in enumerate(sorted_recs, 1):
            rec.rank = rank
        
        return sorted_recs
    
    def _collaborative_filtering(self, user_id: str, limit: int) -> List[Recommendation]:
        """Collaborative filtering: similar users' preferences."""
        profile = self.personalizer.get_or_create_profile(user_id)
        
        if len(profile.interaction_history) < self.personalizer.config.cold_start_threshold:
            return []
        
        recommendations = []
        similar_users = self._find_similar_users(user_id, limit=5)
        
        seen_content = set(i.content_id for i in profile.interaction_history)
        content_scores = defaultdict(float)
        
        for similar_user_id, similarity in similar_users:
            similar_profile = self.personalizer.get_or_create_profile(similar_user_id)
            
            for interaction in similar_profile.interaction_history:
                if interaction.content_id not in seen_content:
                    # Score based on action and similarity
                    action_weight = {
                        'purchased': 5.0,
                        'bookmarked': 3.0,
                        'clicked': 2.0,
                        'viewed': 1.0,
                    }.get(interaction.action.value, 1.0)
                    
                    content_scores[interaction.content_id] += (
                        interaction.value * action_weight * similarity
                    )
        
        for content_id, score in sorted(
            content_scores.items(), key=lambda x: x[1], reverse=True
        )[:limit]:
            recommendations.append(Recommendation(
                content_id=content_id,
                score=min(100.0, score),
                algorithm='collaborative',
                explanation=f"Users like you enjoyed this content"
            ))
        
        return recommendations
    
    def _content_based_filtering(self, user_id: str, limit: int) -> List[Recommendation]:
        """Content-based filtering: similar to liked content."""
        profile = self.personalizer.get_or_create_profile(user_id)
        
        if not profile.category_affinities and not profile.brand_affinities:
            self.personalizer.infer_preferences(user_id)
        
        recommendations = []
        seen_content = set(i.content_id for i in profile.interaction_history)
        
        # Score based on preferences
        content_scores = defaultdict(float)
        
        # Simulate content catalog (in production: fetch from DB)
        catalog = self._get_content_catalog()
        
        for content_id, content_features in catalog.items():
            if content_id in seen_content:
                continue
            
            score = 0.0
            
            # Category match
            if 'category' in content_features:
                category = content_features['category']
                score += profile.category_affinities.get(category, 0.0) * \
                    self.personalizer.config.category_weight * 100
            
            # Brand match
            if 'brand' in content_features:
                brand = content_features['brand']
                score += profile.brand_affinities.get(brand, 0.0) * \
                    self.personalizer.config.brand_weight * 100
            
            # Content type match
            if 'type' in content_features:
                content_type = content_features['type']
                score += profile.content_type_preferences.get(content_type, 0.0) * \
                    self.personalizer.config.type_weight * 100
            
            if score > 0:
                content_scores[content_id] = min(100.0, score)
        
        for content_id, score in sorted(
            content_scores.items(), key=lambda x: x[1], reverse=True
        )[:limit]:
            recommendations.append(Recommendation(
                content_id=content_id,
                score=score,
                algorithm='content_based',
                explanation="Based on your interests and preferences"
            ))
        
        return recommendations
    
    def _trending_recommendations(self, user_id: str, limit: int) -> List[Recommendation]:
        """Trending content recommendations."""
        profile = self.personalizer.get_or_create_profile(user_id)
        seen_content = set(i.content_id for i in profile.interaction_history)
        
        # Calculate trending: most interacted in last 7 days
        trending_scores = defaultdict(float)
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        for other_profile in self.personalizer.profiles.values():
            for interaction in other_profile.interaction_history:
                if interaction.timestamp >= cutoff_date and interaction.content_id not in seen_content:
                    trending_scores[interaction.content_id] += 1
        
        recommendations = []
        for content_id, _ in sorted(
            trending_scores.items(), key=lambda x: x[1], reverse=True
        )[:limit]:
            recommendations.append(Recommendation(
                content_id=content_id,
                score=75.0,
                algorithm='trending',
                explanation="Trending now - popular with users"
            ))
        
        return recommendations
    
    def _apply_diversity(
        self,
        recommendations: List[Recommendation],
        limit: int
    ) -> List[Recommendation]:
        """Apply diversity to reduce similar recommendations."""
        if len(recommendations) <= limit:
            return recommendations
        
        diverse_recs = [recommendations[0]]
        
        for rec in recommendations[1:]:
            if len(diverse_recs) >= limit:
                break
            
            # Check diversity against existing
            is_diverse = True
            for existing in diverse_recs:
                if self._content_similarity(rec.content_id, existing.content_id) > 0.8:
                    is_diverse = False
                    break
            
            if is_diverse:
                diverse_recs.append(rec)
        
        return diverse_recs
    
    def _find_similar_users(self, user_id: str, limit: int = 5) -> List[Tuple[str, float]]:
        """Find similar users using interaction patterns."""
        profile = self.personalizer.get_or_create_profile(user_id)
        similarities = []
        
        for other_id, other_profile in self.personalizer.profiles.items():
            if other_id == user_id:
                continue
            
            similarity = self._user_similarity(profile, other_profile)
            if similarity > 0.1:
                similarities.append((other_id, similarity))
        
        return sorted(similarities, key=lambda x: x[1], reverse=True)[:limit]
    
    def _user_similarity(self, profile1, profile2) -> float:
        """Calculate similarity between two users (cosine similarity)."""
        categories1 = set(profile1.category_affinities.keys())
        categories2 = set(profile2.category_affinities.keys())
        
        if not categories1 or not categories2:
            return 0.0
        
        # Jaccard similarity for categories
        intersection = len(categories1 & categories2)
        union = len(categories1 | categories2)
        
        return intersection / union if union > 0 else 0.0
    
    def _content_similarity(self, content_id1: str, content_id2: str) -> float:
        """Calculate similarity between two content items."""
        # In production: compare embeddings or features
        # For demo: simple hash-based similarity
        hash1 = hash(content_id1) % 100
        hash2 = hash(content_id2) % 100
        
        distance = abs(hash1 - hash2)
        return max(0.0, 1.0 - (distance / 100.0))
    
    def _get_content_catalog(self) -> Dict[str, Dict[str, str]]:
        """Get content catalog (simulated)."""
        categories = ['electronics', 'books', 'clothing', 'home', 'sports']
        brands = ['BrandA', 'BrandB', 'BrandC', 'BrandD']
        types = ['product', 'article', 'video', 'guide']
        
        catalog = {}
        for i in range(100):
            content_id = f"content_{i}"
            catalog[content_id] = {
                'category': categories[i % len(categories)],
                'brand': brands[i % len(brands)],
                'type': types[i % len(types)],
            }
        
        return catalog
    
    def get_engine_metrics(self) -> Dict[str, Any]:
        """Get recommendation engine metrics."""
        total_recommendations = 0
        avg_score = 0.0
        algorithm_counts = defaultdict(int)
        
        # Aggregate from samples
        for profile in list(self.personalizer.profiles.values())[:100]:
            recs = self.get_recommendations(profile.user_id, limit=5)
            total_recommendations += len(recs)
            avg_score += sum(r.score for r in recs) / len(recs) if recs else 0
            for rec in recs:
                algorithm_counts[rec.algorithm] += 1
        
        return {
            'total_recommendations_generated': total_recommendations,
            'average_recommendation_score': f"{avg_score / max(1, len(self.personalizer.profiles)) :.1f}" if total_recommendations > 0 else 0,
            'algorithms_used': dict(algorithm_counts),
        }
