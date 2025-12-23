"""AI assistance panel for document generation"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..core.document import AISession
from ..core.validator import ValidationResult
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AIPanel(QWidget):
    """Panel for AI-assisted document generation"""
    
    # Signals
    promptSent = Signal(str)  # User sent a prompt
    suggestionAccepted = Signal(str, int)  # Suggestion text and position
    suggestionRejected = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Accessibility
        self.setAccessibleName("AI Assistant Panel")
        self.setAccessibleDescription("Panel for interacting with AI to get suggestions and generate content")
        
        self.session: Optional[AISession] = None
        self.mcp_server = None
        
        self._setup_ui()
        logger.debug("AIPanel initialized")
    
    def _setup_ui(self) -> None:
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        title_label = QLabel("🤖 AI Assistant")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(title_label)
        
        # Status label
        self.status_label = QLabel("Not connected")
        self.status_label.setStyleSheet("color: #666; padding: 2px 5px;")
        self.status_label.setAccessibleName("AI Status")
        layout.addWidget(self.status_label)
        
        # Chat history
        history_label = QLabel("Conversation:")
        layout.addWidget(history_label)
        
        self.chat_history = QListWidget()
        self.chat_history.setAlternatingRowColors(True)
        self.chat_history.setAccessibleName("Chat History")
        self.chat_history.setAccessibleDescription("Conversation history with AI assistant")
        layout.addWidget(self.chat_history)
        
        # Prompt input
        prompt_label = QLabel("Ask AI:")
        layout.addWidget(prompt_label)
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Enter your question or request...")
        self.prompt_input.setMaximumHeight(100)
        self.prompt_input.setAccessibleName("AI Prompt Input")
        self.prompt_input.setAccessibleDescription("Enter your question or request for the AI assistant")
        layout.addWidget(self.prompt_input)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.send_button = QPushButton("Send")
        self.send_button.setAccessibleDescription("Send prompt to AI assistant")
        self.send_button.clicked.connect(self._on_send)
        self.send_button.setEnabled(False)
        button_layout.addWidget(self.send_button)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.setAccessibleDescription("Clear conversation history")
        self.clear_button.clicked.connect(self._on_clear)
        button_layout.addWidget(self.clear_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def set_mcp_server(self, mcp_server) -> None:
        """Set the MCP server for AI requests"""
        self.mcp_server = mcp_server
        self._update_status()
    
    def start_session(self, document_path: Optional[Path] = None,
                     context_type: str = "chat",
                     cursor_position: Optional[int] = None,
                     selected_text: Optional[str] = None) -> None:
        """Start a new AI session"""
        self.session = AISession(
            document_path=document_path,
            context_type=context_type,
            cursor_position=cursor_position,
            selected_text=selected_text
        )
        self.chat_history.clear()
        self._update_status()
        logger.info(f"Started AI session: {self.session.session_id}")
    
    def add_user_message(self, content: str) -> None:
        """Add a user message to the chat"""
        if not self.session:
            self.start_session()
        
        self.session.add_message("user", content)
        self._add_chat_item(f"You: {content}", user=True)
    
    def add_ai_message(self, content: str, 
                      suggestion_text: Optional[str] = None,
                      suggestion_position: Optional[int] = None) -> None:
        """Add an AI response to the chat"""
        if not self.session:
            return
        
        message = self.session.add_message(
            "assistant", 
            content,
            suggestion_text=suggestion_text,
            suggestion_position=suggestion_position
        )
        
        display_text = f"AI: {content}"
        if suggestion_text:
            display_text += f"\n\n[Suggestion available]"
        
        self._add_chat_item(display_text, user=False)
    
    def _add_chat_item(self, text: str, user: bool = True) -> None:
        """Add an item to the chat history"""
        item = QListWidgetItem(text)
        
        if user:
            item.setForeground(Qt.blue)
        else:
            item.setForeground(Qt.darkGreen)
        
        self.chat_history.addItem(item)
        self.chat_history.scrollToBottom()
    
    def _update_status(self) -> None:
        """Update the status label with graceful degradation messaging"""
        if not self.mcp_server:
            self.status_label.setText("⚠️ AI service not available - editor remains fully functional")
            self.status_label.setStyleSheet("color: #FF8C00; padding: 2px 5px;")
            self.send_button.setEnabled(False)
            self.send_button.setToolTip("AI service not configured. The editor works fine without AI assistance.")
        elif not self.session:
            self.status_label.setText("💬 Ready - AI assistance available")
            self.status_label.setStyleSheet("color: #666; padding: 2px 5px;")
            self.send_button.setEnabled(True)
            self.send_button.setToolTip("Send message to AI assistant")
        else:
            msg_count = len(self.session.messages)
            self.status_label.setText(f"✓ Active session - {msg_count} messages")
            self.status_label.setStyleSheet("color: #28a745; padding: 2px 5px;")
            self.send_button.setEnabled(True)
            self.send_button.setToolTip("Send message to AI assistant")
    
    def _on_send(self) -> None:
        """Handle send button click with graceful error handling"""
        prompt = self.prompt_input.toPlainText().strip()
        
        if not prompt:
            return
        
        # Check if MCP server is available
        if not self.mcp_server:
            self.add_ai_message(
                "⚠️ AI service is not available.\n\n"
                "The Speckit Editor works perfectly without AI assistance. "
                "You can continue editing, validating, and managing your documents normally.\n\n"
                "AI features will be available when an MCP AI service is configured."
            )
            return
        
        # Add to chat
        self.add_user_message(prompt)
        
        # Clear input
        self.prompt_input.clear()
        
        # Emit signal for processing
        self.promptSent.emit(prompt)
        
        # For now, add a placeholder response
        # TODO: Connect to actual MCP AI service
        try:
            self.add_ai_message(
                "AI response will be implemented when connected to MCP AI service.\n\n"
                "In the meantime, all editor features are fully functional."
            )
        except Exception as e:
            logger.error(f"AI request failed: {e}")
            self.add_ai_message(
                f"⚠️ AI request failed: {str(e)}\n\n"
                "Don't worry - you can continue working without AI assistance."
            )
    
    def _on_clear(self) -> None:
        """Handle clear button click"""
        self.chat_history.clear()
        self.prompt_input.clear()
        if self.session:
            self.session = None
            self._update_status()
    
    def display_validation_errors(self, validation_result: ValidationResult) -> None:
        """
        Display validation errors for AI-generated content
        
        Args:
            validation_result: Result from validating AI-generated content
        """
        if validation_result.is_valid and not validation_result.warnings:
            # Content is valid
            self._add_validation_item(
                "✅ AI content validated successfully",
                is_error=False
            )
            return
        
        # Add validation header
        error_count = len(validation_result.errors)
        warning_count = len(validation_result.warnings)
        
        if error_count > 0:
            header = f"⚠️ Found {error_count} error(s)"
            if warning_count > 0:
                header += f" and {warning_count} warning(s)"
            self._add_validation_item(header, is_error=True)
        elif warning_count > 0:
            self._add_validation_item(
                f"⚠️ Found {warning_count} warning(s)",
                is_error=False
            )
        
        # Display errors
        for error in validation_result.errors:
            error_text = f"ERROR: {error.message}"
            if error.suggestion:
                error_text += f"\n  → {error.suggestion}"
            self._add_validation_item(error_text, is_error=True)
        
        # Display warnings
        for warning in validation_result.warnings:
            warning_text = f"WARNING: {warning.message}"
            if warning.suggestion:
                warning_text += f"\n  → {warning.suggestion}"
            self._add_validation_item(warning_text, is_error=False)
        
        logger.info(f"Displayed validation results: {error_count} errors, {warning_count} warnings")
    
    def _add_validation_item(self, text: str, is_error: bool = True) -> None:
        """Add a validation message to the chat history"""
        item = QListWidgetItem(text)
        
        if is_error:
            item.setForeground(QColor("#d32f2f"))  # Red for errors
        else:
            item.setForeground(QColor("#f57c00"))  # Orange for warnings
        
        # Use a smaller font for validation messages
        font = item.font()
        font.setPointSize(9)
        item.setFont(font)
        
        self.chat_history.addItem(item)
        self.chat_history.scrollToBottom()
