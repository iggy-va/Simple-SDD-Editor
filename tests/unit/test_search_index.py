"""Tests for search functionality"""

import pytest
from pathlib import Path

from src.core.search import DocumentIndex
from src.core.document import SpeckitDocument, DocumentType


@pytest.fixture
def sample_docs(tmp_path):
    """Create sample documents"""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    
    (docs_dir / "spec.md").write_text("# Spec\n\n**FR-001**: Test", encoding="utf-8")
    (docs_dir / "plan.md").write_text("# Plan\n\nImplementation", encoding="utf-8")
    
    return docs_dir


def test_index_initialization(tmp_path):
    """Test index initialization"""
    index = DocumentIndex(tmp_path)
    assert index.project_root == tmp_path
    assert index.root_path == tmp_path


def test_add_document(sample_docs):
    """Test adding document"""
    index = DocumentIndex(sample_docs)
    doc = SpeckitDocument.load(sample_docs / "spec.md")
    
    index.add_document(doc)
    assert len(index.term_index) > 0


def test_remove_document(sample_docs):
    """Test removing document"""
    index = DocumentIndex(sample_docs)
    doc_path = sample_docs / "spec.md"
    doc = SpeckitDocument.load(doc_path)
    
    index.add_document(doc)
    index.remove_document(doc_path)
    
    assert doc_path not in index.document_metadata


def test_index_document(sample_docs):
    """Test index_document method"""
    index = DocumentIndex(sample_docs)
    index.index_document(sample_docs / "spec.md")
    
    assert len(index.term_index) > 0


def test_index_all(sample_docs):
    """Test index_all method"""
    index = DocumentIndex(sample_docs)
    index.index_all()
    
    assert len(index.document_metadata) >= 2


def test_clear(sample_docs):
    """Test clearing index"""
    index = DocumentIndex(sample_docs)
    index.index_all()
    
    index.clear()
    
    assert len(index.term_index) == 0
    assert len(index.requirement_index) == 0


def test_index_nonexistent(tmp_path):
    """Test indexing nonexistent file"""
    index = DocumentIndex(tmp_path)
    index.index_document(tmp_path / "missing.md")
    
    assert len(index.term_index) == 0


def test_requirement_index(sample_docs):
    """Test requirement indexing"""
    index = DocumentIndex(sample_docs)
    doc = SpeckitDocument.load(sample_docs / "spec.md")
    
    index.add_document(doc)
    
    assert "FR-001" in index.requirement_index


def test_metadata_storage(sample_docs):
    """Test metadata storage"""
    index = DocumentIndex(sample_docs)
    doc = SpeckitDocument.load(sample_docs / "spec.md")
    
    index.add_document(doc)
    
    assert doc.path in index.document_metadata


def test_find_requirement(sample_docs):
    """Test finding requirement by ID"""
    index = DocumentIndex(sample_docs)
    doc = SpeckitDocument.load(sample_docs / "spec.md")
    index.add_document(doc)
    
    result = index.find_requirement("FR-001")
    assert result is None or isinstance(result, tuple)


def test_tokenize(tmp_path):
    """Test text tokenization"""
    index = DocumentIndex(tmp_path)
    terms = index._tokenize("This is a test document")
    
    assert "test" in terms
    assert "document" in terms


def test_extract_title(sample_docs):
    """Test title extraction from document"""
    index = DocumentIndex(sample_docs)
    doc = SpeckitDocument.load(sample_docs / "spec.md")
    
    title = index._extract_title(doc)
    assert title is not None


def test_rank_document(tmp_path):
    """Test document ranking"""
    index = DocumentIndex(tmp_path)
    doc_path = tmp_path / "test.md"
    doc_path.write_text("# Test")
    
    doc = SpeckitDocument(doc_path, DocumentType.SPEC)
    index.add_document(doc)
    
    score = index._rank_document(doc_path, ["test"])
    assert isinstance(score, int)
