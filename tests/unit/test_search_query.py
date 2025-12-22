"""Tests for search query classes"""

import pytest
from pathlib import Path
from src.core.search_query import SearchQuery, SearchResult


def test_search_query_creation():
    """Test creating search query"""
    query = SearchQuery(text="test", case_sensitive=True)
    
    assert query.text == "test"
    assert query.case_sensitive is True
    assert query.whole_word is False


def test_search_query_defaults():
    """Test search query default values"""
    query = SearchQuery(text="test")
    
    assert query.case_sensitive is False
    assert query.whole_word is False
    assert query.regex is False


def test_search_result_creation():
    """Test creating search result"""
    result = SearchResult(
        document_path=Path("test.md"),
        line_number=10,
        column=5,
        matched_text="found"
    )
    
    assert result.document_path == Path("test.md")
    assert result.line_number == 10
    assert result.column == 5
    assert result.matched_text == "found"


def test_search_result_with_context():
    """Test search result with context"""
    result = SearchResult(
        document_path=Path("test.md"),
        line_number=10,
        column=5,
        matched_text="found",
        context_before="before",
        context_after="after"
    )
    
    assert result.context_before == "before"
    assert result.context_after == "after"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
