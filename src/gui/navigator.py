"""Project navigator tree view for Speckit projects"""

from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt, Signal, QFileSystemWatcher
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QTreeView

from ..core import SpeckitProject
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ProjectTreeNode:
    """Node in the project tree"""
    
    def __init__(self, path: Path, parent: Optional["ProjectTreeNode"] = None):
        self.path = path
        self.parent = parent
        self.children: list[ProjectTreeNode] = []
        self._loaded = False
        self.change_status: str = ""  # "", "modified", "added", "deleted"
    
    def load_children(self) -> None:
        """Lazy load children for this node"""
        if self._loaded:
            return
        
        if self.path.is_dir():
            try:
                # Sort: directories first, then files alphabetically
                entries = sorted(self.path.iterdir(), 
                               key=lambda p: (not p.is_dir(), p.name.lower()))
                
                for entry in entries:
                    # Skip hidden files and common excludes
                    if entry.name.startswith('.') or entry.name in ('__pycache__', 'node_modules', 'venv'):
                        continue
                    
                    child = ProjectTreeNode(entry, parent=self)
                    self.children.append(child)
                
                self._loaded = True
                logger.debug(f"Loaded {len(self.children)} children for {self.path.name}")
                
            except Exception as e:
                logger.error(f"Failed to load children for {self.path}: {e}")
    
    def child_at(self, row: int) -> Optional["ProjectTreeNode"]:
        """Get child at given row"""
        if 0 <= row < len(self.children):
            return self.children[row]
        return None
    
    def row_index(self) -> int:
        """Get this node's row index in parent"""
        if self.parent:
            return self.parent.children.index(self)
        return 0


