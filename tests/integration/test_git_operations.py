"""Integration tests for git operations with real git repositories

These tests are stateless - each test gets a fresh git repo from fixtures
and cleanup happens automatically. Tests can run repeatedly with same results.
"""

import pytest
from pathlib import Path
from src.core.project import SpeckitProject, FeatureBranch


class TestGitInitialization:
    """Test git repository initialization"""
    
    def test_init_git_repo_success(self, git_repo):
        """Verify SpeckitProject detects existing git repo"""
        repo_path = Path(git_repo.workdir)
        
        # Create .specify directory (required by SpeckitProject)
        specify_dir = repo_path / ".specify" / "memory"
        specify_dir.mkdir(parents=True, exist_ok=True)
        (specify_dir / "constitution.md").write_text("# Constitution")
        
        # Initialize project
        project = SpeckitProject(repo_path)
        
        # Verify git repo was detected
        assert project.git_repo is not None
    
    def test_init_git_repo_not_found(self, tmp_path):
        """Verify SpeckitProject handles non-git directories"""
        # Create non-git directory with .specify
        specify_dir = tmp_path / ".specify" / "memory"
        specify_dir.mkdir(parents=True, exist_ok=True)
        (specify_dir / "constitution.md").write_text("# Constitution")
        
        # Initialize project
        project = SpeckitProject(tmp_path)
        
        # Verify no git repo detected
        assert project.git_repo is None


class TestBranchScanning:
    """Test feature branch scanning"""
    
    def test_scan_branches_finds_features(self, git_repo_with_branches):
        """Verify _scan_branches finds feature branches matching pattern"""
        repo_path = Path(git_repo_with_branches.workdir)
        
        # Initialize project
        project = SpeckitProject(repo_path)
        
        # Verify feature branches were found
        assert len(project.branches) == 3
        
        # Check branch names
        branch_names = set(project.branches.keys())
        assert "001-feature-one" in branch_names
        assert "002-feature-two" in branch_names
        assert "003-another-feature" in branch_names
        
        # Verify non-feature branches excluded
        assert "dev" not in branch_names
        assert "main" not in branch_names
    
    def test_scan_branches_empty_repo(self, git_repo):
        """Verify _scan_branches handles repo with no feature branches"""
        repo_path = Path(git_repo.workdir)
        
        # Create .specify directory
        specify_dir = repo_path / ".specify" / "memory"
        specify_dir.mkdir(parents=True, exist_ok=True)
        (specify_dir / "constitution.md").write_text("# Constitution")
        
        # Initialize project
        project = SpeckitProject(repo_path)
        
        # Verify no feature branches found (only main)
        assert len(project.branches) == 0


class TestTimestampExtraction:
    """Test git history timestamp extraction"""
    
    def test_update_timestamps_from_commits(self, git_repo_with_files):
        """Verify _update_timestamps extracts timestamps from git history"""
        repo_path = Path(git_repo_with_files.workdir)
        
        # Initialize project
        project = SpeckitProject(repo_path)
        
        # Project should have timestamps from git commits
        assert project.created_at is not None
        assert project.last_modified_at is not None


class TestFeatureBranchCreation:
    """Test feature branch creation"""
    
    def test_create_feature_branch_success(self, git_repo_with_files):
        """Verify create_feature_branch creates new branch in git"""
        import pygit2
        
        repo_path = Path(git_repo_with_files.workdir)
        
        # Initialize project
        project = SpeckitProject(repo_path)
        
        # Verify starting state
        initial_count = len(project.branches)
        
        # Create new feature branch (note: feature_id is a string)
        new_branch = project.create_feature_branch(
            feature_id="999",
            feature_name="test-feature"
        )
        
        # Verify branch created
        assert new_branch is not None
        assert new_branch.name == "999-test-feature"
        
        # Verify branch exists in git repo
        assert "999-test-feature" in git_repo_with_files.branches
        
        # Verify branch added to project
        assert len(project.branches) == initial_count + 1
    
    def test_create_feature_branch_incremental_numbers(self, git_repo_with_branches):
        """Verify multiple branch creation uses incremental numbers"""
        repo_path = Path(git_repo_with_branches.workdir)
        
        # Initialize project (has branches 001, 002, 003)
        project = SpeckitProject(repo_path)
        
        # Create new branches
        branch1 = project.create_feature_branch(
            feature_id="004",
            feature_name="fourth-feature"
        )
        
        branch2 = project.create_feature_branch(
            feature_id="005",
            feature_name="fifth-feature"
        )
        
        # Verify branches created with correct numbers
        assert branch1.name == "004-fourth-feature"
        assert branch2.name == "005-fifth-feature"
        
        # Verify all branches in git
        assert "004-fourth-feature" in git_repo_with_branches.branches
        assert "005-fifth-feature" in git_repo_with_branches.branches
        
        # Verify total count
        assert len(project.branches) == 5


class TestGitIntegrationStateless:
    """Verify tests are truly stateless - can run multiple times"""
    
    def test_stateless_repo_creation_run1(self, git_repo):
        """First run of stateless test"""
        repo_path = Path(git_repo.workdir)
        
        # Create .specify directory
        specify_dir = repo_path / ".specify" / "memory"
        specify_dir.mkdir(parents=True, exist_ok=True)
        (specify_dir / "constitution.md").write_text("# Constitution")
        
        # Verify fresh repo
        assert len(list(git_repo.branches)) == 1  # Only main
        
        # Initialize project
        project = SpeckitProject(repo_path)
        assert project.git_repo is not None
        assert len(project.branches) == 0
    
    def test_stateless_repo_creation_run2(self, git_repo):
        """Second run - should get fresh repo, identical to run1"""
        repo_path = Path(git_repo.workdir)
        
        # Create .specify directory
        specify_dir = repo_path / ".specify" / "memory"
        specify_dir.mkdir(parents=True, exist_ok=True)
        (specify_dir / "constitution.md").write_text("# Constitution")
        
        # Verify fresh repo (not contaminated by run1)
        assert len(list(git_repo.branches)) == 1  # Only main
        
        # Initialize project
        project = SpeckitProject(repo_path)
        assert project.git_repo is not None
        assert len(project.branches) == 0
    
    def test_stateless_branch_creation_run1(self, git_repo_with_files):
        """Create branch - first run"""
        repo_path = Path(git_repo_with_files.workdir)
        project = SpeckitProject(repo_path)
        
        # Create branch
        project.create_feature_branch("100", "test")
        
        # Verify created
        assert len(project.branches) == 1
    
    def test_stateless_branch_creation_run2(self, git_repo_with_files):
        """Create branch - second run, should get fresh repo"""
        repo_path = Path(git_repo_with_files.workdir)
        project = SpeckitProject(repo_path)
        
        # Verify starting from clean state (no branch from run1)
        assert len(project.branches) == 0
        
        # Create same branch
        project.create_feature_branch("100", "test")
        
        # Verify created (same as run1, proves stateless)
        assert len(project.branches) == 1
