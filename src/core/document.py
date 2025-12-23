"""Document models and parsing for Speckit Editor"""

import json
import re
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import markdown

from ..utils.logging import get_logger

logger = get_logger(__name__)


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
        """Load document from file (with lazy loading for large files >5MB)"""
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {path}")
        
        try:
            # Check file size
            file_size = path.stat().st_size
            is_large_file = file_size > 5 * 1024 * 1024  # 5MB threshold
            
            if is_large_file:
                logger.warning(f"Large file detected ({file_size / (1024*1024):.1f} MB): {path}")
            
            content = path.read_text(encoding="utf-8")
            
        except PermissionError as e:
            logger.error(f"Permission denied reading {path}: {e}")
            raise PermissionError(
                f"Permission denied: Cannot read '{path.name}'.\n\n"
                f"This file may be:\n"
                f"• Opened exclusively by another program\n"
                f"• Protected by file system permissions\n"
                f"• In a restricted directory\n\n"
                f"Please check file permissions and try again."
            ) from e
        except OSError as e:
            logger.error(f"File system error reading {path}: {e}")
            raise OSError(
                f"File system error: Cannot read '{path.name}'.\n\n"
                f"Possible causes:\n"
                f"• File path is too long\n"
                f"• Network drive is unavailable\n"
                f"• File is corrupted\n\n"
                f"Error: {str(e)}"
            ) from e
        
        relative_path = path.relative_to(project_root) if project_root else path
        
        doc = cls(
            path=path,
            relative_path=relative_path,
            content=content,
            last_saved_at=datetime.fromtimestamp(path.stat().st_mtime),
            last_modified_at=datetime.fromtimestamp(path.stat().st_mtime),
        )
        
        doc._detect_document_type()
        
        # Defer parsing for large files (parse on demand)
        if not is_large_file:
            doc.parse()
        else:
            logger.info(f"Deferring parse for large file: {path}")
        
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


@dataclass
class AIMessage:
    """A message in an AI conversation"""
    role: str  # "user" | "assistant" | "system"
    content: str  # Message text
    timestamp: datetime = field(default_factory=datetime.now)
    
    # For assistant messages that suggest edits
    suggestion_text: Optional[str] = None  # Suggested text to insert
    suggestion_position: Optional[int] = None  # Character offset where to insert
    accepted: bool = False  # Whether user accepted this suggestion


