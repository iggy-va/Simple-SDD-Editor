"""Tests to push coverage over 90%"""

import pytest
from pathlib import Path
from src.core.project import FeatureBranch


def test_feature_branch_find_spec(tmp_path):
    """Test finding spec document"""
    specs_dir = tmp_path / "specs" / "001-test-feature"
    specs_dir.mkdir(parents=True)
    spec_file = specs_dir / "spec.md"
    spec_file.write_text("# Test Spec")
    
    branch = FeatureBranch("001-test-feature", tmp_path)
    
    assert branch.spec_path == spec_file


def test_feature_branch_find_plan(tmp_path):
    """Test finding plan document"""
    specs_dir = tmp_path / "specs" / "002-another-feature"
    specs_dir.mkdir(parents=True)
    plan_file = specs_dir / "plan.md"
    plan_file.write_text("# Test Plan")
    
    branch = FeatureBranch("002-another-feature", tmp_path)
    
    assert branch.plan_path == plan_file


def test_feature_branch_find_tasks(tmp_path):
    """Test finding tasks document"""
    specs_dir = tmp_path / "specs" / "003-feature-with-tasks"
    specs_dir.mkdir(parents=True)
    tasks_file = specs_dir / "tasks.md"
    tasks_file.write_text("# Tasks")
    
    branch = FeatureBranch("003-feature-with-tasks", tmp_path)
    
    assert branch.tasks_path == tasks_file


def test_feature_branch_missing_documents(tmp_path):
    """Test branch with no documents found"""
    branch = FeatureBranch("999-missing", tmp_path)
    
    assert branch.spec_path is None
    assert branch.plan_path is None
    assert branch.tasks_path is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
