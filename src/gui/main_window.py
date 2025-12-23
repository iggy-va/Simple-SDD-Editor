"""Main window for Speckit Editor"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..core import SpeckitDocument, SpeckitProject
from ..utils.logging import get_logger
from .editor import SpeckitEditorWidget
from .navigator import ProjectNavigator
from .search_panel import SearchPanel
from .template_dialog import TemplateDialog

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        self.project: Optional[SpeckitProject] = None
        self.open_editors: dict[Path, SpeckitEditorWidget] = {}  # Track open editors
        
        self._setup_window()
        self._create_menus()
        self._create_toolbar()
        self._create_status_bar()
        self._create_central_widget()
        self._apply_styling()
        
        # Auto-save timer (30 seconds default)
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self._auto_save_all)
        self.auto_save_interval = 30000  # 30 seconds in milliseconds
        self.auto_save_timer.start(self.auto_save_interval)
        
        logger.info("MainWindow initialized")
    
    def _setup_window(self) -> None:
        """Configure main window properties"""
        self.setWindowTitle("Speckit Editor")
        self.resize(1200, 800)
        
        # Set minimum size
        self.setMinimumSize(800, 600)
    
    def _create_menus(self) -> None:
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # New Document
        new_doc_action = QAction("&New Document...", self)
        new_doc_action.setShortcut(QKeySequence.New)
        new_doc_action.setStatusTip("Create a new document from template")
        new_doc_action.triggered.connect(self._on_new_document)
        file_menu.addAction(new_doc_action)
        
        # New Project
        new_project_action = QAction("New &Project...", self)
        new_project_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        new_project_action.setStatusTip("Create a new Speckit project")
        new_project_action.triggered.connect(self._on_new_project)
        file_menu.addAction(new_project_action)
        
        # Open Document
        open_doc_action = QAction("&Open Document...", self)
        open_doc_action.setShortcut(QKeySequence.Open)
        open_doc_action.setStatusTip("Open an existing document")
        open_doc_action.triggered.connect(self._on_open_document)
        file_menu.addAction(open_doc_action)
        
        # Open Project
        open_project_action = QAction("Open &Project...", self)
        open_project_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        open_project_action.setStatusTip("Open an existing Speckit project")
        open_project_action.triggered.connect(self._on_open_project)
        file_menu.addAction(open_project_action)
        
        file_menu.addSeparator()
        
        # Save
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.setStatusTip("Save current document")
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)
        
        # Save All
        save_all_action = QAction("Save &All", self)
        save_all_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_all_action.setStatusTip("Save all open documents")
        save_all_action.triggered.connect(self._on_save_all)
        file_menu.addAction(save_all_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Undo
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self._on_undo)
        edit_menu.addAction(undo_action)
        
        # Redo
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self._on_redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        # Find
        find_action = QAction("&Find...", self)
        find_action.setShortcut(QKeySequence.Find)
        find_action.triggered.connect(self._on_find)
        edit_menu.addAction(find_action)
        
        # Window menu
        window_menu = menubar.addMenu("&Window")
        
        # Next Tab
        next_tab_action = QAction("Next &Tab", self)
        next_tab_action.setShortcut(QKeySequence("Ctrl+Tab"))
        next_tab_action.setStatusTip("Switch to next tab")
        next_tab_action.triggered.connect(self._on_next_tab)
        window_menu.addAction(next_tab_action)
        
        # Previous Tab
        prev_tab_action = QAction("&Previous Tab", self)
        prev_tab_action.setShortcut(QKeySequence("Ctrl+Shift+Tab"))
        prev_tab_action.setStatusTip("Switch to previous tab")
        prev_tab_action.triggered.connect(self._on_previous_tab)
        window_menu.addAction(prev_tab_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Project Explorer
        toggle_explorer_action = QAction("&Project Explorer", self)
        toggle_explorer_action.setCheckable(True)
        toggle_explorer_action.setChecked(True)
        toggle_explorer_action.setStatusTip("Toggle project explorer panel")
        view_menu.addAction(toggle_explorer_action)
        
        view_menu.addSeparator()
        
        # Refresh Project
        refresh_action = QAction("&Refresh Project", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.setStatusTip("Refresh project tree from disk")
        refresh_action.triggered.connect(self._on_refresh_project)
        view_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # About
        about_action = QAction("&About Speckit Editor", self)
        about_action.setStatusTip("About this application")
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _create_toolbar(self) -> None:
        """Create toolbar"""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)
        
        # Add toolbar actions (placeholder for now)
        # TODO: Add icons and actions in T016
    
    def _create_status_bar(self) -> None:
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def _create_central_widget(self) -> None:
        """Create central widget with splitter for navigator and tabs"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main horizontal splitter for navigator and editor+search area
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Project navigator (left panel)
        self.navigator = ProjectNavigator()
        self.navigator.doubleClicked.connect(self._on_navigator_file_double_clicked)
        self.navigator.fileChanged.connect(self._on_external_file_changed)
        self.splitter.addWidget(self.navigator)
        
        # Right side: vertical splitter for tabs and search
        right_splitter = QSplitter(Qt.Vertical)
        
        # Tab widget for open documents (top right)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # Add tab context menu
        self.tab_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_widget.customContextMenuRequested.connect(self._show_tab_context_menu)
        
        right_splitter.addWidget(self.tab_widget)
        
        # Search panel (bottom right, initially hidden)
        self.search_panel = SearchPanel()
        self.search_panel.resultSelected.connect(self._on_search_result_selected)
        self.search_panel.setVisible(False)  # Hidden by default
        right_splitter.addWidget(self.search_panel)
        
        # Set vertical splitter sizes (80% tabs, 20% search when visible)
        right_splitter.setSizes([800, 200])
        
        self.splitter.addWidget(right_splitter)
        
        # Set main splitter sizes (20% navigator, 80% editor area)
        self.splitter.setSizes([200, 800])
        
        layout.addWidget(self.splitter)
        
        # Show welcome message
        self._show_welcome_tab()
    
    def _show_welcome_tab(self) -> None:
        """Show welcome tab when no project is open"""
        from PySide6.QtWidgets import QLabel
        
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        
        label = QLabel("Welcome to Speckit Editor\n\nOpen a project to get started")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: #666;")
        
        welcome_layout.addWidget(label)
        
        self.tab_widget.addTab(welcome_widget, "Welcome")
    
    def _apply_styling(self) -> None:
        """Apply application-wide styling"""
        # Basic stylesheet for focus indicators and theme
        stylesheet = """
        QMainWindow {
            background-color: #ffffff;
        }
        
        QTabWidget::pane {
            border: 1px solid #cccccc;
            background-color: #ffffff;
        }
        
        QTabBar::tab {
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
            border-bottom: none;
            padding: 6px 12px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: #ffffff;
            border-bottom: 1px solid #ffffff;
        }
        
        QTabBar::tab:hover {
            background-color: #e0e0e0;
        }
        
        /* Focus indicators for accessibility */
        *:focus {
            outline: 2px solid #0078d4;
            outline-offset: 2px;
        }
        
        QMenuBar {
            background-color: #f0f0f0;
            border-bottom: 1px solid #cccccc;
        }
        
        QMenuBar::item:selected {
            background-color: #e0e0e0;
        }
        
        QStatusBar {
            background-color: #f0f0f0;
            border-top: 1px solid #cccccc;
        }
        """
        
        self.setStyleSheet(stylesheet)
    
    # Menu action handlers (placeholders)
    
    def _on_new_project(self) -> None:
        """Handle New Project action"""
        logger.info("New Project requested")
        QMessageBox.information(
            self,
            "Not Implemented",
            "New Project feature will be implemented in Phase 4 (US2)"
        )
    
    def _on_new_document(self) -> None:
        """Handle New Document from Template action"""
        logger.info("New Document requested")
        
        if not self.project:
            QMessageBox.warning(
                self,
                "No Project",
                "Please open a project first before creating documents."
            )
            return
        
        # Show template dialog
        templates_dir = self.project.root_path / ".specify" / "templates"
        dialog = TemplateDialog(templates_dir, self)
        
        if dialog.exec() == TemplateDialog.Accepted:
            template, values = dialog.get_result()
            
            if template:
                try:
                    # Instantiate template
                    content = template.instantiate(values)
                    
                    # Create new document
                    # For now, use a temporary path
                    doc_path = self.project.root_path / "specs" / "new_document.md"
                    
                    doc = SpeckitDocument(
                        path=doc_path,
                        relative_path=Path("new_document.md"),
                        content=content,
                    )
                    
                    # Open in editor
                    self._open_document_in_editor(doc)
                    
                except Exception as e:
                    logger.error(f"Failed to create document: {e}")
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to create document:\n{str(e)}"
                    )
    
    def _on_open_document(self) -> None:
        """Handle Open Document action"""
        logger.info("Open Document requested")
        
        if not self.project:
            QMessageBox.warning(
                self,
                "No Project",
                "Please open a project first before opening documents."
            )
            return
        
        # Show file picker
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Speckit Document",
            str(self.project.root_path / "specs"),
            "Markdown Files (*.md);;All Files (*.*)"
        )
        
        if file_path:
            try:
                # Load document
                doc = self.project.get_document(Path(file_path))
                self._open_document_in_editor(doc)
            except Exception as e:
                logger.error(f"Failed to open document: {e}")
                QMessageBox.critical(
                    self,
                    "Error Opening Document",
                    f"Failed to open document:\n{str(e)}"
                )
    
    def _on_open_project(self) -> None:
        """Handle Open Project action"""
        logger.info("Open Project requested")
        
        # Show directory picker
        project_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Speckit Project Directory",
            str(Path.home()),
            QFileDialog.ShowDirsOnly
        )
        
        if project_dir:
            self._load_project(Path(project_dir))
    
    def _load_project(self, project_path: Path) -> None:
        """Load a Speckit project"""
        try:
            logger.info(f"Loading project: {project_path}")
            self.project = SpeckitProject(project_path)
            
            # Update window title
            self.setWindowTitle(f"Speckit Editor - {self.project.name}")
            
            # Update status bar
            self.status_bar.showMessage(f"Loaded project: {self.project.name}")
            
            # Populate project navigator
            self.navigator.set_project(self.project)
            
            # Set project for search panel
            self.search_panel.set_project(self.project)
            
            logger.info(f"Project loaded successfully: {self.project.name}")
        except Exception as e:
            logger.error(f"Failed to load project: {e}")
            QMessageBox.critical(
                self,
                "Error Loading Project",
                f"Failed to load project:\n{str(e)}"
            )
    
    def _on_save(self) -> None:
        """Handle Save action"""
        logger.debug("Save requested")
        
        # Get current tab's editor
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, SpeckitEditorWidget):
            self._save_document(current_widget)
        else:
            logger.debug("No document to save")
    
    def _on_save_all(self) -> None:
        """Handle Save All action"""
        logger.debug("Save All requested")
        
        # Save all open editors
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, SpeckitEditorWidget):
                self._save_document(widget)
    
    def _save_document(self, editor: SpeckitEditorWidget) -> bool:
        """Save a document from an editor widget"""
        try:
            if not editor.document_path:
                logger.warning("Cannot save: no document path")
                return False
            
            # Get content from editor
            content = editor.get_content()
            
            # Update SpeckitDocument if available
            if editor.speckit_document:
                editor.speckit_document.content = content
                editor.speckit_document.save()
            else:
                # Direct file write
                editor.document_path.write_text(content, encoding="utf-8")
            
            # Reset modified flag
            editor.document().setModified(False)
            
            # Update tab title (remove *)
            for i in range(self.tab_widget.count()):
                if self.tab_widget.widget(i) == editor:
                    title = self.tab_widget.tabText(i).rstrip(" *")
                    self.tab_widget.setTabText(i, title)
                    break
            
            self.status_bar.showMessage(f"Saved: {editor.document_path.name}", 2000)
            logger.info(f"Document saved: {editor.document_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save document: {e}")
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save document:\n{str(e)}"
            )
            return False
    
    def _on_undo(self) -> None:
        """Handle Undo action"""
        logger.debug("Undo requested")
        # TODO: Implement in Phase 3 (US1)
    
    def _on_redo(self) -> None:
        """Handle Redo action"""
        logger.debug("Redo requested")
        # TODO: Implement in Phase 3 (US1)
    
    def _on_find(self) -> None:
        """Handle Find action (Ctrl+F)"""
        logger.debug("Find requested")
        
        # Toggle search panel visibility
        self.search_panel.setVisible(not self.search_panel.isVisible())
        
        if self.search_panel.isVisible():
            # Focus on search input
            self.search_panel.search_input.setFocus()
            self.search_panel.search_input.selectAll()
            
            logger.info("Search panel shown")
        else:
            logger.info("Search panel hidden")
    
    def _on_refresh_project(self) -> None:
        """Handle project refresh action (F5)"""
        if not self.project:
            logger.debug("No project to refresh")
            return
        
        logger.info("Refreshing project from disk")
        
        # Refresh navigator tree
        self.navigator.refresh()
        
        # Show status message
        self.statusBar().showMessage("Project refreshed", 3000)
    
    def _on_external_file_changed(self, file_path: str) -> None:
        """Handle external file change notification"""
        changed_path = Path(file_path)
        
        # Check if the changed file is currently open
        if changed_path in self.open_editors:
            editor = self.open_editors[changed_path]
            
            # Check if editor has unsaved changes
            if editor.is_modified():
                # File changed externally but editor has unsaved changes
                # Ask user what to do
                reply = QMessageBox.question(
                    self,
                    "External File Change",
                    f"{changed_path.name} has been modified externally and has unsaved changes.\n\n"
                    "Do you want to reload from disk? (Unsaved changes will be lost)",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
            else:
                # File changed externally with no local changes
                # Ask to reload
                reply = QMessageBox.question(
                    self,
                    "External File Change",
                    f"{changed_path.name} has been modified externally.\n\nReload from disk?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
            
            # Reload the file
            try:
                doc = self.project.get_document(changed_path)
                editor.load_document(doc)
                logger.info(f"Reloaded {changed_path} from disk")
                self.statusBar().showMessage(f"Reloaded {changed_path.name}", 3000)
            except Exception as e:
                logger.error(f"Failed to reload {changed_path}: {e}")
                QMessageBox.critical(
                    self,
                    "Reload Failed",
                    f"Failed to reload {changed_path.name}:\n{e}"
                )
    
    def _on_about(self) -> None:
        """Handle About action"""
        QMessageBox.about(
            self,
            "About Speckit Editor",
            "<h3>Speckit Editor</h3>"
            "<p>A professional IDE for the Speckit methodology</p>"
            "<p>Version 0.1.0</p>"
            "<p>Built with PySide6 and Python</p>"
        )
    
    def _on_tab_close_requested(self, index: int) -> None:
        """Handle tab close request"""
        widget = self.tab_widget.widget(index)
        
        # Save scroll position before potentially closing
        if isinstance(widget, SpeckitEditorWidget):
            widget.save_scroll_position()
        
        # Check for unsaved changes
        if isinstance(widget, SpeckitEditorWidget) and widget.is_modified():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                f"Document has unsaved changes. Save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                if not self._save_document(widget):
                    return  # Save failed, don't close
            elif reply == QMessageBox.Cancel:
                return  # User cancelled
        
        # Remove from tracking
        if isinstance(widget, SpeckitEditorWidget) and widget.document_path:
            self.open_editors.pop(widget.document_path, None)
        
        # Close tab
        self.tab_widget.removeTab(index)
        
        # Show welcome tab if no tabs left
        if self.tab_widget.count() == 0:
            self._show_welcome_tab()
    
    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change - restore scroll position and cursor"""
        if index < 0:
            return
        
        widget = self.tab_widget.widget(index)
        if isinstance(widget, SpeckitEditorWidget):
            widget.restore_scroll_position()
            logger.debug(f"Switched to tab {index}: {widget.document_path}")
    
    def _on_next_tab(self) -> None:
        """Switch to next tab (Ctrl+Tab)"""
        current = self.tab_widget.currentIndex()
        count = self.tab_widget.count()
        if count > 0:
            next_index = (current + 1) % count
            self.tab_widget.setCurrentIndex(next_index)
    
    def _on_previous_tab(self) -> None:
        """Switch to previous tab (Ctrl+Shift+Tab)"""
        current = self.tab_widget.currentIndex()
        count = self.tab_widget.count()
        if count > 0:
            prev_index = (current - 1) % count
            self.tab_widget.setCurrentIndex(prev_index)
    
    def _show_tab_context_menu(self, position) -> None:
        """Show context menu for tabs"""
        from PySide6.QtWidgets import QMenu
        
        # Get tab bar position
        tab_bar = self.tab_widget.tabBar()
        index = tab_bar.tabAt(position)
        
        if index < 0:
            return
        
        menu = QMenu(self)
        
        # Close actions
        close_action = menu.addAction("Close")
        close_others_action = menu.addAction("Close Others")
        close_all_action = menu.addAction("Close All")
        
        action = menu.exec_(tab_bar.mapToGlobal(position))
        
        if action == close_action:
            self._on_tab_close_requested(index)
        elif action == close_others_action:
            self._close_other_tabs(index)
        elif action == close_all_action:
            self._close_all_tabs()
    
    def _close_other_tabs(self, keep_index: int) -> None:
        """Close all tabs except the specified one"""
        # Close tabs after keep_index
        for i in range(self.tab_widget.count() - 1, keep_index, -1):
            self._on_tab_close_requested(i)
        
        # Close tabs before keep_index
        for i in range(keep_index - 1, -1, -1):
            self._on_tab_close_requested(i)
    
    def _close_all_tabs(self) -> None:
        """Close all tabs"""
        while self.tab_widget.count() > 0:
            self._on_tab_close_requested(0)
    
    def _on_search_result_selected(self, file_path: Path, line_number: int) -> None:
        """Handle search result selection - open file and go to line"""
        logger.info(f"Opening search result: {file_path}:{line_number}")
        
        if not self.project:
            return
        
        try:
            # Load document
            doc = self.project.get_document(file_path)
            
            # Open in editor
            self._open_document_in_editor(doc)
            
            # Get the editor widget
            current_widget = self.tab_widget.currentWidget()
            if isinstance(current_widget, SpeckitEditorWidget):
                # Move cursor to line
                cursor = current_widget.textCursor()
                cursor.movePosition(cursor.Start)
                for _ in range(line_number - 1):
                    cursor.movePosition(cursor.Down)
                current_widget.setTextCursor(cursor)
                
                # Ensure line is visible
                current_widget.ensureCursorVisible()
                
                logger.debug(f"Navigated to line {line_number}")
        
        except Exception as e:
            logger.error(f"Failed to open search result: {e}")
    
    def _open_document_in_editor(self, document: SpeckitDocument) -> None:
        """Open a document in a new editor tab"""
        # Check if already open
        if document.path in self.open_editors:
            # Switch to existing tab
            editor = self.open_editors[document.path]
            for i in range(self.tab_widget.count()):
                if self.tab_widget.widget(i) == editor:
                    self.tab_widget.setCurrentIndex(i)
                    return
        
        # Remove welcome tab if present
        if self.tab_widget.count() == 1:
            first_widget = self.tab_widget.widget(0)
            if not isinstance(first_widget, SpeckitEditorWidget):
                self.tab_widget.removeTab(0)
        
        # Create new editor
        editor = SpeckitEditorWidget()
        editor.load_document(document)
        
        # Connect signals
        editor.contentModified.connect(lambda: self._on_editor_modified(editor))
        editor.validationComplete.connect(self._on_validation_complete)
        
        # Add to tab widget
        tab_title = document.path.name
        self.tab_widget.addTab(editor, tab_title)
        self.tab_widget.setCurrentWidget(editor)
        
        # Track editor
        self.open_editors[document.path] = editor
        
        logger.info(f"Opened document in editor: {document.path}")
    
    def _on_editor_modified(self, editor: SpeckitEditorWidget) -> None:
        """Handle editor content modification"""
        # Add * to tab title if modified
        for i in range(self.tab_widget.count()):
            if self.tab_widget.widget(i) == editor:
                title = self.tab_widget.tabText(i)
                if not title.endswith(" *"):
                    self.tab_widget.setTabText(i, title + " *")
                break
    
    def _auto_save_all(self) -> None:
        """Auto-save all modified documents"""
        saved_count = 0
        
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, SpeckitEditorWidget) and widget.is_modified():
                if self._save_document(widget):
                    saved_count += 1
        
        if saved_count > 0:
            self.status_bar.showMessage(f"Auto-saved {saved_count} document(s)", 2000)
            logger.debug(f"Auto-saved {saved_count} documents")
    
    def _on_navigator_file_double_clicked(self, index) -> None:
        """Handle double-click on file in navigator"""
        from PySide6.QtCore import Qt
        
        path = index.data(Qt.UserRole)
        if not path or not path.is_file():
            return
        
        # Only open markdown files
        if path.suffix.lower() not in ['.md', '.markdown']:
            logger.debug(f"Skipping non-markdown file: {path}")
            return
        
        try:
            # Load document from project
            if self.project:
                doc = self.project.get_document(path)
                self._open_document_in_editor(doc)
            else:
                # Fallback: create standalone document
                doc = SpeckitDocument(
                    path=path,
                    relative_path=path.name,
                    content=path.read_text(encoding='utf-8')
                )
                self._open_document_in_editor(doc)
        except Exception as e:
            logger.error(f"Failed to open file from navigator: {e}")
            QMessageBox.critical(
                self,
                "Error Opening File",
                f"Failed to open file:\n{str(e)}"
            )
            
    def _on_validation_complete(self, result) -> None:
        """Handle validation completion"""
        from ..core.validator import ValidationResult
        
        if not isinstance(result, ValidationResult):
            return
        
        # Get current editor
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, SpeckitEditorWidget):
            # Display validation results in editor (squiggly underlines)
            current_widget.display_validation_results(result)
        
        # Display validation status in status bar
        if result.is_valid:
            if result.warnings:
                self.status_bar.showMessage(f"✓ Valid ({len(result.warnings)} warnings)", 3000)
            else:
                self.status_bar.showMessage("✓ Valid", 3000)
        else:
            self.status_bar.showMessage(f"✗ {len(result.errors)} errors, {len(result.warnings)} warnings", 5000)