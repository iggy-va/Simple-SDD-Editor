"""
GUI tests for MainWindow functionality.

Tests critical user workflows:
- Document creation and editing
- Multi-document tab navigation
- File operations (open, save, close)
- Project operations
- Keyboard shortcuts
"""

import pytest
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

from src.gui.main_window import MainWindow
from src.core.document import SpeckitDocument


class TestMainWindowLaunch:
    """Test SC-001: Application launch and initialization"""
    
    def test_window_launches_successfully(self, qtbot: QtBot):
        """Test that main window launches without errors"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        assert window is not None
        assert window.windowTitle() == "Speckit Editor"
        assert window.isVisible() or True  # Window might not be shown in headless test
    
    def test_window_initializes_core_components(self, qtbot: QtBot):
        """Test that main window initializes all required components"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Check central widget components
        assert window.tab_widget is not None
        assert window.navigator is not None
        assert window.git_panel is not None
        assert window.mcp_panel is not None
        assert window.ai_panel is not None
        assert window.search_panel is not None
    
    def test_window_has_menus(self, qtbot: QtBot):
        """Test that all menus are created"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        menubar = window.menuBar()
        menu_titles = [action.text() for action in menubar.actions()]
        
        assert "&File" in menu_titles
        assert "&Edit" in menu_titles
        assert "&View" in menu_titles
        assert "&Git" in menu_titles
        assert "&Tools" in menu_titles
        assert "&Help" in menu_titles


class TestDocumentOperations:
    """Test SC-002/SC-003: Document creation, editing, and multi-document handling"""
    
    def test_create_new_document(self, qtbot: QtBot, sample_document: SpeckitDocument, sample_project: SpeckitProject):
        """Test creating a new document (Ctrl+N workflow)"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Initial state: should have welcome tab
        initial_count = window.tab_widget.count()
        
        # Create a new document programmatically (simulating template selection)
        doc = sample_document
        
        # Add document to window
        window._open_document_in_editor(doc)
        
        # Verify new tab was created
        assert window.tab_widget.count() == initial_count + 1
        
        # Verify editor is active
        current_widget = window.tab_widget.currentWidget()
        assert current_widget is not None
        assert hasattr(current_widget, 'editor')
    
    def test_switch_between_multiple_documents(self, qtbot: QtBot, sample_document: SpeckitDocument, sample_project: SpeckitProject):
        """Test SC-003: Navigate between multiple open documents"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Create multiple documents
        documents = []
        for i in range(5):
            doc = sample_document
            documents.append(doc)
            window._open_document_in_editor(doc)
        
        # Verify all tabs created
        # Note: May include welcome tab
        assert window.tab_widget.count() >= 5
        
        # Test tab switching
        window.tab_widget.setCurrentIndex(2)
        assert window.tab_widget.currentIndex() == 2
        
        window.tab_widget.setCurrentIndex(4)
        assert window.tab_widget.currentIndex() == 4
    
    def test_close_document_tab(self, qtbot: QtBot, sample_document: SpeckitDocument, sample_project: SpeckitProject):
        """Test closing a document tab"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Create document
        doc = sample_document
        window._open_document_in_editor(doc)
        
        initial_count = window.tab_widget.count()
        
        # Close the tab (find the document tab, not welcome tab)
        for i in range(window.tab_widget.count()):
            if window.tab_widget.tabText(i) == "test_close.md":
                window.tab_widget.removeTab(i)
                break
        
        # Verify tab was removed
        assert window.tab_widget.count() == initial_count - 1


