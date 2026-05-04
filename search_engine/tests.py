"""Tests for search engine."""

import pytest
import time
from search_engine.index import SearchIndex, TextProcessor, Document, DocumentType
from search_engine.query import QueryEngine, SearchResult
from search_engine.analytics import SearchAnalytics


class TestTextProcessor:
    """Test text processing."""

    def test_tokenize(self):
        """Test tokenization."""
        text = "Hello, world! This is a test."
        tokens = TextProcessor.tokenize(text)
        assert 'hello' in tokens
        assert 'world' in tokens
        assert 'test' in tokens

    def test_remove_stopwords(self):
        """Test stopword removal."""
        tokens = ['the', 'quick', 'brown', 'fox', 'jumps']
        filtered = TextProcessor.remove_stopwords(tokens)
        assert 'the' not in filtered
        assert 'quick' in filtered
        assert 'fox' in filtered

    def test_stem(self):
        """Test stemming."""
        assert TextProcessor.stem('running') == 'runn'
        assert TextProcessor.stem('played') == 'play'
        assert TextProcessor.stem('cats') == 'cat'

    def test_process(self):
        """Test full text processing."""
        text = "The quick brown fox jumps over the lazy dog"
        tokens = TextProcessor.process(text)
        # Should remove stopwords, lowercase, stem
        assert 'quick' in tokens or 'quic' in tokens  # May be stemmed
        assert 'the' not in tokens  # Stopword


class TestSearchIndex:
    """Test search index."""

    def test_create_index(self):
        """Test creating index."""
        index = SearchIndex()
        assert len(index.documents) == 0
        assert len(index.inverted_index) == 0

    def test_add_document(self):
        """Test adding document."""
        index = SearchIndex()
        doc = index.add_document('doc1', 'Test Document', 'This is a test document')
        
        assert doc.doc_id == 'doc1'
        assert 'doc1' in index.documents

    def test_add_multiple_documents(self):
        """Test adding multiple documents."""
        index = SearchIndex()
        index.add_document('doc1', 'Python Guide', 'Learn Python programming')
        index.add_document('doc2', 'Java Guide', 'Learn Java programming')
        index.add_document('doc3', 'Python Tips', 'Advanced Python tips')
        
        assert len(index.documents) == 3

    def test_get_document(self):
        """Test retrieving document."""
        index = SearchIndex()
        index.add_document('doc1', 'Test', 'Content')
        
        doc = index.get_document('doc1')
        assert doc is not None
        assert doc.title == 'Test'

    def test_update_document(self):
        """Test updating document."""
        index = SearchIndex()
        index.add_document('doc1', 'Original', 'Original content')
        index.add_document('doc1', 'Updated', 'Updated content')
        
        doc = index.get_document('doc1')
        assert doc.title == 'Updated'

    def test_delete_document(self):
        """Test deleting document."""
        index = SearchIndex()
        index.add_document('doc1', 'Test', 'Content')
        
        result = index.delete_document('doc1')
        assert result is True
        assert index.get_document('doc1') is None

    def test_inverted_index_creation(self):
        """Test inverted index is created."""
        index = SearchIndex()
        index.add_document('doc1', 'Python Programming', 'Learn Python')
        
        # Should have terms in inverted index
        assert len(index.inverted_index) > 0

    def test_index_stats(self):
        """Test index statistics."""
        index = SearchIndex()
        index.add_document('doc1', 'Test', 'This is a test document')
        index.add_document('doc2', 'Example', 'This is an example document')
        
        stats = index.get_stats()
        assert stats['total_documents'] == 2
        assert stats['total_terms'] > 0

    def test_document_boost(self):
        """Test document boost factor."""
        index = SearchIndex()
        doc = index.add_document('doc1', 'Test', 'Content', boost=2.0)
        assert doc.boost == 2.0

    def test_metadata(self):
        """Test document metadata."""
        index = SearchIndex()
        metadata = {'author': 'John', 'category': 'tech'}
        doc = index.add_document('doc1', 'Test', 'Content', metadata=metadata)
        
        assert doc.metadata['author'] == 'John'
        assert doc.metadata['category'] == 'tech'

    def test_max_documents_limit(self):
        """Test max documents limit."""
        index = SearchIndex(max_documents=2)
        index.add_document('doc1', 'Test1', 'Content1')
        index.add_document('doc2', 'Test2', 'Content2')
        
        with pytest.raises(RuntimeError):
            index.add_document('doc3', 'Test3', 'Content3')


