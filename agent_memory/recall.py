"""Intelligent memory recall engine."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import math


class RecallStrategy(Enum):
    """Memory recall strategies."""
    RECENCY = "recency"
    RELEVANCE = "relevance"
    FREQUENCY = "frequency"
    PATTERN = "pattern"
    MIXED = "mixed"


@dataclass
class RecalledContext:
    """Context recalled from memory."""
    query: str
    strategy: RecallStrategy
    total_results: int
    context_windows: List[Dict[str, Any]]
    summary: str
    confidence: float = 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'query': self.query,
            'strategy': self.strategy.value,
            'total_results': self.total_results,
            'context_windows': self.context_windows,
            'summary': self.summary,
            'confidence': self.confidence
        }


class RecallEngine:
    """Intelligent memory recall for agents."""
    
    def __init__(self, memory_store):
        """Initialize recall engine."""
        self.memory_store = memory_store
    
    def recall_by_recency(self, agent_id: str, limit: int = 20, minutes: int = 120) -> RecalledContext:
        """Recall recent memories."""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        memories = [
            m for m in self.memory_store.get_agent_memories(agent_id, limit=1000)
            if m.timestamp > cutoff
        ]
        
        # Sort by most recent
        memories = sorted(memories, key=lambda m: m.timestamp, reverse=True)[:limit]
        
        context_windows = [m.to_dict() for m in memories]
        summary = f"Retrieved {len(memories)} recent memories from last {minutes} minutes"
        confidence = min(1.0, len(memories) / limit)
        
        return RecalledContext(
            query=f"Recent memories (last {minutes}min)",
            strategy=RecallStrategy.RECENCY,
            total_results=len(memories),
            context_windows=context_windows,
            summary=summary,
            confidence=confidence
        )
    
    def recall_by_relevance(self, agent_id: str, content: str, limit: int = 20) -> RecalledContext:
        """Recall relevant memories by content similarity."""
        similar = self.memory_store.find_similar(content, agent_id, limit=limit)
        
        # Score by relevance
        scored = []
        for memory in similar:
            score = memory.relevance_score
            if memory.access_count > 0:
                score += 0.2
            scored.append((memory, score))
        
        scored = sorted(scored, key=lambda x: x[1], reverse=True)
        memories = [m for m, _ in scored]
        
        context_windows = [m.to_dict() for m in memories]
        summary = f"Found {len(memories)} relevant memories matching: '{content[:50]}...'"
        confidence = min(1.0, sum(s for _, s in scored) / max(1, len(scored)))
        
        return RecalledContext(
            query=content,
            strategy=RecallStrategy.RELEVANCE,
            total_results=len(memories),
            context_windows=context_windows,
            summary=summary,
            confidence=confidence
        )
    
    def recall_by_frequency(self, agent_id: str, limit: int = 20) -> RecalledContext:
        """Recall frequently accessed memories."""
        memories = self.memory_store.get_agent_memories(agent_id, limit=1000)
        
        # Sort by access count
        memories = sorted(memories, key=lambda m: m.access_count, reverse=True)[:limit]
        
        context_windows = [m.to_dict() for m in memories]
        total_accesses = sum(m.access_count for m in memories)
        summary = f"Retrieved {len(memories)} most frequently used memories ({total_accesses} total accesses)"
        confidence = min(1.0, total_accesses / (len(memories) * 10))
        
        return RecalledContext(
            query="Most frequently accessed",
            strategy=RecallStrategy.FREQUENCY,
            total_results=len(memories),
            context_windows=context_windows,
            summary=summary,
            confidence=confidence
        )
    
    def recall_patterns(self, agent_id: str, limit: int = 20) -> RecalledContext:
        """Recall pattern-based memories."""
        from agent_memory.store import MemoryType
        
        # Get decisions and learnings (pattern-heavy)
        memories = []
        for mtype in [MemoryType.DECISION, MemoryType.LEARNING, MemoryType.REASONING]:
            memories.extend(
                self.memory_store.search_by_type(mtype, agent_id, limit=limit)
            )
        
        # Score by relevance and recency
        scored = []
        for memory in memories:
            time_weight = 1.0 / (1.0 + (datetime.utcnow() - memory.timestamp).total_seconds() / 3600)
            score = memory.relevance_score * 0.6 + time_weight * 0.4
            scored.append((memory, score))
        
        scored = sorted(scored, key=lambda x: x[1], reverse=True)[:limit]
        memories = [m for m, _ in scored]
        
        context_windows = [m.to_dict() for m in memories]
        summary = f"Detected {len(memories)} significant patterns from decisions and learnings"
        confidence = min(1.0, len(scored) / limit)
        
        return RecalledContext(
            query="Behavioral patterns",
            strategy=RecallStrategy.PATTERN,
            total_results=len(memories),
            context_windows=context_windows,
            summary=summary,
            confidence=confidence
        )
    
    def recall_mixed(self, agent_id: str, context_hint: str, limit: int = 30) -> RecalledContext:
        """Recall using mixed strategy."""
        # 30% recency + 40% relevance + 20% frequency + 10% patterns
        recency = self.recall_by_recency(agent_id, limit=int(limit * 0.3))
        relevance = self.recall_by_relevance(agent_id, context_hint, limit=int(limit * 0.4))
        frequency = self.recall_by_frequency(agent_id, limit=int(limit * 0.2))
        patterns = self.recall_patterns(agent_id, limit=int(limit * 0.1))
        
        # Combine and deduplicate
        all_contexts = (
            recency.context_windows +
            relevance.context_windows +
            frequency.context_windows +
            patterns.context_windows
        )
        
        # Remove duplicates by entry_id
        seen = set()
        unique_contexts = []
        for ctx in all_contexts:
            eid = ctx.get('entry_id')
            if eid not in seen:
                seen.add(eid)
                unique_contexts.append(ctx)
        
        # Limit
        unique_contexts = unique_contexts[:limit]
        
        avg_confidence = sum(c.confidence for c in [recency, relevance, frequency, patterns]) / 4
        
        summary = f"Retrieved {len(unique_contexts)} memories using mixed recall strategy"
        
        return RecalledContext(
            query=context_hint,
            strategy=RecallStrategy.MIXED,
            total_results=len(unique_contexts),
            context_windows=unique_contexts,
            summary=summary,
            confidence=avg_confidence
        )
    
    def get_context_for_task(self, agent_id: str, task_description: str) -> Dict[str, Any]:
        """Get optimal context for a specific task."""
        # Use mixed strategy with task description as hint
        recalled = self.recall_mixed(agent_id, task_description, limit=25)
        
        # Extract relevant memory groups
        from agent_memory.store import MemoryType
        
        facts = [c for c in recalled.context_windows if c['memory_type'] == MemoryType.FACT.value]
        decisions = [c for c in recalled.context_windows if c['memory_type'] == MemoryType.DECISION.value]
        learnings = [c for c in recalled.context_windows if c['memory_type'] == MemoryType.LEARNING.value]
        
        return {
            'agent_id': agent_id,
            'task': task_description,
            'total_context': len(recalled.context_windows),
            'facts': facts,
            'decisions': decisions,
            'learnings': learnings,
            'all_memories': recalled.context_windows,
            'confidence': recalled.confidence,
            'recommendation': f"Use {len(facts)} facts, {len(decisions)} decisions, {len(learnings)} learnings"
        }
    
    def get_session_context(self, agent_id: str, session_id: str) -> Dict[str, Any]:
        """Get context for a specific session."""
        session = self.memory_store.get_session(session_id)
        if not session:
            return {'error': 'Session not found'}
        
        return {
            'session': session.to_dict(),
            'agent_id': agent_id,
            'messages': session.messages,
            'decisions': session.decisions_made,
            'goals': session.goals_achieved,
            'errors': session.errors_encountered
        }
    
    def predict_next_action(self, agent_id: str, current_task: str) -> Dict[str, Any]:
        """Predict next action based on memory patterns."""
        from agent_memory.store import MemoryType
        
        # Get similar past decisions
        past_decisions = self.memory_store.search_by_type(MemoryType.DECISION, agent_id, limit=50)
        similar_decisions = [
            d for d in past_decisions
            if len(current_task) > 0 and current_task.lower() in d.content.lower()
        ]
        
        # Get learnings that might apply
        learnings = self.memory_store.search_by_type(MemoryType.LEARNING, agent_id, limit=30)
        
        prediction = {
            'task': current_task,
            'similar_past_cases': len(similar_decisions),
            'relevant_learnings': len(learnings),
            'past_decisions': [d.to_dict() for d in similar_decisions[:5]],
            'relevant_lessons': [l.to_dict() for l in learnings[:3]],
            'confidence': min(1.0, len(similar_decisions) / 10)
        }
        
        return prediction
