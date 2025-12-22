"""Unit tests for document models"""

import tempfile
from pathlib import Path

import pytest

from src.core import (
    DocumentType,
    Requirement,
    RequirementType,
    Section,
    SpeckitDocument,
)


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        specs_dir = project_root / "specs" / "001-test-feature"
        specs_dir.mkdir(parents=True)
        yield project_root


def test_section_creation():
    """Test Section dataclass creation"""
    section = Section(
        level=1,
        title="Overview",
        content="This is the overview section",
        line_start=1,
        line_end=5,
    )
    
    assert section.level == 1
    assert section.title == "Overview"
    assert section.line_start == 1
    assert section.line_end == 5
    assert len(section.subsections) == 0


def test_requirement_creation():
    """Test Requirement dataclass creation"""
    req = Requirement(
        id="FR-001",
        type=RequirementType.FUNCTIONAL,
        text="The system shall support markdown editing",
        line_number=10,
        priority="P1",
    )
    
    assert req.id == "FR-001"
    assert req.type == RequirementType.FUNCTIONAL
    assert req.priority == "P1"
    assert req.line_number == 10


def test_document_type_detection_spec(temp_project_dir):
    """Test document type detection for spec.md"""
    spec_path = temp_project_dir / "specs" / "001-test-feature" / "spec.md"
    spec_path.write_text("# Test Spec\n\nOverview content")
    
    doc = SpeckitDocument.load(spec_path, temp_project_dir)
    
    assert doc.document_type == DocumentType.SPEC
    assert doc.feature_id == "001"


def test_document_type_detection_plan(temp_project_dir):
    """Test document type detection for plan.md"""
    plan_path = temp_project_dir / "specs" / "002-another-feature" / "plan.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text("# Implementation Plan\n")
    
    doc = SpeckitDocument.load(plan_path, temp_project_dir)
    
    assert doc.document_type == DocumentType.PLAN
    assert doc.feature_id == "002"


def test_parse_sections(temp_project_dir):
    """Test parsing markdown sections"""
    content = """# Main Title

Introduction paragraph.

## Section 1

Section 1 content.

### Subsection 1.1

Subsection content.

## Section 2

Section 2 content.
"""
    
    doc_path = temp_project_dir / "test.md"
    doc_path.write_text(content)
    
    doc = SpeckitDocument.load(doc_path, temp_project_dir)
    
    assert len(doc.sections) == 1  # Only top-level section
    assert doc.sections[0].title == "Main Title"
    assert len(doc.sections[0].subsections) == 2  # Section 1 and Section 2
    
    section1 = doc.sections[0].subsections[0]
    assert section1.title == "Section 1"
    assert len(section1.subsections) == 1  # Subsection 1.1


def test_parse_requirements(temp_project_dir):
    """Test parsing requirements from markdown"""
    content = """# Requirements

**FR-001**: The system shall support markdown editing

**FR-002**: The system shall support syntax highlighting (P1)

**SC-001**: Users can edit documents successfully

**CHK-001**: Is markdown syntax documented?
"""
    
    doc_path = temp_project_dir / "spec.md"
    doc_path.write_text(content)
    
    doc = SpeckitDocument.load(doc_path, temp_project_dir)
    
    assert len(doc.requirements) == 4
    
    # Check FR-001
    fr001 = doc.get_requirement("FR-001")
    assert fr001 is not None
    assert fr001.type == RequirementType.FUNCTIONAL
    assert "markdown editing" in fr001.text
    
    # Check FR-002 with priority
    fr002 = doc.get_requirement("FR-002")
    assert fr002 is not None
    assert fr002.priority == "P1"
    
    # Check SC-001
    sc001 = doc.get_requirement("SC-001")
    assert sc001 is not None
    assert sc001.type == RequirementType.SUCCESS_CRITERIA
    
    # Check CHK-001
    chk001 = doc.get_requirement("CHK-001")
    assert chk001 is not None
    assert chk001.type == RequirementType.CHECKLIST


def test_get_section_by_title(temp_project_dir):
    """Test section lookup by title"""
    content = """# Main

## Features

### Editor

Editor content.

## Architecture

Architecture content.
"""
    
    doc_path = temp_project_dir / "doc.md"
    doc_path.write_text(content)
    
    doc = SpeckitDocument.load(doc_path, temp_project_dir)
    
    # Find top-level section
    features = doc.get_section("Features")
    assert features is not None
    assert features.title == "Features"
    
    # Find nested section
    editor = doc.get_section("Editor")
    assert editor is not None
    assert editor.title == "Editor"
    
    # Non-existent section
    missing = doc.get_section("NonExistent")
    assert missing is None


def test_document_save(temp_project_dir):
    """Test saving document to disk"""
    doc_path = temp_project_dir / "new_doc.md"
    
    doc = SpeckitDocument(
        path=doc_path,
        relative_path=Path("new_doc.md"),
        content="# New Document\n\nContent here.",
    )
    
    assert not doc_path.exists()
    assert doc.is_dirty is False
    
    doc.save()
    
    assert doc_path.exists()
    assert doc_path.read_text() == "# New Document\n\nContent here."
    assert doc.last_saved_at is not None


def test_document_dirty_flag(temp_project_dir):
    """Test dirty flag tracking"""
    doc_path = temp_project_dir / "doc.md"
    doc_path.write_text("# Original")
    
    doc = SpeckitDocument.load(doc_path, temp_project_dir)
    assert doc.is_dirty is False
    
    # Apply change
    from src.core import DocumentChange
    from uuid import uuid4
    
    change = DocumentChange(
        change_id=str(uuid4()),
        operation="insert",
        position=len(doc.content),
        old_text="",
        new_text="\n\nNew content",
    )
    
    doc.apply_change(change)
    
    assert doc.is_dirty is True
    assert "\n\nNew content" in doc.content
    
    # Save resets dirty flag
    doc.save()
    assert doc.is_dirty is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
