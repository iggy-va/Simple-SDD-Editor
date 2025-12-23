"""Search panel for finding text across documents"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core.project import SpeckitProject
from ..core.search import SearchOptions
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SearchPanel(QWidget):
    """Search panel for finding text in documents"""
    
    # Signal emitted when user selects a search result
    resultSelected = Signal(Path, int)  # (file_path, line_number)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.project: Optional[SpeckitProject] = None
        
        # Create UI
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Search input row
        input_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.returnPressed.connect(self._on_search)
        input_layout.addWidget(self.search_input)
        
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._on_search)
        input_layout.addWidget(self.search_button)
        
        layout.addLayout(input_layout)
        
        # Options row
        options_layout = QHBoxLayout()
        
        # Scope selection
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["Current Document", "Open Documents", "All Documents"])
        self.scope_combo.setCurrentIndex(2)  # Default to "All Documents"
        options_layout.addWidget(self.scope_combo)
        
        # Case sensitive
        self.case_sensitive_check = QCheckBox("Case Sensitive")
        options_layout.addWidget(self.case_sensitive_check)
        
        # Regex
        self.regex_check = QCheckBox("Regex")
        options_layout.addWidget(self.regex_check)
        
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        # Results list
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self._on_result_double_clicked)
        layout.addWidget(self.results_list)
        
        logger.debug("SearchPanel initialized")
    
    def set_project(self, project: SpeckitProject) -> None:
        """Set the project to search in"""
        self.project = project
        logger.info(f"SearchPanel set to project: {project.name}")
    
    def _on_search(self) -> None:
        """Execute search"""
        query = self.search_input.text().strip()
        
        if not query:
            logger.debug("Empty search query")
            return
        
        if not self.project:
            logger.warning("No project set for search")
            self.results_list.clear()
            item = QListWidgetItem("No project loaded")
            self.results_list.addItem(item)
            return
        
        logger.info(f"Searching for: {query}")
        
        # Clear previous results
        self.results_list.clear()
        
        # Get search options
        options = SearchOptions(
            case_sensitive=self.case_sensitive_check.isChecked(),
            use_regex=self.regex_check.isChecked(),
        )
        
        scope = self.scope_combo.currentText()
        
        # TODO: Implement actual search based on scope
        # For now, show a placeholder result
        if scope == "All Documents":
            # Use DocumentIndex to search
            if hasattr(self.project, 'search_index') and self.project.search_index:
                results = self.project.search_index.search(query, options)
                
                if results:
                    for result_path in results[:50]:  # Limit to 50 results
                        # Read file to find matching lines
                        try:
                            with open(result_path, 'r', encoding='utf-8') as f:
                                for line_num, line in enumerate(f, 1):
                                    if query.lower() in line.lower():
                                        item_text = f"{result_path.name}:{line_num} - {line.strip()[:80]}"
                                        item = QListWidgetItem(item_text)
                                        item.setData(Qt.UserRole, (result_path, line_num))
                                        self.results_list.addItem(item)
                        except Exception as e:
                            logger.error(f"Error reading {result_path}: {e}")
                else:
                    item = QListWidgetItem("No results found")
                    self.results_list.addItem(item)
            else:
                item = QListWidgetItem("Search index not available. Building...")
                self.results_list.addItem(item)
                
                # Build index in background
                if self.project:
                    logger.info("Building search index...")
                    if not hasattr(self.project, 'search_index') or not self.project.search_index:
                        from ..core.search import DocumentIndex
                        self.project.search_index = DocumentIndex(self.project.root_path)
                    
                    self.project.search_index.index_all()
                    
                    # Retry search
                    self._on_search()
        
        elif scope == "Current Document":
            item = QListWidgetItem("Current document search not yet implemented")
            self.results_list.addItem(item)
        
        elif scope == "Open Documents":
            item = QListWidgetItem("Open documents search not yet implemented")
            self.results_list.addItem(item)
    
    def _on_result_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click on search result"""
        data = item.data(Qt.UserRole)
        
        if data and isinstance(data, tuple):
            file_path, line_number = data
            logger.info(f"Opening search result: {file_path}:{line_number}")
            self.resultSelected.emit(file_path, line_number)
