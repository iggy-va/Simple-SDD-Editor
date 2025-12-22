"""Document editor widget with syntax highlighting"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
)
from PySide6.QtWidgets import QTextEdit

from ..core import SpeckitDocument
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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.document_path = None
        self.speckit_document = None
        
        # Setup editor
        self._setup_editor()
        
        # Install syntax highlighter
        self.highlighter = MarkdownHighlighter(self.document())
        
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
    
    def _on_text_changed(self) -> None:
        """Handle text changes"""
        self.contentModified.emit()
        
        # Request validation after 500ms pause (implemented later)
        # For now, just emit signal
        # QTimer.singleShot(500, self.validationRequested.emit)