class TestQueryEngine:
    """Test query engine."""

    def setup_method(self):
        """Setup test index."""
        self.index = SearchIndex()
        self.index.add_document('doc1', 'Python Programming', 'Learn Python programming basics')
        self.index.add_document('doc2', 'Java Guide', 'Complete Java guide for beginners')
        self.index.add_document('doc3', 'Python Advanced', 'Advanced Python programming techniques')
        self.index.add_document('doc4', 'Web Development', 'Build websites with HTML CSS JavaScript')
        self.engine = QueryEngine(self.index)

    def test_search_basic(self):
        """Test basic search."""
        results = self.engine.search('Python')
        assert len(results) > 0
        assert any('Python' in r.title for r in results)

    def test_search_multiple_terms(self):
        """Test search with multiple terms."""
        results = self.engine.search('Python programming')
        assert len(results) > 0

    def test_search_or_operator(self):
        """Test OR search (default)."""
        results = self.engine.search('Python Java', require_all=False)
        assert len(results) > 0

    def test_search_and_operator(self):
        """Test AND search."""
        results = self.engine.search('Python programming', require_all=True)
        assert len(results) > 0

    def test_search_no_results(self):
        """Test search with no results."""
        results = self.engine.search('NonexistentTerm12345')
        assert len(results) == 0

    def test_search_empty_query(self):
        """Test search with empty query."""
        results = self.engine.search('')
        assert len(results) == 0

    def test_search_limit(self):
        """Test search result limit."""
        results = self.engine.search('programming', limit=2)
        assert len(results) <= 2

    def test_phrase_search(self):
        """Test phrase search."""
        results = self.engine.phrase_search('Python programming')
        # Should find exact phrase
        assert any('Python' in r.title for r in results)

    def test_suggestions(self):
        """Test search suggestions."""
        suggestions = self.engine.get_suggestions('pyt')
        assert len(suggestions) > 0

    def test_search_result_ranking(self):
        """Test result ranking by relevance."""
        results = self.engine.search('Python')
        # Results should be sorted by score descending
        if len(results) > 1:
            assert results[0].score >= results[1].score

    def test_search_result_content(self):
        """Test search result contains required fields."""
        results = self.engine.search('programming')
        
        if results:
            result = results[0]
            assert hasattr(result, 'doc_id')
            assert hasattr(result, 'title')
            assert hasattr(result, 'content_preview')
            assert hasattr(result, 'score')
            assert result.score > 0


