"""Document editor widget with syntax highlighting"""

from typing import Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QKeyEvent,
    QPalette,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
)
from PySide6.QtWidgets import QCompleter, QLabel, QTextEdit

from ..core import SpeckitDocument
from ..core.validator import DocumentValidator, ValidationResult
from ..utils.logging import get_logger

logger = get_logger(__name__)


class MarkdownHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Markdown with Speckit extensions"""
    
    def __init__(self, parent: QTextDocument):
        super().__init__(parent)
        
        # Define text formats for different syntax elements
        self.formats = self._create_formats()
        
        # Define highlighting rules (pattern, format)
        self.highlighting_rules = self._create_rules()
    
    def _create_formats(self) -> dict:
        """Create QTextCharFormat objects for syntax elements"""
        formats = {}
        
        # Headers (# ## ###)
        header1_format = QTextCharFormat()
        header1_format.setForeground(QColor("#2B579A"))
        header1_format.setFontWeight(QFont.Bold)
        header1_format.setFontPointSize(18)
        formats["header1"] = header1_format
        
        header2_format = QTextCharFormat()
        header2_format.setForeground(QColor("#2B579A"))
        header2_format.setFontWeight(QFont.Bold)
        header2_format.setFontPointSize(16)
        formats["header2"] = header2_format
        
        header3_format = QTextCharFormat()
        header3_format.setForeground(QColor("#2B579A"))
        header3_format.setFontWeight(QFont.Bold)
        header3_format.setFontPointSize(14)
        formats["header3"] = header3_format
        
        header4_format = QTextCharFormat()
        header4_format.setForeground(QColor("#2B579A"))
        header4_format.setFontWeight(QFont.Bold)
        formats["header4"] = header4_format
        
        # Requirements (FR-001, SC-002, CHK-003, TSK-004)
        requirement_format = QTextCharFormat()
        requirement_format.setForeground(QColor("#0E7490"))
        requirement_format.setFontWeight(QFont.Bold)
        formats["requirement"] = requirement_format
        
        # Priority markers (P1, P2, P3, P4)
        priority_format = QTextCharFormat()
        priority_format.setForeground(QColor("#DC2626"))
        priority_format.setFontWeight(QFont.Bold)
        formats["priority"] = priority_format
        
        # BDD keywords (Given, When, Then, And, But)
        bdd_format = QTextCharFormat()
        bdd_format.setForeground(QColor("#7C3AED"))
        bdd_format.setFontWeight(QFont.Bold)
        formats["bdd"] = bdd_format
        
        # Code blocks (```code```)
        code_block_format = QTextCharFormat()
        code_block_format.setForeground(QColor("#059669"))
        code_block_format.setFontFamily("Courier New")
        code_block_format.setBackground(QColor("#F3F4F6"))
        formats["code_block"] = code_block_format
        
        # Inline code (`code`)
        inline_code_format = QTextCharFormat()
        inline_code_format.setForeground(QColor("#059669"))
        inline_code_format.setFontFamily("Courier New")
        inline_code_format.setBackground(QColor("#F3F4F6"))
        formats["inline_code"] = inline_code_format
        
        # Bold (**text**)
        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Bold)
        formats["bold"] = bold_format
        
        # Italic (*text* or _text_)
        italic_format = QTextCharFormat()
        italic_format.setFontItalic(True)
        formats["italic"] = italic_format
        
        # Links ([text](url))
        link_format = QTextCharFormat()
        link_format.setForeground(QColor("#2563EB"))
        link_format.setFontUnderline(True)
        formats["link"] = link_format
        
        # Lists (- item or 1. item)
        list_format = QTextCharFormat()
        list_format.setForeground(QColor("#6B7280"))
        formats["list"] = list_format
        
        # Issue references ([PROJ-123], [GH-456], etc.) - T137
        issue_format = QTextCharFormat()
        issue_format.setForeground(QColor("#0891B2"))  # Cyan-600
        issue_format.setFontWeight(QFont.Bold)
        issue_format.setFontUnderline(True)
        formats["issue"] = issue_format
        
        return formats
    
    def _create_rules(self) -> list:
        """Create highlighting rules (pattern, format_name)"""
        import re
        
        rules = []
        
        # Headers
        rules.append((re.compile(r"^# .+"), "header1"))
        rules.append((re.compile(r"^## .+"), "header2"))
        rules.append((re.compile(r"^### .+"), "header3"))
        rules.append((re.compile(r"^#### .+"), "header4"))
        
        # Requirements (FR-001, SC-002, CHK-003, TSK-004)
        rules.append((re.compile(r"\*\*(FR|SC|CHK|TSK)-\d{3}\*\*"), "requirement"))
        
        # Priority markers (P1, P2, P3, P4)
        rules.append((re.compile(r"\b(P[1-4])\b"), "priority"))
        
        # Issue references - T137
        # Matches patterns like [PROJ-123], [GH-456], [JIRA-789], etc.
        rules.append((re.compile(r"\[([A-Z][A-Z0-9]+-\d+)\]"), "issue"))
        
        # BDD keywords
        rules.append((re.compile(r"\b(Given|When|Then|And|But)\b"), "bdd"))
        
        # Inline code (`code`)
        rules.append((re.compile(r"`[^`]+`"), "inline_code"))
        
        # Bold (**text**)
        rules.append((re.compile(r"\*\*[^*]+\*\*"), "bold"))
        
        # Italic (*text* or _text_)
        rules.append((re.compile(r"(?<!\*)\*(?!\*)([^*]+)\*(?!\*)"), "italic"))
        rules.append((re.compile(r"_([^_]+)_"), "italic"))
        
        # Links ([text](url))
        rules.append((re.compile(r"\[([^\]]+)\]\(([^)]+)\)"), "link"))
        
        # Lists
        rules.append((re.compile(r"^[\s]*[-*+] "), "list"))
        rules.append((re.compile(r"^[\s]*\d+\. "), "list"))
        
        return rules
    
    def highlightBlock(self, text: str) -> None:
        """Apply syntax highlighting to a block of text"""
        # Apply all highlighting rules
        for pattern, format_name in self.highlighting_rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, self.formats[format_name])


class SpeckitEditorWidget(QTextEdit):
    """Custom text editor for Speckit documents"""
    
    # Signals
    contentModified = Signal()  # Emitted when content changes
    validationRequested = Signal()  # Emitted when validation should run
    validationComplete = Signal(object)  # Emitted with ValidationResult
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.document_path = None
        self.speckit_document = None
        self.validation_result: ValidationResult = None
        self.saved_scroll_position = 0
        self.saved_cursor_position = 0
        
        # AI suggestion state
        self.ai_suggestion: Optional[str] = None
        self.ai_suggestion_position: Optional[int] = None
        self.suggestion_overlay: Optional[QLabel] = None
        
        # Setup editor
        self._setup_editor()
        
        # Install syntax highlighter
        self.highlighter = MarkdownHighlighter(self.document())
        
        # Setup auto-completion
        self._setup_autocomplete()
        
        # Validation timer (1000ms delay after typing stops - optimized for performance)
        self.validation_timer = QTimer(self)
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self._run_validation)
        
        # Connect signals
        self.textChanged.connect(self._on_text_changed)
        
        logger.debug("SpeckitEditorWidget initialized")
    
    def _setup_editor(self) -> None:
        """Configure editor appearance and behavior"""
        # Font
        font = QFont("Consolas", 11)
        self.setFont(font)
        
        # Tab width (4 spaces)
        self.setTabStopDistance(40)  # 4 * 10 pixels per character
        
        # Line wrap
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        
        # Accept rich text (for syntax highlighting)
        self.setAcceptRichText(False)
        
        # Placeholder text
        self.setPlaceholderText("Start typing your specification...")
    
    def _setup_autocomplete(self) -> None:
        """Setup auto-completion for section headings, IDs, keywords, variables"""
        # Completion items
        completions = [
            # Section headings
            "## Clarifications",
            "## User Scenarios & Testing",
            "## Requirements",
            "### Functional Requirements",
            "### Non-Functional Requirements",
            "## Success Criteria",
            "## Testing & Code Quality",
            "## Edge Cases",
            "## Technical Constraints",
            
            # Requirement IDs
            "FR-001", "FR-002", "FR-003", "FR-004", "FR-005",
            "SC-001", "SC-002", "SC-003", "SC-004", "SC-005",
            "NFR-001", "NFR-002", "NFR-003",
            
            # BDD Keywords
            "**Given**", "**When**", "**Then**", "**And**", "**But**",
            
            # Priority markers
            "Priority: P1", "Priority: P2", "Priority: P3", "Priority: P4",
            
            # Template variables
            "[FEATURE_NAME]", "[FEATURE_ID]", "[DATE]", "[AUTHOR]", "[BRANCH]",
            "[TASK_NAME]", "[TASK_ID]", "[TASK_IMPLEMENTER]", 
            "[FEATURE_IMPLEMENTER]", "[DONE_DATE]",
        ]
        
        self.completer = QCompleter(completions, self)
        self.completer.setWidget(self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated.connect(self._insert_completion)
    
    def _insert_completion(self, completion: str) -> None:
        """Insert selected completion at cursor"""
        cursor = self.textCursor()
        
        # Find the word being completed
        cursor.movePosition(cursor.StartOfWord, cursor.KeepAnchor)
        cursor.removeSelectedText()
        
        # Insert completion
        cursor.insertText(completion)
        self.setTextCursor(cursor)
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key presses including Ctrl+Space for auto-completion"""
        # Trigger auto-completion on Ctrl+Space
        if event.key() == Qt.Key_Space and event.modifiers() == Qt.ControlModifier:
            # Show completer
            cursor = self.textCursor()
            cursor.select(cursor.WordUnderCursor)
            prefix = cursor.selectedText()
            
            self.completer.setCompletionPrefix(prefix)
            popup = self.completer.popup()
            popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
            
            # Position popup at cursor
            rect = self.cursorRect()
            rect.setWidth(self.completer.popup().sizeHintForColumn(0)
                         + self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(rect)
            return
        
        # Let completer handle its events
        if self.completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab):
                event.ignore()
                return
        
        # Default handling
        super().keyPressEvent(event)
    
    def load_document(self, document: SpeckitDocument) -> None:
        """Load a SpeckitDocument into the editor"""
        logger.info(f"Loading document: {document.path}")
        
        self.speckit_document = document
        self.document_path = document.path
        
        # Block signals while loading to avoid dirty flag
        self.blockSignals(True)
        self.setPlainText(document.content)
        self.blockSignals(False)
        
        # Reset dirty flag
        self.document().setModified(False)
    
    def get_content(self) -> str:
        """Get current editor content"""
        return self.toPlainText()
    
    def is_modified(self) -> bool:
        """Check if document has unsaved changes"""
        return self.document().isModified()
    
    def save_scroll_position(self) -> None:
        """Save current scroll position and cursor location"""
        self.saved_scroll_position = self.verticalScrollBar().value()
        cursor = self.textCursor()
        self.saved_cursor_position = cursor.position()
        logger.debug(f"Saved position: scroll={self.saved_scroll_position}, cursor={self.saved_cursor_position}")
    
    def restore_scroll_position(self) -> None:
        """Restore saved scroll position and cursor location"""
        self.verticalScrollBar().setValue(self.saved_scroll_position)
        cursor = self.textCursor()
        cursor.setPosition(self.saved_cursor_position)
        self.setTextCursor(cursor)
        logger.debug(f"Restored position: scroll={self.saved_scroll_position}, cursor={self.saved_cursor_position}")
    
    def _on_text_changed(self) -> None:
        """Handle text changes (optimized for typing performance)"""
        self.contentModified.emit()
        
        # Restart validation timer (1000ms delay - optimized to reduce typing lag)
        self.validation_timer.stop()
        self.validation_timer.start(1000)
    
    def _run_validation(self) -> None:
        """Run validation on current document content"""
        if not self.speckit_document:
            return
        
        try:
            # Update document content
            self.speckit_document.content = self.get_content()
            
            # Re-parse document
            self.speckit_document.parse()
            
            # Validate
            validator = DocumentValidator()
            result = validator.validate(self.speckit_document)
            
            # Emit result
            self.validationComplete.emit(result)
            
            logger.debug(f"Validation complete: {len(result.errors)} errors, {len(result.warnings)} warnings")
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
    
    def display_validation_results(self, result: ValidationResult) -> None:
        """Display validation errors and warnings with visual indicators"""
        self.validation_result = result
        
        # Clear previous error formatting by rehighlighting
        if self.highlighter:
            self.highlighter.rehighlight()
        
        # Add squiggly underlines for errors (red) and warnings (yellow)
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.Start)
        
        # Error format (red squiggly underline)
        error_format = QTextCharFormat()
        error_format.setUnderlineColor(QColor("#DC2626"))
        error_format.setUnderlineStyle(QTextCharFormat.WaveUnderline)
        
        # Warning format (yellow squiggly underline)
        warning_format = QTextCharFormat()
        warning_format.setUnderlineColor(QColor("#F59E0B"))
        warning_format.setUnderlineStyle(QTextCharFormat.WaveUnderline)
        
        # Apply error underlines
        for error in result.errors:
            if error.line_number:
                # Move to line (line numbers are 1-based)
                cursor.movePosition(QTextCursor.Start)
                for _ in range(error.line_number - 1):
                    cursor.movePosition(QTextCursor.Down)
                
                # Select the line
                cursor.select(QTextCursor.LineUnderCursor)
                cursor.mergeCharFormat(error_format)
        
        # Apply warning underlines
        for warning in result.warnings:
            if warning.line_number:
                cursor.movePosition(QTextCursor.Start)
                for _ in range(warning.line_number - 1):
                    cursor.movePosition(QTextCursor.Down)
                
                cursor.select(QTextCursor.LineUnderCursor)
                cursor.mergeCharFormat(warning_format)
    
    def show_ai_suggestion(self, suggestion_text: str, position: Optional[int] = None) -> None:
        """Display an inline AI suggestion at the cursor or specified position"""
        if not suggestion_text:
            return
        
        # Store suggestion
        if position is None:
            position = self.textCursor().position()
        
        self.ai_suggestion = suggestion_text
        self.ai_suggestion_position = position
        
        # Create or update overlay label
        if not self.suggestion_overlay:
            self.suggestion_overlay = QLabel(self)
            self.suggestion_overlay.setStyleSheet("""
                QLabel {
                    background-color: #E0F2FE;
                    color: #0369A1;
                    border: 1px solid #7DD3FC;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-family: Consolas;
                    font-size: 11px;
                }
            """)
            self.suggestion_overlay.setWordWrap(True)
        
        # Set suggestion text with hint
        display_text = f"💡 AI Suggestion:\n{suggestion_text}\n\n(Tab to accept, Esc to reject)"
        self.suggestion_overlay.setText(display_text)
        self.suggestion_overlay.adjustSize()
        
        # Position overlay near cursor
        cursor_rect = self.cursorRect()
        overlay_x = cursor_rect.x() + 10
        overlay_y = cursor_rect.y() + cursor_rect.height()
        
        # Keep within editor bounds
        max_width = min(400, self.width() - 20)
        self.suggestion_overlay.setMaximumWidth(max_width)
        self.suggestion_overlay.adjustSize()
        
        if overlay_x + self.suggestion_overlay.width() > self.width():
            overlay_x = self.width() - self.suggestion_overlay.width() - 10
        
        if overlay_y + self.suggestion_overlay.height() > self.height():
            overlay_y = cursor_rect.y() - self.suggestion_overlay.height() - 5
        
        self.suggestion_overlay.move(overlay_x, overlay_y)
        self.suggestion_overlay.show()
        self.suggestion_overlay.raise_()
        
        logger.info(f"AI suggestion displayed at position {position}")
    
    def accept_ai_suggestion(self) -> bool:
        """Accept and insert the current AI suggestion"""
        if not self.ai_suggestion or self.ai_suggestion_position is None:
            return False
        
        # Insert suggestion at saved position
        cursor = self.textCursor()
        cursor.setPosition(self.ai_suggestion_position)
        cursor.insertText(self.ai_suggestion)
        
        # Clear suggestion
        self.clear_ai_suggestion()
        
        logger.info("AI suggestion accepted")
        return True
    
    def reject_ai_suggestion(self) -> bool:
        """Reject and clear the current AI suggestion"""
        if not self.ai_suggestion:
            return False
        
        self.clear_ai_suggestion()
        logger.info("AI suggestion rejected")
        return True
    
    def clear_ai_suggestion(self) -> None:
        """Clear the current AI suggestion"""
        self.ai_suggestion = None
        self.ai_suggestion_position = None
        
        if self.suggestion_overlay:
            self.suggestion_overlay.hide()
    
    def extract_ai_context(self, context_type: str = "completion") -> dict:
        """Extract intelligent context for AI prompts
        
        Args:
            context_type: "completion", "chat", or "generation"
            
        Returns:
            Dictionary with context information
        """
        cursor = self.textCursor()
        full_text = self.toPlainText()
        cursor_position = cursor.position()
        
        # Extract document type from path
        document_type = "unknown"
        if self.document_path:
            name_lower = self.document_path.stem.lower()
            if "spec" in name_lower:
                document_type = "specification"
            elif "plan" in name_lower:
                document_type = "plan"
            elif "task" in name_lower:
                document_type = "tasks"
            elif "checklist" in name_lower:
                document_type = "checklist"
        
        # Get current line and surrounding context
        cursor.select(QTextCursor.LineUnderCursor)
        current_line = cursor.selectedText()
        
        # Get current section (find nearest header above cursor)
        lines_before = full_text[:cursor_position].split("\n")
        current_section = None
        for line in reversed(lines_before):
            if line.strip().startswith("#"):
                current_section = line.strip()
                break
        
        # Get selected text if any
        selected_text = self.textCursor().selectedText()
        
        # Extract context before and after cursor
        context_before_size = 500 if context_type == "completion" else 1000
        context_after_size = 100 if context_type == "completion" else 500
        
        context_start = max(0, cursor_position - context_before_size)
        context_end = min(len(full_text), cursor_position + context_after_size)
        
        context_before = full_text[context_start:cursor_position]
        context_after = full_text[cursor_position:context_end]
        
        # Extract requirements/items near cursor (for spec documents)
        nearby_requirements = []
        if document_type == "specification":
            # Look for FR-XXX, SC-XXX patterns in nearby text
            import re
            nearby_text = full_text[max(0, cursor_position - 1000):min(len(full_text), cursor_position + 1000)]
            req_pattern = r'(FR|SC|NFR)-\d{3}'
            nearby_requirements = re.findall(req_pattern, nearby_text)
        
        # Build context dictionary
        context = {
            "document_type": document_type,
            "document_path": str(self.document_path) if self.document_path else None,
            "cursor_position": cursor_position,
            "current_line": current_line,
            "current_section": current_section,
            "selected_text": selected_text if selected_text else None,
            "context_before": context_before,
            "context_after": context_after,
            "total_lines": len(full_text.split("\n")),
            "total_chars": len(full_text),
            "nearby_requirements": list(set(nearby_requirements)) if nearby_requirements else [],
        }
        
        # Add document-specific context
        if self.speckit_document:
            context["has_frontmatter"] = bool(self.speckit_document.frontmatter)
            if self.speckit_document.sections:
                context["section_count"] = len(self.speckit_document.sections)
                context["section_names"] = [s.title for s in self.speckit_document.sections]
        
        return context
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events, including AI suggestion acceptance/rejection"""
        # Handle AI suggestion controls
        if self.ai_suggestion:
            if event.key() == Qt.Key_Tab and not event.modifiers():
                # Accept suggestion with Tab
                if self.accept_ai_suggestion():
                    event.accept()
                    return
            elif event.key() == Qt.Key_Escape:
                # Reject suggestion with Esc
                if self.reject_ai_suggestion():
                    event.accept()
                    return
        
        # Default handling
        super().keyPressEvent(event)
