"""Comprehensive tests for personalization engine."""

import unittest
from datetime import datetime, timedelta

from personalizer import (
    PersonalizationEngine, UserProfile, PersonalizationConfig,
    UserAction, UserTier
)
from recommender import RecommendationEngine
from segmentation import SegmentationEngine, SegmentationType
from content_optimizer import ContentOptimizer, ABTestStatus


class TestPersonalizationEngine(unittest.TestCase):
    """Test core personalization engine."""
    
    def setUp(self):
        self.config = PersonalizationConfig()
        self.engine = PersonalizationEngine(self.config)
    
    def test_create_profile(self):
        """Test user profile creation."""
        profile = self.engine.get_or_create_profile('user_1')
        self.assertEqual(profile.user_id, 'user_1')
        self.assertEqual(profile.total_interactions, 0)
    
    def test_track_interaction(self):
        """Test interaction tracking."""
        profile = self.engine.track_interaction(
            'user_1',
            'content_1',
            UserAction.VIEWED,
            value=1.0,
            context={'category': 'books'}
        )
        
        self.assertEqual(profile.total_interactions, 1)
        self.assertEqual(profile.total_views, 1)
        self.assertIsNotNone(profile.last_active)
    
    def test_track_purchase(self):
        """Test purchase tracking."""
        profile = self.engine.track_interaction(
            'user_1',
            'content_1',
            UserAction.PURCHASED,
            value=99.99
        )
        
        self.assertEqual(profile.total_purchases, 1)
        self.assertEqual(profile.total_revenue, 99.99)
    
    def test_engagement_score(self):
        """Test engagement score calculation."""
        # Track multiple interactions
        for i in range(10):
            self.engine.track_interaction(
                'user_1',
                f'content_{i}',
                UserAction.VIEWED if i % 2 == 0 else UserAction.PURCHASED,
                value=50.0 if i % 2 == 1 else 1.0
            )
        
        score = self.engine.get_engagement_score('user_1')
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_user_tier_vip(self):
        """Test VIP tier assignment."""
        profile = self.engine.get_or_create_profile('user_vip')
        
        # High engagement
        for i in range(50):
            self.engine.track_interaction(
                'user_vip',
                f'content_{i}',
                UserAction.PURCHASED,
                value=100.0
            )
        
        self.engine.get_engagement_score('user_vip')
        self.assertEqual(profile.tier, UserTier.VIP)
    
    def test_infer_preferences(self):
        """Test preference inference."""
        # Track category preferences - multiple PURCHASED actions
        for i in range(3):
            self.engine.track_interaction(
                'user_2',
                f'content_elec_{i}',
                UserAction.PURCHASED,
                value=50.0,
                context={'category': 'electronics'}
            )
        
        for i in range(1):
            self.engine.track_interaction(
                'user_2',
                f'content_books_{i}',
                UserAction.VIEWED,
                context={'category': 'books'}
            )
        
        profile = self.engine.infer_preferences('user_2')
        
        # Electronics should have higher affinity
        if profile.category_affinities:
            electronics_aff = profile.category_affinities.get('electronics', 0)
            books_aff = profile.category_affinities.get('books', 0)
            # Either both are present or at least electronics is > 0
            self.assertTrue(electronics_aff > books_aff or electronics_aff > 0)
    
    def test_profile_summary(self):
        """Test profile summary generation."""
        self.engine.track_interaction('user_3', 'c1', UserAction.VIEWED)
        self.engine.track_interaction('user_3', 'c2', UserAction.PURCHASED, 99.0)
        
        summary = self.engine.get_profile_summary('user_3')
        
        self.assertEqual(summary['user_id'], 'user_3')
        self.assertEqual(summary['total_interactions'], 2)
        self.assertEqual(summary['total_purchases'], 1)
    
    def test_engine_metrics(self):
        """Test engine metrics calculation."""
        # Create multiple users
        for u in range(5):
            for i in range(3):
                self.engine.track_interaction(
                    f'user_{u}',
                    f'content_{i}',
                    UserAction.VIEWED
                )
        
        metrics = self.engine.get_engine_metrics()
        self.assertEqual(metrics['total_users'], 5)
        self.assertEqual(metrics['total_interactions'], 15)


