"""Shared fixtures for integration tests"""

import pytest
import pygit2
from pathlib import Path
import shutil


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repository with initial commit
    
    This fixture is stateless - creates a fresh repo for each test
    and automatically cleans up when test completes.
    """
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    
    # Initialize git repository
    repo = pygit2.init_repository(str(repo_path))
    
    # Configure git identity for commits
    signature = pygit2.Signature("Test User", "test@example.com")
    
    # Create initial commit
    tree = repo.TreeBuilder().write()
    repo.create_commit(
        "refs/heads/main",
        signature,
        signature,
        "Initial commit",
        tree,
        []
    )
    
    # Set HEAD to main branch
    repo.set_head("refs/heads/main")
    
    yield repo
    
    # Cleanup handled automatically by tmp_path fixture


@pytest.fixture
def git_repo_with_files(git_repo, tmp_path):
    """Create git repo with actual files and commits
    
    Returns repo with:
    - Initial file: README.md
    - .specify/memory/constitution.md
    - One commit with these files
    """
    repo_path = Path(git_repo.workdir)
    
    # Create files
    readme = repo_path / "README.md"
    readme.write_text("# Test Project")
    
    const_dir = repo_path / ".specify" / "memory"
    const_dir.mkdir(parents=True, exist_ok=True)
    (const_dir / "constitution.md").write_text("# Constitution v1.0.0")
    
    # Stage and commit files
    index = git_repo.index
    index.add("README.md")
    index.add(".specify/memory/constitution.md")
    index.write()
    
    tree = index.write_tree()
    signature = pygit2.Signature("Test User", "test@example.com")
    
    git_repo.create_commit(
        "refs/heads/main",
        signature,
        signature,
        "Add initial files",
        tree,
        [git_repo.head.target]
    )
    
    yield git_repo


@pytest.fixture
def git_repo_with_branches(git_repo_with_files):
    """Create git repo with feature branches
    
    Returns repo with:
    - main branch (with files)
    - 001-feature-one branch
    - 002-feature-two branch
    - 003-another-feature branch
    """
    signature = pygit2.Signature("Test User", "test@example.com")
    
    # Get main branch commit
    main_commit = git_repo_with_files.head.peel()
    
    # Create feature branches
    git_repo_with_files.branches.local.create("001-feature-one", main_commit)
    git_repo_with_files.branches.local.create("002-feature-two", main_commit)
    git_repo_with_files.branches.local.create("003-another-feature", main_commit)
    
    # Create a non-feature branch (should be ignored)
    git_repo_with_files.branches.local.create("dev", main_commit)
    
    yield git_repo_with_files
