"""Additional project tests for git operations"""

import pytest
from pathlib import Path
from src.core.project import SpeckitProject, FeatureBranch


def test_feature_branch_creation(tmp_path):
    """Test feature branch object creation"""
    project_root = tmp_path
    (project_root / "specs" / "001-feature-name").mkdir(parents=True)
    (project_root / "specs" / "001-feature-name" / "spec.md").write_text("# Spec")
    
    branch = FeatureBranch("001-feature-name", project_root)
    
    assert branch.name == "001-feature-name"
    assert branch.feature_id == "001"
    assert branch.spec_path is not None


def test_feature_branch_no_documents(tmp_path):
    """Test feature branch with no documents"""
    branch = FeatureBranch("001-test", tmp_path)
    
    assert branch.spec_path is None
    assert branch.plan_path is None
    assert branch.tasks_path is None


def test_feature_branch_ahead_behind(tmp_path):
    """Test ahead/behind count calculation"""
    branch = FeatureBranch("001-test", tmp_path)
    ahead, behind = branch.get_ahead_behind_counts()
    
    assert ahead == 0
    assert behind == 0


def test_project_branches_property(tmp_path):
    """Test project branches dictionary"""
    project = SpeckitProject(tmp_path)
    
    assert isinstance(project.branches, dict)


def test_project_current_branch(tmp_path):
    """Test current branch property"""
    project = SpeckitProject(tmp_path)
    
    # No git repo, should be None
    assert project.current_branch is None


def test_project_git_repo(tmp_path):
    """Test git repo property"""
    project = SpeckitProject(tmp_path)
    
    # No git init, should be None
    assert project.git_repo is None


def test_project_settings(tmp_path):
    """Test project settings property"""
    project = SpeckitProject(tmp_path)
    
    assert project.settings is not None
    assert hasattr(project.settings, 'tab_size')


def test_project_constitution_path(tmp_path):
    """Test constitution path detection"""
    const_path = tmp_path / ".specify" / "memory" / "constitution.md"
    const_path.parent.mkdir(parents=True)
    const_path.write_text("# Constitution")
    
    project = SpeckitProject(tmp_path)
    
    assert project.constitution_path == const_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
