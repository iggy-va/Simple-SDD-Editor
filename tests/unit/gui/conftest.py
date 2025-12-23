"""
Shared fixtures for GUI tests.
"""

import pytest
from pathlib import Path
from PySide6.QtWidgets import QApplication

from src.core.document import SpeckitDocument, DocumentType
from src.core.project import SpeckitProject


@pytest.fixture
def sample_document(tmp_path: Path) -> SpeckitDocument:
    """Create a sample document for testing"""
    doc_path = tmp_path / "test_document.md"
    doc_path.write_text("# Test Document\\n\\nThis is test content.")
    
    return SpeckitDocument(
        path=doc_path,
        relative_path=Path("test_document.md"),
        content="# Test Document\\n\\nThis is test content.",
        document_type=DocumentType.OTHER
    )


@pytest.fixture
def clarify_document(tmp_path: Path) -> SpeckitDocument:
    """Create a clarify document for testing"""
    doc_path = tmp_path / "clarify.md"
    content = """# Clarify: Test Feature

## Problem Statement
The test feature needs clarification.

## Proposed Solution
We will implement a test solution.
"""
    doc_path.write_text(content)
    
    return SpeckitDocument(
        path=doc_path,
        relative_path=Path("clarify.md"),
        content=content,
        document_type=DocumentType.OTHER
    )


@pytest.fixture
def spec_document(tmp_path: Path) -> SpeckitDocument:
    """Create a spec document for testing"""
    doc_path = tmp_path / "spec.md"
    content = """# Spec: Test Feature

## User Stories

### FR-001: User Login
**Priority**: P1

As a user, I want to login so that I can access the system.

**Acceptance Criteria**:
- SC-001: Login form displays
- SC-002: Valid credentials allow access
"""
    doc_path.write_text(content)
    
    return SpeckitDocument(
        path=doc_path,
        relative_path=Path("spec.md"),
        content=content,
        document_type=DocumentType.SPEC
    )


@pytest.fixture
def sample_project(tmp_path: Path) -> SpeckitProject:
    """Create a sample project for testing"""
    project_path = tmp_path / "test_project"
    project_path.mkdir(exist_ok=True)
    
    # Create .specify directory
    specify_dir = project_path / ".specify"
    specify_dir.mkdir(exist_ok=True)
    
    # Create templates directory
    templates_dir = specify_dir / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # Initialize git repo
    import subprocess
    try:
        subprocess.run(["git", "init"], cwd=project_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=project_path, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        pass  # Git might not be available in test environment
    
    return SpeckitProject(root_path=project_path)


@pytest.fixture
def git_project(tmp_path: Path) -> SpeckitProject:
    """Create a project with git initialized"""
    project_path = tmp_path / "git_project"
    project_path.mkdir(exist_ok=True)
    
    # Create .specify directory
    specify_dir = project_path / ".specify"
    specify_dir.mkdir(exist_ok=True)
    
    # Initialize git
    import subprocess
    subprocess.run(["git", "init"], cwd=project_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=project_path, check=True, capture_output=True)
    
    # Create initial commit
    readme = project_path / "README.md"
    readme.write_text("# Test Project")
    subprocess.run(["git", "add", "."], cwd=project_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=project_path, check=True, capture_output=True)
    
    return SpeckitProject(root_path=project_path)


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for tests"""
    # QApplication is already created by pytest-qt
    return QApplication.instance()
