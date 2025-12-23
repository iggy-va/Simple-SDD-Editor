"""Main window for Speckit Editor"""

import re
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..core import SpeckitDocument, SpeckitProject
from ..mcp.server import EmbeddedMCPServer
from ..utils.config import AppSettings, ProjectSettings
from ..utils.logging import get_logger
from .ai_panel import AIPanel
from .editor import SpeckitEditorWidget
from .git_panel import GitPanel
from .mcp_panel import MCPPanel
from .navigator import ProjectNavigator
from .search_panel import SearchPanel
from .settings_dialog import SettingsDialog
from .template_dialog import TemplateDialog
from .template_manager import TemplateManagerWidget

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        self.project: Optional[SpeckitProject] = None
        self.open_editors: dict[Path, SpeckitEditorWidget] = {}  # Track open editors
        
        # Load application settings
        self.app_settings_path = Path.home() / ".speckit" / "settings.json"
        self.app_settings = AppSettings.load(self.app_settings_path)
        self.project_settings: Optional[ProjectSettings] = None
        
        # Initialize crash recovery
        from ..utils.config import CrashRecovery
        self.crash_recovery = CrashRecovery()
        
        # Defer MCP server initialization (lazy loading)
        self.mcp_server: Optional[EmbeddedMCPServer] = None
        self._mcp_initialized = False
        
        self._setup_window()
        self._create_menus()
        self._create_toolbar()
        self._create_status_bar()
        self._create_central_widget()
        self._apply_styling()
        
        # Defer auto-save timer (start after first document is opened)
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self._auto_save_all)
        self.auto_save_interval = 30000  # 30 seconds in milliseconds
        # Don't start until needed
        
        # Auto-save unsaved documents for crash recovery (every 10 seconds)
        self.recovery_timer = QTimer(self)
        self.recovery_timer.timeout.connect(self._save_recovery_cache)
        self.recovery_timer.start(10000)  # 10 seconds
        
        # Defer MCP and welcome screen initialization until after window is shown
        QTimer.singleShot(100, self._deferred_initialization)
        
        logger.info("MainWindow initialized")
    
    def _deferred_initialization(self) -> None:
        """Perform deferred initialization after window is shown (for faster startup)"""
        # Check for crash recovery
        self._check_crash_recovery()
        
        # Initialize MCP server in background
        self._init_mcp_server()
        
        # Show welcome tab if no project is open
        if not self.project:
            self._show_welcome_tab()
    
    def _check_crash_recovery(self) -> None:
        """Check for recoverable documents from previous crash"""
        recoverable = self.crash_recovery.get_recoverable_documents()
        
        if not recoverable:
            return
        
        # Ask user if they want to recover
        msg = f"Found {len(recoverable)} unsaved document(s) from previous session.\n\n"
        msg += "Would you like to recover them?"
        
        reply = QMessageBox.question(
            self,
            "Crash Recovery",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            for original_path, recovery_data in recoverable.items():
                try:
                    content = recovery_data["content"]
                    path = Path(original_path)
                    
                    # Create document with recovered content
                    doc = SpeckitDocument(
                        path=path,
                        relative_path=path.name,
                        content=content
                    )
                    doc.is_dirty = True  # Mark as modified
                    
                    self._open_document_in_editor(doc)
                    logger.info(f"Recovered document: {path}")
                    
                except Exception as e:
                    logger.error(f"Failed to recover document {original_path}: {e}")
        
        # Clear recovery cache after offering recovery
        if reply == QMessageBox.No:
            self.crash_recovery.clear_all()
    
    def _save_recovery_cache(self) -> None:
        """Save unsaved documents to crash recovery cache"""
        for path, editor in self.open_editors.items():
            if editor.document().isModified():
                content = editor.get_content()
                self.crash_recovery.save_unsaved_document(path, content)
    
    def _init_mcp_server(self) -> None:
        """Initialize MCP server (lazy loading)"""
        if self._mcp_initialized:
            return
        
        try:
            # Determine cache directory
            if self.project:
                cache_dir = self.project.root_path / ".specify" / "cache"
            else:
                cache_dir = Path.home() / ".speckit_cache"
            
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Create and start server
            self.mcp_server = EmbeddedMCPServer(cache_dir)
            self.mcp_server.start()
            
            # Update panels with MCP server
            if hasattr(self, 'mcp_panel'):
                self.mcp_panel.set_mcp_server(self.mcp_server)
            if hasattr(self, 'ai_panel'):
                self.ai_panel.set_mcp_server(self.mcp_server)
            
            self._mcp_initialized = True
            logger.info(f"MCP server started with cache dir: {cache_dir}")
        except Exception as e:
            logger.error(f"Failed to initialize MCP server: {e}")
            self.mcp_server = None
    
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
        
        # Git menu
        git_menu = menubar.addMenu("&Git")
        
        # Commit
        commit_action = QAction("&Commit...", self)
        commit_action.setShortcut(QKeySequence("Ctrl+K"))
        commit_action.setStatusTip("Create git commit")
        commit_action.triggered.connect(self._on_git_commit_shortcut)
        git_menu.addAction(commit_action)
        
        git_menu.addSeparator()
        
        # Push
        push_action = QAction("&Push", self)
        push_action.setShortcut(QKeySequence("Ctrl+Shift+P"))
        push_action.setStatusTip("Push to remote")
        push_action.triggered.connect(self._on_git_push)
        git_menu.addAction(push_action)
        
        # Pull
        pull_action = QAction("Pu&ll", self)
        pull_action.setShortcut(QKeySequence("Ctrl+Shift+L"))
        pull_action.setStatusTip("Pull from remote")
        pull_action.triggered.connect(self._on_git_pull)
        git_menu.addAction(pull_action)
        
        git_menu.addSeparator()
        
        # Show Diff
        diff_action = QAction("Show &Diff", self)
        diff_action.setShortcut(QKeySequence("Ctrl+D"))
        diff_action.setStatusTip("Show git diff")
        diff_action.triggered.connect(self._on_git_diff)
        git_menu.addAction(diff_action)
        
        # AI menu
        ai_menu = menubar.addMenu("&AI")
        
        # AI Chat
        ai_chat_action = QAction("AI &Chat", self)
        ai_chat_action.setShortcut(QKeySequence("Ctrl+Shift+A"))
        ai_chat_action.setStatusTip("Open AI assistant chat")
        ai_chat_action.triggered.connect(self._on_ai_chat)
        ai_menu.addAction(ai_chat_action)
        
        # AI Completion (inline)
        ai_completion_action = QAction("AI &Completion", self)
        ai_completion_action.setShortcut(QKeySequence("Ctrl+Space"))
        ai_completion_action.setStatusTip("Get AI completion at cursor")
        ai_completion_action.triggered.connect(self._on_ai_completion)
        ai_menu.addAction(ai_completion_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Manage Templates
        manage_templates_action = QAction("&Manage Templates", self)
        manage_templates_action.setStatusTip("View, edit, and manage document templates")
        manage_templates_action.triggered.connect(self._on_manage_templates)
        tools_menu.addAction(manage_templates_action)
        
        tools_menu.addSeparator()
        
        # Preferences/Settings
        preferences_action = QAction("&Preferences...", self)
        preferences_action.setShortcut(QKeySequence("Ctrl+,"))
        preferences_action.setStatusTip("Configure application settings")
        preferences_action.triggered.connect(self._on_preferences)
        tools_menu.addAction(preferences_action)
        
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
        
        # Git status label (permanent widget on right side)
        self.git_status_label = QLabel("No repo")
        self.git_status_label.setStyleSheet("padding: 0 10px;")
        self.status_bar.addPermanentWidget(self.git_status_label)
        
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
        
        # Accessibility
        self.navigator.setAccessibleName("Project Navigator")
        self.navigator.setAccessibleDescription("Tree view showing all files and folders in the current project")
        
        self.splitter.addWidget(self.navigator)
        
        # Right side: vertical splitter for tabs and bottom panels
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
        
        # Accessibility
        self.tab_widget.setAccessibleName("Open Documents")
        self.tab_widget.setAccessibleDescription("Tab widget containing all currently open documents")
        
        right_splitter.addWidget(self.tab_widget)
        
        # Bottom panel: tabbed widget for search, git, and MCP
        self.bottom_tabs = QTabWidget()
        
        # Accessibility
        self.bottom_tabs.setAccessibleName("Tool Panels")
        self.bottom_tabs.setAccessibleDescription("Tab widget for search, git, MCP, and AI assistant panels")
        
        # Search panel
        self.search_panel = SearchPanel()
        self.search_panel.resultSelected.connect(self._on_search_result_selected)
        self.bottom_tabs.addTab(self.search_panel, "Search")
        
        # Git panel
        self.git_panel = GitPanel()
        self.git_panel.commitRequested.connect(self._on_git_commit)
        self.bottom_tabs.addTab(self.git_panel, "Git")
        
        # MCP panel (server will be set in deferred initialization)
        self.mcp_panel = MCPPanel()
        self.bottom_tabs.addTab(self.mcp_panel, "MCP")
        
        # AI panel (server will be set in deferred initialization)
        self.ai_panel = AIPanel()
        self.ai_panel.promptSent.connect(self._on_ai_prompt)
        self.bottom_tabs.addTab(self.ai_panel, "AI Assistant")
        
        # Initially hidden
        self.bottom_tabs.setVisible(False)
        right_splitter.addWidget(self.bottom_tabs)
        
        # Set vertical splitter sizes (80% tabs, 20% bottom panels when visible)
        right_splitter.setSizes([800, 200])
        
        self.splitter.addWidget(right_splitter)
        
        # Set main splitter sizes (20% navigator, 80% editor area)
        self.splitter.setSizes([200, 800])
        
        layout.addWidget(self.splitter)
        
        # Welcome message will be shown in deferred initialization
    
    def _show_welcome_tab(self) -> None:
        """Show welcome tab when no project is open"""
        from PySide6.QtWidgets import QLabel, QPushButton
        
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setAlignment(Qt.AlignCenter)
        welcome_layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Welcome to Speckit Editor")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        welcome_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("A specialized IDE for Speckit project documentation")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("font-size: 14px; color: #666;")
        welcome_layout.addWidget(subtitle_label)
        
        welcome_layout.addSpacing(40)
        
        # Quick start actions
        actions_widget = QWidget()
        actions_layout = QVBoxLayout(actions_widget)
        actions_layout.setSpacing(15)
        
        # Open project button
        open_project_btn = QPushButton("📁 Open Existing Project")
        open_project_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 12px 24px;
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        open_project_btn.clicked.connect(self._on_open_project)
        actions_layout.addWidget(open_project_btn)
        
        # New project button (placeholder)
        new_project_btn = QPushButton("✨ Create New Project")
        new_project_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 12px 24px;
                background-color: #f0f0f0;
                color: #333;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e5e5e5;
            }
        """)
        new_project_btn.clicked.connect(self._on_new_project)
        actions_layout.addWidget(new_project_btn)
        
        welcome_layout.addWidget(actions_widget)
        
        welcome_layout.addSpacing(40)
        
        # Getting started tips
        tips_label = QLabel(
            "💡 <b>Getting Started:</b><br><br>"
            "• Open a Speckit project folder containing .specify/ directory<br>"
            "• Browse specs, templates, and memory files in the navigator<br>"
            "• Use Ctrl+F to search across all documents<br>"
            "• Git integration available in the Git panel below<br>"
            "• Configure MCP integrations in the MCP panel"
        )
        tips_label.setAlignment(Qt.AlignCenter)
        tips_label.setStyleSheet("font-size: 12px; color: #666; line-height: 1.6;")
        tips_label.setTextFormat(Qt.RichText)
        welcome_layout.addWidget(tips_label)
        
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
            
            # Check for large project and show performance warning
            self._check_project_performance()
            
            # Load project settings
            settings_path = self.project.root / ".specify" / "settings.json"
            self.project_settings = ProjectSettings.load(settings_path)
            
            # Apply settings
            self._apply_settings()
            
            # Update window title
            self.setWindowTitle(f"Speckit Editor - {self.project.name}")
            
            # Update status bar
            self.status_bar.showMessage(f"Loaded project: {self.project.name}")
            
            # Populate project navigator
            self.navigator.set_project(self.project)
            
            # Set project for search panel
            self.search_panel.set_project(self.project)
            
            # Set project for git panel
            self.git_panel.set_project(self.project)
            
            # Update git status
            self._update_git_status()
            
            logger.info(f"Project loaded successfully: {self.project.name}")
        except Exception as e:
            logger.error(f"Failed to load project: {e}")
            QMessageBox.critical(
                self,
                "Error Loading Project",
                f"Failed to load project:\n{str(e)}"
            )
    
    def _check_project_performance(self) -> None:
        """Check project size and show performance warnings if needed"""
        if not self.project:
            return
        
        # Count total files in project
        total_files = 0
        large_files = []
        
        for file_path in self.project.root.rglob("*"):
            if file_path.is_file() and not any(
                part.startswith(".") for part in file_path.parts
            ):
                total_files += 1
                
                # Check for large files (>5MB)
                if file_path.stat().st_size > 5 * 1024 * 1024:
                    large_files.append((file_path.name, file_path.stat().st_size / (1024*1024)))
        
        # Show warning for large projects (>1000 files)
        if total_files > 1000:
            msg = f"⚠️ Large Project Detected\n\n"
            msg += f"This project contains {total_files} files.\n"
            msg += f"Some operations may be slower than usual.\n\n"
            msg += f"Recommendations:\n"
            msg += f"• Close unused documents\n"
            msg += f"• Consider splitting into smaller projects\n"
            msg += f"• Disable auto-indexing if not needed"
            
            QMessageBox.warning(
                self,
                "Performance Warning",
                msg
            )
            logger.warning(f"Large project loaded: {total_files} files")
        
        # Show warning for large files
        if large_files:
            msg = f"⚠️ Large Files Detected\n\n"
            msg += f"The following files are very large:\n\n"
            for name, size in large_files[:5]:  # Show first 5
                msg += f"• {name}: {size:.1f} MB\n"
            if len(large_files) > 5:
                msg += f"\n...and {len(large_files) - 5} more\n"
            msg += f"\nEditing these files may be slower."
            
            QMessageBox.information(
                self,
                "Large Files",
                msg
            )
            logger.info(f"Large files in project: {len(large_files)}")
    
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
            
            # Clear crash recovery cache for successfully saved document
            self.crash_recovery.clear_recovery(str(editor.document_path.absolute()))
            
            self.status_bar.showMessage(f"Saved: {editor.document_path.name}", 3000)
            logger.info(f"Saved document: {editor.document_path}")
            return True
            
        except PermissionError as e:
            # Show actionable error message for permission issues
            QMessageBox.critical(
                self,
                "Permission Denied",
                str(e)
            )
            logger.error(f"Permission error saving document: {e}")
            return False
            
        except OSError as e:
            # Show actionable error message for file system issues
            QMessageBox.critical(
                self,
                "File System Error",
                str(e)
            )
            logger.error(f"OS error saving document: {e}")
            return False
            
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
        
        # Show bottom tabs and switch to search
        self.bottom_tabs.setVisible(True)
        self.bottom_tabs.setCurrentWidget(self.search_panel)
        
        # Focus on search input
        self.search_panel.search_input.setFocus()
        self.search_panel.search_input.selectAll()
        
        logger.info("Search panel shown")
    
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
        
        # Start auto-save timer on first document (deferred until actually needed)
        if len(self.open_editors) == 1 and not self.auto_save_timer.isActive():
            self.auto_save_timer.start(self.auto_save_interval)
        
        # Check for template upgrade opportunity
        self._check_template_upgrade(document)
        
        logger.info(f"Opened document in editor: {document.path}")
    
    def _check_template_upgrade(self, document: SpeckitDocument) -> None:
        """Check if document could benefit from template upgrade"""
        if not self.project:
            return
        
        try:
            from ..core.template import TemplateManager
            
            templates_dir = self.project.root / ".specify" / "templates"
            if not templates_dir.exists():
                return
            
            template_manager = TemplateManager(templates_dir)
            
            # Determine document template type (basic heuristic from filename)
            doc_name = document.path.stem.lower()
            template_type = None
            
            if "spec" in doc_name or "specification" in doc_name:
                template_type = "spec-template"
            elif "plan" in doc_name:
                template_type = "plan-template"
            elif "task" in doc_name:
                template_type = "tasks-template"
            
            if not template_type:
                return
            
            # Check if newer template versions exist
            versions = template_manager.get_template_versions(template_type)
            if len(versions) <= 1:
                return  # No newer versions available
            
            # Get latest version
            latest_template = versions[0]
            
            # Prompt user for upgrade
            reply = QMessageBox.question(
                self,
                "Template Upgrade Available",
                f"A newer version of the '{template_type}' template is available:\n\n"
                f"Latest: {latest_template.name}\n"
                f"Updated: {latest_template.updated_at.strftime('%Y-%m-%d') if latest_template.updated_at else 'Unknown'}\n\n"
                f"Would you like to upgrade this document to the new template?\n\n"
                f"Note: A backup will be created automatically.",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Yes:
                self._upgrade_document_template(document, latest_template.name, template_manager)
        
        except Exception as e:
            logger.error(f"Error checking template upgrade: {e}")
    
    def _upgrade_document_template(self, document: SpeckitDocument, 
                                   new_template_name: str,
                                   template_manager) -> None:
        """Upgrade document to new template version"""
        try:
            # Perform migration
            success, messages = template_manager.migrate_document_to_template(
                document.path,
                new_template_name,
                create_backup=True
            )
            
            if success:
                # Reload document in editor
                if document.path in self.open_editors:
                    editor = self.open_editors[document.path]
                    
                    # Reload from disk
                    updated_document = SpeckitDocument.load(document.path)
                    editor.load_document(updated_document)
                
                # Show success message with details
                message_text = "Document upgraded successfully!\n\n"
                message_text += "\n".join(messages)
                
                QMessageBox.information(
                    self,
                    "Template Upgrade Complete",
                    message_text
                )
            else:
                # Show error with rollback option
                self._handle_migration_failure(document, messages)
        
        except Exception as e:
            logger.error(f"Template upgrade failed: {e}")
            self._handle_migration_failure(document, [str(e)])
    
    def _handle_migration_failure(self, document: SpeckitDocument, 
                                  error_messages: List[str]) -> None:
        """Handle migration failure and offer rollback"""
        error_text = "Template migration failed:\n\n"
        error_text += "\n".join(error_messages)
        error_text += "\n\nWould you like to restore from backup?"
        
        reply = QMessageBox.question(
            self,
            "Migration Failed",
            error_text,
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._rollback_migration(document)
    
    def _rollback_migration(self, document: SpeckitDocument) -> None:
        """Rollback to backup after failed migration"""
        try:
            backup_dir = document.path.parent / ".backups"
            if not backup_dir.exists():
                QMessageBox.warning(
                    self,
                    "No Backup Found",
                    "No backup directory found. Cannot rollback."
                )
                return
            
            # Find most recent backup for this document
            import glob
            pattern = f"{document.path.stem}_backup_*{document.path.suffix}"
            backups = list(backup_dir.glob(pattern))
            
            if not backups:
                QMessageBox.warning(
                    self,
                    "No Backup Found",
                    f"No backup found for {document.path.name}"
                )
                return
            
            # Sort by modification time, get most recent
            latest_backup = max(backups, key=lambda p: p.stat().st_mtime)
            
            # Restore from backup
            import shutil
            shutil.copy2(latest_backup, document.path)
            
            # Reload in editor
            if document.path in self.open_editors:
                editor = self.open_editors[document.path]
                restored_document = SpeckitDocument.load(document.path)
                editor.load_document(restored_document)
            
            QMessageBox.information(
                self,
                "Rollback Complete",
                f"Document restored from backup:\n{latest_backup.name}"
            )
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            QMessageBox.critical(
                self,
                "Rollback Failed",
                f"Failed to restore from backup:\n{str(e)}"
            )
    
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
                
        except PermissionError as e:
            # Show actionable error message for permission issues
            QMessageBox.critical(
                self,
                "Permission Denied",
                str(e)
            )
            logger.error(f"Permission error opening file: {e}")
            
        except OSError as e:
            # Show actionable error message for file system issues
            QMessageBox.critical(
                self,
                "File System Error",
                str(e)
            )
            logger.error(f"OS error opening file: {e}")
            
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
    
    def _on_git_commit(self, message: str) -> None:
        """Handle git commit request"""
        if not self.project:
            logger.warning("No project loaded for commit")
            QMessageBox.warning(
                self,
                "No Project",
                "No project loaded"
            )
            return
        
        commit_sha = self.project.commit(message)
        if commit_sha:
            logger.info(f"Created commit: {commit_sha}")
            self.status_bar.showMessage(f"Committed: {message[:50]}...", 3000)
            # Refresh git panel
            if hasattr(self, 'git_panel'):
                self.git_panel._refresh_status()
            # Update git status in status bar
            self._update_git_status()
        else:
            logger.error("Failed to create commit")
            QMessageBox.warning(
                self,
                "Commit Failed",
                "Failed to create commit. Check that files are staged."
            )
            self.status_bar.showMessage("Commit failed", 3000)
    
    def _on_git_commit_shortcut(self) -> None:
        """Handle commit keyboard shortcut"""
        # Switch to git tab and focus commit message
        if hasattr(self, 'bottom_tabs') and hasattr(self, 'git_panel'):
            for i in range(self.bottom_tabs.count()):
                if self.bottom_tabs.widget(i) == self.git_panel:
                    self.bottom_tabs.setCurrentIndex(i)
                    self.git_panel.commit_message.setFocus()
                    break
    
    def _on_git_push(self) -> None:
        """Handle git push"""
        if hasattr(self, 'git_panel'):
            self.git_panel._on_push()
    
    def _on_git_pull(self) -> None:
        """Handle git pull"""
        if hasattr(self, 'git_panel'):
            self.git_panel._on_pull()
    
    def _on_git_diff(self) -> None:
        """Handle show diff"""
        # Switch to git tab
        if hasattr(self, 'bottom_tabs') and hasattr(self, 'git_panel'):
            for i in range(self.bottom_tabs.count()):
                if self.bottom_tabs.widget(i) == self.git_panel:
                    self.bottom_tabs.setCurrentIndex(i)
                    break
    
    def _update_git_status(self) -> None:
        """Update git status in status bar"""
        if not self.project or not self.project.git_repo:
            self.git_status_label.setText("No repo")
            return
        
        try:
            git_status = self.project.get_git_status()
            if not git_status:
                self.git_status_label.setText("No repo")
                return
            
            # Build status text
            parts = []
            
            # Branch name
            if git_status.current_branch:
                parts.append(f"⎇ {git_status.current_branch}")
            
            # Ahead/behind
            if git_status.ahead > 0:
                parts.append(f"↑{git_status.ahead}")
            if git_status.behind > 0:
                parts.append(f"↓{git_status.behind}")
            
            # Changes
            if git_status.has_changes:
                change_count = len(git_status.files)
                parts.append(f"✎ {change_count}")
            
            status_text = " ".join(parts) if parts else "No changes"
            self.git_status_label.setText(status_text)
            
        except Exception as e:
            logger.error(f"Failed to update git status: {e}")
            self.git_status_label.setText("Error")
    
    def _on_ai_chat(self) -> None:
        """Handle AI chat shortcut"""
        # Switch to AI tab and start session
        if hasattr(self, 'bottom_tabs') and hasattr(self, 'ai_panel'):
            for i in range(self.bottom_tabs.count()):
                if self.bottom_tabs.widget(i) == self.ai_panel:
                    self.bottom_tabs.setCurrentIndex(i)
                    self.bottom_tabs.setVisible(True)
                    
                    # Start session with current document context
                    current_widget = self.tab_widget.currentWidget()
                    if isinstance(current_widget, SpeckitEditorWidget):
                        self.ai_panel.start_session(
                            document_path=current_widget.document_path,
                            context_type="chat"
                        )
                    else:
                        self.ai_panel.start_session(context_type="chat")
                    
                    self.ai_panel.prompt_input.setFocus()
                    break
    
    def _on_ai_completion(self) -> None:
        """Handle AI completion shortcut"""
        current_widget = self.tab_widget.currentWidget()
        if not isinstance(current_widget, SpeckitEditorWidget):
            return
        
        # Extract intelligent context from editor
        context = current_widget.extract_ai_context(context_type="completion")
        
        # Log context for debugging
        logger.info(f"AI completion requested - Doc type: {context['document_type']}, "
                   f"Section: {context['current_section']}, Cursor: {context['cursor_position']}")
        
        # For now, show a placeholder suggestion based on document type
        # TODO: Connect to actual MCP AI service with full context
        if context['document_type'] == "specification":
            placeholder_suggestion = " [AI-generated requirement here]"
        elif context['document_type'] == "plan":
            placeholder_suggestion = " [AI-generated implementation plan here]"
        elif context['document_type'] == "tasks":
            placeholder_suggestion = " [AI-generated task here]"
        else:
            placeholder_suggestion = " [AI-generated content here]"
        
        current_widget.show_ai_suggestion(placeholder_suggestion, context['cursor_position'])
    
    def _on_ai_prompt(self, prompt: str) -> None:
        """Handle AI prompt submission"""
        logger.info(f"AI prompt: {prompt}")
        # TODO: Connect to MCP AI service to process the prompt
        # For now, this is handled within AIPanel with a placeholder response
    
    def _on_preferences(self) -> None:
        """Open preferences/settings dialog"""
        dialog = SettingsDialog(
            app_settings=self.app_settings,
            project_settings=self.project_settings,
            parent=self
        )
        
        if dialog.exec():
            # Save application settings
            self.app_settings.save(self.app_settings_path)
            
            # Save project settings if project is loaded
            if self.project and self.project_settings:
                settings_path = self.project.root / ".specify" / "settings.json"
                self.project_settings.save(settings_path)
            
            # Apply new settings
            self._apply_settings()
            
            QMessageBox.information(
                self,
                "Settings Saved",
                "Your settings have been saved successfully."
            )
    
    def _apply_settings(self) -> None:
        """Apply current settings to the UI"""
        # Apply font settings to all editors
        from PySide6.QtGui import QFont
        font = QFont(self.app_settings.font_family, self.app_settings.font_size)
        
        for editor in self.open_editors.values():
            editor.setFont(font)
        
        # Apply auto-save interval if project settings exist
        if self.project_settings:
            if self.project_settings.auto_save_enabled:
                self.auto_save_interval = self.project_settings.auto_save_interval * 1000
                self.auto_save_timer.start(self.auto_save_interval)
            else:
                self.auto_save_timer.stop()
            
            # Apply accessibility settings
            self._apply_accessibility_settings()
        
        logger.info("Settings applied to UI")
    
    def _apply_accessibility_settings(self) -> None:
        """Apply accessibility settings including focus indicators"""
        if not self.project_settings:
            return
        
        # Build focus indicator style based on settings
        focus_style = ""
        if self.project_settings.focus_indicators:
            focus_style = """
            /* Enhanced focus indicators for accessibility */
            *:focus {
                outline: 2px solid #0078d4;
                outline-offset: 2px;
            }
            
            QPushButton:focus {
                border: 2px solid #0078d4;
                outline: none;
            }
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border: 2px solid #0078d4;
            }
            
            QTreeView:focus, QListView:focus {
                border: 2px solid #0078d4;
            }
            
            QTabBar::tab:focus {
                outline: 2px solid #0078d4;
                outline-offset: -2px;
            }
            """
        
        # Get current stylesheet and update it
        current_style = self.styleSheet()
        
        # Remove old focus indicator styles
        import re
        current_style = re.sub(
            r'/\*\s*Enhanced focus indicators.*?\*/.*?\}',
            '',
            current_style,
            flags=re.DOTALL
        )
        current_style = re.sub(
            r'/\*\s*Focus indicators for accessibility.*?\*/.*?\*:focus\s*\{[^}]*\}',
            '',
            current_style,
            flags=re.DOTALL
        )
        
        # Add new focus indicator styles
        self.setStyleSheet(current_style + focus_style)
        
        logger.info(f"Accessibility settings applied: focus_indicators={self.project_settings.focus_indicators}")
    
    def _on_manage_templates(self) -> None:
        """Open template manager dialog"""
        if not self.project:
            QMessageBox.information(
                self,
                "No Project",
                "Please open a project first to manage templates."
            )
            return
        
        templates_dir = self.project.root / ".specify" / "templates"
        
        # Create and show template manager dialog
        dialog = TemplateManagerWidget(templates_dir, parent=self)
        dialog.exec()
    
    
    def keyPressEvent(self, event) -> None:
        """Handle keyboard navigation"""
        if not self.project_settings or not self.project_settings.keyboard_navigation:
            super().keyPressEvent(event)
            return
        
        from PySide6.QtGui import QKeyEvent
        
        # Ctrl+Tab: Next tab
        if event.key() == Qt.Key.Key_Tab and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            current = self.right_panel.currentIndex()
            next_index = (current + 1) % self.right_panel.count()
            self.right_panel.setCurrentIndex(next_index)
            event.accept()
            return
        
        # Ctrl+Shift+Tab: Previous tab
        if event.key() == Qt.Key.Key_Tab and event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            current = self.right_panel.currentIndex()
            prev_index = (current - 1) % self.right_panel.count()
            self.right_panel.setCurrentIndex(prev_index)
            event.accept()
            return
        
        # Ctrl+1 through Ctrl+5: Jump to specific tab
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            key = event.key()
            tab_mapping = {
                Qt.Key.Key_1: 0,  # Editor
                Qt.Key.Key_2: 1,  # Git
                Qt.Key.Key_3: 2,  # MCP
                Qt.Key.Key_4: 3,  # AI
                Qt.Key.Key_5: 4,  # Search
            }
            
            if key in tab_mapping:
                tab_index = tab_mapping[key]
                if tab_index < self.right_panel.count():
                    self.right_panel.setCurrentIndex(tab_index)
                    event.accept()
                    return
        
        # Ctrl+B: Toggle focus between navigator and editor
        if event.key() == Qt.Key.Key_B and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if self.navigator.hasFocus():
                # Focus current editor if available
                current_widget = self.editor_tabs.currentWidget()
                if current_widget:
                    current_widget.setFocus()
            else:
                # Focus navigator
                self.navigator.setFocus()
            event.accept()
            return
        
        # Ctrl+E: Focus current editor
        if event.key() == Qt.Key.Key_E and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            current_widget = self.editor_tabs.currentWidget()
            if current_widget:
                current_widget.setFocus()
            event.accept()
            return
        
        # Alt+Left/Right: Navigate between open editor tabs
        if event.modifiers() == Qt.KeyboardModifier.AltModifier:
            if event.key() == Qt.Key.Key_Left:
                current = self.editor_tabs.currentIndex()
                if current > 0:
                    self.editor_tabs.setCurrentIndex(current - 1)
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Right:
                current = self.editor_tabs.currentIndex()
                if current < self.editor_tabs.count() - 1:
                    self.editor_tabs.setCurrentIndex(current + 1)
                event.accept()
                return
        
        # Pass unhandled events to parent
        super().keyPressEvent(event)
    
    def closeEvent(self, event) -> None:
        """Handle window close event"""
        # Stop MCP server
        if self.mcp_server:
            try:
                self.mcp_server.stop()
                logger.info("MCP server stopped")
            except Exception as e:
                logger.error(f"Error stopping MCP server: {e}")
        
        # Accept the close event
        event.accept()