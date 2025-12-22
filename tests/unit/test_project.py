"""Unit tests for SpeckitProject"""

import tempfile
from pathlib import Path

import pytest

from src.core import SpeckitProject


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory with basic structure"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        # Create basic project structure
        (project_root / "specs").mkdir()
        (project_root / ".specify" / "memory").mkdir(parents=True)
        (project_root / ".specify" / "templates").mkdir(parents=True)
        
        # Create constitution
        constitution = project_root / ".specify" / "memory" / "constitution.md"
        constitution.write_text("# Constitution\n\nProject principles.")
        
        # Create sample documents
        spec_dir = project_root / "specs" / "001-test-feature"
        spec_dir.mkdir(parents=True)
        
        (spec_dir / "spec.md").write_text("# Test Feature\n\n**FR-001**: Test requirement")
        (spec_dir / "plan.md").write_text("# Implementation Plan\n")
        
        yield project_root


def test_project_initialization(temp_project_dir):
    """Test SpeckitProject initialization"""
    project = SpeckitProject(temp_project_dir)
    
    assert project.root_path == temp_project_dir
    assert project.name == temp_project_dir.name
    assert project.constitution_path is not None
    assert project.constitution_path.exists()


def test_project_find_constitution(temp_project_dir):
    """Test constitution file discovery"""
    project = SpeckitProject(temp_project_dir)
    
    assert project.constitution_path is not None
    assert "constitution.md" in str(project.constitution_path)


def test_project_scan_documents(temp_project_dir):
    """Test document scanning"""
    project = SpeckitProject(temp_project_dir)
    
    documents = project.scan_documents("**/*.md")
    
    # Should find spec.md, plan.md, and constitution.md
    assert len(documents) >= 2
    
    # Check that spec.md is found
    doc_names = [d.name for d in documents]
    assert "spec.md" in doc_names
    assert "plan.md" in doc_names


def test_project_get_document(temp_project_dir):
    """Test document loading with caching"""
    project = SpeckitProject(temp_project_dir)
    
    spec_path = temp_project_dir / "specs" / "001-test-feature" / "spec.md"
    
    # Load document
    doc1 = project.get_document(spec_path)
    assert doc1 is not None
    assert doc1.path == spec_path
    assert "Test Feature" in doc1.content
    
    # Load same document again (should return cached)
    doc2 = project.get_document(spec_path)
    assert doc2 is doc1  # Same object


def test_project_get_document_relative_path(temp_project_dir):
    """Test document loading with relative path"""
    project = SpeckitProject(temp_project_dir)
    
    relative_path = Path("specs") / "001-test-feature" / "spec.md"
    
    doc = project.get_document(relative_path)
    assert doc is not None
    assert doc.content is not None


def test_project_get_document_force_reload(temp_project_dir):
    """Test forced document reload"""
    project = SpeckitProject(temp_project_dir)
    
    spec_path = temp_project_dir / "specs" / "001-test-feature" / "spec.md"
    
    # Load document
    doc1 = project.get_document(spec_path)
    
    # Modify file on disk
    spec_path.write_text("# Modified Content\n")
    
    # Load without force reload (cached version)
    doc2 = project.get_document(spec_path)
    assert "Test Feature" in doc2.content  # Still has old content
    
    # Load with force reload
    doc3 = project.get_document(spec_path, force_reload=True)
    assert "Modified Content" in doc3.content


def test_project_validate_structure(temp_project_dir):
    """Test project structure validation"""
    project = SpeckitProject(temp_project_dir)
    
    result = project.validate_structure()
    
    # Should pass validation with basic structure
    assert result.is_valid or len(result.errors) == 0


def test_project_settings_integration(temp_project_dir):
    """Test ProjectSettings integration"""
    project = SpeckitProject(temp_project_dir)
    
    assert project.settings is not None
    assert project.settings.tab_size == 4  # Default value
    
    # Modify and save settings
    project.settings.tab_size = 8
    project.settings.save(temp_project_dir / ".specify" / "settings.json")
    
    # Create new project instance
    project2 = SpeckitProject(temp_project_dir)
    assert project2.settings.tab_size == 8


