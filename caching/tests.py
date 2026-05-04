"""Caching system tests."""

import unittest
from caching.cache_engine import LRUCache, BloomFilter, QueryCache, DistributedCache, CacheWarmer, CacheMetrics
from caching.optimizer import QueryPlanner, PerformanceOptimizer, ConnectionPool, IndexType
from caching.dashboard import generate_caching_dashboard


class TestLRUCache(unittest.TestCase):
    def setUp(self):
        self.cache = LRUCache(max_size=3)
    
    def test_set_and_get(self):
        self.cache.set('key1', 'value1')
        self.assertEqual(self.cache.get('key1'), 'value1')
    
    def test_ttl_expiration(self):
        self.cache.set('key1', 'value1', ttl=0)
        self.assertIsNone(self.cache.get('key1'))
    
    def test_lru_eviction(self):
        self.cache.set('k1', 'v1')
        self.cache.set('k2', 'v2')
        self.cache.set('k3', 'v3')
        self.cache.set('k4', 'v4')  # Should evict k1
        
        self.assertIsNone(self.cache.get('k1'))
        self.assertIsNotNone(self.cache.get('k4'))
    
    def test_hit_rate(self):
        self.cache.set('k1', 'v1')
        self.cache.get('k1')
        self.cache.get('k1')
        self.cache.get('missing')
        
        hit_rate = self.cache.get_hit_rate()
        self.assertGreater(hit_rate, 50)
    
    def test_stats(self):
        self.cache.set('k1', 'v1')
        stats = self.cache.get_stats()
        self.assertEqual(stats['size'], 1)
        self.assertEqual(stats['max_size'], 3)


class TestBloomFilter(unittest.TestCase):
    def test_add_and_contains(self):
        bf = BloomFilter(size=100, num_hashes=3)
        bf.add('item1')
        self.assertTrue(bf.contains('item1'))
    
    def test_not_contains(self):
        bf = BloomFilter(size=100, num_hashes=3)
        bf.add('item1')
        # Bloom filter allows false positives but not false negatives
        self.assertFalse(bf.contains('definitely_not_added'))
    
    def test_multiple_items(self):
        bf = BloomFilter(size=100, num_hashes=3)
        items = ['item1', 'item2', 'item3']
        for item in items:
            bf.add(item)
        
        for item in items:
            self.assertTrue(bf.contains(item))


class TestQueryCache(unittest.TestCase):
    def setUp(self):
        self.qcache = QueryCache(cache_size=10)
    
    def test_cache_query_result(self):
        result = {'rows': [1, 2, 3]}
        self.qcache.set_query_result('SELECT * FROM users', result)
        cached = self.qcache.get_query_result('SELECT * FROM users')
        self.assertEqual(cached, result)
    
    def test_invalidate_by_table(self):
        self.qcache.set_query_result('SELECT * FROM users', {'rows': []})
        self.qcache.set_query_result('SELECT * FROM products', {'rows': []})
        
        count = self.qcache.invalidate_by_table('users')
        self.assertGreater(count, 0)


class TestDistributedCache(unittest.TestCase):
    def test_replicate(self):
        dc = DistributedCache('node1')
        result = dc.replicate('key1', 'value1')
        self.assertTrue(result)
    
    def test_sync_status(self):
        dc = DistributedCache('node1')
        dc.replicate('k1', 'v1')
        status = dc.get_sync_status()
        self.assertEqual(status['node_id'], 'node1')
        self.assertGreater(status['sync_events'], 0)


class TestCacheWarmer(unittest.TestCase):
    def test_warm_cache(self):
        cache = LRUCache()
        warmer = CacheWarmer(cache)
        
        def loader():
            return {'k1': 'v1', 'k2': 'v2', 'k3': 'v3'}
        
        warmer.add_strategy('test_strategy', loader)
        result = warmer.warm_cache('test_strategy')
        self.assertEqual(result['items_loaded'], 3)


class TestCacheMetrics(unittest.TestCase):
    def test_metrics_tracking(self):
        metrics = CacheMetrics()
        metrics.record_hit()
        metrics.record_hit()
        metrics.record_miss()
        
        result = metrics.get_metrics()
        self.assertEqual(result['total_hits'], 2)
        self.assertEqual(result['total_misses'], 1)
        self.assertGreater(result['hit_rate_percent'], 50)


class TestQueryPlanner(unittest.TestCase):
    def setUp(self):
        self.planner = QueryPlanner()
    
    def test_add_index(self):
        result = self.planner.add_index('idx_users_id', 'users', ['id'], IndexType.BTREE)
        self.assertTrue(result)
    
    def test_plan_query(self):
        self.planner.set_table_stats('users', 1000, 256)
        plan = self.planner.plan_query('SELECT * FROM users', ['users'])
        self.assertGreater(plan.estimated_cost, 0)
        self.assertIn('scan(users)', plan.operations)


class TestPerformanceOptimizer(unittest.TestCase):
    def test_analyze_slow_queries(self):
        optimizer = PerformanceOptimizer()
        queries = [
            {'table': 'users', 'duration_ms': 50},
            {'table': 'orders', 'duration_ms': 150},
            {'table': 'products', 'duration_ms': 200},
        ]
        slow = optimizer.analyze_slow_queries(queries)
        self.assertEqual(len(slow), 2)
    
    def test_recommendations(self):
        optimizer = PerformanceOptimizer()
        queries = [{'table': 'users', 'duration_ms': 150}]
        optimizer.analyze_slow_queries(queries)
        recs = optimizer.get_recommendations()
        self.assertGreater(len(recs), 0)


class TestConnectionPool(unittest.TestCase):
    def test_get_and_release(self):
        pool = ConnectionPool(max_connections=5)
        self.assertTrue(pool.get_connection())
        self.assertTrue(pool.get_connection())
        self.assertTrue(pool.release_connection())
    
    def test_pool_exhaustion(self):
        pool = ConnectionPool(max_connections=2)
        pool.get_connection()
        pool.get_connection()
        self.assertFalse(pool.get_connection())
    
    def test_pool_status(self):
        pool = ConnectionPool(max_connections=10)
        pool.get_connection()
        pool.get_connection()
        status = pool.get_status()
        self.assertEqual(status['max_connections'], 10)
        self.assertGreater(status['utilization_percent'], 0)


class TestDashboard(unittest.TestCase):
    def test_dashboard_generation(self):
        metrics = {
            'hit_rate': 85.5,
            'total_hits': 8550,
            'total_misses': 1450,
            'total_evictions': 100,
            'total_invalidations': 50,
            'cache_size': 500,
        }
        html = generate_caching_dashboard(metrics)
        self.assertIn('Caching Performance Dashboard', html)
        self.assertIn('85.5', html)
        self.assertIn('8,550', html)


if __name__ == '__main__':
    unittest.main()
