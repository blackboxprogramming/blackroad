"""Agent memory and context management system."""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import hashlib
import json


class MemoryType(Enum):
    """Types of memories."""
    CONVERSATION = "conversation"
    FACT = "fact"
    DECISION = "decision"
    REASONING = "reasoning"
    LEARNING = "learning"
    ERROR = "error"


class RelevanceType(Enum):
    """How memory is relevant."""
    DIRECT = "direct"
    CONTEXTUAL = "contextual"
    HISTORICAL = "historical"
    PATTERN = "pattern"


@dataclass
class MemoryEntry:
    """Single memory entry."""
    entry_id: str
    memory_type: MemoryType
    content: str
    agent_id: str
    timestamp: datetime
    tags: List[str] = field(default_factory=list)
    related_entries: List[str] = field(default_factory=list)
    relevance_score: float = 0.0
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    embedding_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'entry_id': self.entry_id,
            'memory_type': self.memory_type.value,
            'content': self.content,
            'agent_id': self.agent_id,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags,
            'relevance_score': self.relevance_score,
            'access_count': self.access_count,
            'metadata': self.metadata
        }
    
    def calculate_embedding_hash(self) -> str:
        """Calculate hash for semantic similarity."""
        content_bytes = self.content.encode('utf-8')
        return hashlib.sha256(content_bytes).hexdigest()


@dataclass
class SessionContext:
    """Context for a session."""
    session_id: str
    agent_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    messages: List[Dict[str, str]] = field(default_factory=list)
    decisions_made: List[str] = field(default_factory=list)
    errors_encountered: List[str] = field(default_factory=list)
    goals_achieved: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str):
        """Add message to session."""
        self.messages.append({
            'timestamp': datetime.utcnow().isoformat(),
            'role': role,
            'content': content
        })
    
    def close(self):
        """Close session."""
        self.end_time = datetime.utcnow()
    
    def duration_seconds(self) -> float:
        """Get session duration."""
        end = self.end_time or datetime.utcnow()
        return (end - self.start_time).total_seconds()
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'session_id': self.session_id,
            'agent_id': self.agent_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.duration_seconds(),
            'message_count': len(self.messages),
            'decisions': self.decisions_made,
            'goals': self.goals_achieved,
            'errors': self.errors_encountered
        }


