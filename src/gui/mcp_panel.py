"""MCP panel for managing service connections"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..mcp.server import ConnectionState, EmbeddedMCPServer, MCPConnection, ServiceType
from ..mcp.credentials import ServiceCredential
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AddConnectionDialog(QDialog):
    """Dialog for adding new MCP connection"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Add MCP Connection")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Form
        form_layout = QFormLayout()
        
        # Connection name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("My Jira Connection")
        form_layout.addRow("Connection Name:", self.name_input)
        
        # Service type
        self.service_combo = QComboBox()
        for service in ServiceType:
            self.service_combo.addItem(service.value.title(), service)
        form_layout.addRow("Service Type:", self.service_combo)
        
        # Configuration fields
        self.config_input = QTextEdit()
        self.config_input.setPlaceholderText("Configuration (JSON format)\nExample:\n{\n  \"url\": \"https://jira.example.com\"\n}")
        self.config_input.setMaximumHeight(100)
        form_layout.addRow("Configuration:", self.config_input)
        
        layout.addLayout(form_layout)
        
        # Credentials section
        cred_group = QGroupBox("Credentials (Optional)")
        cred_layout = QFormLayout(cred_group)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("username")
        cred_layout.addRow("Username:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("password")
        cred_layout.addRow("Password:", self.password_input)
        
        self.api_token_input = QLineEdit()
        self.api_token_input.setPlaceholderText("API token or personal access token")
        cred_layout.addRow("API Token:", self.api_token_input)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("API key")
        cred_layout.addRow("API Key:", self.api_key_input)
        
        layout.addWidget(cred_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_connection(self) -> Optional[MCPConnection]:
        """Get connection from dialog inputs"""
        name = self.name_input.text().strip()
        if not name:
            return None
        
        service_type = self.service_combo.currentData()
        
        # Parse config
        config_text = self.config_input.toPlainText().strip()
        config = {}
        
        if config_text:
            try:
                import json
                config = json.loads(config_text)
            except json.JSONDecodeError:
                # Fallback: treat as simple key-value
                config = {'raw_config': config_text}
        
        return MCPConnection(
            service_type=service_type,
            name=name,
            config=config
        )
    
    def get_credentials(self) -> Optional[ServiceCredential]:
        """Get credentials from dialog inputs"""
        username = self.username_input.text().strip() or None
        password = self.password_input.text().strip() or None
        api_token = self.api_token_input.text().strip() or None
        api_key = self.api_key_input.text().strip() or None
        
        # Only create credentials if at least one field is filled
        if any([username, password, api_token, api_key]):
            return ServiceCredential(
                username=username,
                password=password,
                api_token=api_token,
                api_key=api_key
            )
        return None


class MCPPanel(QWidget):
    """Panel for managing MCP connections"""
    
    # Signal emitted when connection is tested
    connectionTested = Signal(str, bool, str)  # (name, success, message)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Accessibility
        self.setAccessibleName("MCP Panel")
        self.setAccessibleDescription("Panel for managing Model Context Protocol integrations and connections")
        
        self.mcp_server: Optional[EmbeddedMCPServer] = None
        
        # Create UI
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header
        header_label = QLabel("<b>MCP Integrations</b>")
        layout.addWidget(header_label)
        
        # Connection list
        list_group = QGroupBox("Connections")
        list_layout = QVBoxLayout(list_group)
        
        self.connections_list = QListWidget()
        self.connections_list.setAccessibleName("MCP Connections")
        self.connections_list.setAccessibleDescription("List of configured MCP connections")
        self.connections_list.itemSelectionChanged.connect(self._on_selection_changed)
        list_layout.addWidget(self.connections_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Add...")
        self.add_button.setAccessibleDescription("Add a new MCP connection")
        self.add_button.clicked.connect(self._on_add_connection)
        button_layout.addWidget(self.add_button)
        
        self.remove_button = QPushButton("Remove")
        self.remove_button.setAccessibleDescription("Remove selected MCP connection")
        self.remove_button.clicked.connect(self._on_remove_connection)
        self.remove_button.setEnabled(False)
        button_layout.addWidget(self.remove_button)
        
        self.test_button = QPushButton("Test Connection")
        self.test_button.setAccessibleDescription("Test the selected MCP connection")
        self.test_button.clicked.connect(self._on_test_connection)
        self.test_button.setEnabled(False)
        button_layout.addWidget(self.test_button)
        
        button_layout.addStretch()
        list_layout.addLayout(button_layout)
        
        layout.addWidget(list_group)
        
        # Query and Results section (T130-T139)
        query_results_group = QGroupBox("Query & Results")
        query_results_layout = QVBoxLayout(query_results_group)
        
        # Query input (T130)
        query_input_layout = QHBoxLayout()
        
        self.query_type_combo = QComboBox()
        self.query_type_combo.addItems(["JQL (Jira)", "SQL (Database)", "GitHub Query", "Terminal Command"])
        self.query_type_combo.setAccessibleDescription("Select query type")
        query_input_layout.addWidget(QLabel("Type:"))
        query_input_layout.addWidget(self.query_type_combo)
        query_input_layout.addStretch()
        
        query_results_layout.addLayout(query_input_layout)
        
        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("Enter query...\nExamples:\n  JQL: project = PROJ AND status = Open\n  SQL: SELECT * FROM users LIMIT 10\n  GitHub: is:issue is:open label:bug\n  Terminal: ls -la")
        self.query_input.setMaximumHeight(100)
        self.query_input.setAccessibleName("Query Input")
        self.query_input.setAccessibleDescription("Enter JQL, SQL, GitHub query, or terminal command")
        query_results_layout.addWidget(self.query_input)
        
        # Execute button (T132)
        execute_layout = QHBoxLayout()
        
        self.execute_button = QPushButton("Execute Query")
        self.execute_button.setAccessibleDescription("Execute the entered query")
        self.execute_button.clicked.connect(self._on_execute_query)
        self.execute_button.setEnabled(False)
        execute_layout.addWidget(self.execute_button)
        
        self.export_button = QPushButton("Export Results...")
        self.export_button.setAccessibleDescription("Export query results")
        self.export_button.clicked.connect(self._on_export_results)
        self.export_button.setEnabled(False)
        execute_layout.addWidget(self.export_button)
        
        execute_layout.addStretch()
        query_results_layout.addLayout(execute_layout)
        
        # Results display (T131)
        self.results_tabs = QTabWidget()
        self.results_tabs.setAccessibleName("Query Results")
        
        # Table view for database results (T133)
        self.results_table = QTableWidget()
        self.results_table.setAccessibleName("Results Table")
        self.results_table.setAccessibleDescription("Database query results in table format")
        self.results_table.setSortingEnabled(True)
        self.results_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self._on_table_context_menu)
        self.results_tabs.addTab(self.results_table, "Table")
        
        # List view for Jira/GitHub (T134)
        self.results_list = QListWidget()
        self.results_list.setAccessibleName("Results List")
        self.results_list.setAccessibleDescription("Jira or GitHub issue results")
        self.results_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_list.customContextMenuRequested.connect(self._on_list_context_menu)
        self.results_tabs.addTab(self.results_list, "List")
        
        # Terminal output (T135)
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setAccessibleName("Terminal Output")
        self.terminal_output.setAccessibleDescription("Real-time terminal command output")
        self.terminal_output.setStyleSheet("QTextEdit { background-color: #1e1e1e; color: #d4d4d4; font-family: 'Consolas', 'Courier New', monospace; }")
        self.results_tabs.addTab(self.terminal_output, "Terminal")
        
        # JSON view
        self.json_output = QTextEdit()
        self.json_output.setReadOnly(True)
        self.json_output.setAccessibleName("JSON Output")
        self.json_output.setAccessibleDescription("Query results in JSON format")
        self.json_output.setStyleSheet("QTextEdit { font-family: 'Consolas', 'Courier New', monospace; }")
        self.results_tabs.addTab(self.json_output, "JSON")
        
        query_results_layout.addWidget(self.results_tabs)
        
        layout.addWidget(query_results_group)
        
        # Status area
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("No connection selected")
        self.status_label.setWordWrap(True)
        self.status_label.setAccessibleName("Connection Status")
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_group)
        
        layout.addStretch()
        
        logger.debug("MCPPanel initialized")
    
    def set_mcp_server(self, server: EmbeddedMCPServer) -> None:
        """Set the MCP server instance"""
        self.mcp_server = server
        self._refresh_connections()
        logger.info("MCPPanel connected to MCP server")
    
    def _refresh_connections(self) -> None:
        """Refresh the connections list"""
        self.connections_list.clear()
        
        if not self.mcp_server:
            return
        
        connections = self.mcp_server.list_connections()
        
        for conn in connections:
            # Create list item with status indicator
            status_icon = self._get_status_icon(conn.state)
            item_text = f"{status_icon} {conn.name} ({conn.service_type.value})"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, conn.name)
            
            self.connections_list.addItem(item)
        
        logger.debug(f"Refreshed {len(connections)} connections")
    
    def _get_status_icon(self, state: ConnectionState) -> str:
        """Get icon for connection state"""
        if state == ConnectionState.CONNECTED:
            return "✓"
        elif state == ConnectionState.ERROR:
            return "✗"
        elif state == ConnectionState.CONNECTING:
            return "⟳"
        else:
            return "○"
    
    def _on_selection_changed(self) -> None:
        """Handle selection change"""
        selected = self.connections_list.selectedItems()
        has_selection = len(selected) > 0
        
        self.remove_button.setEnabled(has_selection)
        self.test_button.setEnabled(has_selection)
        self.execute_button.setEnabled(has_selection)  # Enable query execution when connection selected
        
        if has_selection and self.mcp_server:
            conn_name = selected[0].data(Qt.UserRole)
            conn = self.mcp_server.get_connection(conn_name)
            
            if conn:
                status_text = f"<b>{conn.name}</b><br>"
                status_text += f"Type: {conn.service_type.value}<br>"
                status_text += f"State: {conn.state.value}<br>"
                
                if conn.error_message:
                    status_text += f"<br><span style='color: red;'>Error: {conn.error_message}</span>"
                
                self.status_label.setText(status_text)
        else:
            self.status_label.setText("No connection selected")
    
    def _on_add_connection(self) -> None:
        """Handle add connection"""
        dialog = AddConnectionDialog(self)
        
        if dialog.exec() == QDialog.Accepted:
            conn = dialog.get_connection()
            credentials = dialog.get_credentials()
            
            if conn and self.mcp_server:
                # Add connection
                if self.mcp_server.add_connection(conn):
                    # Store credentials if provided
                    if credentials:
                        self.mcp_server.credential_store.store_credentials(conn.name, credentials)
                        logger.info(f"Stored credentials for {conn.name}")
                    
                    self._refresh_connections()
                    logger.info(f"Added connection: {conn.name}")
                else:
                    QMessageBox.warning(
                        self,
                        "Add Failed",
                        "Failed to add connection."
                    )
    
    def _on_remove_connection(self) -> None:
        """Handle remove connection"""
        selected = self.connections_list.selectedItems()
        
        if not selected or not self.mcp_server:
            return
        
        conn_name = selected[0].data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Confirm Remove",
            f"Remove connection '{conn_name}'?\n\nThis will also delete any stored credentials.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.mcp_server.remove_connection(conn_name):
                # Also delete credentials
                self.mcp_server.credential_store.delete_credentials(conn_name)
                self._refresh_connections()
                logger.info(f"Removed connection and credentials: {conn_name}")
    
    def _on_test_connection(self) -> None:
        """Handle test connection"""
        selected = self.connections_list.selectedItems()
        
        if not selected or not self.mcp_server:
            return
        
        conn_name = selected[0].data(Qt.UserRole)
        conn = self.mcp_server.get_connection(conn_name)
        
        if not conn:
            return
        
        logger.info(f"Testing connection: {conn_name}")
        self.status_label.setText(f"<b>Testing {conn_name}...</b><br>Please wait up to 5 seconds...")
        
        # Refresh to show connecting state
        self._refresh_connections()
        
        # Force UI update
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        
        # Test connection (synchronous for now)
        success, error_msg = self.mcp_server.test_connection(conn_name)
        
        if success:
            status_html = f"<b style='color: green;'>✓ Connection Successful</b><br>"
            status_html += f"Service: {conn.service_type.value}<br>"
            status_html += f"State: Connected"
            self.status_label.setText(status_html)
            self.connectionTested.emit(conn_name, True, "Connection successful")
        else:
            status_html = f"<b style='color: red;'>✗ Connection Failed</b><br>"
            status_html += f"Service: {conn.service_type.value}<br>"
            status_html += f"Error: {error_msg or 'Unknown error'}<br><br>"
            
            # Add helpful suggestions based on error type
            if "timeout" in (error_msg or "").lower():
                status_html += "<i>Suggestion: Check network connection and service URL</i>"
            elif "credentials" in (error_msg or "").lower() or "auth" in (error_msg or "").lower():
                status_html += "<i>Suggestion: Verify your username, password, or API token</i>"
            elif "not found" in (error_msg or "").lower():
                status_html += "<i>Suggestion: Check the service URL or configuration</i>"
            
            self.status_label.setText(status_html)
            self.connectionTested.emit(conn_name, False, error_msg or "Unknown error")
        
        # Refresh to update status icons
        self._refresh_connections()    
    def _on_execute_query(self) -> None:
        """Handle query execution (T132)"""
        query = self.query_input.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "Empty Query", "Please enter a query to execute.")
            return
        
        selected = self.connections_list.selectedItems()
        if not selected or not self.mcp_server:
            QMessageBox.warning(self, "No Connection", "Please select a connection first.")
            return
        
        conn_name = selected[0].data(Qt.UserRole)
        query_type = self.query_type_combo.currentText()
        
        self.status_label.setText(f"<b>Executing {query_type}...</b><br>Please wait...")
        
        # Mock query execution - in real implementation, this would call MCP service
        import json
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        
        try:
            # Simulate query based on type
            if "JQL" in query_type or "GitHub" in query_type:
                # Mock issue list (T134)
                self._populate_issue_list([
                    {"key": "PROJ-123", "summary": "Example bug report", "status": "Open", "assignee": "user@example.com"},
                    {"key": "PROJ-124", "summary": "Feature request", "status": "In Progress", "assignee": "dev@example.com"},
                    {"key": "PROJ-125", "summary": "Documentation update", "status": "Done", "assignee": "doc@example.com"},
                ])
                self.results_tabs.setCurrentWidget(self.results_list)
            elif "SQL" in query_type:
                # Mock database results (T133)
                self._populate_table([
                    {"id": "1", "name": "Alice", "email": "alice@example.com", "role": "Admin"},
                    {"id": "2", "name": "Bob", "email": "bob@example.com", "role": "User"},
                    {"id": "3", "name": "Charlie", "email": "charlie@example.com", "role": "Developer"},
                ])
                self.results_tabs.setCurrentWidget(self.results_table)
            elif "Terminal" in query_type:
                # Mock terminal output (T135)
                self._append_terminal_output(f"$ {query}\n")
                self._append_terminal_output("total 48\n")
                self._append_terminal_output("drwxr-xr-x  12 user  group   384 Dec 23 11:00 .\n")
                self._append_terminal_output("drwxr-xr-x   8 user  group   256 Dec 22 10:30 ..\n")
                self._append_terminal_output("-rw-r--r--   1 user  group  1234 Dec 23 09:15 main.py\n")
                self._append_terminal_output("-rw-r--r--   1 user  group  5678 Dec 23 10:45 README.md\n")
                self.results_tabs.setCurrentWidget(self.terminal_output)
            
            # Also show JSON view
            self.json_output.setText(json.dumps({
                "query": query,
                "query_type": query_type,
                "connection": conn_name,
                "timestamp": "2025-12-23T11:36:00Z",
                "result_count": 3,
                "status": "success"
            }, indent=2))
            
            self.status_label.setText(f"<b style='color: green;'>✓ Query Executed Successfully</b><br>Type: {query_type}<br>Results: 3 items")
            self.export_button.setEnabled(True)
            
        except Exception as e:
            self.status_label.setText(f"<b style='color: red;'>✗ Query Failed</b><br>Error: {str(e)}")
            logger.error(f"Query execution failed: {e}")
    
    def _populate_table(self, results: list) -> None:
        """Populate results table (T133)"""
        if not results:
            self.results_table.setRowCount(0)
            self.results_table.setColumnCount(0)
            return
        
        # Set up columns
        columns = list(results[0].keys())
        self.results_table.setColumnCount(len(columns))
        self.results_table.setHorizontalHeaderLabels(columns)
        
        # Populate rows
        self.results_table.setRowCount(len(results))
        for row_idx, row_data in enumerate(results):
            for col_idx, col_name in enumerate(columns):
                item = QTableWidgetItem(str(row_data.get(col_name, "")))
                self.results_table.setItem(row_idx, col_idx, item)
        
        # Auto-resize columns
        self.results_table.resizeColumnsToContents()
    
    def _populate_issue_list(self, issues: list) -> None:
        """Populate issue list for Jira/GitHub (T134)"""
        self.results_list.clear()
        
        for issue in issues:
            key = issue.get("key", "")
            summary = issue.get("summary", "")
            status = issue.get("status", "")
            assignee = issue.get("assignee", "Unassigned")
            
            # Format: [KEY] Summary - Status (Assignee)
            item_text = f"[{key}] {summary} - {status} ({assignee})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, issue)  # Store full issue data
            
            # Add tooltip with more info (T138)
            tooltip = f"<b>{key}</b><br>"
            tooltip += f"<b>Summary:</b> {summary}<br>"
            tooltip += f"<b>Status:</b> {status}<br>"
            tooltip += f"<b>Assignee:</b> {assignee}"
            item.setToolTip(tooltip)
            
            self.results_list.addItem(item)
    
    def _append_terminal_output(self, text: str) -> None:
        """Append text to terminal output (T135)"""
        # In real implementation, this would handle ANSI color codes
        self.terminal_output.append(text.rstrip())
    
    def _on_table_context_menu(self, position) -> None:
        """Show context menu for table results (T136)"""
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        
        menu = QMenu(self)
        
        insert_action = QAction("Insert Reference at Cursor", self)
        insert_action.triggered.connect(lambda: self._insert_reference_from_table())
        menu.addAction(insert_action)
        
        copy_action = QAction("Copy Cell", self)
        copy_action.triggered.connect(self._copy_table_cell)
        menu.addAction(copy_action)
        
        menu.exec(self.results_table.viewport().mapToGlobal(position))
    
    def _on_list_context_menu(self, position) -> None:
        """Show context menu for issue list (T136)"""
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        
        item = self.results_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        insert_action = QAction("Insert Issue Reference at Cursor", self)
        insert_action.triggered.connect(lambda: self._insert_reference_from_list(item))
        menu.addAction(insert_action)
        
        copy_key_action = QAction("Copy Issue Key", self)
        copy_key_action.triggered.connect(lambda: self._copy_issue_key(item))
        menu.addAction(copy_key_action)
        
        menu.exec(self.results_list.viewport().mapToGlobal(position))
    
    def _insert_reference_from_table(self) -> None:
        """Insert table reference at cursor (T136)"""
        current_item = self.results_table.currentItem()
        if not current_item:
            return
        
        text = current_item.text()
        # TODO: Insert into active editor at cursor position
        # For now, just copy to clipboard
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(text)
        self.status_label.setText(f"<b>Copied to clipboard:</b> {text[:50]}...")
    
    def _insert_reference_from_list(self, item: QListWidgetItem) -> None:
        """Insert issue reference at cursor (T136)"""
        issue_data = item.data(Qt.UserRole)
        key = issue_data.get("key", "")
        
        if key:
            # TODO: Insert into active editor at cursor position
            # For now, just copy to clipboard
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(f"[{key}]")
            self.status_label.setText(f"<b>Copied to clipboard:</b> [{key}]")
    
    def _copy_table_cell(self) -> None:
        """Copy selected table cell to clipboard"""
        current_item = self.results_table.currentItem()
        if current_item:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(current_item.text())
    
    def _copy_issue_key(self, item: QListWidgetItem) -> None:
        """Copy issue key to clipboard"""
        issue_data = item.data(Qt.UserRole)
        key = issue_data.get("key", "")
        if key:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(key)
    
    def _on_export_results(self) -> None:
        """Export results to file (T139)"""
        from PySide6.QtWidgets import QFileDialog, QMenu
        from PySide6.QtGui import QAction
        
        menu = QMenu(self)
        
        csv_action = QAction("Export as CSV", self)
        csv_action.triggered.connect(lambda: self._export_as_csv())
        menu.addAction(csv_action)
        
        json_action = QAction("Export as JSON", self)
        json_action.triggered.connect(lambda: self._export_as_json())
        menu.addAction(json_action)
        
        md_action = QAction("Export as Markdown Table", self)
        md_action.triggered.connect(lambda: self._export_as_markdown())
        menu.addAction(md_action)
        
        # Show menu at button position
        menu.exec(self.export_button.mapToGlobal(self.export_button.rect().bottomLeft()))
    
    def _export_as_csv(self) -> None:
        """Export table results as CSV"""
        from PySide6.QtWidgets import QFileDialog
        import csv
        
        filename, _ = QFileDialog.getSaveFileName(self, "Export as CSV", "", "CSV Files (*.csv)")
        if not filename:
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write headers
                headers = [self.results_table.horizontalHeaderItem(i).text() 
                          for i in range(self.results_table.columnCount())]
                writer.writerow(headers)
                
                # Write rows
                for row in range(self.results_table.rowCount()):
                    row_data = [self.results_table.item(row, col).text() 
                               for col in range(self.results_table.columnCount())]
                    writer.writerow(row_data)
            
            self.status_label.setText(f"<b style='color: green;'>✓ Exported to CSV:</b><br>{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export CSV: {str(e)}")
    
    def _export_as_json(self) -> None:
        """Export results as JSON"""
        from PySide6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(self, "Export as JSON", "", "JSON Files (*.json)")
        if not filename:
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.json_output.toPlainText())
            
            self.status_label.setText(f"<b style='color: green;'>✓ Exported to JSON:</b><br>{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export JSON: {str(e)}")
    
    def _export_as_markdown(self) -> None:
        """Export table results as Markdown table"""
        from PySide6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(self, "Export as Markdown", "", "Markdown Files (*.md)")
        if not filename:
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # Write header row
                headers = [self.results_table.horizontalHeaderItem(i).text() 
                          for i in range(self.results_table.columnCount())]
                f.write("| " + " | ".join(headers) + " |\n")
                f.write("| " + " | ".join(["---"] * len(headers)) + " |\n")
                
                # Write data rows
                for row in range(self.results_table.rowCount()):
                    row_data = [self.results_table.item(row, col).text() 
                               for col in range(self.results_table.columnCount())]
                    f.write("| " + " | ".join(row_data) + " |\n")
            
            self.status_label.setText(f"<b style='color: green;'>✓ Exported to Markdown:</b><br>{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export Markdown: {str(e)}")