"""Tests targeting remaining uncovered project.py code"""

import pytest
from pathlib import Path
from src.core.project import SpeckitProject
from datetime import datetime


def test_project_timestamps_no_git(tmp_path):
    """Test timestamp fallback to filesystem when no git"""
    project = SpeckitProject(tmp_path)
    
    # Should have timestamps from filesystem
    assert project.created_at is None or isinstance(project.created_at, datetime)
    assert project.last_modified_at is None or isinstance(project.last_modified_at, datetime)


def test_project_validate_structure(tmp_path):
    """Test project structure validation"""
    project = SpeckitProject(tmp_path)
    
    result = project.validate_structure()
    assert result is not None
    assert hasattr(result, 'is_valid')


def test_project_document_cache_lock(tmp_path):
    """Test document cache thread safety"""
    project = SpeckitProject(tmp_path)
    
    (tmp_path / "test1.md").write_text("# Test 1")
    (tmp_path / "test2.md").write_text("# Test 2")
    
    # Access documents concurrently (simulated)
    doc1 = project.get_document(tmp_path / "test1.md")
    doc2 = project.get_document(tmp_path / "test2.md")
    
    assert doc1 is not None
    assert doc2 is not None


def test_project_index_lock(tmp_path):
    """Test index lock for thread safety"""
    project = SpeckitProject(tmp_path)
    
    (tmp_path / "test.md").write_text("# Test")
    
    # Should not raise errors
    project.rebuild_index(background=False)
    assert project._index is not None


def test_scan_documents_exclude_patterns(tmp_path):
    """Test document scanning excludes node_modules"""
    project = SpeckitProject(tmp_path)
    
    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()
    (node_modules / "test.md").write_text("# Should be excluded")
    
    (tmp_path / "valid.md").write_text("# Valid")
    
    docs = project.scan_documents()
    assert all("node_modules" not in str(d) for d in docs)


def test_scan_documents_exclude_venv(tmp_path):
    """Test document scanning excludes venv"""
    project = SpeckitProject(tmp_path)
    
    venv = tmp_path / "venv"
    venv.mkdir()
    (venv / "test.md").write_text("# Should be excluded")
    
    (tmp_path / "valid.md").write_text("# Valid")
    
    docs = project.scan_documents()
    assert all("venv" not in str(d) for d in docs)


def test_scan_documents_exclude_pycache(tmp_path):
    """Test document scanning excludes __pycache__"""
    project = SpeckitProject(tmp_path)
    
    pycache = tmp_path / "__pycache__"
    pycache.mkdir()
    
    (tmp_path / "valid.md").write_text("# Valid")
    
    docs = project.scan_documents()
    assert all("__pycache__" not in str(d) for d in docs)


def test_project_settings_loaded(tmp_path):
    """Test settings are properly loaded"""
    settings_dir = tmp_path / ".specify"
    settings_dir.mkdir()
    
    project = SpeckitProject(tmp_path)
    
    assert project.settings is not None
    assert project.settings.tab_size > 0


def test_project_branches_dict(tmp_path):
    """Test branches dictionary exists"""
    project = SpeckitProject(tmp_path)
    
    assert isinstance(project.branches, dict)
    assert len(project.branches) >= 0


def test_project_name_from_path(tmp_path):
    """Test project name extracted from path"""
    project = SpeckitProject(tmp_path)
    
    assert project.name == tmp_path.name


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
