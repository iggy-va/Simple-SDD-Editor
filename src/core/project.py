"""Project model for Speckit Editor"""

import threading
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

import pygit2

from ..utils.config import ProjectSettings
from ..utils.logging import get_logger
from .document import DocumentType, SpeckitDocument
from .validator import ProjectValidator, ValidationResult

logger = get_logger(__name__)


class FileStatus(Enum):
    """Git file status"""
    UNMODIFIED = "unmodified"
    MODIFIED = "modified"
    ADDED = "added"
    DELETED = "deleted"
    RENAMED = "renamed"
    UNTRACKED = "untracked"
    CONFLICTED = "conflicted"


@dataclass
class GitCommit:
    """Git commit information"""
    sha: str
    message: str
    author: str
    author_email: str
    timestamp: datetime
    parent_shas: List[str]


@dataclass
class GitFileStatus:
    """Status of a single file in git"""
    path: str
    status: FileStatus
    staged: bool = False


@dataclass
class GitStatus:
    """Overall git repository status"""
    files: List[GitFileStatus]
    current_branch: Optional[str] = None
    ahead: int = 0  # Commits ahead of remote
    behind: int = 0  # Commits behind remote
    
    @property
    def has_changes(self) -> bool:
        return len(self.files) > 0
    
    @property
    def staged_files(self) -> List[GitFileStatus]:
        return [f for f in self.files if f.staged]
    
    @property
    def unstaged_files(self) -> List[GitFileStatus]:
        return [f for f in self.files if not f.staged]


