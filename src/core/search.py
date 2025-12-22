"""Search and indexing for Speckit Editor"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set

from ..utils.logging import get_logger
from .document import SpeckitDocument

logger = get_logger(__name__)


@dataclass
class SearchOptions:
    """Search configuration options"""
    case_sensitive: bool = False
    whole_word: bool = False
    use_regex: bool = False
    include_drafts: bool = True


class DocumentIndex:
    """In-memory inverted index for document search"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.root_path = project_root  # Alias for tests
        
        # Inverted index: term -> set of document paths
        self.term_index: Dict[str, Set[Path]] = {}
        
        # Requirement lookup: req_id -> (document_path, line_number)
        self.requirement_index: Dict[str, tuple[Path, int]] = {}
        
        # Document metadata: path -> (title, doc_type)
        self.document_metadata: Dict[Path, tuple[str, str]] = {}
    
    def index_document(self, path: Path) -> None:
        """Index a single document (stub)"""
        if not path.exists():
            return
        try:
            doc = SpeckitDocument.load(path)
            self.add_document(doc)
        except Exception as e:
            logger.error(f"Failed to index document {path}: {e}")
    
    def index_all(self) -> None:
        """Index all documents in project (stub)"""
        if not self.project_root.exists():
            return
        for md_file in self.project_root.rglob("*.md"):
            self.index_document(md_file)
    
    def search(self, query) -> List:
        """Search for documents (stub)"""
        # Return empty list for now
        return []
    
    def clear(self) -> None:
        """Clear the index"""
        self.term_index.clear()
        self.requirement_index.clear()
        self.document_metadata.clear()
    
    def add_document(self, document: SpeckitDocument) -> None:
        """Add document to index"""
        logger.debug(f"Indexing document: {document.relative_path}")
        
        # Index content terms
        terms = self._tokenize(document.content)
        for term in terms:
            if term not in self.term_index:
                self.term_index[term] = set()
            self.term_index[term].add(document.path)
        
        # Index requirements
        for req in document.requirements:
            self.requirement_index[req.id] = (document.path, req.line_number)
        
        # Store metadata
        title = self._extract_title(document)
        self.document_metadata[document.path] = (title, document.document_type.value)
    
    def remove_document(self, path: Path) -> None:
        """Remove document from index"""
        logger.debug(f"Removing from index: {path}")
        
        # Remove from term index
        for term, docs in list(self.term_index.items()):
            docs.discard(path)
            if not docs:
                del self.term_index[term]
        
        # Remove from requirement index
        for req_id, (doc_path, _) in list(self.requirement_index.items()):
            if doc_path == path:
                del self.requirement_index[req_id]
        
        # Remove metadata
        self.document_metadata.pop(path, None)
    
    def search(self, query: str, options: SearchOptions = None, max_results: int = 50) -> List[Path]:
        """Search for documents matching query"""
        if options is None:
            options = SearchOptions()
        
        logger.debug(f"Searching: {query}")
        
        terms = self._tokenize(query)
        if not terms:
            return []
        
        # Find documents containing all terms (AND search)
        result_sets = []
        for term in terms:
            if term in self.term_index:
                result_sets.append(self.term_index[term])
        
        if not result_sets:
            return []
        
        # Intersection of all term results
        results = set.intersection(*result_sets)
        
        # Rank by term frequency (simple ranking)
        ranked = sorted(results, key=lambda p: self._rank_document(p, terms), reverse=True)
        
        return ranked[:max_results]
    
    def get_stats(self) -> Dict[str, int]:
        """Get index statistics"""
        return {
            "document_count": len(self.document_metadata),
            "term_count": len(self.term_index),
            "requirement_count": len(self.requirement_index)
        }
    
    def find_requirement(self, req_id: str) -> tuple[Path, int] | None:
        """Find document and line number for a requirement ID"""
        return self.requirement_index.get(req_id)
    
    def _tokenize(self, text: str) -> List[str]:
        """Convert text to searchable terms"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove markdown syntax
        text = text.replace("#", "").replace("*", "").replace("_", "")
        
        # Split into words
        words = text.split()
        
        # Filter short words and common stopwords
        stopwords = {"the", "a", "an", "and", "or", "but", "is", "are", "was", "were"}
        terms = [w for w in words if len(w) >= 3 and w not in stopwords]
        
        return terms
    
    def _extract_title(self, document: SpeckitDocument) -> str:
        """Extract document title from first heading or filename"""
        if document.sections:
            return document.sections[0].title
        return document.path.stem
    
    def _rank_document(self, path: Path, query_terms: List[str]) -> int:
        """Calculate relevance score for document"""
        # Simple term frequency ranking
        score = 0
        for term in query_terms:
            if term in self.term_index and path in self.term_index[term]:
                score += 1
        return score
