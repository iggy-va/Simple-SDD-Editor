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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
