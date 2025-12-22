"""Project navigator tree view for Speckit projects"""

from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt
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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.project: Optional[SpeckitProject] = None
        self.model = LazyProjectModel()
        self.setModel(self.model)
        
        # Configure tree view
        self.setHeaderHidden(True)  # Hide header for single column
        self.setIndentation(20)  # 20px indentation per level
        self.setAnimated(True)  # Smooth expand/collapse
        self.setUniformRowHeights(True)  # Performance optimization
        
        # Connect signals
        self.clicked.connect(self._on_item_clicked)
        self.doubleClicked.connect(self._on_item_double_clicked)
        
        logger.debug("ProjectNavigator initialized")
    
    def set_project(self, project: SpeckitProject) -> None:
        """Set the project to display"""
        self.project = project
        self.model.set_project(project)
        
        # Expand root level
        root_index = self.model.index(0, 0)
        if root_index.isValid():
            self.expand(root_index)
        
        logger.info(f"Navigator displaying project: {project.name}")
    
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
