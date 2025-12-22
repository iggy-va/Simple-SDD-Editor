"""Project model for Speckit Editor"""

import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

import pygit2

from ..utils.config import ProjectSettings
from ..utils.logging import get_logger
from .document import DocumentType, SpeckitDocument
from .validator import ProjectValidator, ValidationResult

logger = get_logger(__name__)


class SpeckitProject:
    """Root aggregate for a Speckit project"""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.name = root_path.name
        
        # Constitution
        self.constitution_path = self._find_constitution()
        
        # Documents (lazy-loaded cache)
        self._documents: Dict[Path, SpeckitDocument] = {}
        self._documents_lock = threading.Lock()
        
        # Git integration
        self.git_repo: Optional[pygit2.Repository] = None
        self._init_git_repo()
        
        # Branches
        self.branches: Dict[str, "FeatureBranch"] = {}
        self.current_branch: Optional[str] = None
        self._scan_branches()
        
        # Settings
        self.settings = ProjectSettings.load(root_path / ".specify" / "settings.json")
        
        # Search index (lazy-initialized)
        self._index: Optional["DocumentIndex"] = None
        self._index_lock = threading.Lock()
        
        # Timestamps
        self.created_at: Optional[datetime] = None
        self.last_modified_at: Optional[datetime] = None
        self._update_timestamps()
    
    def _find_constitution(self) -> Optional[Path]:
        """Locate constitution.md file"""
        candidates = [
            self.root_path / ".specify" / "memory" / "constitution.md",
            self.root_path / "constitution.md",
        ]
        
        for path in candidates:
            if path.exists():
                logger.info(f"Found constitution: {path}")
                return path
        
        logger.warning("No constitution.md found")
        return None
    
    def _init_git_repo(self) -> None:
        """Initialize git repository connection"""
        try:
            self.git_repo = pygit2.Repository(str(self.root_path))
            logger.info(f"Git repository loaded: {self.root_path}")
        except Exception as e:
            logger.warning(f"Not a git repository: {e}")
            self.git_repo = None
    
    def _scan_branches(self) -> None:
        """Scan git branches for feature branches"""
        if not self.git_repo:
            return
        
        try:
            # Get current branch
            if not self.git_repo.head_is_unborn:
                self.current_branch = self.git_repo.head.shorthand
            
            # Scan all branches
            for branch_name in self.git_repo.branches.local:
                # Look for feature branch pattern (e.g., 001-feature-name)
                if branch_name.startswith(tuple("0123456789")):
                    self.branches[branch_name] = FeatureBranch(
                        name=branch_name,
                        project_root=self.root_path,
                    )
            
            logger.info(f"Found {len(self.branches)} feature branches")
        except Exception as e:
            logger.error(f"Error scanning branches: {e}")
    
    def _update_timestamps(self) -> None:
        """Update project timestamps from git or filesystem"""
        if self.git_repo:
            try:
                # Use first commit time as created_at
                walker = self.git_repo.walk(
                    self.git_repo.head.target,
                    pygit2.GIT_SORT_TIME | pygit2.GIT_SORT_REVERSE
                )
                first_commit = next(walker, None)
                if first_commit:
                    self.created_at = datetime.fromtimestamp(first_commit.commit_time)
                
                # Use latest commit time as last_modified_at
                latest = self.git_repo.revparse_single("HEAD")
                if latest:
                    self.last_modified_at = datetime.fromtimestamp(latest.commit_time)
            except Exception as e:
                logger.warning(f"Could not determine git timestamps: {e}")
        
        # Fallback to filesystem timestamps
        if not self.created_at:
            self.created_at = datetime.fromtimestamp(self.root_path.stat().st_ctime)
        if not self.last_modified_at:
            self.last_modified_at = datetime.fromtimestamp(self.root_path.stat().st_mtime)
    
    def scan_documents(self, pattern: str = "**/*.md") -> List[Path]:
        """Enumerate documents matching pattern (lazy, no parsing)"""
        logger.info(f"Scanning for documents: {pattern}")
        
        # Exclude certain directories
        exclude_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv"}
        
        documents = []
        for path in self.root_path.rglob(pattern):
            # Skip if in excluded directory
            if any(excluded in path.parts for excluded in exclude_dirs):
                continue
            
            documents.append(path)
        
        logger.info(f"Found {len(documents)} documents")
        return documents
    
    def get_document(self, path: Path, force_reload: bool = False) -> SpeckitDocument:
        """Load document with caching"""
        absolute_path = path if path.is_absolute() else self.root_path / path
        
        with self._documents_lock:
            # Return cached document if available
            if not force_reload and absolute_path in self._documents:
                return self._documents[absolute_path]
            
            # Load and cache
            logger.debug(f"Loading document: {absolute_path}")
            document = SpeckitDocument.load(absolute_path, project_root=self.root_path)
            self._documents[absolute_path] = document
            
            return document
    
    def create_feature_branch(self, feature_id: str, feature_name: str,
                             from_branch: str = "main") -> "FeatureBranch":
        """Create a new feature branch"""
        if not self.git_repo:
            raise RuntimeError("Not a git repository")
        
        branch_name = f"{feature_id}-{feature_name}"
        
        # Check if branch already exists
        if branch_name in self.git_repo.branches.local:
            raise ValueError(f"Branch already exists: {branch_name}")
        
        # Create branch from specified base
        base_branch = self.git_repo.branches.get(from_branch)
        if not base_branch:
            raise ValueError(f"Base branch not found: {from_branch}")
        
        # Create new branch
        new_branch = self.git_repo.branches.local.create(
            branch_name,
            base_branch.peel()
        )
        
        logger.info(f"Created feature branch: {branch_name}")
        
        # Create FeatureBranch object
        feature_branch = FeatureBranch(
            name=branch_name,
            project_root=self.root_path,
        )
        self.branches[branch_name] = feature_branch
        
        return feature_branch
    
    def validate_structure(self) -> ValidationResult:
        """Validate project structure against speckit conventions"""
        logger.info("Validating project structure")
        
        validator = ProjectValidator(self.root_path)
        result = validator.validate()
        
        if result.is_valid:
            logger.info("✓ Project structure valid")
        else:
            logger.warning(f"✗ Project validation failed: {len(result.errors)} errors")
        
        return result
    
    def rebuild_index(self, background: bool = True) -> None:
        """Rebuild search index for all documents"""
        if background:
            thread = threading.Thread(target=self._rebuild_index_task, daemon=True)
            thread.start()
            logger.info("Started background index rebuild")
        else:
            self._rebuild_index_task()
    
    def _rebuild_index_task(self) -> None:
        """Background task to rebuild search index"""
        logger.info("Rebuilding document index...")
        
        try:
            from .search import DocumentIndex
            
            with self._index_lock:
                self._index = DocumentIndex(self.root_path)
                
                # Index all markdown documents
                documents = self.scan_documents("**/*.md")
                for doc_path in documents:
                    try:
                        doc = self.get_document(doc_path)
                        self._index.add_document(doc)
                    except Exception as e:
                        logger.error(f"Failed to index {doc_path}: {e}")
            
            logger.info(f"Index rebuilt: {len(documents)} documents")
        except Exception as e:
            logger.error(f"Index rebuild failed: {e}")
    
    def get_feature_documents(self, feature_id: str) -> List[Path]:
        """Get all documents for a feature"""
        feature_dir = self.root_path / "specs" / f"{feature_id}-*"
        docs = []
        for dir_path in self.root_path.glob(str(feature_dir.relative_to(self.root_path))):
            if dir_path.is_dir():
                docs.extend(dir_path.glob("*.md"))
        return docs
    
    def create_document(self, path: Path, doc_type: DocumentType, content: str = "") -> SpeckitDocument:
        """Create new document"""
        doc_path = self.root_path / path if not path.is_absolute() else path
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text(content, encoding="utf-8")
        doc = SpeckitDocument(doc_path, doc_type)
        with self._documents_lock:
            self._documents[doc_path] = doc
        return doc
    
    def save_document(self, doc: SpeckitDocument) -> None:
        """Save document to disk"""
        doc.path.write_text(doc.content, encoding="utf-8")


