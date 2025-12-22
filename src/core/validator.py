"""Document validation for Speckit Editor"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

from .document import RequirementType, SpeckitDocument


@dataclass
class ValidationError:
    """Represents a validation error in a document"""
    severity: str  # error | warning | info
    message: str  # Human-readable error message
    line_number: Optional[int] = None  # Line where error occurs
    requirement_id: Optional[str] = None  # Related requirement ID
    suggestion: Optional[str] = None  # Suggested fix


@dataclass
class ValidationResult:
    """Result of validating a document or project"""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    
    def add_error(self, message: str, line: Optional[int] = None, 
                  req_id: Optional[str] = None, suggestion: Optional[str] = None) -> None:
        """Add an error to the result"""
        self.errors.append(ValidationError(
            severity="error",
            message=message,
            line_number=line,
            requirement_id=req_id,
            suggestion=suggestion
        ))
        self.is_valid = False
    
    def add_warning(self, message: str, line: Optional[int] = None,
                    req_id: Optional[str] = None, suggestion: Optional[str] = None) -> None:
        """Add a warning to the result"""
        self.warnings.append(ValidationError(
            severity="warning",
            message=message,
            line_number=line,
            requirement_id=req_id,
            suggestion=suggestion
        ))


class DocumentValidator:
    """Validates speckit documents"""
    
    # Valid requirement ID patterns
    REQ_PATTERN = re.compile(r"^(FR|SC|CHK|TSK)-(\d{3})$")
    
    def __init__(self):
        self.seen_ids: Set[str] = set()
    
    def validate(self, document: SpeckitDocument) -> ValidationResult:
        """Validate a single document"""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        self.seen_ids.clear()
        
        # Validate requirement IDs
        self._validate_requirement_ids(document, result)
        
        # Validate sequential numbering
        self._validate_sequential_numbering(document, result)
        
        # Validate cross-references
        self._validate_cross_references(document, result)
        
        # Validate duplicates
        self._validate_duplicates(document, result)
        
        # Validate document structure
        self._validate_structure(document, result)
        
        return result
    
    def _validate_requirement_ids(self, document: SpeckitDocument, 
                                  result: ValidationResult) -> None:
        """Validate requirement ID format"""
        for req in document.requirements:
            # Check pattern
            if not self.REQ_PATTERN.match(req.id):
                result.add_error(
                    message=f"Invalid requirement ID format: {req.id}",
                    line=req.line_number,
                    req_id=req.id,
                    suggestion=f"Use format: {req.type.value}-NNN (e.g., FR-001)"
                )
            
            # Track for duplicate detection
            self.seen_ids.add(req.id)
    
    def _validate_sequential_numbering(self, document: SpeckitDocument,
                                       result: ValidationResult) -> None:
        """Check that requirement numbers are sequential within each type"""
        # Group requirements by type
        by_type: Dict[RequirementType, List[int]] = {}
        
        for req in document.requirements:
            if req.type not in by_type:
                by_type[req.type] = []
            
            match = self.REQ_PATTERN.match(req.id)
            if match:
                number = int(match.group(2))
                by_type[req.type].append(number)
        
        # Check sequential numbering for each type
        for req_type, numbers in by_type.items():
            sorted_numbers = sorted(numbers)
            expected = 1
            
            for num in sorted_numbers:
                if num != expected:
                    result.add_warning(
                        message=f"Non-sequential {req_type.value} numbering: "
                               f"expected {req_type.value}-{expected:03d}, "
                               f"found {req_type.value}-{num:03d}",
                        suggestion="Renumber requirements sequentially starting from 001"
                    )
                expected = num + 1
    
    def _validate_cross_references(self, document: SpeckitDocument,
                                   result: ValidationResult) -> None:
        """Verify that cross-references point to existing requirements"""
        # Extract all requirement IDs from this document
        valid_ids = {req.id for req in document.requirements}
        
        # Look for references in requirement text
        ref_pattern = re.compile(r"\b(FR|SC|CHK|TSK)-(\d{3})\b")
        
        for req in document.requirements:
            refs = ref_pattern.findall(req.text)
            for ref_type, ref_num in refs:
                ref_id = f"{ref_type}-{ref_num}"
                
                # Skip self-references
                if ref_id == req.id:
                    continue
                
                # Check if reference exists in document
                if ref_id not in valid_ids:
                    result.add_warning(
                        message=f"Cross-reference {ref_id} not found in document",
                        line=req.line_number,
                        req_id=req.id,
                        suggestion=f"Ensure {ref_id} exists or is a valid external reference"
                    )
    
    def _validate_duplicates(self, document: SpeckitDocument,
                            result: ValidationResult) -> None:
        """Check for duplicate requirement IDs"""
        seen: Set[str] = set()
        
        for req in document.requirements:
            if req.id in seen:
                result.add_error(
                    message=f"Duplicate requirement ID: {req.id}",
                    line=req.line_number,
                    req_id=req.id,
                    suggestion=f"Use a unique ID for each requirement"
                )
            seen.add(req.id)
    
    def _validate_structure(self, document: SpeckitDocument,
                           result: ValidationResult) -> None:
        """Validate document structure based on type"""
        from .document import DocumentType
        
        if document.document_type == DocumentType.SPEC:
            self._validate_spec_structure(document, result)
        elif document.document_type == DocumentType.PLAN:
            self._validate_plan_structure(document, result)
        elif document.document_type == DocumentType.TASKS:
            self._validate_tasks_structure(document, result)
    
    def _validate_spec_structure(self, document: SpeckitDocument,
                                result: ValidationResult) -> None:
        """Validate spec.md structure"""
        required_sections = {
            "Overview",
            "Requirements",
            "Success Criteria",
        }
        
        found_sections = {section.title for section in document.sections}
        missing = required_sections - found_sections
        
        if missing:
            result.add_warning(
                message=f"Missing recommended sections: {', '.join(missing)}",
                suggestion="Add missing sections to follow speckit template"
            )
        
        # Check for at least one FR requirement
        has_fr = any(req.type == RequirementType.FUNCTIONAL 
                    for req in document.requirements)
        if not has_fr:
            result.add_warning(
                message="No functional requirements (FR) found",
                suggestion="Add at least one FR-NNN requirement"
            )
    
    def _validate_plan_structure(self, document: SpeckitDocument,
                                result: ValidationResult) -> None:
        """Validate plan.md structure"""
        required_sections = {
            "Technical Context",
            "Project Structure",
        }
        
        found_sections = {section.title for section in document.sections}
        missing = required_sections - found_sections
        
        if missing:
            result.add_warning(
                message=f"Missing recommended sections: {', '.join(missing)}",
                suggestion="Add missing sections to follow speckit template"
            )
    
    def _validate_tasks_structure(self, document: SpeckitDocument,
                                  result: ValidationResult) -> None:
        """Validate tasks.md structure"""
        # Check for task markers (T### or TSK-###)
        task_pattern = re.compile(r"\b(T|TSK)-?(\d{3})\b")
        
        has_tasks = False
        for line in document.content.split("\n"):
            if task_pattern.search(line):
                has_tasks = True
                break
        
        if not has_tasks:
            result.add_warning(
                message="No task identifiers (T### or TSK-###) found",
                suggestion="Add task IDs to track implementation progress"
            )


class ProjectValidator:
    """Validates entire speckit project structure"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
    
    def validate(self) -> ValidationResult:
        """Validate entire project structure"""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # Check for required directories
        self._validate_directories(result)
        
        # Check for constitution
        self._validate_constitution(result)
        
        # Check for .specify directory
        self._validate_specify_folder(result)
        
        return result
    
    def _validate_directories(self, result: ValidationResult) -> None:
        """Check for required directory structure"""
        required_dirs = [
            "specs",
            ".specify",
        ]
        
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                result.add_error(
                    message=f"Required directory not found: {dir_name}",
                    suggestion=f"Create {dir_name}/ directory in project root"
                )
    
    def _validate_constitution(self, result: ValidationResult) -> None:
        """Check for constitution file"""
        constitution_paths = [
            self.project_root / ".specify" / "memory" / "constitution.md",
            self.project_root / "constitution.md",
        ]
        
        found = False
        for path in constitution_paths:
            if path.exists():
                found = True
                break
        
        if not found:
            result.add_warning(
                message="No constitution.md found",
                suggestion="Create .specify/memory/constitution.md to define project principles"
            )
    
    def _validate_specify_folder(self, result: ValidationResult) -> None:
        """Check .specify folder structure"""
        specify_path = self.project_root / ".specify"
        
        if not specify_path.exists():
            result.add_error(
                message=".specify directory not found",
                suggestion="Initialize speckit project with .specify/ folder"
            )
            return
        
        # Check for templates
        templates_path = specify_path / "templates"
        if not templates_path.exists():
            result.add_warning(
                message="No templates/ directory found in .specify",
                suggestion="Create .specify/templates/ for document templates"
            )