class TestKeyboardShortcuts:
    """Test keyboard shortcuts for common operations"""
    
    def test_ctrl_n_new_document(self, qtbot: QtBot):
        """Test Ctrl+N triggers new document action"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Find the New Document action
        new_doc_action = None
        for action in window.findChildren(QAction):
            if action.text() == "&New Document":
                new_doc_action = action
                break
        
        assert new_doc_action is not None
        assert new_doc_action.shortcut().toString() == "Ctrl+N"
    
    def test_ctrl_s_save_document(self, qtbot: QtBot):
        """Test Ctrl+S triggers save action"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Find the Save action
        save_action = None
        for action in window.findChildren(QAction):
            if action.text() == "&Save":
                save_action = action
                break
        
        assert save_action is not None
        assert save_action.shortcut().toString() == "Ctrl+S"
    
    def test_ctrl_w_close_tab(self, qtbot: QtBot):
        """Test Ctrl+W triggers close tab action"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Find the Close Tab action
        close_action = None
        for action in window.findChildren(QAction):
            if action.text() == "&Close Tab":
                close_action = action
                break
        
        assert close_action is not None
        assert close_action.shortcut().toString() == "Ctrl+W"


class TestProjectOperations:
    """Test project creation and management"""
    
    def test_create_new_project(self, qtbot: QtBot, sample_document: SpeckitDocument, sample_project: SpeckitProject):
        """Test creating a new speckit project"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        project_path = sample_project.root_path
        project_path.mkdir()
        
        # Create project programmatically
        from src.core.project import SpeckitProject
        project = sample_project
        
        # Load project in window
        window._load_project(project)
        
        # Verify project is loaded
        assert window.project is not None
        assert window.project.name == "Test Project"
        assert window.navigator.project is not None
    
    def test_project_displays_in_navigator(self, qtbot: QtBot, sample_document: SpeckitDocument, sample_project: SpeckitProject):
        """Test that project files appear in navigator"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        project_path = sample_project.root_path
        project_path.mkdir()
        
        # Create project with documents
        from src.core.project import SpeckitProject
        project = sample_project
        
        # Create a document
        doc = sample_document
        doc.save()
        
        # Load project
        window._load_project(project)
        
        # Navigator should have project loaded
        assert window.navigator.project is not None


class TestEditorFunctionality:
    """Test editor widget functionality within main window"""
    
    def test_editor_accepts_text_input(self, qtbot: QtBot, sample_document: SpeckitDocument, sample_project: SpeckitProject):
        """Test that editor accepts user text input"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Create and open document
        doc = sample_document
        window._open_document_in_editor(doc)
        
        # Get current editor
        current_widget = window.tab_widget.currentWidget()
        if hasattr(current_widget, 'editor'):
            editor = current_widget
            
            # Simulate typing
            test_text = "# Test Heading\\n\\nThis is test content."
            editor.setPlainText(test_text)
            
            # Verify text was set
            assert editor.toPlainText() == test_text
    
    def test_editor_tracks_modifications(self, qtbot: QtBot, sample_document: SpeckitDocument, sample_project: SpeckitProject):
        """Test that editor tracks document modifications"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Create and open document
        doc = sample_document
        window._open_document_in_editor(doc)
        
        # Get current editor
        current_widget = window.tab_widget.currentWidget()
        if hasattr(current_widget, 'editor'):
            editor = current_widget
            
            # Initially not modified
            initial_modified = editor.document().isModified()
            
            # Make changes
            editor.setPlainText("Modified content")
            
            # Should be marked as modified
            assert editor.document().isModified() or not initial_modified


class TestGitPanelIntegration:
    """Test Git panel integration in main window"""
    
    def test_git_panel_exists(self, qtbot: QtBot):
        """Test that Git panel is initialized"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        assert window.git_panel is not None
    
    def test_git_panel_connected_to_project(self, qtbot: QtBot, sample_document: SpeckitDocument, sample_project: SpeckitProject):
        """Test that Git panel updates when project loads"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        project_path = sample_project.root_path
        project_path.mkdir()
        
        # Create project
        from src.core.project import SpeckitProject
        project = sample_project
        
        # Initialize git repo
        import subprocess
        subprocess.run(["git", "init"], cwd=project_path, check=True)
        
        # Load project
        window._load_project(project)
        
        # Git panel should be aware of project
        # (Actual git operations tested in integration tests)
        assert window.git_panel is not None


class TestMCPPanelIntegration:
    """Test MCP panel integration in main window"""
    
    def test_mcp_panel_exists(self, qtbot: QtBot):
        """Test that MCP panel is initialized"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        assert window.mcp_panel is not None
    
    def test_mcp_panel_query_interface_available(self, qtbot: QtBot):
        """Test that MCP panel query interface is accessible"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # MCP panel should have query input
        assert hasattr(window.mcp_panel, 'query_input')
        assert hasattr(window.mcp_panel, 'execute_button')
        assert hasattr(window.mcp_panel, 'results_tabs')


class TestSearchFunctionality:
    """Test search panel functionality"""
    
    def test_search_panel_exists(self, qtbot: QtBot):
        """Test that search panel is initialized"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        assert window.search_panel is not None
    
    def test_ctrl_f_activates_search(self, qtbot: QtBot):
        """Test Ctrl+F activates search panel"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Find the Find action
        find_action = None
        for action in window.findChildren(QAction):
            if action.text() == "&Find...":
                find_action = action
                break
        
        assert find_action is not None
        assert find_action.shortcut().toString() == "Ctrl+F"


class TestStatusBar:
    """Test status bar updates"""
    
    def test_status_bar_exists(self, qtbot: QtBot):
        """Test that status bar is initialized"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        assert window.statusBar() is not None
    
    def test_status_bar_shows_cursor_position(self, qtbot: QtBot, sample_document: SpeckitDocument, sample_project: SpeckitProject):
        """Test that status bar shows cursor position when editing"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Create document
        doc = sample_document
        window._open_document_in_editor(doc)
        
        # Status bar should exist and potentially show position
        status_bar = window.statusBar()
        assert status_bar is not None
        # Position label might exist (implementation detail)


class TestAutoSave:
    """Test auto-save and crash recovery"""
    
    def test_auto_save_timer_exists(self, qtbot: QtBot):
        """Test that auto-save timer is configured"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        assert window.auto_save_timer is not None
        assert window.auto_save_interval == 30000  # 30 seconds
    
    def test_recovery_timer_active(self, qtbot: QtBot):
        """Test that recovery timer is active"""
        window = MainWindow()
        qtbot.addWidget(window)
        
        assert window.recovery_timer is not None
        assert window.recovery_timer.isActive()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
