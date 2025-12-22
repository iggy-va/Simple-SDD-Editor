"""Unit tests for document validator"""

import tempfile
from pathlib import Path

import pytest

from src.core import (
    DocumentValidator,
    ProjectValidator,
    RequirementType,
    SpeckitDocument,
)


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        specs_dir = project_root / "specs"
        specs_dir.mkdir(parents=True)
        yield project_root


def test_validate_requirement_id_format(temp_project_dir):
    """Test requirement ID format validation"""
    content = """# Requirements

**FR-001**: Valid requirement

**FR-99**: Invalid - should be FR-099

**INVALID-001**: Invalid type

**FR001**: Missing hyphen
"""
    
    doc_path = temp_project_dir / "spec.md"
    doc_path.write_text(content)
    
    doc = SpeckitDocument.load(doc_path, temp_project_dir)
    validator = DocumentValidator()
    result = validator.validate(doc)
    
    assert not result.is_valid
    assert len(result.errors) > 0
    
    # Should find errors for invalid IDs
    error_messages = [e.message for e in result.errors]
    assert any("INVALID-001" in msg for msg in error_messages)


def test_validate_sequential_numbering(temp_project_dir):
    """Test sequential numbering validation"""
    content = """# Requirements

**FR-001**: First requirement

**FR-002**: Second requirement

**FR-005**: Skipped FR-003 and FR-004

**SC-001**: First success criteria

**SC-003**: Skipped SC-002
"""
    
    doc_path = temp_project_dir / "spec.md"
    doc_path.write_text(content)
    
    doc = SpeckitDocument.load(doc_path, temp_project_dir)
    validator = DocumentValidator()
    result = validator.validate(doc)
    
    # Should have warnings for non-sequential numbering
    assert len(result.warnings) >= 2  # FR and SC gaps
    
    warning_messages = [w.message for w in result.warnings]
    assert any("FR" in msg and "005" in msg for msg in warning_messages)
    assert any("SC" in msg and "003" in msg for msg in warning_messages)


def test_validate_duplicate_ids(temp_project_dir):
    """Test duplicate requirement ID detection"""
    content = """# Requirements

**FR-001**: First occurrence

Some text in between.

**FR-001**: Duplicate ID - should error

**FR-002**: Different ID
"""
    
    doc_path = temp_project_dir / "spec.md"
    doc_path.write_text(content)
    
    doc = SpeckitDocument.load(doc_path, temp_project_dir)
    validator = DocumentValidator()
    result = validator.validate(doc)
    
    assert not result.is_valid
    assert len(result.errors) >= 1
    
    error_messages = [e.message for e in result.errors]
    assert any("Duplicate" in msg and "FR-001" in msg for msg in error_messages)


def test_validate_cross_references(temp_project_dir):
    """Test cross-reference validation"""
    content = """# Requirements

**FR-001**: This requirement references FR-002

**FR-002**: This is valid

**FR-003**: This references FR-999 which doesn't exist
"""
    
    doc_path = temp_project_dir / "spec.md"
    doc_path.write_text(content)
    
    doc = SpeckitDocument.load(doc_path, temp_project_dir)
    validator = DocumentValidator()
    result = validator.validate(doc)
    
    # Should warn about FR-999 not found
    warning_messages = [w.message for w in result.warnings]
    assert any("FR-999" in msg for msg in warning_messages)


def test_validate_spec_structure(temp_project_dir):
    """Test spec.md structure validation"""
    # Missing recommended sections
    content = """# Spec Title

Just some content without proper sections.
"""
    
    doc_path = temp_project_dir / "specs" / "001-test" / "spec.md"
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(content)
    
    doc = SpeckitDocument.load(doc_path, temp_project_dir)
    validator = DocumentValidator()
    result = validator.validate(doc)
    
    # Should warn about missing sections
    warning_messages = [w.message for w in result.warnings]
    assert any("Missing" in msg and "sections" in msg for msg in warning_messages)


def test_validate_plan_structure(temp_project_dir):
    """Test plan.md structure validation"""
    # Missing recommended sections
    content = """# Plan

Missing technical context and project structure.
"""
    
    doc_path = temp_project_dir / "specs" / "001-test" / "plan.md"
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(content)
    
    doc = SpeckitDocument.load(doc_path, temp_project_dir)
    validator = DocumentValidator()
    result = validator.validate(doc)
    
    # Should warn about missing sections
    warning_messages = [w.message for w in result.warnings]
    assert any("Missing" in msg for msg in warning_messages)


def test_project_validator_directories(temp_project_dir):
    """Test project directory validation"""
    # Missing required directories
    validator = ProjectValidator(temp_project_dir)
    result = validator.validate()
    
    # specs/ exists but .specify/ doesn't
    assert not result.is_valid
    error_messages = [e.message for e in result.errors]
    assert any(".specify" in msg for msg in error_messages)


def test_project_validator_with_valid_structure(temp_project_dir):
    """Test project validation with valid structure"""
    # Create required directories
    (temp_project_dir / "specs").mkdir(exist_ok=True)
    (temp_project_dir / ".specify" / "templates").mkdir(parents=True)
    (temp_project_dir / ".specify" / "memory").mkdir(parents=True)
    
    # Create constitution
    constitution = temp_project_dir / ".specify" / "memory" / "constitution.md"
    constitution.write_text("# Constitution\n\nPrinciples go here.")
    
    validator = ProjectValidator(temp_project_dir)
    result = validator.validate()
    
    # Should pass validation
    assert result.is_valid or len(result.errors) == 0


def test_validation_result_add_error():
    """Test ValidationResult error tracking"""
    from src.core import ValidationResult
    
    result = ValidationResult(is_valid=True, errors=[], warnings=[])
    
    result.add_error("Test error", line=10, req_id="FR-001")
    
    assert not result.is_valid
    assert len(result.errors) == 1
    assert result.errors[0].severity == "error"
    assert result.errors[0].line_number == 10


def test_validation_result_add_warning():
    """Test ValidationResult warning tracking"""
    from src.core import ValidationResult
    
    result = ValidationResult(is_valid=True, errors=[], warnings=[])
    
    result.add_warning("Test warning", suggestion="Fix it this way")
    
    assert result.is_valid  # Warnings don't invalidate
    assert len(result.warnings) == 1
    assert result.warnings[0].severity == "warning"
    assert result.warnings[0].suggestion == "Fix it this way"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
