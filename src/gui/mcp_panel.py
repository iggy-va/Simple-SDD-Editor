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
