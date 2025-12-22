"""Document models and parsing for Speckit Editor"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import markdown


class DocumentType(Enum):
    """Type of speckit document"""
    SPEC = "spec"
    PLAN = "plan"
    TASKS = "tasks"
    CONSTITUTION = "constitution"
    CHECKLIST = "checklist"
    RESEARCH = "research"
    DATA_MODEL = "data-model"
    QUICKSTART = "quickstart"
    OTHER = "other"


class RequirementType(Enum):
    """Type of requirement identifier"""
    FUNCTIONAL = "FR"
    SUCCESS_CRITERIA = "SC"
    CHECKLIST = "CHK"
    TASK = "TSK"


@dataclass
class Section:
    """Hierarchical section in a document"""
    level: int  # Heading level (1-6)
    title: str  # Heading text
    content: str  # Section content (excluding subsections)
    line_start: int  # Starting line number
    line_end: int  # Ending line number
    subsections: List["Section"] = field(default_factory=list)


@dataclass
class Requirement:
    """A requirement or checklist item"""
    id: str  # e.g., "FR-001", "SC-005", "CHK-042"
    type: RequirementType  # FR | SC | CHK | TSK
    text: str  # Requirement description
    line_number: int  # Line in document
    priority: Optional[str] = None  # P1 | P2 | P3 | P4
    status: Optional[str] = None  # For CHK items: checked | unchecked
    references: List[str] = field(default_factory=list)  # Cross-references


@dataclass
class DocumentChange:
    """Represents a single edit operation for undo/redo"""
    change_id: str  # Unique identifier (UUID)
    operation: str  # insert | delete | replace
    position: int  # Character offset in document
    old_text: str  # Text before change (for undo)
    new_text: str  # Text after change (for redo)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SpeckitDocument:
    """Represents a single markdown document"""
    path: Path  # Absolute path to file
    relative_path: Path  # Path relative to project root
    content: str = ""  # Raw markdown content
    document_type: DocumentType = DocumentType.OTHER
    
    # Parsed structure (cached)
    frontmatter: Optional[Dict[str, Any]] = None
    sections: List[Section] = field(default_factory=list)
    requirements: List[Requirement] = field(default_factory=list)
    
    # Metadata
    feature_id: Optional[str] = None  # Feature ID if spec/plan/tasks
    template_source: Optional[str] = None
    
    # State tracking
    is_dirty: bool = False
    last_saved_at: Optional[datetime] = None
    last_modified_at: Optional[datetime] = None
    change_history: List[DocumentChange] = field(default_factory=list)
    
    # Validation
    validation_errors: List[str] = field(default_factory=list)
    
    @classmethod
    def load(cls, path: Path, project_root: Optional[Path] = None) -> "SpeckitDocument":
        """Load document from file"""
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {path}")
        
        content = path.read_text(encoding="utf-8")
        relative_path = path.relative_to(project_root) if project_root else path
        
        doc = cls(
            path=path,
            relative_path=relative_path,
            content=content,
            last_saved_at=datetime.fromtimestamp(path.stat().st_mtime),
            last_modified_at=datetime.fromtimestamp(path.stat().st_mtime),
        )
        
        doc._detect_document_type()
        doc.parse()
        
        return doc
    
    def _detect_document_type(self) -> None:
        """Detect document type from filename"""
        name = self.path.stem.lower()
        
        if name == "spec":
            self.document_type = DocumentType.SPEC
        elif name == "plan":
            self.document_type = DocumentType.PLAN
        elif name == "tasks":
            self.document_type = DocumentType.TASKS
        elif name == "constitution":
            self.document_type = DocumentType.CONSTITUTION
        elif "checklist" in name:
            self.document_type = DocumentType.CHECKLIST
        elif name == "research":
            self.document_type = DocumentType.RESEARCH
        elif name == "data-model":
            self.document_type = DocumentType.DATA_MODEL
        elif name == "quickstart":
            self.document_type = DocumentType.QUICKSTART
        else:
            self.document_type = DocumentType.OTHER
        
        # Extract feature ID from path (e.g., specs/001-feature/spec.md)
        if len(self.relative_path.parts) >= 2:
            folder = self.relative_path.parts[-2]
            match = re.match(r"(\d{3})-", folder)
            if match:
                self.feature_id = match.group(1)
    
    def parse(self) -> None:
        """Parse markdown into structured sections and requirements"""
        lines = self.content.split("\n")
        self.sections = []
        self.requirements = []
        
        # Parse sections
        current_section: Optional[Section] = None
        section_stack: List[Section] = []
        
        for i, line in enumerate(lines, start=1):
            # Check for markdown headers
            header_match = re.match(r"^(#{1,6})\s+(.+)", line)
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                
                section = Section(
                    level=level,
                    title=title,
                    content="",
                    line_start=i,
                    line_end=i,
                )
                
                # Pop sections from stack until we find the parent level
                while section_stack and section_stack[-1].level >= level:
                    section_stack.pop()
                
                # Add as subsection to parent or as root section
                if section_stack:
                    section_stack[-1].subsections.append(section)
                else:
                    self.sections.append(section)
                
                section_stack.append(section)
                current_section = section
            elif current_section:
                # Add content to current section
                current_section.content += line + "\n"
                current_section.line_end = i
        
        # Parse requirements
        req_pattern = re.compile(r"\*\*([A-Z]{2,4})-(\d{3})\*\*:\s*(.+)")
        for i, line in enumerate(lines, start=1):
            match = req_pattern.search(line)
            if match:
                req_type_str = match.group(1)
                req_num = match.group(2)
                req_text = match.group(3)
                
                try:
                    req_type = RequirementType(req_type_str)
                except ValueError:
                    continue  # Skip unknown requirement types
                
                req = Requirement(
                    id=f"{req_type_str}-{req_num}",
                    type=req_type,
                    text=req_text,
                    line_number=i,
                )
                
                # Check for priority markers (P1, P2, P3, P4)
                priority_match = re.search(r"\b(P[1-4])\b", line)
                if priority_match:
                    req.priority = priority_match.group(1)
                
                self.requirements.append(req)
    
    def save(self) -> None:
        """Write content to disk"""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self.content, encoding="utf-8")
        self.last_saved_at = datetime.now()
        self.is_dirty = False
    
    def apply_change(self, change: DocumentChange) -> None:
        """Apply edit and update change history"""
        # Apply the change based on operation type
        if change.operation == "insert":
            self.content = (
                self.content[:change.position]
                + change.new_text
                + self.content[change.position:]
            )
        elif change.operation == "delete":
            self.content = (
                self.content[:change.position]
                + self.content[change.position + len(change.old_text):]
            )
        elif change.operation == "replace":
            self.content = (
                self.content[:change.position]
                + change.new_text
                + self.content[change.position + len(change.old_text):]
            )
        
        self.change_history.append(change)
        self.is_dirty = True
        self.last_modified_at = datetime.now()
        
        # Re-parse after change
        self.parse()
    
    def get_requirement(self, req_id: str) -> Optional[Requirement]:
        """Lookup requirement by ID"""
        for req in self.requirements:
            if req.id == req_id:
                return req
        return None
    
    def get_section(self, title: str) -> Optional[Section]:
        """Lookup section by title (recursive search)"""
        def search_sections(sections: List[Section]) -> Optional[Section]:
            for section in sections:
                if section.title == title:
                    return section
                result = search_sections(section.subsections)
                if result:
                    return result
            return None
        
        return search_sections(self.sections)
