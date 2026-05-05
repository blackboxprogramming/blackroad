"""GraphQL tests."""

import unittest
from graphql.schema import SchemaBuilder, FieldType, QueryExecutor, QueryPlan, ValidationEngine
from graphql.gateway import APIGateway, Request, OperationType, FieldResolver, MiddlewareChain
from graphql.subscriptions import SubscriptionManager, SubscriptionEvent, RealtimeSync
from graphql.dashboard import generate_graphql_dashboard


class TestSchemaBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = SchemaBuilder()
    
    def test_add_query(self):
        self.builder.add_query('getUser', FieldType.OBJECT, lambda x: {'id': '1', 'name': 'Alice'})
        self.assertIn('getUser', self.builder.queries)
    
    def test_add_mutation(self):
        self.builder.add_mutation('createUser', FieldType.OBJECT, lambda x: {'id': '1', 'name': 'Bob'})
        self.assertIn('createUser', self.builder.mutations)
    
    def test_build_schema(self):
        self.builder.add_query('getUser', FieldType.OBJECT, lambda x: {})
        self.builder.add_mutation('createUser', FieldType.OBJECT, lambda x: {})
        schema = self.builder.build()
        self.assertEqual(schema['query_count'], 1)
        self.assertEqual(schema['mutation_count'], 1)
    
    def test_schema_sdl(self):
        self.builder.add_query('users', FieldType.LIST, lambda x: [])
        sdl = self.builder.get_schema_sdl()
        self.assertIn('type Query', sdl)
        self.assertIn('users', sdl)


class TestQueryExecutor(unittest.TestCase):
    def setUp(self):
        self.builder = SchemaBuilder()
        self.builder.add_query('getUser', FieldType.OBJECT, lambda x: {'id': '1', 'name': 'Alice'})
        self.executor = QueryExecutor(self.builder)
    
    def test_execute_query(self):
        result = self.executor.execute('{ getUser }')
        self.assertIn('data', result)
        self.assertGreater(result['execution_time_ms'], 0)
    
    def test_empty_query(self):
        result = self.executor.execute('')
        self.assertIn('errors', result)
    
    def test_execution_time(self):
        self.executor.execute('{ getUser }')
        self.assertGreater(self.executor.execution_time_ms, 0)


class TestQueryPlan(unittest.TestCase):
    def test_analyze_simple_query(self):
        plan = QueryPlan('{ getUser }')
        analysis = plan.analyze()
        self.assertEqual(analysis['depth'], 1)
        self.assertEqual(analysis['complexity_level'], 'low')
    
    def test_analyze_nested_query(self):
        plan = QueryPlan('{ user { profile { settings } } }')
        analysis = plan.analyze()
        self.assertEqual(analysis['depth'], 3)


class TestValidationEngine(unittest.TestCase):
    def setUp(self):
        self.builder = SchemaBuilder()
        self.builder.add_query('getUser', FieldType.OBJECT, lambda x: {})
        self.validator = ValidationEngine(self.builder)
    
    def test_valid_query(self):
        is_valid = self.validator.validate('{ getUser }')
        self.assertTrue(is_valid)
    
    def test_invalid_field(self):
        is_valid = self.validator.validate('{ unknownField }')
        self.assertFalse(is_valid)
        self.assertGreater(len(self.validator.get_errors()), 0)
    
    def test_unmatched_braces(self):
        is_valid = self.validator.validate('{ getUser')
        self.assertFalse(is_valid)


class TestAPIGateway(unittest.TestCase):
    def setUp(self):
        self.gateway = APIGateway(max_depth=5, max_queries_per_batch=10)
    
    def test_handle_simple_request(self):
        req = Request(OperationType.QUERY, '{ getUser }')
        result = self.gateway.handle_request(req)
        self.assertIn('data', result)
    
    def test_deep_query_rejection(self):
        req = Request(OperationType.QUERY, '{ a { b { c { d { e { f } } } } } }')
        result = self.gateway.handle_request(req)
        self.assertIn('errors', result)
    
    def test_batch_requests(self):
        reqs = [Request(OperationType.QUERY, '{ getUser }') for _ in range(5)]
        results = self.gateway.batch_requests(reqs)
        self.assertEqual(len(results), 5)
    
    def test_gateway_metrics(self):
        req = Request(OperationType.QUERY, '{ getUser }')
        self.gateway.handle_request(req)
        metrics = self.gateway.get_metrics()
        self.assertEqual(metrics['total_requests'], 1)


class TestFieldResolver(unittest.TestCase):
    def setUp(self):
        self.resolver = FieldResolver()
    
    def test_register_resolver(self):
        self.resolver.register_resolver('getUser', lambda x: {'id': '1'})
        result = self.resolver.resolve('getUser', {})
        self.assertEqual(result['id'], '1')
    
    def test_resolve_many(self):
        self.resolver.register_resolver('getUser', lambda x: {'id': '1'})
        self.resolver.register_resolver('getOrders', lambda x: [])
        results = self.resolver.resolve_many(['getUser', 'getOrders'], {})
        self.assertIn('getUser', results)


class TestSubscriptionManager(unittest.TestCase):
    def setUp(self):
        self.manager = SubscriptionManager()
    
    def test_subscribe(self):
        callback = lambda x: None
        sub_id = self.manager.subscribe([SubscriptionEvent.USER_CREATED], callback)
        self.assertIsNotNone(sub_id)
    
    def test_unsubscribe(self):
        callback = lambda x: None
        sub_id = self.manager.subscribe([SubscriptionEvent.USER_CREATED], callback)
        result = self.manager.unsubscribe(sub_id)
        self.assertTrue(result)
    
    def test_emit_event(self):
        received = []
        def callback(data):
            received.append(data)
        
        self.manager.subscribe([SubscriptionEvent.USER_CREATED], callback)
        count = self.manager.emit(SubscriptionEvent.USER_CREATED, {'id': '1', 'name': 'Alice'})
        self.assertEqual(count, 1)
        self.assertEqual(len(received), 1)
    
    def test_subscriber_count(self):
        callback = lambda x: None
        self.manager.subscribe([SubscriptionEvent.USER_CREATED], callback)
        self.manager.subscribe([SubscriptionEvent.USER_CREATED], callback)
        count = self.manager.get_subscriber_count(SubscriptionEvent.USER_CREATED)
        self.assertEqual(count, 2)


class TestRealtimeSync(unittest.TestCase):
    def setUp(self):
        self.sync = RealtimeSync()
    
    def test_queue_sync(self):
        result = self.sync.queue_sync('User', '1', 'created', {'name': 'Alice'})
        self.assertTrue(result)
    
    def test_process_queue(self):
        self.sync.queue_sync('User', '1', 'created', {'name': 'Alice'})
        result = self.sync.process_sync_queue()
        self.assertEqual(result['synced'], 1)
    
    def test_sync_status(self):
        self.sync.queue_sync('User', '1', 'created', {})
        status = self.sync.get_sync_status()
        self.assertEqual(status['queue_size'], 1)


class TestDashboard(unittest.TestCase):
    def test_dashboard_generation(self):
        metrics = {
            'total_requests': 5000,
            'total_errors': 50,
            'avg_depth': 2.5,
            'request_log_size': 1000,
            'subscribers': 150,
        }
        html = generate_graphql_dashboard(metrics)
        self.assertIn('GraphQL API Gateway', html)
        self.assertIn('5,000', html)
        self.assertIn('150', html)


if __name__ == '__main__':
    unittest.main()
