"""Feature flags tests."""

import unittest
from datetime import datetime
from feature_flags.engine import (
    FlagEngine, FeatureFlag, Context, FlagType, FlagStatus, FlagEvaluator, FlagStore
)
from feature_flags.targeting import (
    TargetingEngine, TargetingRule, RuleOperator, Segment, SegmentManager
)
from feature_flags.analytics import FlagMetrics, AnalyticsCollector
from feature_flags.dashboard import generate_feature_flags_dashboard


class TestFeatureFlag(unittest.TestCase):
    def test_create_flag(self):
        flag = FeatureFlag(
            flag_id='new_feature',
            name='New Feature',
            description='A new experimental feature',
            flag_type=FlagType.BOOLEAN,
            status=FlagStatus.DEVELOPMENT
        )
        self.assertEqual(flag.flag_id, 'new_feature')
        self.assertEqual(flag.flag_type, FlagType.BOOLEAN)


class TestFlagStore(unittest.TestCase):
    def setUp(self):
        self.store = FlagStore()
    
    def test_create_flag(self):
        flag = FeatureFlag(
            flag_id='test_flag',
            name='Test',
            description='',
            flag_type=FlagType.BOOLEAN,
            status=FlagStatus.DEVELOPMENT
        )
        result = self.store.create_flag(flag)
        self.assertTrue(result)
    
    def test_get_flag(self):
        flag = FeatureFlag(
            flag_id='test_flag',
            name='Test',
            description='',
            flag_type=FlagType.BOOLEAN,
            status=FlagStatus.DEVELOPMENT
        )
        self.store.create_flag(flag)
        retrieved = self.store.get_flag('test_flag')
        self.assertIsNotNone(retrieved)
    
    def test_enable_disable(self):
        flag = FeatureFlag(
            flag_id='test',
            name='Test',
            description='',
            flag_type=FlagType.BOOLEAN,
            status=FlagStatus.DEVELOPMENT,
            enabled=False
        )
        self.store.create_flag(flag)
        
        self.store.enable_flag('test')
        flag = self.store.get_flag('test')
        self.assertTrue(flag.enabled)
        
        self.store.disable_flag('test')
        flag = self.store.get_flag('test')
        self.assertFalse(flag.enabled)
    
    def test_list_flags(self):
        for i in range(3):
            flag = FeatureFlag(
                flag_id=f'flag_{i}',
                name=f'Flag {i}',
                description='',
                flag_type=FlagType.BOOLEAN,
                status=FlagStatus.PRODUCTION if i > 0 else FlagStatus.DEVELOPMENT
            )
            self.store.create_flag(flag)
        
        prod_flags = self.store.list_flags(FlagStatus.PRODUCTION)
        self.assertEqual(len(prod_flags), 2)


class TestFlagEvaluator(unittest.TestCase):
    def setUp(self):
        self.evaluator = FlagEvaluator()
    
    def test_evaluate_disabled_flag(self):
        flag = FeatureFlag(
            flag_id='test',
            name='Test',
            description='',
            flag_type=FlagType.BOOLEAN,
            status=FlagStatus.DEVELOPMENT,
            enabled=False
        )
        context = Context(user_id='user1')
        result = self.evaluator.evaluate(flag, context)
        self.assertFalse(result)
    
    def test_evaluate_boolean_flag(self):
        flag = FeatureFlag(
            flag_id='test',
            name='Test',
            description='',
            flag_type=FlagType.BOOLEAN,
            status=FlagStatus.DEVELOPMENT,
            enabled=True
        )
        context = Context(user_id='user1')
        result = self.evaluator.evaluate(flag, context)
        self.assertTrue(result)
    
    def test_evaluate_percentage_flag(self):
        flag = FeatureFlag(
            flag_id='test',
            name='Test',
            description='',
            flag_type=FlagType.PERCENTAGE,
            status=FlagStatus.DEVELOPMENT,
            enabled=True,
            percentage=50.0
        )
        context = Context(user_id='user1')
        result = self.evaluator.evaluate(flag, context)
        self.assertIsInstance(result, bool)
    
    def test_get_variant(self):
        flag = FeatureFlag(
            flag_id='test',
            name='Test',
            description='',
            flag_type=FlagType.MULTI_VARIANT,
            status=FlagStatus.DEVELOPMENT,
            enabled=True,
            variants={'control': {}, 'treatment_a': {}, 'treatment_b': {}}
        )
        context = Context(user_id='user1')
        variant = self.evaluator.get_variant(flag, context)
        self.assertIn(variant, flag.variants.keys())