class LazyProjectModel(QAbstractItemModel):
    """Lazy-loading model for project tree (handles 1000+ files efficiently)"""
    
    def __init__(self, project: Optional[SpeckitProject] = None, parent=None):
        super().__init__(parent)
        self.project = project
        self.root_node: Optional[ProjectTreeNode] = None
        
        if project:
            self.set_project(project)
    
    def set_project(self, project: SpeckitProject) -> None:
        """Set the project to display"""
        self.beginResetModel()
        self.project = project
        self.root_node = ProjectTreeNode(project.root_path)
        self.root_node.load_children()
        self.endResetModel()
        logger.info(f"Loaded project tree: {project.name}")
    
    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        """Create model index for given position"""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        
        if not parent.isValid():
            # Root level
            parent_node = self.root_node
        else:
            parent_node = parent.internalPointer()
        
        if parent_node:
            child_node = parent_node.child_at(row)
            if child_node:
                return self.createIndex(row, column, child_node)
        
        return QModelIndex()
    
    def parent(self, index: QModelIndex) -> QModelIndex:
        """Get parent index"""
        if not index.isValid():
            return QModelIndex()
        
        node = index.internalPointer()
        if not node or not node.parent or node.parent == self.root_node:
            return QModelIndex()
        
        parent_node = node.parent
        return self.createIndex(parent_node.row_index(), 0, parent_node)
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Get number of rows under parent"""
        if parent.column() > 0:
            return 0
        
        if not parent.isValid():
            parent_node = self.root_node
        else:
            parent_node = parent.internalPointer()
        
        if parent_node:
            # Lazy load children when rowCount is queried
            parent_node.load_children()
            return len(parent_node.children)
        
        return 0
    
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Get number of columns"""
        return 1  # Single column: file/folder name
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """Get data for index"""
        if not index.isValid():
            return None
        
        node = index.internalPointer()
        if not node:
            return None
        
        if role == Qt.DisplayRole:
            return node.path.name
        
        elif role == Qt.DecorationRole:
            # Return icon based on file type
            return self._get_icon_for_path(node.path)
        
        elif role == Qt.ToolTipRole:
            # Show full path as tooltip
            if self.project:
                try:
                    rel_path = node.path.relative_to(self.project.root_path)
                    return str(rel_path)
                except ValueError:
                    pass
            return str(node.path)
        
        elif role == Qt.UserRole:
            # Store full path for easy access
            return node.path
        
        return None
    
    def _get_icon_for_path(self, path: Path) -> Optional[QIcon]:
        """Get icon for file/folder based on type"""
        # Use Qt standard icons for simplicity
        from PySide6.QtWidgets import QApplication, QStyle
        
        style = QApplication.style()
        
        if path.is_dir():
            # Folder icons
            if path.name == 'specs':
                return style.standardIcon(QStyle.SP_DirIcon)
            elif path.name == '.specify' or path.name.startswith('.'):
                return style.standardIcon(QStyle.SP_DirClosedIcon)
            else:
                return style.standardIcon(QStyle.SP_DirIcon)
        
        else:
            # File icons based on name
            name_lower = path.name.lower()
            
            if name_lower == 'spec.md':
                return style.standardIcon(QStyle.SP_FileDialogDetailedView)
            elif name_lower == 'plan.md':
                return style.standardIcon(QStyle.SP_FileDialogListView)
            elif name_lower == 'tasks.md':
                return style.standardIcon(QStyle.SP_FileDialogContentsView)
            elif name_lower.endswith('.md'):
                return style.standardIcon(QStyle.SP_FileIcon)
            else:
                return style.standardIcon(QStyle.SP_FileIcon)
        
        return None
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Get item flags"""
        if not index.isValid():
            return Qt.NoItemFlags
        
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    def hasChildren(self, parent: QModelIndex = QModelIndex()) -> bool:
        """Check if parent has children"""
        if not parent.isValid():
            parent_node = self.root_node
        else:
            parent_node = parent.internalPointer()
        
        if parent_node and parent_node.path.is_dir():
            return True
        
        return False


class ProjectNavigator(QTreeView):
    """Tree view widget for navigating Speckit projects"""
    
    # Signal emitted when file changes are detected
    fileChanged = Signal(str)  # path to changed file
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.project: Optional[SpeckitProject] = None
        self.model = LazyProjectModel()
        self.setModel(self.model)
        
        # File system watcher for external changes
        self.file_watcher = QFileSystemWatcher(self)
        self.file_watcher.directoryChanged.connect(self._on_directory_changed)
        self.file_watcher.fileChanged.connect(self._on_file_changed)
        
        # Track watched directories
        self._watched_dirs: set[str] = set()
        
        # Configure tree view
        self.setHeaderHidden(True)  # Hide header for single column
        self.setIndentation(20)  # 20px indentation per level
        self.setAnimated(True)  # Smooth expand/collapse
        self.setUniformRowHeights(True)  # Performance optimization
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Connect signals
        self.clicked.connect(self._on_item_clicked)
        self.doubleClicked.connect(self._on_item_double_clicked)
        
        logger.debug("ProjectNavigator initialized")
    
    def set_project(self, project: SpeckitProject) -> None:
        """Set the project to display"""
        self.project = project
        self.model.set_project(project)
        
        # Set up file watching for project directory
        self._setup_file_watching()
        
        # Expand root level
        root_index = self.model.index(0, 0)
        if root_index.isValid():
            self.expand(root_index)
        
        logger.info(f"Navigator displaying project: {project.name}")
    
    def refresh(self) -> None:
        """Refresh the project tree (reload from disk)"""
        if not self.project:
            return
        
        logger.info("Refreshing project navigator")
        
        # Reset model
        self.model.beginResetModel()
        
        # Reload project structure
        if self.project.root_path.exists():
            self.model.root_node = ProjectTreeNode(self.project.root_path)
        
        self.model.endResetModel()
        
        # Re-expand root
        root_index = self.model.index(0, 0)
        if root_index.isValid():
            self.expand(root_index)
        
        logger.info("Project navigator refreshed")
    
    def _setup_file_watching(self) -> None:
        """Set up filesystem watching for the project"""
        if not self.project:
            return
        
        # Clear existing watches
        if self._watched_dirs:
            self.file_watcher.removePaths(list(self._watched_dirs))
            self._watched_dirs.clear()
        
        # Watch project root and key subdirectories
        project_root = str(self.project.root_path)
        
        dirs_to_watch = [project_root]
        
        # Add specs directory if exists
        specs_dir = self.project.root_path / 'specs'
        if specs_dir.exists():
            dirs_to_watch.append(str(specs_dir))
            
            # Watch individual spec folders (001-feature-name, etc.)
            for spec_folder in specs_dir.iterdir():
                if spec_folder.is_dir() and not spec_folder.name.startswith('.'):
                    dirs_to_watch.append(str(spec_folder))
        
        # Add .specify directory if exists
        specify_dir = self.project.root_path / '.specify'
        if specify_dir.exists():
            dirs_to_watch.append(str(specify_dir))
        
        # Add templates directory if exists
        templates_dir = self.project.root_path / '.specify' / 'templates'
        if templates_dir.exists():
            dirs_to_watch.append(str(templates_dir))
        
        # Add to watcher
        added = self.file_watcher.addPaths(dirs_to_watch)
        self._watched_dirs = set(added)
        
        logger.debug(f"Watching {len(self._watched_dirs)} directories for changes")
    
    def _on_directory_changed(self, path: str) -> None:
        """Handle directory change notification"""
        logger.info(f"Directory changed: {path}")
        # Auto-refresh on directory changes
        self.refresh()
    
    def _on_file_changed(self, path: str) -> None:
        """Handle file change notification"""
        logger.info(f"File changed: {path}")
        self.fileChanged.emit(path)
    
    def _on_item_clicked(self, index: QModelIndex) -> None:
        """Handle single click on item"""
        path = index.data(Qt.UserRole)
        if path:
            logger.debug(f"Clicked: {path}")
    
    def _on_item_double_clicked(self, index: QModelIndex) -> None:
        """Handle double click on item (open file)"""
        path = index.data(Qt.UserRole)
        if path and path.is_file():
            logger.info(f"Double-clicked file: {path}")
            # Signal will be connected by MainWindow to open in editor
            # For now, just log
    
    def _show_context_menu(self, position) -> None:
        """Show context menu for navigator items"""
        from PySide6.QtWidgets import QMenu, QMessageBox
        import subprocess
        import platform
        
        index = self.indexAt(position)
        if not index.isValid():
            return
        
        path = index.data(Qt.UserRole)
        if not path:
            return
        
        menu = QMenu(self)
        
        # Open (for files)
        if path.is_file():
            open_action = menu.addAction("Open")
            open_action.triggered.connect(lambda: self._on_item_double_clicked(index))
            menu.addSeparator()
        
        # Copy Path
        copy_path_action = menu.addAction("Copy Path")
        copy_path_action.triggered.connect(lambda: self._copy_path(path))
        
        # Copy Relative Path
        copy_rel_path_action = menu.addAction("Copy Relative Path")
        copy_rel_path_action.triggered.connect(lambda: self._copy_relative_path(path))
        
        menu.addSeparator()
        
        # Reveal in Explorer/Finder
        if platform.system() == "Windows":
            reveal_text = "Reveal in Explorer"
        elif platform.system() == "Darwin":
            reveal_text = "Reveal in Finder"
        else:
            reveal_text = "Show in File Manager"
        
        reveal_action = menu.addAction(reveal_text)
        reveal_action.triggered.connect(lambda: self._reveal_in_explorer(path))
        
        # Open in External Editor
        if path.is_file():
            open_external_action = menu.addAction("Open in External Editor")
            open_external_action.triggered.connect(lambda: self._open_external(path))
        
        menu.addSeparator()
        
        # Rename
        rename_action = menu.addAction("Rename...")
        rename_action.triggered.connect(lambda: self._rename_item(path))
        
        # Duplicate (for files)
        if path.is_file():
            duplicate_action = menu.addAction("Duplicate")
            duplicate_action.triggered.connect(lambda: self._duplicate_file(path))
        
        menu.addSeparator()
        
        # Delete
        delete_action = menu.addAction("Delete...")
        delete_action.triggered.connect(lambda: self._delete_item(path))
        
        # Show menu at cursor
        menu.exec_(self.viewport().mapToGlobal(position))
    
    def _copy_path(self, path: Path) -> None:
        """Copy full path to clipboard"""
        from PySide6.QtWidgets import QApplication
        
        clipboard = QApplication.clipboard()
        clipboard.setText(str(path))
        logger.info(f"Copied path to clipboard: {path}")
    
    def _copy_relative_path(self, path: Path) -> None:
        """Copy relative path to clipboard"""
        from PySide6.QtWidgets import QApplication
        
        if self.project:
            try:
                rel_path = path.relative_to(self.project.root_path)
                clipboard = QApplication.clipboard()
                clipboard.setText(str(rel_path))
                logger.info(f"Copied relative path to clipboard: {rel_path}")
            except ValueError:
                logger.warning(f"Path {path} is not relative to project root")
    
    def _reveal_in_explorer(self, path: Path) -> None:
        """Open file location in system file manager"""
        import subprocess
        import platform
        
        try:
            if platform.system() == "Windows":
                # Windows: Use explorer with /select flag
                subprocess.run(['explorer', '/select,', str(path)])
            elif platform.system() == "Darwin":
                # macOS: Use open with -R flag
                subprocess.run(['open', '-R', str(path)])
            else:
                # Linux: Open parent directory
                parent = path.parent if path.is_file() else path
                subprocess.run(['xdg-open', str(parent)])
            
            logger.info(f"Revealed in file manager: {path}")
        except Exception as e:
            logger.error(f"Failed to reveal in explorer: {e}")
    
    def _open_external(self, path: Path) -> None:
        """Open file in default external application"""
        import subprocess
        import platform
        
        try:
            if platform.system() == "Windows":
                subprocess.run(['start', '', str(path)], shell=True)
            elif platform.system() == "Darwin":
                subprocess.run(['open', str(path)])
            else:
                subprocess.run(['xdg-open', str(path)])
            
            logger.info(f"Opened in external app: {path}")
        except Exception as e:
            logger.error(f"Failed to open external: {e}")
    
    def _rename_item(self, path: Path) -> None:
        """Rename file or folder"""
        from PySide6.QtWidgets import QInputDialog, QMessageBox
        
        current_name = path.name
        new_name, ok = QInputDialog.getText(
            self,
            "Rename",
            f"New name for '{current_name}':",
            text=current_name
        )
        
        if ok and new_name and new_name != current_name:
            new_path = path.parent / new_name
            
            if new_path.exists():
                QMessageBox.warning(
                    self,
                    "Rename Failed",
                    f"'{new_name}' already exists."
                )
                return
            
            try:
                path.rename(new_path)
                logger.info(f"Renamed {path} to {new_path}")
                self.refresh()
            except Exception as e:
                logger.error(f"Failed to rename: {e}")
                QMessageBox.critical(
                    self,
                    "Rename Failed",
                    f"Failed to rename:\n{e}"
                )
    
    def _duplicate_file(self, path: Path) -> None:
        """Duplicate a file"""
        import shutil
        
        # Generate new name
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        
        # Find available name (file_copy.md, file_copy_2.md, etc.)
        counter = 1
        while True:
            if counter == 1:
                new_name = f"{stem}_copy{suffix}"
            else:
                new_name = f"{stem}_copy_{counter}{suffix}"
            
            new_path = parent / new_name
            if not new_path.exists():
                break
            counter += 1
        
        try:
            shutil.copy2(path, new_path)
            logger.info(f"Duplicated {path} to {new_path}")
            self.refresh()
        except Exception as e:
            logger.error(f"Failed to duplicate: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Duplicate Failed",
                f"Failed to duplicate file:\n{e}"
            )
    
    def _delete_item(self, path: Path) -> None:
        """Delete file or folder with confirmation"""
        from PySide6.QtWidgets import QMessageBox
        import shutil
        
        item_type = "folder" if path.is_dir() else "file"
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this {item_type}?\n\n{path.name}\n\n"
            f"This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                
                logger.info(f"Deleted {path}")
                self.refresh()
            except Exception as e:
                logger.error(f"Failed to delete: {e}")
                QMessageBox.critical(
                    self,
                    "Delete Failed",
                    f"Failed to delete {item_type}:\n{e}"
                )
