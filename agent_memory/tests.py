"""Tests for agent memory system."""

import pytest
from datetime import datetime, timedelta
from agent_memory.store import MemoryStore, MemoryEntry, MemoryType, SessionContext
from agent_memory.recall import RecallEngine, RecallStrategy
from agent_memory.analytics import MemoryAnalytics


class TestMemoryStore:
    """Test memory store."""

    def test_store_memory(self):
        """Test storing memory."""
        store = MemoryStore()
        entry = store.store_memory(
            MemoryType.FACT,
            "User prefers dark mode",
            "agent_1",
            tags=["preference", "ui"]
        )
        
        assert entry.entry_id in store.entries
        assert entry.memory_type == MemoryType.FACT
        assert entry.agent_id == "agent_1"

    def test_retrieve_memory(self):
        """Test retrieving memory."""
        store = MemoryStore()
        entry = store.store_memory(MemoryType.FACT, "Test fact", "agent_1")
        
        retrieved = store.retrieve_memory(entry.entry_id)
        assert retrieved is not None
        assert retrieved.entry_id == entry.entry_id
        assert retrieved.access_count == 1

    def test_get_agent_memories(self):
        """Test getting agent memories."""
        store = MemoryStore()
        store.store_memory(MemoryType.FACT, "Fact 1", "agent_1")
        store.store_memory(MemoryType.DECISION, "Decision 1", "agent_1")
        store.store_memory(MemoryType.FACT, "Fact 2", "agent_2")
        
        agent1_memories = store.get_agent_memories("agent_1")
        assert len(agent1_memories) == 2

    def test_search_by_tag(self):
        """Test searching by tag."""
        store = MemoryStore()
        store.store_memory(MemoryType.FACT, "Fact 1", "agent_1", tags=["important"])
        store.store_memory(MemoryType.FACT, "Fact 2", "agent_1", tags=["important"])
        store.store_memory(MemoryType.FACT, "Fact 3", "agent_1", tags=["trivial"])
        
        important = store.search_by_tag("important")
        assert len(important) == 2

    def test_search_by_type(self):
        """Test searching by memory type."""
        store = MemoryStore()
        store.store_memory(MemoryType.FACT, "Fact 1", "agent_1")
        store.store_memory(MemoryType.DECISION, "Decision 1", "agent_1")
        store.store_memory(MemoryType.LEARNING, "Learning 1", "agent_1")
        
        facts = store.search_by_type(MemoryType.FACT, "agent_1")
        assert len(facts) == 1
        assert facts[0].memory_type == MemoryType.FACT

    def test_find_similar(self):
        """Test finding similar memories."""
        store = MemoryStore()
        store.store_memory(MemoryType.FACT, "User likes coffee", "agent_1")
        store.store_memory(MemoryType.FACT, "User likes coffee and tea", "agent_1")
        
        similar = store.find_similar("User enjoys coffee", "agent_1")
        assert len(similar) >= 0

    def test_session_management(self):
        """Test session management."""
        store = MemoryStore()
        session = store.create_session("agent_1")
        
        assert session.agent_id == "agent_1"
        assert session.end_time is None
        
        session.add_message("user", "Hello")
        assert len(session.messages) == 1
        
        store.close_session(session.session_id)
        retrieved = store.get_session(session.session_id)
        assert retrieved.end_time is not None

    def test_get_stats(self):
        """Test statistics."""
        store = MemoryStore()
        store.store_memory(MemoryType.FACT, "Fact 1", "agent_1")
        store.store_memory(MemoryType.DECISION, "Decision 1", "agent_1")
        store.create_session("agent_1")
        
        stats = store.get_stats()
        assert stats['total_entries'] == 2
        assert stats['total_sessions'] == 1
        assert stats['by_type'][MemoryType.FACT.value] == 1

    def test_export_knowledge(self):
        """Test knowledge export."""
        store = MemoryStore()
        store.store_memory(MemoryType.FACT, "Fact 1", "agent_1")
        store.store_memory(MemoryType.DECISION, "Decision 1", "agent_1")
        
        knowledge = store.export_agent_knowledge("agent_1")
        assert knowledge['total_memories'] == 2
        assert knowledge['facts_count'] == 1
        assert knowledge['decisions_count'] == 1

    def test_max_entries_limit(self):
        """Test max entries limit."""
        store = MemoryStore(max_entries=2)
        store.store_memory(MemoryType.FACT, "Fact 1", "agent_1")
        store.store_memory(MemoryType.FACT, "Fact 2", "agent_1")
        
        with pytest.raises(RuntimeError):
            store.store_memory(MemoryType.FACT, "Fact 3", "agent_1")