class MemoryStore:
    """Persistent memory storage for agents."""
    
    def __init__(self, max_entries: int = 50000):
        """Initialize memory store."""
        self.max_entries = max_entries
        self.entries: Dict[str, MemoryEntry] = {}
        self.sessions: Dict[str, SessionContext] = {}
        self.agent_memories: Dict[str, List[str]] = {}  # agent_id -> entry_ids
        self.tags_index: Dict[str, List[str]] = {}  # tag -> entry_ids
        self.stats = {
            'total_entries': 0,
            'total_sessions': 0,
            'by_type': {mt.value: 0 for mt in MemoryType}
        }
    
    def store_memory(self, memory_type: MemoryType, content: str, agent_id: str,
                    tags: List[str] = None, metadata: Dict = None) -> MemoryEntry:
        """Store a memory entry."""
        if len(self.entries) >= self.max_entries:
            raise RuntimeError(f"Memory store limit exceeded: {self.max_entries}")
        
        tags = tags or []
        metadata = metadata or {}
        entry_id = f"mem_{len(self.entries)}_{int(datetime.utcnow().timestamp() * 1000)}"
        
        entry = MemoryEntry(
            entry_id=entry_id,
            memory_type=memory_type,
            content=content,
            agent_id=agent_id,
            timestamp=datetime.utcnow(),
            tags=tags,
            metadata=metadata
        )
        entry.embedding_hash = entry.calculate_embedding_hash()
        
        self.entries[entry_id] = entry
        
        # Update indexes
        if agent_id not in self.agent_memories:
            self.agent_memories[agent_id] = []
        self.agent_memories[agent_id].append(entry_id)
        
        for tag in tags:
            if tag not in self.tags_index:
                self.tags_index[tag] = []
            self.tags_index[tag].append(entry_id)
        
        # Update stats
        self.stats['total_entries'] += 1
        self.stats['by_type'][memory_type.value] += 1
        
        return entry
    
    def retrieve_memory(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a specific memory."""
        if entry_id in self.entries:
            entry = self.entries[entry_id]
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()
            entry.relevance_score = min(1.0, entry.relevance_score + 0.01)
            return entry
        return None
    
    def get_agent_memories(self, agent_id: str, limit: int = 100) -> List[MemoryEntry]:
        """Get all memories for an agent."""
        if agent_id not in self.agent_memories:
            return []
        
        entry_ids = self.agent_memories[agent_id][-limit:]
        return [self.entries[eid] for eid in entry_ids if eid in self.entries]
    
    def search_by_tag(self, tag: str, limit: int = 50) -> List[MemoryEntry]:
        """Search memories by tag."""
        if tag not in self.tags_index:
            return []
        
        entry_ids = self.tags_index[tag][-limit:]
        return [self.entries[eid] for eid in entry_ids if eid in self.entries]
    
    def search_by_type(self, memory_type: MemoryType, agent_id: str = None, limit: int = 50) -> List[MemoryEntry]:
        """Search memories by type."""
        results = []
        for entry in self.entries.values():
            if entry.memory_type == memory_type:
                if agent_id is None or entry.agent_id == agent_id:
                    results.append(entry)
        
        return sorted(results, key=lambda e: e.timestamp, reverse=True)[:limit]
    
    def find_similar(self, content: str, agent_id: str, limit: int = 10) -> List[MemoryEntry]:
        """Find similar memories."""
        target_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        agent_entries = self.get_agent_memories(agent_id, limit=1000)
        similar = []
        
        for entry in agent_entries:
            # Simple hash similarity (first 8 chars match)
            if entry.embedding_hash[:8] == target_hash[:8]:
                similar.append(entry)
        
        return sorted(similar, key=lambda e: e.relevance_score, reverse=True)[:limit]
    
    def create_session(self, agent_id: str) -> SessionContext:
        """Create new session for agent."""
        session_id = f"sess_{agent_id}_{int(datetime.utcnow().timestamp() * 1000)}"
        session = SessionContext(
            session_id=session_id,
            agent_id=agent_id,
            start_time=datetime.utcnow()
        )
        self.sessions[session_id] = session
        self.stats['total_sessions'] += 1
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Retrieve session."""
        return self.sessions.get(session_id)
    
    def close_session(self, session_id: str):
        """Close session."""
        if session_id in self.sessions:
            self.sessions[session_id].close()
    
    def get_agent_sessions(self, agent_id: str, limit: int = 50) -> List[SessionContext]:
        """Get sessions for agent."""
        sessions = [s for s in self.sessions.values() if s.agent_id == agent_id]
        return sorted(sessions, key=lambda s: s.start_time, reverse=True)[:limit]
    
    def get_recent_context(self, agent_id: str, minutes: int = 60) -> Dict[str, Any]:
        """Get recent context for agent."""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        
        recent_memories = [
            m for m in self.get_agent_memories(agent_id, limit=1000)
            if m.timestamp > cutoff
        ]
        
        recent_sessions = [
            s for s in self.get_agent_sessions(agent_id, limit=100)
            if s.start_time > cutoff
        ]
        
        return {
            'agent_id': agent_id,
            'time_window_minutes': minutes,
            'memories': len(recent_memories),
            'sessions': len(recent_sessions),
            'memory_entries': [m.to_dict() for m in recent_memories[:20]],
            'session_summaries': [s.to_dict() for s in recent_sessions[:10]]
        }
    
    def export_agent_knowledge(self, agent_id: str) -> Dict[str, Any]:
        """Export all knowledge for an agent."""
        memories = self.get_agent_memories(agent_id, limit=10000)
        sessions = self.get_agent_sessions(agent_id, limit=1000)
        
        facts = [m for m in memories if m.memory_type == MemoryType.FACT]
        decisions = [m for m in memories if m.memory_type == MemoryType.DECISION]
        learnings = [m for m in memories if m.memory_type == MemoryType.LEARNING]
        
        return {
            'agent_id': agent_id,
            'total_memories': len(memories),
            'total_sessions': len(sessions),
            'facts_count': len(facts),
            'decisions_count': len(decisions),
            'learnings_count': len(learnings),
            'facts': [m.to_dict() for m in facts],
            'decisions': [m.to_dict() for m in decisions],
            'learnings': [m.to_dict() for m in learnings]
        }
    
    def get_stats(self) -> dict:
        """Get memory statistics."""
        total_accesses = sum(e.access_count for e in self.entries.values())
        avg_relevance = sum(e.relevance_score for e in self.entries.values()) / max(1, len(self.entries))
        
        return {
            'total_entries': self.stats['total_entries'],
            'total_sessions': self.stats['total_sessions'],
            'by_type': self.stats['by_type'],
            'total_agents': len(self.agent_memories),
            'total_accesses': total_accesses,
            'average_relevance': avg_relevance,
            'storage_utilization': f"{(len(self.entries) / self.max_entries) * 100:.1f}%"
        }
    
    def clear_old_memories(self, days: int = 30):
        """Clear memories older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        to_remove = [eid for eid, entry in self.entries.items() if entry.timestamp < cutoff]
        
        for eid in to_remove:
            del self.entries[eid]
        
        return len(to_remove)
    
    def clear_all(self):
        """Clear all memories."""
        self.entries.clear()
        self.sessions.clear()
        self.agent_memories.clear()
        self.tags_index.clear()
        self.stats = {
            'total_entries': 0,
            'total_sessions': 0,
            'by_type': {mt.value: 0 for mt in MemoryType}
        }
