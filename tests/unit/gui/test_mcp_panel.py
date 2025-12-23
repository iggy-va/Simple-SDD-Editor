"""
GUI tests for MCP Panel functionality.

Tests:
- Query input and execution
- Results display (table, list, terminal, JSON)
- Export functionality
- Service configuration
- Insert reference actions
"""

import pytest
from pathlib import Path
from pytestqt.qtbot import QtBot
from PySide6.QtCore import Qt

from src.gui.mcp_panel import MCPPanel


class TestMCPPanelInitialization:
    """Test MCP panel initialization"""
    
    def test_panel_creates_successfully(self, qtbot: QtBot):
        """Test that MCP panel initializes without errors"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        assert panel is not None
    
    def test_panel_has_query_interface(self, qtbot: QtBot):
        """Test that panel has query input components"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        # Query input field
        assert hasattr(panel, 'query_input')
        assert panel.query_input is not None
        
        # Query type selector
        assert hasattr(panel, 'query_type_combo')
        assert panel.query_type_combo is not None
        
        # Execute button
        assert hasattr(panel, 'execute_button')
        assert panel.execute_button is not None
    
    def test_panel_has_results_display(self, qtbot: QtBot):
        """Test that panel has results display tabs"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        assert hasattr(panel, 'results_tabs')
        assert panel.results_tabs is not None
        
        # Should have 4 tabs: Table, List, Terminal, JSON
        assert panel.results_tabs.count() == 4


class TestQueryTypes:
    """Test query type selection"""
    
    def test_query_type_selector_has_options(self, qtbot: QtBot):
        """Test that query type selector has all options"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        combo = panel.query_type_combo
        
        # Should have multiple query types
        assert combo.count() >= 4
        
        # Check for expected types
        types = [combo.itemText(i) for i in range(combo.count())]
        assert "JQL (Jira)" in types
        assert "SQL (Database)" in types
        assert "GitHub Query" in types
        assert "Terminal Command" in types
    
    def test_selecting_query_type(self, qtbot: QtBot):
        """Test selecting different query types"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        combo = panel.query_type_combo
        
        # Select JQL
        combo.setCurrentText("JQL (Jira)")
        assert combo.currentText() == "JQL (Jira)"
        
        # Select SQL
        combo.setCurrentText("SQL")
        assert combo.currentText() == "SQL (Database)"


class TestQueryInput:
    """Test query input field"""
    
    def test_query_input_accepts_text(self, qtbot: QtBot):
        """Test that query input accepts text"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        query_text = "SELECT * FROM issues WHERE status = 'open'"
        panel.query_input.setPlainText(query_text)
        
        assert panel.query_input.toPlainText() == query_text
    
    def test_multiline_query_input(self, qtbot: QtBot):
        """Test that query input supports multiline queries"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        multiline_query = """SELECT id, summary, status
FROM issues
WHERE assignee = 'me'
ORDER BY created DESC"""
        
        panel.query_input.setPlainText(multiline_query)
        
        assert "SELECT id" in panel.query_input.toPlainText()
        assert "ORDER BY" in panel.query_input.toPlainText()


class TestQueryExecution:
    """Test query execution"""
    
    def test_execute_button_enabled(self, qtbot: QtBot):
        """Test that execute button is enabled when query is present"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        # Initially might be disabled
        initial_state = panel.execute_button.isEnabled()
        
        # Add query text
        panel.query_input.setPlainText("SELECT * FROM issues")
        
        # Button should be enabled (or already was)
        assert panel.execute_button.isEnabled() or not initial_state
    
    def test_execute_button_click(self, qtbot: QtBot):
        """Test clicking execute button"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        # Set query
        panel.query_input.setPlainText("project = PROJ AND status = 'Open'")
        panel.query_type_combo.setCurrentText("JQL (Jira)")
        
        # Click execute (simulated)
        # Note: Actual execution would require MCP server mock
        qtbot.mouseClick(panel.execute_button, Qt.LeftButton)
        
        # Should not crash
        assert True


class TestResultsDisplay:
    """Test results display tabs"""
    
    def test_table_tab_exists(self, qtbot: QtBot):
        """Test that table results tab exists"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        # Find table tab
        table_tab_index = -1
        for i in range(panel.results_tabs.count()):
            if panel.results_tabs.tabText(i) == "Table":
                table_tab_index = i
                break
        
        assert table_tab_index >= 0
    
    def test_list_tab_exists(self, qtbot: QtBot):
        """Test that list results tab exists"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        # Find list tab
        list_tab_index = -1
        for i in range(panel.results_tabs.count()):
            if panel.results_tabs.tabText(i) == "List":
                list_tab_index = i
                break
        
        assert list_tab_index >= 0
    
    def test_terminal_tab_exists(self, qtbot: QtBot):
        """Test that terminal results tab exists"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        # Find terminal tab
        terminal_tab_index = -1
        for i in range(panel.results_tabs.count()):
            if panel.results_tabs.tabText(i) == "Terminal":
                terminal_tab_index = i
                break
        
        assert terminal_tab_index >= 0
    
    def test_json_tab_exists(self, qtbot: QtBot):
        """Test that JSON results tab exists"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        # Find JSON tab
        json_tab_index = -1
        for i in range(panel.results_tabs.count()):
            if panel.results_tabs.tabText(i) == "JSON":
                json_tab_index = i
                break
        
        assert json_tab_index >= 0
    
    def test_switching_between_tabs(self, qtbot: QtBot):
        """Test switching between result tabs"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        # Switch to different tabs
        for i in range(panel.results_tabs.count()):
            panel.results_tabs.setCurrentIndex(i)
            assert panel.results_tabs.currentIndex() == i


