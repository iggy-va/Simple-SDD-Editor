"""Template selection and variable input dialog"""

from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
)

from ..core.template import Template, TemplateManager
from ..utils.logging import get_logger

logger = get_logger(__name__)


class TemplateDialog(QDialog):
    """Dialog for selecting a template and providing variable values"""
    
    def __init__(self, templates_dir: Path, parent=None):
        super().__init__(parent)
        
        self.templates_dir = templates_dir
        self.template_manager = TemplateManager(templates_dir)
        self.selected_template: Optional[Template] = None
        self.variable_values: Dict[str, str] = {}
        
        self._setup_ui()
        self._load_templates()
    
    def _setup_ui(self) -> None:
        """Setup dialog UI"""
        self.setWindowTitle("New Document from Template")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Template selection
        template_label = QLabel("Select Template:")
        self.template_combo = QComboBox()
        self.template_combo.currentTextChanged.connect(self._on_template_changed)
        
        layout.addWidget(template_label)
        layout.addWidget(self.template_combo)
        
        # Template description
        self.description_label = QLabel("")
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.description_label)
        
        # Variable input form
        self.form_layout = QFormLayout()
        layout.addLayout(self.form_layout)
        
        # Preview (read-only)
        preview_label = QLabel("Preview:")
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        self.preview_text.setPlaceholderText("Select a template to see preview...")
        
        layout.addWidget(preview_label)
        layout.addWidget(self.preview_text)
        
        # Dialog buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        layout.addWidget(self.button_box)
    
    def _load_templates(self) -> None:
        """Load available templates into combo box"""
        templates = self.template_manager.list_templates()
        
        if not templates:
            logger.warning("No templates found")
            self.template_combo.addItem("No templates available")
            self.template_combo.setEnabled(False)
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
            return
        
        for template_name in templates:
            self.template_combo.addItem(template_name)
    
    def _on_template_changed(self, template_name: str) -> None:
        """Handle template selection change"""
        if not template_name or template_name == "No templates available":
            return
        
        try:
            # Load template
            self.selected_template = self.template_manager.get_template(template_name)
            
            # Update description
            if self.selected_template.description:
                self.description_label.setText(self.selected_template.description)
            else:
                self.description_label.setText("")
            
            # Clear existing form inputs
            self._clear_form()
            
            # Create input fields for variables
            self.variable_inputs = {}
            for variable in self.selected_template.variables:
                # Create input field
                line_edit = QLineEdit()
                line_edit.setPlaceholderText(variable.description)
                
                # Set default value
                if variable.default:
                    line_edit.setText(variable.default)
                
                # Mark required fields
                label_text = variable.description
                if variable.required:
                    label_text += " *"
                
                # Add to form
                self.form_layout.addRow(label_text, line_edit)
                self.variable_inputs[variable.name] = line_edit
                
                # Connect to preview update
                line_edit.textChanged.connect(self._update_preview)
            
            # Initial preview
            self._update_preview()
            
        except Exception as e:
            logger.error(f"Failed to load template: {e}")
            self.description_label.setText(f"Error loading template: {e}")
    
    def _clear_form(self) -> None:
        """Clear form layout"""
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def _update_preview(self) -> None:
        """Update preview with current variable values"""
        if not self.selected_template:
            return
        
        try:
            # Collect current values
            values = {}
            for var_name, input_widget in self.variable_inputs.items():
                values[var_name] = input_widget.text()
            
            # Try to instantiate template
            preview = self.selected_template.instantiate(values)
            
            # Show first 20 lines of preview
            preview_lines = preview.split("\n")[:20]
            preview_text = "\n".join(preview_lines)
            if len(preview.split("\n")) > 20:
                preview_text += "\n\n... (preview truncated)"
            
            self.preview_text.setPlainText(preview_text)
            
        except Exception as e:
            # Show error in preview
            self.preview_text.setPlainText(f"Preview unavailable: {str(e)}")
    
    def get_result(self) -> tuple[Optional[Template], Dict[str, str]]:
        """Get selected template and variable values"""
        if not self.selected_template:
            return None, {}
        
        # Collect final values
        values = {}
        for var_name, input_widget in self.variable_inputs.items():
            values[var_name] = input_widget.text()
        
        self.variable_values = values
        return self.selected_template, values