@dataclass
class AISession:
    """An AI assistance session for a document"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_path: Optional[Path] = None  # Associated document
    messages: List[AIMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Session state
    context_type: Optional[str] = None  # "inline" | "chat" | "completion"
    cursor_position: Optional[int] = None  # Cursor position when session started
    selected_text: Optional[str] = None  # Text selection when session started
    
    def add_message(self, role: str, content: str, 
                   suggestion_text: Optional[str] = None,
                   suggestion_position: Optional[int] = None) -> AIMessage:
        """Add a message to the conversation"""
        message = AIMessage(
            role=role,
            content=content,
            suggestion_text=suggestion_text,
            suggestion_position=suggestion_position
        )
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message
    
    def accept_suggestion(self, message: AIMessage) -> None:
        """Mark a suggestion as accepted"""
        message.accepted = True
        self.updated_at = datetime.now()
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation in format suitable for AI API"""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for persistence"""
        return {
            'session_id': self.session_id,
            'document_path': str(self.document_path) if self.document_path else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'context_type': self.context_type,
            'cursor_position': self.cursor_position,
            'selected_text': self.selected_text,
            'messages': [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'suggestion_text': msg.suggestion_text,
                    'suggestion_position': msg.suggestion_position,
                    'accepted': msg.accepted
                }
                for msg in self.messages
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AISession':
        """Create session from dictionary"""
        messages = [
            AIMessage(
                role=msg['role'],
                content=msg['content'],
                timestamp=datetime.fromisoformat(msg['timestamp']),
                suggestion_text=msg.get('suggestion_text'),
                suggestion_position=msg.get('suggestion_position'),
                accepted=msg.get('accepted', False)
            )
            for msg in data.get('messages', [])
        ]
        
        return cls(
            session_id=data['session_id'],
            document_path=Path(data['document_path']) if data.get('document_path') else None,
            messages=messages,
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            context_type=data.get('context_type'),
            cursor_position=data.get('cursor_position'),
            selected_text=data.get('selected_text')
        )
    
    @staticmethod
    def init_database(cache_dir: Path) -> None:
        """Initialize SQLite database for session history"""
        db_path = cache_dir / "ai_sessions.db"
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_sessions (
                    session_id TEXT PRIMARY KEY,
                    document_path TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    context_type TEXT,
                    cursor_position INTEGER,
                    selected_text TEXT,
                    messages TEXT NOT NULL
                )
            ''')
            
            # Create index for faster lookups by document
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_document
                ON ai_sessions(document_path)
            ''')
            
            # Create index for recent sessions
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_updated
                ON ai_sessions(updated_at DESC)
            ''')
            
            conn.commit()
            conn.close()
            
            logger.debug("AI sessions database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI sessions database: {e}")
    
    def save_to_database(self, cache_dir: Path) -> None:
        """Save session to database"""
        db_path = cache_dir / "ai_sessions.db"
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            session_data = self.to_dict()
            
            cursor.execute('''
                INSERT OR REPLACE INTO ai_sessions
                (session_id, document_path, created_at, updated_at, 
                 context_type, cursor_position, selected_text, messages)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.session_id,
                str(self.document_path) if self.document_path else None,
                self.created_at.isoformat(),
                self.updated_at.isoformat(),
                self.context_type,
                self.cursor_position,
                self.selected_text,
                json.dumps(session_data['messages'])
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Saved AI session {self.session_id} to database")
            
        except Exception as e:
            logger.error(f"Failed to save AI session: {e}")
    
    @staticmethod
    def load_sessions_for_document(cache_dir: Path, document_path: Path) -> List['AISession']:
        """Load all sessions for a specific document"""
        db_path = cache_dir / "ai_sessions.db"
        
        if not db_path.exists():
            return []
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT session_id, document_path, created_at, updated_at,
                       context_type, cursor_position, selected_text, messages
                FROM ai_sessions
                WHERE document_path = ?
                ORDER BY updated_at DESC
            ''', (str(document_path),))
            
            sessions = []
            for row in cursor.fetchall():
                messages_data = json.loads(row[7])
                session_data = {
                    'session_id': row[0],
                    'document_path': row[1],
                    'created_at': row[2],
                    'updated_at': row[3],
                    'context_type': row[4],
                    'cursor_position': row[5],
                    'selected_text': row[6],
                    'messages': messages_data
                }
                sessions.append(AISession.from_dict(session_data))
            
            conn.close()
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to load AI sessions: {e}")
            return []
    
    @staticmethod
    def load_recent_sessions(cache_dir: Path, limit: int = 10) -> List['AISession']:
        """Load most recent sessions across all documents"""
        db_path = cache_dir / "ai_sessions.db"
        
        if not db_path.exists():
            return []
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT session_id, document_path, created_at, updated_at,
                       context_type, cursor_position, selected_text, messages
                FROM ai_sessions
                ORDER BY updated_at DESC
                LIMIT ?
            ''', (limit,))
            
            sessions = []
            for row in cursor.fetchall():
                messages_data = json.loads(row[7])
                session_data = {
                    'session_id': row[0],
                    'document_path': row[1],
                    'created_at': row[2],
                    'updated_at': row[3],
                    'context_type': row[4],
                    'cursor_position': row[5],
                    'selected_text': row[6],
                    'messages': messages_data
                }
                sessions.append(AISession.from_dict(session_data))
            
            conn.close()
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to load recent AI sessions: {e}")
            return []
