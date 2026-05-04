"""Analytics tests."""

import unittest
from datetime import datetime, timedelta
from analytics.warehouse import DataWarehouse, FactRow, FactTable, DimensionTable
from analytics.analytics import AnalyticsEngine
from analytics.pipelines import ETLPipeline, DataValidator
from analytics.dashboard import generate_analytics_dashboard


class TestDataWarehouse(unittest.TestCase):
    def setUp(self):
        self.warehouse = DataWarehouse()
    
    def test_create_fact_table(self):
        table = self.warehouse.create_fact_table('events_fact')
        self.assertIsNotNone(table)
        self.assertEqual(self.warehouse.metrics['fact_tables'], 1)
    
    def test_create_dimension_table(self):
        table = self.warehouse.create_dimension_table('users_dim')
        self.assertIsNotNone(table)
        self.assertEqual(self.warehouse.metrics['dimension_tables'], 1)
    
    def test_insert_fact(self):
        table = self.warehouse.create_fact_table('events_fact')
        row = FactRow('f1', 20240101, 'user1', 'purchase', revenue=10.0)
        result = self.warehouse.insert_fact('events_fact', row)
        self.assertTrue(result)
        self.assertEqual(self.warehouse.metrics['total_rows'], 1)
    
    def test_fact_query(self):
        table = self.warehouse.create_fact_table('events_fact')
        row1 = FactRow('f1', 20240101, 'user1', 'purchase', revenue=10.0)
        row2 = FactRow('f2', 20240102, 'user2', 'click', revenue=0.0)
        self.warehouse.insert_fact('events_fact', row1)
        self.warehouse.insert_fact('events_fact', row2)
        
        results = table.query((20240101, 20240102))
        self.assertEqual(len(results), 2)
    
    def test_rollup_aggregation(self):
        table = self.warehouse.create_fact_table('events_fact')
        self.warehouse.insert_fact('events_fact', FactRow('f1', 20240101, 'user1', 'purchase', revenue=50.0))
        self.warehouse.insert_fact('events_fact', FactRow('f2', 20240101, 'user2', 'purchase', revenue=30.0))
        self.warehouse.insert_fact('events_fact', FactRow('f3', 20240101, 'user3', 'click', revenue=0.0))
        
        rollup = self.warehouse.compute_rollup('events_fact', ['event_type'], 'revenue')
        self.assertIn('purchase', rollup)
        self.assertAlmostEqual(rollup['purchase'], 80.0)


class TestAnalyticsEngine(unittest.TestCase):
    def setUp(self):
        self.warehouse = DataWarehouse()
        self.engine = AnalyticsEngine(self.warehouse)
    
    def test_funnel_analysis(self):
        events = [
            {'event_type': 'view', 'user_id': 'u1'},
            {'event_type': 'view', 'user_id': 'u2'},
            {'event_type': 'click', 'user_id': 'u1'},
            {'event_type': 'purchase', 'user_id': 'u1'},
        ]
        funnel = self.engine.calculate_funnel(events)
        self.assertIn('view', funnel)
        self.assertIn('purchase', funnel)
        self.assertEqual(funnel['view'], 2)
    
    def test_ltv_calculation(self):
        ltv = self.engine.calculate_ltv(revenue=100, churn_rate=0.05)
        self.assertGreater(ltv, 0)
    
    def test_arpu_calculation(self):
        arpu = self.engine.calculate_arpu(total_revenue=1000, user_count=100)
        self.assertEqual(arpu, 10.0)
    
    def test_metrics_report(self):
        self.warehouse.create_fact_table('events_fact')
        self.warehouse.insert_fact('events_fact', FactRow('f1', 20240101, 'user1', 'click', revenue=0.0))
        report = self.engine.get_metrics_report()
        self.assertIn('metrics', report)
        self.assertIn('total_events', report['metrics'])


class TestETLPipeline(unittest.TestCase):
    def setUp(self):
        self.warehouse = DataWarehouse()
        self.warehouse.create_fact_table('events_fact')
    
    def test_extract(self):
        pipeline = ETLPipeline('test_etl')
        source = [{'user_id': 'u1', 'event': 'click'}]
        extracted = pipeline.extract(source)
        self.assertEqual(len(extracted), 1)
    
    def test_transformation(self):
        pipeline = ETLPipeline('test_etl')
        pipeline.add_transformation(lambda row: {**row, 'processed': True})
        source = [{'user_id': 'u1'}]
        transformed = pipeline.transform(source)
        self.assertTrue(transformed[0]['processed'])
    
    def test_full_pipeline(self):
        pipeline = ETLPipeline('test_etl')
        pipeline.add_transformation(lambda row: {**row, 'normalized': True})
        
        source = [
            {'user_id': 'u1', 'revenue': 10.0},
            {'user_id': 'u2', 'revenue': 20.0},
        ]
        result = pipeline.run(source, self.warehouse)
        self.assertEqual(result['rows_extracted'], 2)
        self.assertEqual(result['rows_transformed'], 2)


class TestDataValidator(unittest.TestCase):
    def test_validation_rule(self):
        validator = DataValidator()
        validator.add_rule('user_id', lambda x: isinstance(x, str) and len(x) > 0)
        
        row = {'user_id': 'u1'}
        self.assertTrue(validator.validate(row))
    
    def test_validation_failure(self):
        validator = DataValidator()
        validator.add_rule('user_id', lambda x: isinstance(x, str) and len(x) > 0)
        
        row = {'user_id': ''}
        self.assertFalse(validator.validate(row))
    
    def test_batch_validation(self):
        validator = DataValidator()
        validator.add_rule('user_id', lambda x: isinstance(x, str) and len(x) > 0)
        validator.add_rule('revenue', lambda x: isinstance(x, (int, float)) and x >= 0)
        
        rows = [
            {'user_id': 'u1', 'revenue': 10.0},
            {'user_id': 'u2', 'revenue': 20.0},
        ]
        result = validator.validate_batch(rows)
        self.assertEqual(result['valid_rows'], 2)
        self.assertEqual(result['invalid_rows'], 0)


class TestDashboard(unittest.TestCase):
    def test_dashboard_generation(self):
        metrics = {
            'total_events': 1000,
            'unique_users': 100,
            'total_revenue': 5000.0,
            'fact_tables': 5,
            'dimension_tables': 3,
            'total_rows': 2000,
        }
        html = generate_analytics_dashboard(metrics)
        self.assertIn('Analytics Dashboard', html)
        self.assertIn('1,000', html)
        self.assertIn('100', html)
        self.assertIn('$5,000.00', html)


if __name__ == '__main__':
    unittest.main()
