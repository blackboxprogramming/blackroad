#!/usr/bin/env python3
"""
Database Optimization Script for BlackRoad
Implements recommended indexes, materialized views, and connection pooling
"""

import os
import psycopg2
from sqlalchemy import create_engine, text
from datetime import datetime

class DatabaseOptimizer:
    def __init__(self, database_url):
        self.engine = create_engine(database_url)
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        self.connection = self.engine.connect()
        print("✅ Connected to database")
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
        print("✅ Disconnected from database")
    
    def create_performance_indexes(self):
        """Create recommended performance indexes"""
        print("\n📊 Creating performance indexes...")
        
        indexes = [
            # Monthly usage indexes
            {
                'name': 'idx_monthly_usage_customer_month',
                'table': 'monthly_usage',
                'columns': 'customer_id, year_month DESC'
            },
            # Charges indexes
            {
                'name': 'idx_charges_customer_created',
                'table': 'charges',
                'columns': 'customer_id, created_at DESC'
            },
            {
                'name': 'idx_charges_status_date',
                'table': 'charges',
                'columns': 'status, created_at DESC'
            },
            # Invoices indexes
            {
                'name': 'idx_invoices_status_due',
                'table': 'invoices',
                'columns': 'status, due_date ASC'
            },
            # User tier indexes
            {
                'name': 'idx_user_tiers_customer_status',
                'table': 'user_tiers',
                'columns': 'customer_id, status'
            },
        ]
        
        for idx in indexes:
            sql = f"""
            CREATE INDEX IF NOT EXISTS {idx['name']}
            ON {idx['table']}({idx['columns']});
            """
            try:
                self.connection.execute(text(sql))
                print(f"  ✅ Created index: {idx['name']}")
            except Exception as e:
                print(f"  ⚠️  Index {idx['name']}: {str(e)}")
        
        self.connection.commit()
    
    def create_materialized_views(self):
        """Create materialized views for common aggregations"""
        print("\n📊 Creating materialized views...")
        
        views = [
            {
                'name': 'mv_daily_revenue',
                'query': '''
                    SELECT 
                        created_at::date as date,
                        SUM(amount) as total_revenue,
                        COUNT(*) as transaction_count,
                        COUNT(DISTINCT customer_id) as unique_customers
                    FROM charges
                    WHERE created_at > NOW() - INTERVAL '90 days'
                    GROUP BY created_at::date
                '''
            },
            {
                'name': 'mv_tier_statistics',
                'query': '''
                    SELECT 
                        ut.tier,
                        COUNT(DISTINCT ut.customer_id) as user_count,
                        COALESCE(SUM(sc.total_revenue), 0) as total_revenue,
                        COALESCE(AVG(sc.total_revenue), 0) as avg_revenue
                    FROM user_tiers ut
                    LEFT JOIN stripe_customers sc 
                        ON ut.customer_id = sc.customer_id
                    WHERE ut.status = 'active'
                    GROUP BY ut.tier
                '''
            },
        ]
        
        for view in views:
            # Drop if exists
            sql_drop = f"DROP MATERIALIZED VIEW IF EXISTS {view['name']} CASCADE;"
            self.connection.execute(text(sql_drop))
            
            # Create view
            sql_create = f"CREATE MATERIALIZED VIEW {view['name']} AS {view['query']}"
            try:
                self.connection.execute(text(sql_create))
                print(f"  ✅ Created view: {view['name']}")
            except Exception as e:
                print(f"  ⚠️  View {view['name']}: {str(e)}")
        
        self.connection.commit()
    
    def analyze_queries(self):
        """Analyze expensive queries"""
        print("\n📊 Analyzing query performance...")
        
        queries = [
            {
                'name': 'Daily Revenue Query',
                'query': '''
                    SELECT DATE(created_at), SUM(amount)
                    FROM charges
                    GROUP BY DATE(created_at)
                    ORDER BY DATE(created_at) DESC
                    LIMIT 30
                '''
            },
        ]
        
        for q in queries:
            print(f"\n  Analyzing: {q['name']}")
            sql = f"EXPLAIN ANALYZE {q['query']}"
            try:
                result = self.connection.execute(text(sql))
                for row in result:
                    print(f"    {row[0]}")
            except Exception as e:
                print(f"    Error: {str(e)}")
    
    def get_table_stats(self):
        """Get table size and row count statistics"""
        print("\n📊 Table Statistics:")
        
        sql = text('''
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                n_live_tup as rows
            FROM pg_stat_user_tables
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        ''')
        
        result = self.connection.execute(sql)
        
        print(f"\n{'Table':<30} {'Size':<15} {'Rows':<15}")
        print("-" * 60)
        
        for row in result:
            print(f"{row[1]:<30} {row[2]:<15} {row[3]:<15}")
    
    def get_index_stats(self):
        """Get index statistics"""
        print("\n📊 Index Statistics:")
        
        sql = text('''
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes
            ORDER BY idx_scan DESC
        ''')
        
        result = self.connection.execute(sql)
        
        print(f"\n{'Index':<30} {'Scans':<15} {'Reads':<15} {'Fetches':<15}")
        print("-" * 75)
        
        for row in result:
            print(f"{row[2]:<30} {row[3]:<15} {row[4]:<15} {row[5]:<15}")
    
    def get_cache_stats(self):
        """Get cache hit statistics"""
        print("\n📊 Cache Statistics:")
        
        sql = text('''
            SELECT 
                sum(heap_blks_read) as heap_read,
                sum(heap_blks_hit) as heap_hit,
                sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
            FROM pg_statio_user_tables
        ''')
        
        result = self.connection.execute(sql).fetchone()
        
        if result[0] + result[1] > 0:
            ratio = (result[1] / (result[1] + result[0])) * 100
            print(f"  Heap reads: {result[0]}")
            print(f"  Heap hits: {result[1]}")
            print(f"  Cache hit ratio: {ratio:.2f}%")
        else:
            print("  No cache statistics available")
    
    def run_all_optimizations(self):
        """Run all optimization steps"""
        print("\n" + "="*60)
        print("BlackRoad Database Optimization")
        print("="*60)
        
        try:
            self.connect()
            self.create_performance_indexes()
            self.create_materialized_views()
            self.get_table_stats()
            self.get_index_stats()
            self.get_cache_stats()
            self.disconnect()
            
            print("\n" + "="*60)
            print("✅ Optimization complete!")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ Error during optimization: {str(e)}")
            self.disconnect()

if __name__ == '__main__':
    import sys
    
    # Get database URL from environment or command line
    db_url = os.environ.get('DATABASE_URL', 
        'postgresql://admin:password@localhost:5432/blackroad')
    
    if len(sys.argv) > 1:
        db_url = sys.argv[1]
    
    optimizer = DatabaseOptimizer(db_url)
    optimizer.run_all_optimizations()
