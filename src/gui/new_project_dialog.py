"""New Project Dialog for Speckit Editor"""

from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QFileDialog, QCheckBox,
    QLabel, QMessageBox
)

from ..utils.logging import get_logger

logger = get_logger(__name__)


class NewProjectDialog(QDialog):
    """Dialog for creating a new Speckit project"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Speckit Project")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self.project_name = ""
        self.project_path = Path.home()
        self.initialize_git = True
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout()
        
        # Form layout
        form = QFormLayout()
        
        # Project name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("my-project")
        self.name_edit.textChanged.connect(self._update_full_path)
        form.addRow("Project Name:", self.name_edit)
        
        # Location
        location_layout = QHBoxLayout()
        self.location_edit = QLineEdit()
        self.location_edit.setText(str(Path.home()))
        self.location_edit.setReadOnly(True)
        location_layout.addWidget(self.location_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_location)
        location_layout.addWidget(browse_btn)
        form.addRow("Location:", location_layout)
        
        # Full path display
        self.full_path_label = QLabel()
        self._update_full_path()
        form.addRow("Full Path:", self.full_path_label)
        
        # Git initialization checkbox
        self.git_checkbox = QCheckBox("Initialize Git repository")
        self.git_checkbox.setChecked(True)
        form.addRow("", self.git_checkbox)
        
        layout.addLayout(form)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Create Project")
        create_btn.setDefault(True)
        create_btn.clicked.connect(self._create_project)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Focus project name
        self.name_edit.setFocus()
    
    def _update_full_path(self):
        """Update full path label"""
        name = self.name_edit.text().strip()
        location = Path(self.location_edit.text())
        
        if name:
            full_path = location / name
            self.full_path_label.setText(str(full_path))
        else:
            self.full_path_label.setText("(enter project name)")
    
    def _browse_location(self):
        """Browse for project location"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Project Location",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            self.location_edit.setText(directory)
            self._update_full_path()
    
    def _create_project(self):
        """Validate and create project"""
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(
                self,
                "Invalid Project Name",
                "Please enter a project name."
            )
            return
        
        # Validate project name (basic)
        if any(c in name for c in '<>:"|?*'):
            QMessageBox.warning(
                self,
                "Invalid Project Name",
                "Project name contains invalid characters."
            )
            return
        
        location = Path(self.location_edit.text())
        full_path = location / name
        
        if full_path.exists():
            QMessageBox.warning(
                self,
                "Directory Exists",
                f"Directory already exists:\n{full_path}\n\nPlease choose a different name or location."
            )
            return
        
        # Store values
        self.project_name = name
        self.project_path = location
        self.initialize_git = self.git_checkbox.isChecked()
        
        self.accept()
    
    def get_project_info(self):
        """Get project creation info
        
        Returns:
            tuple: (project_path, project_name, initialize_git)
        """
        return (self.project_path, self.project_name, self.initialize_git)
