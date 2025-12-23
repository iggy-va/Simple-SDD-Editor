"""Git panel for source control operations"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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

from ..core.project import FileStatus
from ..utils.logging import get_logger

logger = get_logger(__name__)


class GitPanel(QWidget):
    """Panel for git operations"""
    
    # Signals
    fileSelected = Signal(str)  # file path
    commitRequested = Signal(str)  # commit message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Accessibility
        self.setAccessibleName("Git Panel")
        self.setAccessibleDescription("Panel for version control operations including staging, committing, and viewing diffs")
        
        self.project = None
        self._setup_ui()
        
        logger.debug("GitPanel initialized")
    
    def _setup_ui(self) -> None:
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main splitter (file list | diff viewer)
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side: File status list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Branch selector
        branch_layout = QHBoxLayout()
        branch_label = QLabel("Branch:")
        branch_layout.addWidget(branch_label)
        
        self.branch_combo = QComboBox()
        self.branch_combo.setAccessibleName("Git Branch")
        self.branch_combo.setAccessibleDescription("Select current git branch")
        self.branch_combo.currentTextChanged.connect(self._on_branch_changed)
        branch_layout.addWidget(self.branch_combo)
        
        self.new_branch_button = QPushButton("New...")
        self.new_branch_button.setAccessibleName("New Branch")
        self.new_branch_button.setAccessibleDescription("Create a new git branch")
        self.new_branch_button.clicked.connect(self._on_new_branch)
        branch_layout.addWidget(self.new_branch_button)
        
        left_layout.addLayout(branch_layout)
        
        # Status label
        self.status_label = QLabel("No changes")
        self.status_label.setStyleSheet("font-weight: bold; padding: 5px;")
        self.status_label.setAccessibleName("Git Status")
        left_layout.addWidget(self.status_label)
        
        # File list
        self.file_list = QListWidget()
        self.file_list.setAccessibleName("Changed Files")
        self.file_list.setAccessibleDescription("List of files with uncommitted changes")
        self.file_list.itemSelectionChanged.connect(self._on_file_selected)
        left_layout.addWidget(self.file_list)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.stage_button = QPushButton("Stage")
        self.stage_button.setAccessibleDescription("Stage selected files for commit")
        self.stage_button.clicked.connect(self._on_stage)
        self.stage_button.setEnabled(False)
        button_layout.addWidget(self.stage_button)
        
        self.unstage_button = QPushButton("Unstage")
        self.unstage_button.clicked.connect(self._on_unstage)
        self.unstage_button.setEnabled(False)
        button_layout.addWidget(self.unstage_button)
        
        button_layout.addStretch()
        left_layout.addLayout(button_layout)
        
        # Commit section
        commit_label = QLabel("Commit Message:")
        left_layout.addWidget(commit_label)
        
        self.commit_message = QTextEdit()
        self.commit_message.setPlaceholderText("Enter commit message...")
        self.commit_message.setMaximumHeight(80)
        left_layout.addWidget(self.commit_message)
        
        commit_btn_layout = QHBoxLayout()
        
        self.commit_button = QPushButton("Commit")
        self.commit_button.clicked.connect(self._on_commit)
        self.commit_button.setEnabled(False)
        commit_btn_layout.addWidget(self.commit_button)
        
        self.push_button = QPushButton("Push")
        self.push_button.clicked.connect(self._on_push)
        commit_btn_layout.addWidget(self.push_button)
        
        self.pull_button = QPushButton("Pull")
        self.pull_button.clicked.connect(self._on_pull)
        commit_btn_layout.addWidget(self.pull_button)
        
        commit_btn_layout.addStretch()
        left_layout.addLayout(commit_btn_layout)
        
        splitter.addWidget(left_widget)
        
        # Right side: Diff viewer
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        diff_label = QLabel("Diff View")
        diff_label.setStyleSheet("font-weight: bold; padding: 5px;")
        right_layout.addWidget(diff_label)
        
        self.diff_viewer = QTextEdit()
        self.diff_viewer.setReadOnly(True)
        self.diff_viewer.setFont(QFont("Courier New", 9))
        right_layout.addWidget(self.diff_viewer)
        
        splitter.addWidget(right_widget)
        
        # Set splitter sizes (40% file list, 60% diff)
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)
    
    def set_project(self, project) -> None:
        """Set the project to display git status for"""
        self.project = project
        self._refresh_branches()
        self._refresh_status()
    
    def _refresh_status(self) -> None:
        """Refresh git status display"""
        self.file_list.clear()
        self.diff_viewer.clear()
        
        if not self.project:
            self.status_label.setText("No project open")
            return
        
        git_status = self.project.get_git_status()
        if not git_status:
            self.status_label.setText("Not a git repository")
            return
        
        # Update status label
        if git_status.has_changes:
            change_count = len(git_status.files)
            self.status_label.setText(f"{change_count} change(s)")
        else:
            self.status_label.setText("Working tree clean")
        
        # Update file list
        for file_status in git_status.files:
            item = QListWidgetItem(file_status.path)
            
            # Set color based on status
            if file_status.status == FileStatus.ADDED:
                item.setForeground(QColor("green"))
            elif file_status.status == FileStatus.MODIFIED:
                item.setForeground(QColor("orange"))
            elif file_status.status == FileStatus.DELETED:
                item.setForeground(QColor("red"))
            elif file_status.status == FileStatus.CONFLICTED:
                item.setForeground(QColor("purple"))
            
            # Add staging indicator
            if file_status.staged:
                item.setText(f"✓ {file_status.path}")
            
            # Store full status in item data
            item.setData(Qt.UserRole, file_status)
            self.file_list.addItem(item)
        
        logger.debug(f"Refreshed git status: {change_count if git_status.has_changes else 0} changes")
    
    def _on_file_selected(self) -> None:
        """Handle file selection"""
        selected = self.file_list.selectedItems()
        
        if selected:
            file_status = selected[0].data(Qt.UserRole)
            self.stage_button.setEnabled(True)
            self.unstage_button.setEnabled(True)
            
            # Show diff for selected file
            if self.project:
                diff_text = self.project.get_file_diff(file_status.path)
                if diff_text:
                    self.diff_viewer.setPlainText(diff_text)
                else:
                    self.diff_viewer.setPlainText("No diff available")
            
            self.fileSelected.emit(file_status.path)
        else:
            self.stage_button.setEnabled(False)
            self.unstage_button.setEnabled(False)
            self.diff_viewer.clear()
            self.unstage_button.setEnabled(False)
            self.diff_viewer.clear()
    
    def _on_stage(self) -> None:
        """Handle stage file"""
        selected = self.file_list.selectedItems()
        if selected and self.project:
            file_status = selected[0].data(Qt.UserRole)
            if self.project.stage_file(file_status.path):
                logger.info(f"Staged file: {file_status.path}")
                self._refresh_status()
            else:
                QMessageBox.warning(
                    self,
                    "Stage Failed",
                    f"Failed to stage {file_status.path}"
                )
    
    def _on_unstage(self) -> None:
        """Handle unstage file"""
        selected = self.file_list.selectedItems()
        if selected and self.project:
            file_status = selected[0].data(Qt.UserRole)
            if self.project.unstage_file(file_status.path):
                logger.info(f"Unstaged file: {file_status.path}")
                self._refresh_status()
            else:
                QMessageBox.warning(
                    self,
                    "Unstage Failed",
                    f"Failed to unstage {file_status.path}"
                )
    
    def _on_commit(self) -> None:
        """Handle commit"""
        message = self.commit_message.toPlainText().strip()
        
        if not message:
            QMessageBox.warning(
                self,
                "Invalid Commit",
                "Please enter a commit message"
            )
            return
        
        # Emit signal for main window to handle
        self.commitRequested.emit(message)
        self.commit_message.clear()
        self._refresh_status()
    
    def _on_push(self) -> None:
        """Handle push"""
        if not self.project:
            QMessageBox.warning(
                self,
                "No Project",
                "No project loaded"
            )
            return
        
        # TODO: Could add remote selection dialog here
        success, message = self.project.push()
        
        if success:
            logger.info(f"Push successful: {message}")
            QMessageBox.information(
                self,
                "Push Successful",
                message
            )
            self._refresh_status()
        else:
            logger.error(f"Push failed: {message}")
            QMessageBox.warning(
                self,
                "Push Failed",
                message
            )
    
    def _on_pull(self) -> None:
        """Handle pull"""
        if not self.project:
            QMessageBox.warning(
                self,
                "No Project",
                "No project loaded"
            )
            return
        
        # TODO: Could add remote selection dialog here
        success, message = self.project.pull()
        
        if success:
            logger.info(f"Pull successful: {message}")
            QMessageBox.information(
                self,
                "Pull Successful",
                message
            )
            self._refresh_status()
        else:
            logger.error(f"Pull failed: {message}")
            
            # Special handling for merge conflicts
            if "conflict" in message.lower():
                QMessageBox.warning(
                    self,
                    "Merge Conflicts",
                    f"{message}\n\nPlease resolve conflicts manually and commit the result."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Pull Failed",
                    message
                )
    
    def _on_branch_changed(self, branch_name: str) -> None:
        """Handle branch change"""
        if not branch_name or not self.project:
            return
        
        # Don't checkout if already on this branch
        if branch_name == self.project.current_branch:
            return
        
        if self.project.checkout_branch(branch_name):
            logger.info(f"Switched to branch: {branch_name}")
            self._refresh_status()
        else:
            logger.error(f"Failed to checkout branch: {branch_name}")
            # Revert combo box to current branch
            self._refresh_branches()
    
    def _on_new_branch(self) -> None:
        """Handle new branch creation"""
        if not self.project:
            return
        
        # Prompt for branch name
        branch_name, ok = QInputDialog.getText(
            self,
            "Create New Branch",
            "Branch name:",
            text="feature/"
        )
        
        if ok and branch_name:
            # Validate branch name
            if not branch_name.strip():
                logger.warning("Branch name cannot be empty")
                return
            
            if self.project.create_branch(branch_name.strip(), checkout=True):
                logger.info(f"Created and checked out branch: {branch_name}")
                self._refresh_branches()
                self._refresh_status()
            else:
                logger.error(f"Failed to create branch: {branch_name}")
    
    def _refresh_branches(self) -> None:
        """Refresh branch list"""
        if not self.project:
            self.branch_combo.clear()
            return
        
        branches = self.project.get_branches()
        current_branch = self.project.current_branch
        
        # Update combo box
        self.branch_combo.blockSignals(True)  # Prevent triggering change event
        self.branch_combo.clear()
        self.branch_combo.addItems(branches)
        
        # Select current branch
        if current_branch:
            index = self.branch_combo.findText(current_branch)
            if index >= 0:
                self.branch_combo.setCurrentIndex(index)
        
        self.branch_combo.blockSignals(False)
