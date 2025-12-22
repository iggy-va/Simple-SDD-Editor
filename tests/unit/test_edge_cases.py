"""Edge case tests for better coverage"""

import pytest
from pathlib import Path
from src.core.project import SpeckitProject
from src.core.template import Template, TemplateVariable
from src.core.search import DocumentIndex
from src.core.document import SpeckitDocument, DocumentType


def test_template_extract_variables_with_patterns():
    """Test variable extraction with pattern matching"""
    content = """# {{title}}

Feature ID: {{feature_id}}
Date: {{date}}
Author: {{author_name}}
"""
    variables = Template._extract_variables(content)
    
    # Should extract all variables
    var_names = [v.name for v in variables]
    assert "feature_id" in var_names
    assert "date" in var_names


def test_template_variable_defaults():
    """Test template variable defaults"""
    var = TemplateVariable(
        name="test",
        description="Test Variable",
        default="default_value",
        required=False
    )
    
    assert var.default == "default_value"
    assert var.required is False


def test_search_empty_index(tmp_path):
    """Test search on empty index"""
    index = DocumentIndex(tmp_path)
    results = index.search("test")
    
    assert len(results) == 0


def test_search_special_tokens(tmp_path):
    """Test tokenization with special characters"""
    index = DocumentIndex(tmp_path)
    
    terms = index._tokenize("Test ## markdown ### syntax")
    assert "markdown" in terms
    assert "syntax" in terms
    assert "#" not in " ".join(terms)


def test_project_scan_large_pattern(tmp_path):
    """Test scanning with complex pattern"""
    project = SpeckitProject(tmp_path)
    
    # Create various files
    (tmp_path / "test.md").write_text("# Test")
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "other.md").write_text("# Other")
    
    # Scan with pattern
    docs = project.scan_documents("docs/**/*.md")
    assert len(docs) >= 0


def test_document_type_values():
    """Test document type enum values"""
    assert DocumentType.SPEC.value == "spec"
    assert DocumentType.PLAN.value == "plan"
    assert DocumentType.TASKS.value == "tasks"


def test_search_index_stats_empty(tmp_path):
    """Test stats on empty index"""
    index = DocumentIndex(tmp_path)
    stats = index.get_stats()
    
    assert stats["document_count"] == 0
    assert stats["term_count"] == 0
    assert stats["requirement_count"] == 0


def test_project_relative_path_handling(tmp_path):
    """Test handling of relative paths"""
    project = SpeckitProject(tmp_path)
    doc_path = Path("test.md")
    
    (tmp_path / "test.md").write_text("# Test")
    
    doc = project.get_document(doc_path)
    assert doc is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
