"""Main window for Speckit Editor"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..core import SpeckitDocument, SpeckitProject
from ..utils.logging import get_logger
from .editor import SpeckitEditorWidget
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
        
        # Open Project
        open_project_action = QAction("&Open Project...", self)
        open_project_action.setShortcut(QKeySequence.Open)
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
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Project Explorer
        toggle_explorer_action = QAction("&Project Explorer", self)
        toggle_explorer_action.setCheckable(True)
        toggle_explorer_action.setChecked(True)
        toggle_explorer_action.setStatusTip("Toggle project explorer panel")
        view_menu.addAction(toggle_explorer_action)
        
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
        """Create central widget with tab container"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab widget for open documents
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)
        
        layout.addWidget(self.tab_widget)
        
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
            
            # TODO: Populate project explorer in Phase 4
            
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
        """Handle Find action"""
        logger.debug("Find requested")
        # TODO: Implement in Phase 3 (US1)
    
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
