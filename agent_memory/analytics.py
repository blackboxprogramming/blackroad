"""Agent memory analytics."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any


@dataclass
class MemoryMetrics:
    """Memory metrics for an agent."""
    agent_id: str
    total_memories: int
    total_sessions: int
    avg_session_duration: float
    most_common_type: str
    total_accesses: int
    avg_relevance: float
    last_activity: str  # ISO timestamp
    memory_growth_24h: int
    session_growth_24h: int


class MemoryAnalytics:
    """Analytics for agent memory."""
    
    def __init__(self, memory_store):
        """Initialize analytics."""
        self.memory_store = memory_store
    
    def get_agent_metrics(self, agent_id: str) -> MemoryMetrics:
        """Get metrics for agent."""
        memories = self.memory_store.get_agent_memories(agent_id, limit=10000)
        sessions = self.memory_store.get_agent_sessions(agent_id, limit=1000)
        
        # Calculate metrics
        total_accesses = sum(m.access_count for m in memories)
        avg_relevance = sum(m.relevance_score for m in memories) / max(1, len(memories))
        
        # Session duration
        durations = [s.duration_seconds() for s in sessions if s.end_time]
        avg_duration = sum(durations) / max(1, len(durations)) if durations else 0
        
        # Most common memory type
        type_counts = defaultdict(int)
        for m in memories:
            type_counts[m.memory_type.value] += 1
        most_common = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else "unknown"
        
        # 24h growth
        cutoff_24h = datetime.utcnow() - timedelta(days=1)
        growth_24h_mem = sum(1 for m in memories if m.timestamp > cutoff_24h)
        growth_24h_ses = sum(1 for s in sessions if s.start_time > cutoff_24h)
        
        # Last activity
        last_activity = "never"
        if memories:
            last_accessed_times = [m.last_accessed for m in memories if m.last_accessed]
            if last_accessed_times:
                last_activity = max(last_accessed_times).isoformat()
        
        return MemoryMetrics(
            agent_id=agent_id,
            total_memories=len(memories),
            total_sessions=len(sessions),
            avg_session_duration=avg_duration,
            most_common_type=most_common,
            total_accesses=total_accesses,
            avg_relevance=avg_relevance,
            last_activity=last_activity,
            memory_growth_24h=growth_24h_mem,
            session_growth_24h=growth_24h_ses
        )
    
    def get_memory_timeline(self, agent_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get memory timeline."""
        memories = self.memory_store.get_agent_memories(agent_id, limit=10000)
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Group by day
        daily_counts = defaultdict(int)
        for m in memories:
            if m.timestamp > cutoff:
                day_key = m.timestamp.strftime('%Y-%m-%d')
                daily_counts[day_key] += 1
        
        # Convert to timeline
        timeline = []
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
            count = daily_counts.get(date, 0)
            timeline.append({
                'date': date,
                'memories_created': count
            })
        
        return sorted(timeline, key=lambda x: x['date'])
    
    def get_memory_distribution(self, agent_id: str) -> Dict[str, int]:
        """Get distribution of memory types."""
        memories = self.memory_store.get_agent_memories(agent_id, limit=10000)
        
        distribution = defaultdict(int)
        for m in memories:
            distribution[m.memory_type.value] += 1
        
        return dict(distribution)
    
    def get_top_tags(self, agent_id: str, limit: int = 20) -> List[tuple]:
        """Get most used tags."""
        memories = self.memory_store.get_agent_memories(agent_id, limit=10000)
        
        tag_counts = defaultdict(int)
        for m in memories:
            for tag in m.tags:
                tag_counts[tag] += 1
        
        return sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def get_learning_efficiency(self, agent_id: str) -> Dict[str, Any]:
        """Measure learning efficiency."""
        from agent_memory.store import MemoryType
        
        learnings = self.memory_store.search_by_type(MemoryType.LEARNING, agent_id, limit=100)
        
        if not learnings:
            return {'efficiency': 0, 'learnings': 0}
        
        # Score based on how recent and relevant
        scores = []
        now = datetime.utcnow()
        for learning in learnings:
            age_hours = (now - learning.timestamp).total_seconds() / 3600
            recency_score = 1.0 / (1.0 + age_hours)
            efficiency_score = learning.relevance_score * 0.6 + recency_score * 0.4
            scores.append(efficiency_score)
        
        avg_efficiency = sum(scores) / len(scores) if scores else 0
        
        return {
            'efficiency': avg_efficiency,
            'learnings': len(learnings),
            'avg_relevance': sum(l.relevance_score for l in learnings) / len(learnings),
            'recent_learnings': sum(1 for l in learnings if (now - l.timestamp).total_seconds() < 86400)
        }
    
    def get_decision_impact(self, agent_id: str) -> Dict[str, Any]:
        """Measure decision quality."""
        from agent_memory.store import MemoryType
        
        decisions = self.memory_store.search_by_type(MemoryType.DECISION, agent_id, limit=100)
        
        if not decisions:
            return {'total_decisions': 0, 'avg_impact': 0}
        
        # Score based on access count and relevance
        impacts = []
        for decision in decisions:
            impact = (decision.access_count / 10.0) + decision.relevance_score
            impacts.append(impact)
        
        avg_impact = sum(impacts) / len(impacts) if impacts else 0
        
        return {
            'total_decisions': len(decisions),
            'avg_impact': avg_impact,
            'high_impact': sum(1 for d in decisions if d.access_count > 5),
            'avg_accesses': sum(d.access_count for d in decisions) / len(decisions)
        }
    
    def compare_agents(self, agent_ids: List[str]) -> Dict[str, Any]:
        """Compare metrics across agents."""
        metrics = {}
        for agent_id in agent_ids:
            metrics[agent_id] = self.get_agent_metrics(agent_id)
        
        # Find leaders
        top_memory = max(metrics.items(), key=lambda x: x[1].total_memories)[0]
        top_sessions = max(metrics.items(), key=lambda x: x[1].total_sessions)[0]
        top_accesses = max(metrics.items(), key=lambda x: x[1].total_accesses)[0]
        
        return {
            'agents_compared': len(agent_ids),
            'metrics': {aid: {
                'total_memories': m.total_memories,
                'total_sessions': m.total_sessions,
                'total_accesses': m.total_accesses,
                'avg_relevance': m.avg_relevance
            } for aid, m in metrics.items()},
            'leaders': {
                'most_memories': top_memory,
                'most_sessions': top_sessions,
                'most_accessed': top_accesses
            }
        }