class SpeckitProject:
    """Root aggregate for a Speckit project"""
    
    @staticmethod
    def create_new(root_path: Path, project_name: str, initialize_git: bool = True) -> "SpeckitProject":
        """Create a new Speckit project with proper structure
        
        Args:
            root_path: Parent directory where project will be created
            project_name: Name of the project (becomes folder name)
            initialize_git: Whether to initialize git repository
            
        Returns:
            SpeckitProject instance
            
        Raises:
            FileExistsError: If project directory already exists
            PermissionError: If cannot create directories
        """
        project_path = root_path / project_name
        
        if project_path.exists():
            raise FileExistsError(f"Directory already exists: {project_path}")
        
        logger.info(f"Creating new project: {project_path}")
        
        # Create project structure
        project_path.mkdir(parents=True, exist_ok=False)
        specify_dir = project_path / ".specify"
        specify_dir.mkdir()
        
        # Create subdirectories
        templates_dir = specify_dir / "templates"
        templates_dir.mkdir()
        (specify_dir / "memory").mkdir()
        (specify_dir / "scripts").mkdir()
        (project_path / "specs").mkdir()
        
        # Create default templates
        (templates_dir / "spec-template.md").write_text("""# [FEATURE_ID] - [FEATURE_NAME]

## Overview
Brief description of the feature.

## User Stories
- As a [user type], I want [goal] so that [benefit]

## Requirements
### Functional Requirements
- FR-001: Description

### Non-Functional Requirements
- NFR-001: Description

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Technical Notes
Implementation considerations.
""", encoding="utf-8")
        
        (templates_dir / "plan-template.md").write_text("""# Implementation Plan: [FEATURE_NAME]

## Technology Stack
- Language: 
- Framework: 
- Libraries: 

## Architecture
Describe the high-level architecture.

## Project Structure
```
project/
├── src/
└── tests/
```

## Dependencies
- Dependency 1
- Dependency 2

## Development Phases
1. Phase 1: Setup
2. Phase 2: Core implementation
3. Phase 3: Testing
""", encoding="utf-8")
        
        (templates_dir / "tasks-template.md").write_text("""# Tasks: [FEATURE_NAME]

## Phase 1: Setup
- [ ] T001 Create project structure
- [ ] T002 Setup dependencies

## Phase 2: Implementation
- [ ] T003 Implement core feature
- [ ] T004 Add tests

## Phase 3: Testing & Documentation
- [ ] T005 Integration testing
- [ ] T006 Documentation
""", encoding="utf-8")
        
        # Create initial constitution
        constitution = specify_dir / "memory" / "constitution.md"
        constitution.write_text(f"""# {project_name} - Project Constitution

## Purpose
Define the purpose and principles of this project here.

## Core Principles
1. Principle 1
2. Principle 2
3. Principle 3

## Technical Decisions
- Decision 1
- Decision 2
""", encoding="utf-8")
        
        # Create README
        readme = project_path / "README.md"
        readme.write_text(f"""# {project_name}

Created with Speckit Editor on {datetime.now().strftime('%Y-%m-%d')}

## Project Structure
- `specs/` - Feature specifications
- `.specify/templates/` - Document templates
- `.specify/memory/` - Project memory and constitution
- `.specify/scripts/` - Automation scripts
""", encoding="utf-8")
        
        # Initialize git if requested
        if initialize_git:
            import subprocess
            try:
                subprocess.run(["git", "init"], cwd=project_path, check=True, capture_output=True)
                subprocess.run(["git", "config", "user.name", "Speckit User"], cwd=project_path, check=False, capture_output=True)
                subprocess.run(["git", "config", "user.email", "user@speckit.local"], cwd=project_path, check=False, capture_output=True)
                
                # Initial commit
                subprocess.run(["git", "add", "."], cwd=project_path, check=True, capture_output=True)
                subprocess.run(["git", "commit", "-m", "Initial commit - Project created"], cwd=project_path, check=True, capture_output=True)
                logger.info("Git repository initialized")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Could not initialize git: {e}")
            except FileNotFoundError:
                logger.warning("Git not found - skipping git initialization")
        
        logger.info(f"Project created successfully: {project_path}")
        return SpeckitProject(root_path=project_path)
    
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
    
    def get_git_status(self) -> Optional[GitStatus]:
        """Get current git status"""
        if not self.git_repo:
            return None
        
        try:
            files = []
            status_flags = self.git_repo.status()
            
            for filepath, flags in status_flags.items():
                # Determine status
                if flags & pygit2.GIT_STATUS_CONFLICTED:
                    status = FileStatus.CONFLICTED
                elif flags & (pygit2.GIT_STATUS_INDEX_NEW | pygit2.GIT_STATUS_WT_NEW):
                    status = FileStatus.ADDED
                elif flags & (pygit2.GIT_STATUS_INDEX_DELETED | pygit2.GIT_STATUS_WT_DELETED):
                    status = FileStatus.DELETED
                elif flags & (pygit2.GIT_STATUS_INDEX_MODIFIED | pygit2.GIT_STATUS_WT_MODIFIED):
                    status = FileStatus.MODIFIED
                elif flags & (pygit2.GIT_STATUS_INDEX_RENAMED | pygit2.GIT_STATUS_WT_RENAMED):
                    status = FileStatus.RENAMED
                else:
                    status = FileStatus.UNTRACKED
                
                # Check if staged
                staged = bool(flags & (pygit2.GIT_STATUS_INDEX_NEW | 
                                     pygit2.GIT_STATUS_INDEX_MODIFIED | 
                                     pygit2.GIT_STATUS_INDEX_DELETED | 
                                     pygit2.GIT_STATUS_INDEX_RENAMED))
                
                files.append(GitFileStatus(
                    path=filepath,
                    status=status,
                    staged=staged
                ))
            
            # Get ahead/behind counts
            ahead, behind = 0, 0
            try:
                if not self.git_repo.head_is_unborn:
                    local_branch = self.git_repo.head
                    upstream = local_branch.upstream
                    if upstream:
                        ahead, behind = self.git_repo.ahead_behind(
                            local_branch.target, upstream.target
                        )
            except Exception:
                pass
            
            return GitStatus(
                files=files,
                current_branch=self.current_branch,
                ahead=ahead,
                behind=behind
            )
        except Exception as e:
            logger.error(f"Failed to get git status: {e}")
            return None
    
    def stage_file(self, filepath: str) -> bool:
        """Stage a file for commit"""
        if not self.git_repo:
            logger.warning("No git repository")
            return False
        
        try:
            self.git_repo.index.add(filepath)
            self.git_repo.index.write()
            logger.info(f"Staged file: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to stage {filepath}: {e}")
            return False
    
    def unstage_file(self, filepath: str) -> bool:
        """Unstage a file"""
        if not self.git_repo:
            logger.warning("No git repository")
            return False
        
        try:
            # Reset to HEAD
            self.git_repo.index.remove(filepath)
            self.git_repo.index.write()
            logger.info(f"Unstaged file: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to unstage {filepath}: {e}")
            return False
    
    def commit(self, message: str, author_name: Optional[str] = None, 
               author_email: Optional[str] = None) -> Optional[str]:
        """Create a git commit"""
        if not self.git_repo:
            logger.warning("No git repository")
            return None
        
        try:
            # Get author from config or use defaults
            if not author_name or not author_email:
                try:
                    config = self.git_repo.config
                    author_name = author_name or config['user.name']
                    author_email = author_email or config['user.email']
                except Exception:
                    author_name = author_name or "Speckit User"
                    author_email = author_email or "user@example.com"
            
            # Create signature
            author = pygit2.Signature(author_name, author_email)
            
            # Get tree from index
            tree = self.git_repo.index.write_tree()
            
            # Get parent commit
            parents = []
            if not self.git_repo.head_is_unborn:
                parents = [self.git_repo.head.target]
            
            # Create commit
            commit_sha = self.git_repo.create_commit(
                'HEAD',
                author,
                author,
                message,
                tree,
                parents
            )
            
            logger.info(f"Created commit: {commit_sha}")
            return str(commit_sha)
        except Exception as e:
            logger.error(f"Failed to commit: {e}")
            return None
    
    def get_file_diff(self, filepath: str) -> Optional[str]:
        """Get diff for a specific file"""
        if not self.git_repo:
            return None
        
        try:
            # Get HEAD tree
            if self.git_repo.head_is_unborn:
                # No commits yet, show as new file
                file_path = self.root_path / filepath
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8')
                    lines = content.split('\n')
                    diff_text = f"--- /dev/null\n+++ b/{filepath}\n"
                    for i, line in enumerate(lines, 1):
                        diff_text += f"+{i}: {line}\n"
                    return diff_text
                return None
            
            head_commit = self.git_repo.head.peel(pygit2.Commit)
            head_tree = head_commit.tree
            
            # Get diff
            diff = self.git_repo.diff(head_tree, flags=pygit2.GIT_DIFF_INCLUDE_UNTRACKED)
            
            # Find the patch for this file
            for patch in diff:
                if patch.delta.new_file.path == filepath:
                    return patch.text
            
            return None
        except Exception as e:
            logger.error(f"Failed to get diff for {filepath}: {e}")
            return None
    
    def get_branches(self) -> List[str]:
        """Get list of all local branches"""
        if not self.git_repo:
            return []
        
        try:
            return list(self.git_repo.branches.local)
        except Exception as e:
            logger.error(f"Failed to get branches: {e}")
            return []
    
    def checkout_branch(self, branch_name: str) -> bool:
        """Checkout a branch"""
        if not self.git_repo:
            logger.warning("No git repository")
            return False
        
        try:
            branch = self.git_repo.branches.get(branch_name)
            if not branch:
                logger.error(f"Branch not found: {branch_name}")
                return False
            
            # Checkout the branch
            self.git_repo.checkout(branch)
            self.git_repo.set_head(branch.name)
            self.current_branch = branch_name
            logger.info(f"Checked out branch: {branch_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to checkout branch {branch_name}: {e}")
            return False
    
    def create_branch(self, branch_name: str, checkout: bool = True) -> bool:
        """Create a new branch"""
        if not self.git_repo:
            logger.warning("No git repository")
            return False
        
        try:
            # Get current commit
            if self.git_repo.head_is_unborn:
                logger.error("Cannot create branch: no commits yet")
                return False
            
            commit = self.git_repo.head.peel(pygit2.Commit)
            
            # Create branch
            self.git_repo.branches.local.create(branch_name, commit)
            logger.info(f"Created branch: {branch_name}")
            
            # Optionally checkout
            if checkout:
                return self.checkout_branch(branch_name)
            
            return True
        except Exception as e:
            logger.error(f"Failed to create branch {branch_name}: {e}")
            return False
    
    def push(self, remote_name: str = "origin", branch_name: Optional[str] = None) -> tuple[bool, str]:
        """Push to remote repository
        
        Returns:
            tuple[bool, str]: (success, message)
        """
        if not self.git_repo:
            return False, "No git repository"
        
        try:
            # Use current branch if not specified
            if not branch_name:
                branch_name = self.current_branch
            
            if not branch_name:
                return False, "No branch to push"
            
            # Get remote
            try:
                remote = self.git_repo.remotes[remote_name]
            except KeyError:
                return False, f"Remote '{remote_name}' not found"
            
            # Get local branch
            try:
                local_branch = self.git_repo.branches.get(branch_name)
                if not local_branch:
                    return False, f"Branch '{branch_name}' not found"
            except Exception:
                return False, f"Branch '{branch_name}' not found"
            
            # Push
            refspec = f"refs/heads/{branch_name}:refs/heads/{branch_name}"
            try:
                remote.push([refspec])
                logger.info(f"Pushed {branch_name} to {remote_name}")
                return True, f"Successfully pushed to {remote_name}"
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Push failed: {error_msg}")
                return False, f"Push failed: {error_msg}"
                
        except Exception as e:
            logger.error(f"Push operation failed: {e}")
            return False, f"Push failed: {str(e)}"
    
    def pull(self, remote_name: str = "origin", branch_name: Optional[str] = None) -> tuple[bool, str]:
        """Pull from remote repository
        
        Returns:
            tuple[bool, str]: (success, message)
        """
        if not self.git_repo:
            return False, "No git repository"
        
        try:
            # Use current branch if not specified
            if not branch_name:
                branch_name = self.current_branch
            
            if not branch_name:
                return False, "No branch to pull"
            
            # Get remote
            try:
                remote = self.git_repo.remotes[remote_name]
            except KeyError:
                return False, f"Remote '{remote_name}' not found"
            
            # Fetch first
            try:
                remote.fetch()
                logger.info(f"Fetched from {remote_name}")
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Fetch failed: {error_msg}")
                return False, f"Fetch failed: {error_msg}"
            
            # Get remote branch
            remote_branch_name = f"{remote_name}/{branch_name}"
            try:
                remote_ref = self.git_repo.references.get(f"refs/remotes/{remote_branch_name}")
                if not remote_ref:
                    return False, f"Remote branch '{remote_branch_name}' not found"
            except Exception:
                return False, f"Remote branch '{remote_branch_name}' not found"
            
            # Get current HEAD
            if self.git_repo.head_is_unborn:
                return False, "Cannot pull: no commits yet"
            
            local_commit = self.git_repo.head.peel(pygit2.Commit)
            remote_commit = remote_ref.peel(pygit2.Commit)
            
            # Check if already up to date
            if local_commit.id == remote_commit.id:
                logger.info("Already up to date")
                return True, "Already up to date"
            
            # Perform merge
            merge_result, _ = self.git_repo.merge_analysis(remote_commit.id)
            
            if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
                return True, "Already up to date"
            elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
                # Fast-forward merge
                self.git_repo.checkout_tree(remote_commit)
                self.git_repo.head.set_target(remote_commit.id)
                logger.info(f"Fast-forwarded to {remote_commit.id}")
                return True, "Successfully pulled (fast-forward)"
            elif merge_result & pygit2.GIT_MERGE_ANALYSIS_NORMAL:
                # Normal merge required
                self.git_repo.merge(remote_commit.id)
                
                # Check for conflicts
                if self.git_repo.index.conflicts:
                    logger.warning("Merge conflicts detected")
                    return False, "Merge conflicts detected - please resolve manually"
                
                # Create merge commit
                user_sig = self.git_repo.default_signature
                tree = self.git_repo.index.write_tree()
                message = f"Merge {remote_branch_name} into {branch_name}"
                
                self.git_repo.create_commit(
                    'HEAD',
                    user_sig,
                    user_sig,
                    message,
                    tree,
                    [local_commit.id, remote_commit.id]
                )
                
                logger.info(f"Merged {remote_branch_name}")
                return True, "Successfully pulled (merge)"
            else:
                return False, "Cannot pull: unexpected merge analysis result"
                
        except Exception as e:
            logger.error(f"Pull operation failed: {e}")
            return False, f"Pull failed: {str(e)}"
    
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
        """Save document to disk with permission error handling"""
        try:
            # Ensure parent directory exists
            doc.path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write document content
            doc.path.write_text(doc.content, encoding="utf-8")
            
            # Update timestamp
            doc.last_saved_at = datetime.now()
            doc.is_dirty = False
            
        except PermissionError as e:
            logger.error(f"Permission denied writing to {doc.path}: {e}")
            raise PermissionError(
                f"Permission denied: Cannot write to '{doc.path.name}'.\n\n"
                f"This file may be:\n"
                f"• Opened in another program\n"
                f"• Read-only or protected\n"
                f"• In a restricted directory\n\n"
                f"Please check file permissions and try again."
            ) from e
        except OSError as e:
            logger.error(f"File system error writing to {doc.path}: {e}")
            raise OSError(
                f"File system error: Cannot write to '{doc.path.name}'.\n\n"
                f"Possible causes:\n"
                f"• Disk is full\n"
                f"• File path is too long\n"
                f"• Network drive is unavailable\n\n"
                f"Error: {str(e)}"
            ) from e


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