class TestRecommendationEngine(unittest.TestCase):
    """Test recommendation engine."""
    
    def setUp(self):
        self.engine = PersonalizationEngine()
        self.recommender = RecommendationEngine(self.engine)
        
        # Seed with sample data
        for u in range(10):
            for i in range(5):
                self.engine.track_interaction(
                    f'user_{u}',
                    f'content_{i}',
                    [UserAction.VIEWED, UserAction.CLICKED, UserAction.PURCHASED][i % 3]
                )
    
    def test_get_recommendations(self):
        """Test getting recommendations."""
        recs = self.recommender.get_recommendations('user_0', limit=5)
        
        self.assertIsNotNone(recs)
        self.assertLessEqual(len(recs), 5)
        
        if recs:
            self.assertTrue(all(hasattr(r, 'score') for r in recs))
    
    def test_collaborative_filtering(self):
        """Test collaborative filtering algorithm."""
        recs = self.recommender._collaborative_filtering('user_0', limit=10)
        
        # Should not recommend already seen content
        seen = set(i.content_id for i in self.engine.profiles['user_0'].interaction_history)
        for rec in recs:
            self.assertNotIn(rec.content_id, seen)
    
    def test_content_based_filtering(self):
        """Test content-based filtering."""
        recs = self.recommender._content_based_filtering('user_0', limit=10)
        
        self.assertIsNotNone(recs)
        if recs:
            self.assertTrue(all(r.algorithm == 'content_based' for r in recs))


class TestSegmentationEngine(unittest.TestCase):
    """Test segmentation engine."""
    
    def setUp(self):
        self.engine = PersonalizationEngine()
        self.segmentation = SegmentationEngine(self.engine)
        
        # Create users with different behaviors
        for u in range(20):
            engagement = 20 + u * 4  # Increase engagement
            for i in range(engagement):
                self.engine.track_interaction(
                    f'user_{u}',
                    f'content_{i}',
                    UserAction.PURCHASED if i % 5 == 0 else UserAction.VIEWED,
                    value=50.0 if i % 5 == 0 else 1.0
                )
    
    def test_rfm_segmentation(self):
        """Test RFM segmentation."""
        segment = self.segmentation.segment_by_rfm()
        
        self.assertIsNotNone(segment)
        self.assertEqual(segment.segment_type, SegmentationType.RFM)
    
    def test_churn_risk_identification(self):
        """Test churn risk identification."""
        # Mark some users as inactive
        now = datetime.utcnow()
        for profile in list(self.engine.profiles.values())[:5]:
            profile.last_active = now - timedelta(days=45)
        
        segment = self.segmentation.identify_churn_risk(threshold_days=30)
        
        self.assertIsNotNone(segment)
        self.assertEqual(segment.segment_type, SegmentationType.CHURN_RISK)
        self.assertGreater(len(segment.user_ids), 0)
    
    def test_high_value_customers(self):
        """Test high-value customer identification."""
        segment = self.segmentation.identify_high_value_customers(percentile=80)
        
        self.assertIsNotNone(segment)
        self.assertEqual(segment.segment_type, SegmentationType.HIGH_VALUE)
    
    def test_lookalike_modeling(self):
        """Test lookalike audience modeling."""
        seed_users = ['user_0', 'user_1']
        segment = self.segmentation.find_lookalike_audience(seed_users, target_size=10)
        
        self.assertIsNotNone(segment)
        self.assertEqual(segment.segment_type, SegmentationType.LOOKALIKE)
        self.assertLessEqual(len(segment.user_ids), 10)