def test_project_timestamps(temp_project_dir):
    """Test project timestamp tracking"""
    project = SpeckitProject(temp_project_dir)
    
    assert project.created_at is not None
    assert project.last_modified_at is not None


def test_scan_documents_pattern(temp_project_dir):
    """Test scanning with pattern"""
    project = SpeckitProject(temp_project_dir)
    docs = project.scan_documents("**/spec.md")
    assert len(docs) >= 1


def test_get_feature_documents(temp_project_dir):
    """Test getting feature documents"""
    project = SpeckitProject(temp_project_dir)
    feature_dir = temp_project_dir / "specs" / "001-test-feature"
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "spec.md").write_text("# Spec")
    (feature_dir / "plan.md").write_text("# Plan")
    docs = project.get_feature_documents("001")
    assert len(docs) >= 2


def test_create_document(temp_project_dir):
    """Test creating new document"""
    project = SpeckitProject(temp_project_dir)
    new_path = temp_project_dir / "specs" / "001-test-feature" / "research.md"
    content = "# Research"
    
    doc = project.create_document(new_path, content)
    assert doc.path == new_path
    assert new_path.exists()


def test_save_document(temp_project_dir):
    """Test saving document"""
    project = SpeckitProject(temp_project_dir)
    spec_path = temp_project_dir / "specs" / "001-test-feature" / "spec.md"
    doc = project.get_document(spec_path)
    
    doc.content = "# Modified"
    project.save_document(doc)
    
    assert spec_path.read_text(encoding="utf-8") == "# Modified"


def test_project_without_constitution(tmp_path):
    """Test project without constitution"""
    project_root = tmp_path / "no_const"
    project_root.mkdir()
    
    project = SpeckitProject(project_root)
    assert project.constitution_path is None


def test_project_name(temp_project_dir):
    """Test project name extraction"""
    project = SpeckitProject(temp_project_dir)
    assert project.name == temp_project_dir.name


def test_rebuild_index(temp_project_dir):
    """Test rebuild index"""
    project = SpeckitProject(temp_project_dir)
    (temp_project_dir / "test.md").write_text("# Test")
    project.rebuild_index(background=False)
    assert project._index is not None


def test_get_document_caching(temp_project_dir):
    """Test document caching"""
    project = SpeckitProject(temp_project_dir)
    doc_path = temp_project_dir / "test.md"
    doc_path.write_text("# Test")
    doc1 = project.get_document(doc_path)
    doc2 = project.get_document(doc_path)
    assert doc1 is doc2


def test_project_root_path(temp_project_dir):
    """Test project root path"""
    project = SpeckitProject(temp_project_dir)
    assert project.root_path == temp_project_dir


def test_scan_documents_excludes_git(temp_project_dir):
    """Test scan excludes .git directory"""
    project = SpeckitProject(temp_project_dir)
    git_dir = temp_project_dir / ".git"
    git_dir.mkdir(exist_ok=True)
    (temp_project_dir / "valid.md").write_text("# Valid")
    
    docs = project.scan_documents()
    assert all(".git" not in str(d) for d in docs)


def test_document_force_reload(temp_project_dir):
    """Test force reloading document"""
    project = SpeckitProject(temp_project_dir)
    doc_path = temp_project_dir / "test.md"
    doc_path.write_text("# Original")
    
    doc1 = project.get_document(doc_path)
    doc_path.write_text("# Modified")
    doc2 = project.get_document(doc_path, force_reload=True)
    
    assert doc1 is not doc2


def test_project_settings_integration(temp_project_dir):
    """Test project settings loaded correctly"""
    project = SpeckitProject(temp_project_dir)
    assert project.settings is not None
    assert hasattr(project.settings, "tab_size")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