class FeatureBranch:
    """Represents a feature branch with associated spec/plan/tasks"""
    
    def __init__(self, name: str, project_root: Path):
        self.name = name
        self.project_root = project_root
        
        # Extract feature ID from branch name (e.g., "001" from "001-feature-name")
        self.feature_id = name.split("-")[0] if "-" in name else name
        
        # Document paths
        self.spec_path = self._find_document("spec.md")
        self.plan_path = self._find_document("plan.md")
        self.tasks_path = self._find_document("tasks.md")
        
        # Git metadata (lazy-loaded)
        self._ahead_count: Optional[int] = None
        self._behind_count: Optional[int] = None
        self._last_commit: Optional[datetime] = None
    
    def _find_document(self, filename: str) -> Optional[Path]:
        """Find document in feature directory"""
        # Look in specs/{feature_id}/ directory
        feature_dir = self.project_root / "specs" / f"{self.feature_id}-*"
        
        for dir_path in self.project_root.glob(str(feature_dir.relative_to(self.project_root))):
            if dir_path.is_dir():
                doc_path = dir_path / filename
                if doc_path.exists():
                    return doc_path
        
        return None
    
    def get_ahead_behind_counts(self, base_branch: str = "main") -> tuple[int, int]:
        """Calculate commits ahead/behind base branch"""
        # This would require git operations - placeholder for now
        return (0, 0)
