"""Test that all modules can be imported without syntax errors"""

import pytest


def test_core_imports():
    """Test core module imports"""
    from src.core import document, project, search, template, validator
    from src.core.search_query import SearchQuery, SearchResult


def test_utils_imports():
    """Test utils module imports"""
    from src.utils import config, logging


def test_gui_imports():
    """Test GUI module imports"""
    from src.gui.main_window import MainWindow
    from src.gui.editor import SpeckitEditorWidget
    from src.gui.navigator import ProjectNavigator
    from src.gui.search_panel import SearchPanel
    from src.gui.template_dialog import TemplateDialog
    from src.gui.template_manager import TemplateManagerWidget
    from src.gui.settings_dialog import SettingsDialog
    from src.gui.mcp_panel import MCPPanel
    from src.gui.git_panel import GitPanel
    from src.gui.ai_panel import AIPanel


def test_mcp_imports():
    """Test MCP module imports"""
    from src.mcp.server import EmbeddedMCPServer, MCPConnection, ServiceType, ConnectionState
    from src.mcp.credentials import ServiceCredential, CredentialStore
    from src.mcp.base_service import BaseMCPService
    from src.mcp.services import (
        JiraService, GitHubService, DatabaseService,
        TerminalService, ChromeService, GitService
    )


def test_main_entry_point():
    """Test that main.py can be imported"""
    # This will catch syntax errors in main.py
    import importlib.util
    import sys
    from pathlib import Path
    
    main_path = Path(__file__).parent.parent.parent / "main.py"
    
    spec = importlib.util.spec_from_file_location("main", main_path)
    if spec and spec.loader:
        main_module = importlib.util.module_from_spec(spec)
        # Don't execute (would start the app), just compile
        spec.loader.exec_module(main_module)