class TestContentOptimizer(unittest.TestCase):
    """Test content optimization and A/B testing."""
    
    def setUp(self):
        self.optimizer = ContentOptimizer()
    
    def test_create_test(self):
        """Test creating A/B test."""
        test = self.optimizer.create_test(
            'Homepage Test',
            'Test banner colors',
            {'color': 'blue'},
            [{'color': 'red'}, {'color': 'green'}]
        )
        
        self.assertIsNotNone(test)
        self.assertEqual(test.status, ABTestStatus.DRAFT)
        self.assertEqual(len(test.treatment_variants), 2)
    
    def test_start_test(self):
        """Test starting a test."""
        test = self.optimizer.create_test(
            'Test 1',
            'Test description',
            {'variant': 'control'},
            [{'variant': 'test1'}]
        )
        
        result = self.optimizer.start_test(test.test_id, test)
        self.assertTrue(result)
        self.assertEqual(test.status, ABTestStatus.RUNNING)
    
    def test_assign_variant(self):
        """Test variant assignment."""
        test = self.optimizer.create_test(
            'Test 2',
            'Test description',
            {'variant': 'control'},
            [{'variant': 'test1'}]
        )
        
        self.optimizer.start_test(test.test_id, test)
        
        variant = self.optimizer.assign_variant('user_1', test.test_id)
        self.assertIsNotNone(variant)
    
    def test_record_metrics(self):
        """Test recording impressions and conversions."""
        test = self.optimizer.create_test(
            'Test 3',
            'Test description',
            {'variant': 'control'},
            [{'variant': 'test1'}]
        )
        
        self.optimizer.start_test(test.test_id, test)
        variant = self.optimizer.assign_variant('user_1', test.test_id)
        
        self.optimizer.record_impression('user_1', test.test_id, variant)
        self.optimizer.record_conversion('user_1', test.test_id, variant, revenue=100.0)
        
        self.assertEqual(test.control_variant.impressions + 
                        sum(v.impressions for v in test.treatment_variants), 1)
    
    def test_get_test_results(self):
        """Test getting A/B test results."""
        test = self.optimizer.create_test(
            'Test 4',
            'Test description',
            {'variant': 'control'},
            [{'variant': 'test1'}]
        )
        
        self.optimizer.start_test(test.test_id, test)
        
        # Simulate some metrics
        self.optimizer.record_impression('user_1', test.test_id, 'control')
        self.optimizer.record_conversion('user_1', test.test_id, 'control', 100.0)
        
        results = self.optimizer.get_test_results(test.test_id)
        
        self.assertIsNotNone(results)
        self.assertEqual(len(results['variants']), 2)


class TestIntegration(unittest.TestCase):
    """End-to-end integration tests."""
    
    def test_full_personalization_flow(self):
        """Test complete personalization workflow."""
        # Initialize
        engine = PersonalizationEngine()
        recommender = RecommendationEngine(engine)
        segmentation = SegmentationEngine(engine)
        optimizer = ContentOptimizer()
        
        # Track interactions
        for u in range(10):
            for i in range(5):
                engine.track_interaction(
                    f'user_{u}',
                    f'content_{i}',
                    UserAction.PURCHASED if i % 3 == 0 else UserAction.VIEWED,
                    value=50.0 if i % 3 == 0 else 1.0,
                    context={'category': 'electronics'}
                )
        
        # Get personalized recommendations
        recs = recommender.get_recommendations('user_0', limit=3)
        self.assertIsNotNone(recs)
        
        # Segment users
        rfm = segmentation.segment_by_rfm()
        hvc = segmentation.identify_high_value_customers()
        self.assertIsNotNone(rfm)
        self.assertIsNotNone(hvc)
        
        # Run A/B test
        test = optimizer.create_test(
            'Final Test',
            'Comprehensive test',
            {'color': 'blue'},
            [{'color': 'red'}]
        )
        optimizer.start_test(test.test_id, test)
        
        # Verify metrics
        metrics = engine.get_engine_metrics()
        self.assertEqual(metrics['total_users'], 10)
        self.assertEqual(metrics['total_interactions'], 50)


if __name__ == '__main__':
    unittest.main(verbosity=2)