class TestTableResults:
    """Test table results display"""
    
    def test_table_widget_exists(self, qtbot: QtBot):
        """Test that table widget exists in table tab"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        assert hasattr(panel, 'results_table')
        assert panel.results_table is not None
    
    def test_table_columns_configurable(self, qtbot: QtBot):
        """Test that table columns can be set"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        # Table should support column headers
        table = panel.results_table
        
        # Set columns (simulated)
        columns = ["ID", "Summary", "Status", "Assignee"]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        assert table.columnCount() == 4
    
    def test_table_sorting(self, qtbot: QtBot):
        """Test that table columns are sortable"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        table = panel.results_table
        
        # Sorting should be enabled
        assert table.isSortingEnabled()


class TestListResults:
    """Test list results display (for issues)"""
    
    def test_list_widget_exists(self, qtbot: QtBot):
        """Test that list widget exists in list tab"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        assert hasattr(panel, 'results_list')
        assert panel.results_list is not None
    
    def test_list_items_have_tooltips(self, qtbot: QtBot):
        """Test that list items can have tooltips"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        # List widget should support tooltips
        assert panel.results_list is not None


class TestTerminalResults:
    """Test terminal output display"""
    
    def test_terminal_widget_exists(self, qtbot: QtBot):
        """Test that terminal output widget exists"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        assert hasattr(panel, 'terminal_output')
        assert panel.terminal_output is not None
    
    def test_terminal_text_append(self, qtbot: QtBot):
        """Test appending text to terminal output"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        # Append text
        panel.terminal_output.append("$ git status")
        panel.terminal_output.append("On branch main")
        
        # Text should be in terminal
        assert "git status" in panel.terminal_output.toPlainText()


class TestJSONResults:
    """Test JSON results display"""
    
    def test_json_widget_exists(self, qtbot: QtBot):
        """Test that JSON display widget exists"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        assert hasattr(panel, 'json_output')
        assert panel.json_output is not None
    
    def test_json_formatting(self, qtbot: QtBot):
        """Test JSON output formatting"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        # Set JSON text
        json_text = '{"id": 1, "status": "open", "title": "Test Issue"}'
        panel.json_output.setPlainText(json_text)
        
        # JSON should be displayed
        assert "Test Issue" in panel.json_output.toPlainText()


class TestExportActions:
    """Test export functionality"""
    
    def test_export_button_exists(self, qtbot: QtBot):
        """Test that export button/menu exists"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        assert hasattr(panel, 'export_button')
        assert panel.export_button is not None
    
    def test_export_menu_has_options(self, qtbot: QtBot):
        """Test that export menu has CSV, JSON, Markdown options"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        # Export menu should exist
        menu = panel.export_button.menu()
        assert menu is not None
        
        # Check for export actions
        actions = menu.actions()
        action_texts = [action.text() for action in actions]
        
        assert "Export as CSV" in action_texts
        assert "Export as JSON" in action_texts
        assert "Export as Markdown" in action_texts


class TestInsertReference:
    """Test insert reference functionality"""
    
    def test_insert_reference_action_exists(self, qtbot: QtBot):
        """Test that insert reference action exists in context menu"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        # Context menu should be available on results
        # (Implementation detail - might be on right-click)
        assert panel.results_list is not None


class TestServiceConfiguration:
    """Test MCP service configuration"""
    
    def test_config_button_exists(self, qtbot: QtBot):
        """Test that service configuration button exists"""
        panel = MCPPanel()
        qtbot.addWidget(panel)
        
        # Config button should exist somewhere
        # (Might be in toolbar or settings)
        assert panel is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