class TestSearchAnalytics:
    """Test search analytics."""

    def test_create_analytics(self):
        """Test creating analytics."""
        analytics = SearchAnalytics()
        assert analytics.metrics['total_searches'] == 0

    def test_record_search(self):
        """Test recording search."""
        analytics = SearchAnalytics()
        query = analytics.record_search('python', 5, 12.5)
        
        assert query.query == 'python'
        assert query.result_count == 5
        assert analytics.metrics['total_searches'] == 1

    def test_record_multiple_searches(self):
        """Test recording multiple searches."""
        analytics = SearchAnalytics()
        analytics.record_search('python', 10, 5.0)
        analytics.record_search('java', 8, 6.0)
        analytics.record_search('python', 12, 4.5)
        
        assert analytics.metrics['total_searches'] == 3

    def test_zero_result_queries(self):
        """Test tracking zero result queries."""
        analytics = SearchAnalytics()
        analytics.record_search('python', 10, 5.0)
        analytics.record_search('xyz', 0, 3.0)
        analytics.record_search('java', 8, 6.0)
        
        assert analytics.metrics['zero_result_searches'] == 1

    def test_trending_queries(self):
        """Test trending queries."""
        analytics = SearchAnalytics()
        analytics.record_search('python', 5, 5.0)
        analytics.record_search('python', 10, 5.0)
        analytics.record_search('java', 8, 6.0)
        analytics.record_search('python', 12, 4.5)
        
        trending = analytics.get_trending_queries(5)
        assert trending[0][0] == 'python'
        assert trending[0][1] == 3

    def test_query_performance(self):
        """Test query performance metrics."""
        analytics = SearchAnalytics()
        analytics.record_search('python', 5, 5.0)
        analytics.record_search('java', 8, 3.0)
        analytics.record_search('go', 2, 7.0)
        
        perf = analytics.get_query_performance()
        assert perf['total_searches'] == 3
        assert perf['avg_exec_time_ms'] > 0
        assert perf['avg_result_count'] > 0

    def test_query_types_breakdown(self):
        """Test query types breakdown."""
        analytics = SearchAnalytics()
        analytics.record_search('python', 5, 5.0, query_type='normal')
        analytics.record_search('python tutorial', 8, 6.0, query_type='phrase')
        analytics.record_search('pyt', 0, 2.0, query_type='suggest')
        
        breakdown = analytics.get_query_types_breakdown()
        assert 'normal' in breakdown
        assert 'phrase' in breakdown
        assert 'suggest' in breakdown

    def test_zero_result_queries_list(self):
        """Test getting zero result queries."""
        analytics = SearchAnalytics()
        analytics.record_search('xyz', 0, 3.0)
        analytics.record_search('abc', 0, 2.0)
        analytics.record_search('python', 5, 5.0)
        
        zero_queries = analytics.get_zero_result_queries(5)
        assert 'xyz' in zero_queries or 'abc' in zero_queries

    def test_recent_queries(self):
        """Test getting recent queries."""
        analytics = SearchAnalytics()
        analytics.record_search('python', 5, 5.0)
        analytics.record_search('java', 8, 6.0)
        
        recent = analytics.get_recent_queries(10)
        assert len(recent) == 2

    def test_metrics_summary(self):
        """Test getting all metrics."""
        analytics = SearchAnalytics()
        analytics.record_search('python', 5, 5.0)
        analytics.record_search('java', 8, 6.0)
        
        metrics = analytics.get_metrics()
        assert 'queries_recorded' in metrics
        assert 'total_searches' in metrics
        assert 'performance' in metrics
        assert 'query_types' in metrics


class TestSearchEngineIntegration:
    """Integration tests."""

    def test_end_to_end_search(self):
        """Test end-to-end search workflow."""
        index = SearchIndex()
        
        # Add documents
        index.add_document('doc1', 'Python Tutorial', 'Learn Python programming step by step')
        index.add_document('doc2', 'Java Tutorial', 'Complete Java programming guide')
        index.add_document('doc3', 'Python Advanced', 'Advanced Python techniques and best practices')
        
        # Create query engine
        engine = QueryEngine(index)
        
        # Search
        results = engine.search('Python', limit=10)
        
        assert len(results) > 0
        assert results[0].score > 0

    def test_search_with_analytics(self):
        """Test search with analytics tracking."""
        index = SearchIndex()
        index.add_document('doc1', 'Test', 'Content')
        
        engine = QueryEngine(index)
        analytics = SearchAnalytics()
        
        # Perform search
        start = time.time()
        results = engine.search('test')
        exec_time = (time.time() - start) * 1000
        
        # Record analytics
        analytics.record_search('test', len(results), exec_time)
        
        assert analytics.metrics['total_searches'] == 1

    def test_multiple_document_types(self):
        """Test with different document types."""
        index = SearchIndex()
        
        index.add_document('doc1', 'Text Doc', 'Some text content', doc_type=DocumentType.TEXT)
        index.add_document('doc2', 'HTML Doc', '<html>Content</html>', doc_type=DocumentType.HTML)
        index.add_document('doc3', 'JSON Doc', '{"key": "value"}', doc_type=DocumentType.JSON)
        
        engine = QueryEngine(index)
        results = engine.search('content')
        
        assert len(results) > 0


# Run tests if executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
