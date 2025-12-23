"""Template management widget for viewing, editing, and versioning templates"""

from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..core.template import Template, TemplateManager
from ..utils.logging import get_logger

logger = get_logger(__name__)


class TemplateManagerWidget(QDialog):
    """Dialog for managing templates - view, edit, create, version"""
    
    templateCreated = Signal(str)  # Emitted when new template created
    templateModified = Signal(str)  # Emitted when template modified
    
    def __init__(self, templates_dir: Path, parent=None):
        super().__init__(parent)
        
        self.templates_dir = templates_dir
        self.template_manager = TemplateManager(templates_dir)
        self.current_template: Optional[Template] = None
        self.is_modified = False
        
        self._setup_ui()
        self._load_templates()
    
    def _setup_ui(self) -> None:
        """Setup template manager UI"""
        self.setWindowTitle("Template Manager")
        self.setMinimumSize(900, 600)
        
        layout = QVBoxLayout(self)
        
        # Title and description
        title = QLabel("📄 Template Manager")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        subtitle = QLabel("View, edit, and manage document templates")
        subtitle.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(subtitle)
        
        # Main splitter (template list | editor)
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Template list with controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Template list label
        list_label = QLabel("Available Templates:")
        left_layout.addWidget(list_label)
        
        # Template list widget
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self._on_template_selected)
        left_layout.addWidget(self.template_list)
        
        # Template controls
        controls_layout = QHBoxLayout()
        
        self.new_button = QPushButton("New Template")
        self.new_button.clicked.connect(self._on_new_template)
        controls_layout.addWidget(self.new_button)
        
        self.copy_button = QPushButton("Copy")
        self.copy_button.setEnabled(False)
        self.copy_button.clicked.connect(self._on_copy_template)
        controls_layout.addWidget(self.copy_button)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self._on_delete_template)
        controls_layout.addWidget(self.delete_button)
        
        left_layout.addLayout(controls_layout)
        
        # Version history section
        version_label = QLabel("Version History:")
        left_layout.addWidget(version_label)
        
        self.version_list = QListWidget()
        self.version_list.setMaximumHeight(150)
        self.version_list.currentItemChanged.connect(self._on_version_selected)
        left_layout.addWidget(self.version_list)
        
        splitter.addWidget(left_panel)
        
        # Right panel: Template editor
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Template info
        self.template_info = QLabel("Select a template to view or edit")
        self.template_info.setStyleSheet("font-style: italic; color: #666; margin-bottom: 5px;")
        right_layout.addWidget(self.template_info)
        
        # Template editor
        self.template_editor = QTextEdit()
        self.template_editor.setPlaceholderText("Template content will appear here...")
        self.template_editor.textChanged.connect(self._on_editor_changed)
        right_layout.addWidget(self.template_editor)
        
        # Editor controls
        editor_controls = QHBoxLayout()
        
        self.save_button = QPushButton("Save Changes")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self._on_save_template)
        editor_controls.addWidget(self.save_button)
        
        self.save_version_button = QPushButton("Save as New Version")
        self.save_version_button.setEnabled(False)
        self.save_version_button.clicked.connect(self._on_save_version)
        editor_controls.addWidget(self.save_version_button)
        
        self.view_variables_button = QPushButton("View Variables")
        self.view_variables_button.setEnabled(False)
        self.view_variables_button.clicked.connect(self._on_view_variables)
        editor_controls.addWidget(self.view_variables_button)
        
        self.revert_button = QPushButton("Revert Changes")
        self.revert_button.setEnabled(False)
        self.revert_button.clicked.connect(self._on_revert_changes)
        editor_controls.addWidget(self.revert_button)
        
        editor_controls.addStretch()
        right_layout.addLayout(editor_controls)
        
        splitter.addWidget(right_panel)
        
        # Set splitter proportions (1:2 ratio)
        splitter.setSizes([300, 600])
        layout.addWidget(splitter)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.close)
        layout.addWidget(button_box)
    
    def _load_templates(self) -> None:
        """Load templates into list widget"""
        self.template_list.clear()
        
        # Group templates by type
        grouped = self.template_manager.list_templates_by_type()
        
        if not grouped:
            item = QListWidgetItem("No templates found")
            item.setFlags(Qt.ItemIsEnabled)  # Not selectable
            self.template_list.addItem(item)
            return
        
        # Add templates grouped by type
        for type_name in sorted(grouped.keys()):
            templates = grouped[type_name]
            
            # Add type header
            header = QListWidgetItem(f"── {type_name.upper()} ──")
            header.setFlags(Qt.ItemIsEnabled)  # Not selectable
            header.setBackground(Qt.lightGray)
            self.template_list.addItem(header)
            
            # Add templates of this type
            for template in templates:
                item = QListWidgetItem(f"  {template.name}")
                item.setData(Qt.UserRole, template.name)
                self.template_list.addItem(item)
    
    def _on_template_selected(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        """Handle template selection from list"""
        if not current or not current.data(Qt.UserRole):
            return
        
        # Check for unsaved changes
        if self.is_modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Discard them?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                # Revert selection
                if previous:
                    self.template_list.setCurrentItem(previous)
                return
        
        template_name = current.data(Qt.UserRole)
        self._load_template(template_name)
    
    def _load_template(self, template_name: str) -> None:
        """Load template into editor"""
        try:
            template = self.template_manager.get_template(template_name, force_reload=True)
            if not template:
                logger.error(f"Template not found: {template_name}")
                return
            
            self.current_template = template
            self.is_modified = False
            
            # Update editor
            self.template_editor.blockSignals(True)  # Prevent triggering textChanged
            self.template_editor.setPlainText(template.content)
            self.template_editor.blockSignals(False)
            
            # Update info label
            info = f"{template.name}"
            if template.description:
                info += f" - {template.description}"
            if template.updated_at:
                info += f" (Modified: {template.updated_at.strftime('%Y-%m-%d %H:%M')})"
            self.template_info.setText(info)
            
            # Enable buttons
            self.copy_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            self.save_version_button.setEnabled(True)
            self.view_variables_button.setEnabled(True)
            self.save_button.setEnabled(False)
            self.revert_button.setEnabled(False)
            
            # Load version history
            self._load_versions(template_name)
            
        except Exception as e:
            logger.error(f"Failed to load template: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load template: {e}")
    
    def _load_versions(self, base_name: str) -> None:
        """Load version history for template"""
        self.version_list.clear()
        
        # Get base name without version suffix
        if "-v" in base_name:
            base_name = base_name.split("-v")[0]
        
        versions = self.template_manager.get_template_versions(base_name)
        
        if not versions:
            return
        
        for template in versions:
            version_text = template.name
            if template.updated_at:
                version_text += f" ({template.updated_at.strftime('%Y-%m-%d %H:%M')})"
            
            item = QListWidgetItem(version_text)
            item.setData(Qt.UserRole, template.name)
            self.version_list.addItem(item)
    
    def _on_version_selected(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        """Handle version selection from history"""
        if not current:
            return
        
        template_name = current.data(Qt.UserRole)
        self._load_template(template_name)
    
    def _on_editor_changed(self) -> None:
        """Handle editor content changes"""
        if not self.current_template:
            return
        
        self.is_modified = True
        self.save_button.setEnabled(True)
        self.revert_button.setEnabled(True)
    
    def _on_save_template(self) -> None:
        """Save changes to current template"""
        if not self.current_template:
            return
        
        try:
            # Update template content
            new_content = self.template_editor.toPlainText()
            self.current_template.content = new_content
            
            # Save to file
            self.current_template.save(self.current_template.path)
            
            self.is_modified = False
            self.save_button.setEnabled(False)
            self.revert_button.setEnabled(False)
            
            self.templateModified.emit(self.current_template.name)
            
            QMessageBox.information(
                self,
                "Saved",
                f"Template '{self.current_template.name}' saved successfully."
            )
            
        except Exception as e:
            logger.error(f"Failed to save template: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save template: {e}")
    
    def _on_save_version(self) -> None:
        """Save current template as new version"""
        if not self.current_template:
            return
        
        try:
            # Get base name
            base_name = self.current_template.name
            if "-v" in base_name:
                base_name = base_name.split("-v")[0]
            
            # Save as new version
            new_content = self.template_editor.toPlainText()
            new_template = self.template_manager.save_template_version(
                base_name,
                new_content,
                self.current_template.description
            )
            
            # Reload template list and select new version
            self._load_templates()
            self.is_modified = False
            
            self.templateCreated.emit(new_template.name)
            
            QMessageBox.information(
                self,
                "Version Created",
                f"New version '{new_template.name}' created successfully."
            )
            
            # Select the new version
            for i in range(self.template_list.count()):
                item = self.template_list.item(i)
                if item.data(Qt.UserRole) == new_template.name:
                    self.template_list.setCurrentItem(item)
                    break
            
        except Exception as e:
            logger.error(f"Failed to create version: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create version: {e}")
    
    def _on_revert_changes(self) -> None:
        """Revert editor to saved template content"""
        if not self.current_template:
            return
        
        reply = QMessageBox.question(
            self,
            "Revert Changes",
            "Are you sure you want to discard all unsaved changes?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._load_template(self.current_template.name)
    
    def _on_new_template(self) -> None:
        """Create new template"""
        name, ok = QInputDialog.getText(
            self,
            "New Template",
            "Template name (e.g., 'my-template'):",
        )
        
        if not ok or not name:
            return
        
        # Validate name
        if not name.replace("-", "").replace("_", "").isalnum():
            QMessageBox.warning(
                self,
                "Invalid Name",
                "Template name must contain only letters, numbers, hyphens, and underscores."
            )
            return
        
        try:
            # Create blank template
            template = self.template_manager.create_template(
                name=name,
                content="# New Template\n\nTemplate content goes here...\n",
                description="Custom template"
            )
            
            # Reload list and select new template
            self._load_templates()
            
            self.templateCreated.emit(template.name)
            
            # Select the new template
            for i in range(self.template_list.count()):
                item = self.template_list.item(i)
                if item.data(Qt.UserRole) == template.name:
                    self.template_list.setCurrentItem(item)
                    break
            
        except FileExistsError:
            QMessageBox.warning(
                self,
                "Template Exists",
                f"A template named '{name}' already exists."
            )
        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create template: {e}")
    
    def _on_copy_template(self) -> None:
        """Copy current template with new name"""
        if not self.current_template:
            return
        
        name, ok = QInputDialog.getText(
            self,
            "Copy Template",
            f"New name for copy of '{self.current_template.name}':",
        )
        
        if not ok or not name:
            return
        
        try:
            template = self.template_manager.copy_template(
                self.current_template.name,
                name
            )
            
            # Reload list and select new template
            self._load_templates()
            
            self.templateCreated.emit(template.name)
            
            # Select the copied template
            for i in range(self.template_list.count()):
                item = self.template_list.item(i)
                if item.data(Qt.UserRole) == template.name:
                    self.template_list.setCurrentItem(item)
                    break
            
        except Exception as e:
            logger.error(f"Failed to copy template: {e}")
            QMessageBox.critical(self, "Error", f"Failed to copy template: {e}")
    
    def _on_delete_template(self) -> None:
        """Delete current template"""
        if not self.current_template:
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Template",
            f"Are you sure you want to delete '{self.current_template.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        try:
            # Delete template file
            self.current_template.path.unlink()
            
            # Remove from manager cache
            if self.current_template.name in self.template_manager.templates:
                del self.template_manager.templates[self.current_template.name]
            if self.current_template.name in self.template_manager._cache:
                del self.template_manager._cache[self.current_template.name]
            
            # Clear editor
            self.current_template = None
            self.is_modified = False
            self.template_editor.clear()
            self.template_info.setText("Select a template to view or edit")
            
            # Reload list
            self._load_templates()
            
            QMessageBox.information(self, "Deleted", "Template deleted successfully.")
            
        except Exception as e:
            logger.error(f"Failed to delete template: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete template: {e}")
    
    def _on_view_variables(self) -> None:
        """Display template variables in a dialog"""
        if not self.current_template:
            return
        
        # Reload template to get fresh variable extraction
        template = self.template_manager.get_template(self.current_template.name, force_reload=True)
        if not template:
            return
        
        if not template.variables:
            QMessageBox.information(
                self,
                "Template Variables",
                f"No variables found in '{template.name}'.\n\n"
                "Variables should be in format: {{variable_name}} or [VARIABLE_NAME]"
            )
            return
        
        # Build variables display
        var_text = f"Variables in '{template.name}':\n\n"
        
        for var in template.variables:
            var_text += f"• {var.name}\n"
            var_text += f"  Description: {var.description}\n"
            if var.default:
                var_text += f"  Default: {var.default}\n"
            if var.pattern:
                var_text += f"  Pattern: {var.pattern}\n"
            var_text += f"  Required: {'Yes' if var.required else 'No'}\n\n"
        
        var_text += "\nNote: Variables are automatically extracted from template content.\n"
        var_text += "Format: {{variable_name}} or [VARIABLE_NAME]"
        
        # Show in message box
        msg = QMessageBox(self)
        msg.setWindowTitle("Template Variables")
        msg.setText(var_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec()
    
    def closeEvent(self, event) -> None:
        """Handle dialog close with unsaved changes check"""
        if self.is_modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Discard them?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        event.accept()
