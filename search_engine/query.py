"""Search query engine with ranking and relevance."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
import math
from search_engine.index import SearchIndex, TextProcessor


@dataclass
class SearchResult:
    """Individual search result."""
    doc_id: str
    title: str
    content_preview: str
    score: float
    matched_terms: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'doc_id': self.doc_id,
            'title': self.title,
            'content_preview': self.content_preview,
            'score': round(self.score, 4),
            'matched_terms': self.matched_terms,
            'metadata': self.metadata
        }


class RankingAlgorithm:
    """Relevance ranking algorithm (TF-IDF with BM25)."""

    def __init__(self, search_index: SearchIndex):
        self.index = search_index
        self._build_statistics()

    def _build_statistics(self) -> None:
        """Build IDF statistics."""
        self.idf_cache: Dict[str, float] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_length = 0.0

        total_length = 0
        for doc_id, doc in self.index.documents.items():
            tokens = TextProcessor.process(doc.title + ' ' + doc.content)
            self.doc_lengths[doc_id] = len(tokens)
            total_length += len(tokens)

        if self.index.documents:
            self.avg_doc_length = total_length / len(self.index.documents)

        # Calculate IDF for all terms
        num_docs = len(self.index.documents)
        for term, entry in self.index.inverted_index.items():
            doc_freq = len(entry.doc_ids)
            self.idf_cache[term] = math.log(num_docs / max(1, doc_freq))

    def get_idf(self, term: str) -> float:
        """Get IDF score for term."""
        return self.idf_cache.get(term, 0.0)

    def calculate_score(self, doc_id: str, terms: List[str], query_boost: float = 1.0) -> float:
        """Calculate BM25 relevance score."""
        score = 0.0
        k1 = 1.5  # Term frequency saturation
        b = 0.75  # Length normalization
        
        doc = self.index.documents.get(doc_id)
        if not doc:
            return 0.0

        doc_length = self.doc_lengths.get(doc_id, 0)

        for term in terms:
            if term not in self.index.inverted_index:
                continue

            entry = self.index.inverted_index[term]
            
            if doc_id not in entry.frequencies:
                continue

            term_freq = entry.frequencies[doc_id]
            idf = self.get_idf(term)

            # BM25 formula
            numerator = term_freq * (k1 + 1)
            denominator = term_freq + k1 * (1 - b + b * (doc_length / max(1, self.avg_doc_length)))
            bm25 = idf * (numerator / max(1, denominator))
            
            # Apply document boost
            score += bm25 * doc.boost

        # Apply query boost
        score *= query_boost

        return score

    def rank_results(self, results: List[Tuple[str, List[str]]]) -> List[SearchResult]:
        """Rank and format results."""
        scored_results = []

        for doc_id, matched_terms in results:
            doc = self.index.documents[doc_id]
            score = self.calculate_score(doc_id, matched_terms)
            
            # Create preview
            content_preview = doc.content[:150].replace('\n', ' ')
            if len(doc.content) > 150:
                content_preview += '...'

            result = SearchResult(
                doc_id=doc_id,
                title=doc.title,
                content_preview=content_preview,
                score=score,
                matched_terms=matched_terms,
                metadata=doc.metadata
            )
            scored_results.append(result)

        # Sort by score descending
        scored_results.sort(key=lambda r: r.score, reverse=True)
        return scored_results


class QueryEngine:
    """Query parsing and execution."""

    def __init__(self, search_index: SearchIndex):
        self.index = search_index
        self.ranker = RankingAlgorithm(search_index)

    def search(self, query: str, limit: int = 10, require_all: bool = False) -> List[SearchResult]:
        """Execute search query."""
        if not query or not query.strip():
            return []

        # Process query terms
        query_terms = TextProcessor.process(query)

        if not query_terms:
            return []

        # Find matching documents
        if require_all:
            # All terms must be present
            matching_docs = self._search_and(query_terms)
        else:
            # Any term can match (OR)
            matching_docs = self._search_or(query_terms)

        if not matching_docs:
            return []

        # Convert to results with matched terms
        results = [
            (doc_id, [t for t in query_terms if t in self.index.inverted_index and 
                     doc_id in self.index.inverted_index[t].doc_ids])
            for doc_id in matching_docs
        ]

        # Rank results
        ranked = self.ranker.rank_results(results)

        # Return top N
        return ranked[:limit]

    def _search_or(self, terms: List[str]) -> Set[str]:
        """OR search - union of all matching documents."""
        matching_docs = set()

        for term in terms:
            if term in self.index.inverted_index:
                matching_docs.update(self.index.inverted_index[term].doc_ids)

        return matching_docs

    def _search_and(self, terms: List[str]) -> Set[str]:
        """AND search - intersection of matching documents."""
        if not terms:
            return set()

        matching_docs = None

        for term in terms:
            if term not in self.index.inverted_index:
                return set()

            if matching_docs is None:
                matching_docs = self.index.inverted_index[term].doc_ids.copy()
            else:
                matching_docs &= self.index.inverted_index[term].doc_ids

        return matching_docs or set()

    def phrase_search(self, phrase: str, limit: int = 10) -> List[SearchResult]:
        """Search for exact phrase."""
        query_terms = TextProcessor.process(phrase)

        if not query_terms or len(query_terms) < 1:
            return []

        # Find documents containing all terms
        matching_docs = self._search_and(query_terms)

        if not matching_docs:
            return []

        # Filter by phrase proximity
        results = []

        for doc_id in matching_docs:
            entry = self.index.inverted_index[query_terms[0]]
            positions = entry.positions.get(doc_id, [])

            # Check if phrase appears consecutively
            for pos in positions:
                if all(term in self.index.inverted_index and 
                       doc_id in self.index.inverted_index[term].doc_ids
                       for term in query_terms):
                    doc = self.index.documents[doc_id]
                    score = self.ranker.calculate_score(doc_id, query_terms) * 1.5  # Boost phrase matches
                    
                    content_preview = doc.content[:150].replace('\n', ' ')
                    if len(doc.content) > 150:
                        content_preview += '...'

                    results.append(SearchResult(
                        doc_id=doc_id,
                        title=doc.title,
                        content_preview=content_preview,
                        score=score,
                        matched_terms=query_terms,
                        metadata=doc.metadata
                    ))
                    break

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def get_suggestions(self, prefix: str, limit: int = 5) -> List[str]:
        """Get search suggestions by term prefix."""
        suggestions = []

        prefix_lower = prefix.lower()

        for term in self.index.inverted_index.keys():
            if term.startswith(prefix_lower):
                suggestions.append(term)

        # Sort by frequency
        suggestions.sort(
            key=lambda t: len(self.index.inverted_index[t].doc_ids),
            reverse=True
        )

        return suggestions[:limit]