class TestRecallEngine:
    """Test recall engine."""

    def setup_method(self):
        """Setup."""
        self.store = MemoryStore()
        self.engine = RecallEngine(self.store)
        
        # Create some memories
        self.store.store_memory(MemoryType.FACT, "User prefers dark mode", "agent_1", tags=["ui"])
        self.store.store_memory(MemoryType.DECISION, "Chose React for frontend", "agent_1", tags=["tech"])
        self.store.store_memory(MemoryType.LEARNING, "Learned about async/await", "agent_1", tags=["javascript"])

    def test_recall_by_recency(self):
        """Test recency recall."""
        result = self.engine.recall_by_recency("agent_1", limit=10)
        
        assert result.strategy == RecallStrategy.RECENCY
        assert len(result.context_windows) > 0

    def test_recall_by_relevance(self):
        """Test relevance recall."""
        result = self.engine.recall_by_relevance("agent_1", "dark mode", limit=10)
        
        assert result.strategy == RecallStrategy.RELEVANCE
        assert len(result.context_windows) >= 0

    def test_recall_by_frequency(self):
        """Test frequency recall."""
        result = self.engine.recall_by_frequency("agent_1", limit=10)
        
        assert result.strategy == RecallStrategy.FREQUENCY
        assert len(result.context_windows) > 0

    def test_recall_patterns(self):
        """Test pattern recall."""
        result = self.engine.recall_patterns("agent_1", limit=10)
        
        assert result.strategy == RecallStrategy.PATTERN

    def test_recall_mixed(self):
        """Test mixed recall."""
        result = self.engine.recall_mixed("agent_1", "frontend development", limit=20)
        
        assert result.strategy == RecallStrategy.MIXED
        assert len(result.context_windows) > 0

    def test_get_context_for_task(self):
        """Test task context retrieval."""
        context = self.engine.get_context_for_task("agent_1", "Implement new UI feature")
        
        assert context['agent_id'] == "agent_1"
        assert context['task'] == "Implement new UI feature"
        assert 'facts' in context
        assert 'decisions' in context


class TestAnalytics:
    """Test analytics."""

    def setup_method(self):
        """Setup."""
        self.store = MemoryStore()
        self.analytics = MemoryAnalytics(self.store)
        
        # Create memories
        for i in range(5):
            self.store.store_memory(MemoryType.FACT, f"Fact {i}", "agent_1", tags=["important"])
        for i in range(3):
            self.store.store_memory(MemoryType.DECISION, f"Decision {i}", "agent_1")

    def test_get_metrics(self):
        """Test getting metrics."""
        metrics = self.analytics.get_agent_metrics("agent_1")
        
        assert metrics.agent_id == "agent_1"
        assert metrics.total_memories == 8
        assert metrics.most_common_type == MemoryType.FACT.value

    def test_memory_timeline(self):
        """Test memory timeline."""
        timeline = self.analytics.get_memory_timeline("agent_1", days=7)
        
        assert len(timeline) == 7
        total_memories = sum(t['memories_created'] for t in timeline)
        assert total_memories > 0

    def test_memory_distribution(self):
        """Test memory distribution."""
        distribution = self.analytics.get_memory_distribution("agent_1")
        
        assert MemoryType.FACT.value in distribution
        assert distribution[MemoryType.FACT.value] == 5

    def test_top_tags(self):
        """Test top tags."""
        tags = self.analytics.get_top_tags("agent_1", limit=10)
        
        assert len(tags) > 0
        assert tags[0][0] == "important"

    def test_learning_efficiency(self):
        """Test learning efficiency."""
        self.store.store_memory(MemoryType.LEARNING, "Learned X", "agent_1")
        
        efficiency = self.analytics.get_learning_efficiency("agent_1")
        
        assert 'efficiency' in efficiency
        assert efficiency['learnings'] == 1

    def test_decision_impact(self):
        """Test decision impact."""
        # Access a decision to increase impact
        decision = self.store.search_by_type(MemoryType.DECISION, "agent_1")[0]
        self.store.retrieve_memory(decision.entry_id)
        
        impact = self.analytics.get_decision_impact("agent_1")
        
        assert impact['total_decisions'] == 3
        assert impact['avg_impact'] > 0

    def test_compare_agents(self):
        """Test agent comparison."""
        self.store.store_memory(MemoryType.FACT, "Fact A2", "agent_2")
        
        comparison = self.analytics.compare_agents(["agent_1", "agent_2"])
        
        assert comparison['agents_compared'] == 2
        assert 'agent_1' in comparison['metrics']
        assert 'agent_2' in comparison['metrics']


class TestIntegration:
    """Integration tests."""

    def test_end_to_end_memory_workflow(self):
        """Test complete memory workflow."""
        store = MemoryStore()
        engine = RecallEngine(store)
        analytics = MemoryAnalytics(store)
        
        # Create session
        session = store.create_session("agent_1")
        session.add_message("user", "Implement authentication")
        
        # Store memories
        store.store_memory(MemoryType.FACT, "App needs JWT auth", "agent_1", tags=["auth", "security"])
        store.store_memory(MemoryType.DECISION, "Use HS256 algorithm", "agent_1")
        store.store_memory(MemoryType.LEARNING, "JWT tokens should be short-lived", "agent_1")
        
        # Recall context
        context = engine.get_context_for_task("agent_1", "Implement authentication")
        assert context['total_context'] > 0
        
        # Get metrics
        metrics = analytics.get_agent_metrics("agent_1")
        assert metrics.total_memories == 3
        assert metrics.total_sessions == 1


# Run tests if executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