class TestFlagEngine(unittest.TestCase):
    def setUp(self):
        self.engine = FlagEngine()
    
    def test_create_flag(self):
        flag = self.engine.create_flag(
            flag_id='new_feature',
            name='New Feature',
            flag_type=FlagType.BOOLEAN
        )
        self.assertIsNotNone(flag)
    
    def test_is_enabled(self):
        flag = self.engine.create_flag(
            flag_id='feature',
            name='Feature',
            flag_type=FlagType.BOOLEAN
        )
        self.engine.store.enable_flag('feature')
        
        context = Context(user_id='user1')
        result = self.engine.is_enabled('feature', context)
        self.assertTrue(result)


class TestTargetingEngine(unittest.TestCase):
    def setUp(self):
        self.engine = TargetingEngine()
    
    def test_add_rule(self):
        rule = TargetingRule(
            rule_id='r1',
            attribute='country',
            operator=RuleOperator.EQUALS,
            value='US'
        )
        result = self.engine.add_rule('flag1', rule)
        self.assertTrue(result)
    
    def test_evaluate_equals(self):
        rule = TargetingRule(
            rule_id='r1',
            attribute='tier',
            operator=RuleOperator.EQUALS,
            value='premium'
        )
        self.engine.add_rule('flag1', rule)
        
        context = {'tier': 'premium'}
        result = self.engine.evaluate_rules('flag1', context)
        self.assertTrue(result)
    
    def test_evaluate_in_list(self):
        rule = TargetingRule(
            rule_id='r1',
            attribute='country',
            operator=RuleOperator.IN,
            value=['US', 'CA', 'MX']
        )
        self.engine.add_rule('flag1', rule)
        
        context = {'country': 'CA'}
        result = self.engine.evaluate_rules('flag1', context)
        self.assertTrue(result)


class TestSegmentManager(unittest.TestCase):
    def setUp(self):
        self.manager = SegmentManager()
    
    def test_create_segment(self):
        segment = self.manager.create_segment('seg1', 'Premium Users')
        self.assertIsNotNone(segment)
    
    def test_get_segments_for_user(self):
        segment = self.manager.create_segment('premium', 'Premium')
        rule = TargetingRule(
            rule_id='r1',
            attribute='tier',
            operator=RuleOperator.EQUALS,
            value='premium'
        )
        segment.add_rule(rule)
        
        context = {'tier': 'premium'}
        segments = self.manager.get_segments_for_user(context)
        self.assertIn('premium', segments)


class TestFlagMetrics(unittest.TestCase):
    def test_record_evaluation(self):
        metrics = FlagMetrics('flag1')
        metrics.record_evaluation(True, user_id='user1')
        metrics.record_evaluation(False, user_id='user2')
        
        m = metrics.get_metrics()
        self.assertEqual(m['total_evaluations'], 2)
        self.assertEqual(m['enabled_count'], 1)
        self.assertEqual(m['disabled_count'], 1)


class TestAnalyticsCollector(unittest.TestCase):
    def setUp(self):
        self.collector = AnalyticsCollector()
    
    def test_record_evaluation(self):
        self.collector.record_evaluation('flag1', True, {'user_id': 'user1'})
        self.assertEqual(self.collector.get_event_count(), 1)
    
    def test_get_flag_metrics(self):
        self.collector.record_evaluation('flag1', True, {'user_id': 'user1'})
        self.collector.record_evaluation('flag1', False, {'user_id': 'user2'})
        
        metrics = self.collector.get_flag_metrics('flag1')
        self.assertEqual(metrics['total_evaluations'], 2)
    
    def test_top_flags(self):
        for i in range(5):
            self.collector.record_evaluation('flag1', True)
        for i in range(3):
            self.collector.record_evaluation('flag2', True)
        
        top = self.collector.get_top_flags_by_usage(1)
        self.assertEqual(top[0]['flag_id'], 'flag1')


class TestDashboard(unittest.TestCase):
    def test_dashboard_generation(self):
        metrics = {
            'total_flags': 50,
            'enabled_flags': 35,
            'enabled_rate': 70.0,
            'total_evaluations': 10000,
            'segments': 15,
            'rules': 45,
        }
        html = generate_feature_flags_dashboard(metrics)
        self.assertIn('Feature Flags', html)
        self.assertIn('50', html)
        self.assertIn('70.0', html)


if __name__ == '__main__':
    unittest.main()
