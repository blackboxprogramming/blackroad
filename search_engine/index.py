"""Full-text search index engine."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Set, Optional, Any, Tuple
import re
from collections import defaultdict
import math


class DocumentType(Enum):
    """Type of document being indexed."""
    TEXT = "text"
    JSON = "json"
    HTML = "html"


@dataclass
class Document:
    """Individual searchable document."""
    doc_id: str
    title: str
    content: str
    doc_type: DocumentType = DocumentType.TEXT
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    boost: float = 1.0  # Relevance multiplier

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'doc_id': self.doc_id,
            'title': self.title,
            'content': self.content[:100],  # Preview only
            'doc_type': self.doc_type.value,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'boost': self.boost
        }


@dataclass
class InvertedIndexEntry:
    """Entry in inverted index."""
    term: str
    doc_ids: Set[str] = field(default_factory=set)
    frequencies: Dict[str, int] = field(default_factory=dict)  # doc_id -> frequency
    positions: Dict[str, List[int]] = field(default_factory=dict)  # doc_id -> positions


class TextProcessor:
    """Process and tokenize text."""

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Tokenize text into words."""
        # Convert to lowercase and split
        text = text.lower()
        # Remove special chars but keep hyphens
        text = re.sub(r'[^\w\s\-]', ' ', text)
        # Split on whitespace and hyphens
        tokens = re.split(r'[\s\-]+', text)
        # Filter empty and short tokens
        return [t for t in tokens if t and len(t) > 1]

    @staticmethod
    def remove_stopwords(tokens: List[str]) -> List[str]:
        """Remove common stopwords."""
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
        return [t for t in tokens if t not in stopwords]

    @staticmethod
    def stem(word: str) -> str:
        """Simple stemming (remove common suffixes)."""
        # Simple rules for English
        if word.endswith('ing'):
            return word[:-3]
        elif word.endswith('ed'):
            return word[:-2]
        elif word.endswith('s'):
            return word[:-1]
        return word

    @classmethod
    def process(cls, text: str, stemming: bool = True, stopwords: bool = True) -> List[str]:
        """Full text processing pipeline."""
        tokens = cls.tokenize(text)
        
        if stopwords:
            tokens = cls.remove_stopwords(tokens)
        
        if stemming:
            tokens = [cls.stem(t) for t in tokens]
        
        return tokens


class SearchIndex:
    """Full-text search index."""

    def __init__(self, max_documents: int = 100000):
        self.max_documents = max_documents
        self.documents: Dict[str, Document] = {}
        self.inverted_index: Dict[str, InvertedIndexEntry] = {}
        self.metrics = {
            'total_indexed': 0,
            'total_updated': 0,
            'total_deleted': 0,
        }

    def add_document(self, doc_id: str, title: str, content: str, 
                    metadata: Optional[Dict[str, Any]] = None, boost: float = 1.0,
                    doc_type: DocumentType = DocumentType.TEXT) -> Document:
        """Add document to index."""
        if len(self.documents) >= self.max_documents and doc_id not in self.documents:
            raise RuntimeError(f"Index capacity ({self.max_documents}) reached")

        # Create document
        doc = Document(
            doc_id=doc_id,
            title=title,
            content=content,
            doc_type=doc_type,
            metadata=metadata or {},
            boost=boost
        )

        # Check if updating existing
        is_update = doc_id in self.documents
        
        if is_update:
            # Remove old terms
            self._remove_from_index(doc_id)
            self.metrics['total_updated'] += 1
        else:
            self.metrics['total_indexed'] += 1

        # Add to document store
        self.documents[doc_id] = doc

        # Index text
        self._index_text(doc_id, doc.title, is_title=True)
        self._index_text(doc_id, doc.content, is_title=False)

        return doc

    def _index_text(self, doc_id: str, text: str, is_title: bool = False) -> None:
        """Index text with positional information."""
        tokens = TextProcessor.process(text)
        
        for position, token in enumerate(tokens):
            if token not in self.inverted_index:
                self.inverted_index[token] = InvertedIndexEntry(term=token)
            
            entry = self.inverted_index[token]
            entry.doc_ids.add(doc_id)
            
            # Track frequency
            entry.frequencies[doc_id] = entry.frequencies.get(doc_id, 0) + 1
            
            # Track positions for phrase queries
            if doc_id not in entry.positions:
                entry.positions[doc_id] = []
            entry.positions[doc_id].append(position)

    def _remove_from_index(self, doc_id: str) -> None:
        """Remove document from index."""
        # Find all terms that reference this doc
        for term, entry in list(self.inverted_index.items()):
            if doc_id in entry.doc_ids:
                entry.doc_ids.discard(doc_id)
                entry.frequencies.pop(doc_id, None)
                entry.positions.pop(doc_id, None)
                
                # Remove term if no docs left
                if not entry.doc_ids:
                    del self.inverted_index[term]

    def delete_document(self, doc_id: str) -> bool:
        """Delete document from index."""
        if doc_id not in self.documents:
            return False
        
        self._remove_from_index(doc_id)
        del self.documents[doc_id]
        self.metrics['total_deleted'] += 1
        return True

    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get document by ID."""
        return self.documents.get(doc_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        total_terms = len(self.inverted_index)
        total_postings = sum(len(e.doc_ids) for e in self.inverted_index.values())
        avg_postings = total_postings / total_terms if total_terms > 0 else 0
        
        return {
            'total_documents': len(self.documents),
            'total_terms': total_terms,
            'total_postings': total_postings,
            'average_postings_per_term': avg_postings,
            'index_size_mb': (total_terms * 100 + len(self.documents) * 500) / (1024 * 1024),
            'capacity_percent': (len(self.documents) / self.max_documents * 100),
            'indexed': self.metrics['total_indexed'],
            'updated': self.metrics['total_updated'],
            'deleted': self.metrics['total_deleted']
        }

    def list_documents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List documents with limit."""
        docs = list(self.documents.values())[:limit]
        return [d.to_dict() for d in docs]

    def get_term_frequency(self, term: str) -> Dict[str, int]:
        """Get term frequency across documents."""
        if term not in self.inverted_index:
            return {}
        
        entry = self.inverted_index[term]
        return dict(entry.frequencies)
