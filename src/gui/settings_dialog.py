"""Settings dialog for application preferences"""

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
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..utils.config import AppSettings, ProjectSettings, KeyboardShortcuts
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SettingsDialog(QDialog):
    """Dialog for managing application and project settings"""
    
    settingsChanged = Signal()  # Emitted when settings are saved
    
    def __init__(self, app_settings: AppSettings, 
                 project_settings: Optional[ProjectSettings] = None,
                 parent=None):
        super().__init__(parent)
        
        self.app_settings = app_settings
        self.project_settings = project_settings
        self.shortcuts = app_settings.get_shortcuts()
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self) -> None:
        """Setup settings dialog UI"""
        self.setWindowTitle("Settings")
        self.setMinimumSize(700, 600)
        
        layout = QVBoxLayout(self)
        
        # Tab widget for different setting categories
        self.tab_widget = QTabWidget()
        
        # Add tabs
        self.tab_widget.addTab(self._create_editor_tab(), "📝 Editor")
        self.tab_widget.addTab(self._create_appearance_tab(), "🎨 Appearance")
        self.tab_widget.addTab(self._create_git_tab(), "🔀 Git")
        self.tab_widget.addTab(self._create_mcp_tab(), "🔌 MCP")
        self.tab_widget.addTab(self._create_ai_tab(), "🤖 AI")
        self.tab_widget.addTab(self._create_shortcuts_tab(), "⌨️ Shortcuts")
        self.tab_widget.addTab(self._create_accessibility_tab(), "♿ Accessibility")
        
        layout.addWidget(self.tab_widget)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self._restore_defaults)
        
        layout.addWidget(button_box)
    
    def _create_editor_tab(self) -> QWidget:
        """Create editor settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Editor behavior group
        behavior_group = QGroupBox("Editor Behavior")
        behavior_layout = QFormLayout()
        
        self.tab_size_spin = QSpinBox()
        self.tab_size_spin.setRange(2, 8)
        self.tab_size_spin.setSuffix(" spaces")
        behavior_layout.addRow("Tab Size:", self.tab_size_spin)
        
        self.line_numbers_check = QCheckBox("Show line numbers")
        behavior_layout.addRow(self.line_numbers_check)
        
        self.word_wrap_check = QCheckBox("Enable word wrap")
        behavior_layout.addRow(self.word_wrap_check)
        
        self.show_whitespace_check = QCheckBox("Show whitespace characters")
        behavior_layout.addRow(self.show_whitespace_check)
        
        self.syntax_highlight_check = QCheckBox("Enable syntax highlighting")
        behavior_layout.addRow(self.syntax_highlight_check)
        
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)
        
        # Auto-save group
        autosave_group = QGroupBox("Auto-Save")
        autosave_layout = QFormLayout()
        
        self.autosave_enabled_check = QCheckBox("Enable auto-save")
        autosave_layout.addRow(self.autosave_enabled_check)
        
        self.autosave_interval_spin = QSpinBox()
        self.autosave_interval_spin.setRange(10, 300)
        self.autosave_interval_spin.setSuffix(" seconds")
        autosave_layout.addRow("Auto-save interval:", self.autosave_interval_spin)
        
        autosave_group.setLayout(autosave_layout)
        layout.addWidget(autosave_group)
        
        layout.addStretch()
        return widget
    
    def _create_appearance_tab(self) -> QWidget:
        """Create appearance settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Theme group
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Default", "Dark", "Light"])
        theme_layout.addRow("Theme:", self.theme_combo)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Font group
        font_group = QGroupBox("Font")
        font_layout = QFormLayout()
        
        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems(["Consolas", "Courier New", "Monaco", "Source Code Pro"])
        font_layout.addRow("Font Family:", self.font_family_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setSuffix(" pt")
        font_layout.addRow("Font Size:", self.font_size_spin)
        
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)
        
        layout.addStretch()
        return widget
    
    def _create_git_tab(self) -> QWidget:
        """Create Git settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        git_group = QGroupBox("Git Preferences")
        git_layout = QFormLayout()
        
        self.git_auto_fetch_check = QCheckBox("Auto-fetch on project open")
        git_layout.addRow(self.git_auto_fetch_check)
        
        self.conventional_commits_check = QCheckBox("Validate conventional commit format")
        git_layout.addRow(self.conventional_commits_check)
        
        self.commit_template_edit = QLineEdit()
        self.commit_template_edit.setPlaceholderText("e.g., feat: ")
        git_layout.addRow("Commit message template:", self.commit_template_edit)
        
        git_group.setLayout(git_layout)
        layout.addWidget(git_group)
        
        layout.addStretch()
        return widget
    
    def _create_mcp_tab(self) -> QWidget:
        """Create MCP settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        mcp_group = QGroupBox("MCP Connection")
        mcp_layout = QFormLayout()
        
        self.mcp_auto_connect_check = QCheckBox("Auto-connect on startup")
        mcp_layout.addRow(self.mcp_auto_connect_check)
        
        self.mcp_timeout_spin = QSpinBox()
        self.mcp_timeout_spin.setRange(5, 60)
        self.mcp_timeout_spin.setSuffix(" seconds")
        mcp_layout.addRow("Connection timeout:", self.mcp_timeout_spin)
        
        mcp_group.setLayout(mcp_layout)
        layout.addWidget(mcp_group)
        
        layout.addStretch()
        return widget
    
    def _create_ai_tab(self) -> QWidget:
        """Create AI settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        ai_group = QGroupBox("AI Assistance")
        ai_layout = QFormLayout()
        
        self.ai_inline_check = QCheckBox("Enable inline AI suggestions")
        ai_layout.addRow(self.ai_inline_check)
        
        self.ai_autocomplete_check = QCheckBox("Enable AI auto-complete")
        ai_layout.addRow(self.ai_autocomplete_check)
        
        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)
        
        layout.addStretch()
        return widget
    
    def _create_shortcuts_tab(self) -> QWidget:
        """Create keyboard shortcuts tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info_label = QLabel("Click on a shortcut to customize it:")
        info_label.setStyleSheet("color: #666; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # File operations
        file_group = QGroupBox("File Operations")
        file_layout = QFormLayout()
        
        self.shortcut_new = QLineEdit()
        file_layout.addRow("New File:", self.shortcut_new)
        
        self.shortcut_open = QLineEdit()
        file_layout.addRow("Open File:", self.shortcut_open)
        
        self.shortcut_save = QLineEdit()
        file_layout.addRow("Save:", self.shortcut_save)
        
        self.shortcut_save_all = QLineEdit()
        file_layout.addRow("Save All:", self.shortcut_save_all)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Git operations
        git_group = QGroupBox("Git Operations")
        git_layout = QFormLayout()
        
        self.shortcut_git_commit = QLineEdit()
        git_layout.addRow("Commit:", self.shortcut_git_commit)
        
        self.shortcut_git_push = QLineEdit()
        git_layout.addRow("Push:", self.shortcut_git_push)
        
        self.shortcut_git_pull = QLineEdit()
        git_layout.addRow("Pull:", self.shortcut_git_pull)
        
        git_group.setLayout(git_layout)
        layout.addWidget(git_group)
        
        # AI operations
        ai_group = QGroupBox("AI Operations")
        ai_layout = QFormLayout()
        
        self.shortcut_ai_chat = QLineEdit()
        ai_layout.addRow("AI Chat:", self.shortcut_ai_chat)
        
        self.shortcut_ai_completion = QLineEdit()
        ai_layout.addRow("AI Completion:", self.shortcut_ai_completion)
        
        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)
        
        layout.addStretch()
        return widget
    
    def _create_accessibility_tab(self) -> QWidget:
        """Create accessibility settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        a11y_group = QGroupBox("Accessibility Features")
        a11y_layout = QFormLayout()
        
        self.keyboard_nav_check = QCheckBox("Enable full keyboard navigation")
        a11y_layout.addRow(self.keyboard_nav_check)
        
        self.focus_indicators_check = QCheckBox("Show visible focus indicators")
        a11y_layout.addRow(self.focus_indicators_check)
        
        self.screen_reader_check = QCheckBox("Screen reader mode")
        self.screen_reader_check.setToolTip("Optimizes UI for screen readers")
        a11y_layout.addRow(self.screen_reader_check)
        
        a11y_group.setLayout(a11y_layout)
        layout.addWidget(a11y_group)
        
        layout.addStretch()
        return widget
    
    def _load_settings(self) -> None:
        """Load current settings into UI"""
        # Editor tab
        if self.project_settings:
            self.tab_size_spin.setValue(self.project_settings.tab_size)
            self.autosave_enabled_check.setChecked(self.project_settings.auto_save_enabled)
            self.autosave_interval_spin.setValue(self.project_settings.auto_save_interval)
            self.syntax_highlight_check.setChecked(self.project_settings.syntax_highlighting_enabled)
        
        # Appearance tab
        self.theme_combo.setCurrentText(self.app_settings.theme.title())
        self.font_family_combo.setCurrentText(self.app_settings.font_family)
        self.font_size_spin.setValue(self.app_settings.font_size)
        self.line_numbers_check.setChecked(self.app_settings.line_numbers)
        self.word_wrap_check.setChecked(self.app_settings.word_wrap)
        self.show_whitespace_check.setChecked(self.app_settings.show_whitespace)
        
        # Git tab
        if self.project_settings:
            self.git_auto_fetch_check.setChecked(self.project_settings.git_auto_fetch)
            self.conventional_commits_check.setChecked(self.project_settings.conventional_commits)
            self.commit_template_edit.setText(self.project_settings.commit_message_template)
        
        # MCP tab
        if self.project_settings:
            self.mcp_auto_connect_check.setChecked(self.project_settings.mcp_auto_connect)
            self.mcp_timeout_spin.setValue(self.project_settings.mcp_connection_timeout)
        
        # AI tab
        if self.project_settings:
            self.ai_inline_check.setChecked(self.project_settings.ai_inline_suggestions)
            self.ai_autocomplete_check.setChecked(self.project_settings.ai_auto_complete)
        
        # Shortcuts tab
        self.shortcut_new.setText(self.shortcuts.new_file)
        self.shortcut_open.setText(self.shortcuts.open_file)
        self.shortcut_save.setText(self.shortcuts.save_file)
        self.shortcut_save_all.setText(self.shortcuts.save_all)
        self.shortcut_git_commit.setText(self.shortcuts.git_commit)
        self.shortcut_git_push.setText(self.shortcuts.git_push)
        self.shortcut_git_pull.setText(self.shortcuts.git_pull)
        self.shortcut_ai_chat.setText(self.shortcuts.ai_chat)
        self.shortcut_ai_completion.setText(self.shortcuts.ai_completion)
        
        # Accessibility tab
        if self.project_settings:
            self.keyboard_nav_check.setChecked(self.project_settings.keyboard_navigation_enabled)
            self.focus_indicators_check.setChecked(self.project_settings.focus_indicators_enabled)
            self.screen_reader_check.setChecked(self.project_settings.screen_reader_mode)
    
    def _save_settings(self) -> None:
        """Save settings from UI to config objects"""
        # Editor tab
        if self.project_settings:
            self.project_settings.tab_size = self.tab_size_spin.value()
            self.project_settings.auto_save_enabled = self.autosave_enabled_check.isChecked()
            self.project_settings.auto_save_interval = self.autosave_interval_spin.value()
            self.project_settings.syntax_highlighting_enabled = self.syntax_highlight_check.isChecked()
        
        # Appearance tab
        self.app_settings.theme = self.theme_combo.currentText().lower()
        self.app_settings.font_family = self.font_family_combo.currentText()
        self.app_settings.font_size = self.font_size_spin.value()
        self.app_settings.line_numbers = self.line_numbers_check.isChecked()
        self.app_settings.word_wrap = self.word_wrap_check.isChecked()
        self.app_settings.show_whitespace = self.show_whitespace_check.isChecked()
        
        # Git tab
        if self.project_settings:
            self.project_settings.git_auto_fetch = self.git_auto_fetch_check.isChecked()
            self.project_settings.conventional_commits = self.conventional_commits_check.isChecked()
            self.project_settings.commit_message_template = self.commit_template_edit.text()
        
        # MCP tab
        if self.project_settings:
            self.project_settings.mcp_auto_connect = self.mcp_auto_connect_check.isChecked()
            self.project_settings.mcp_connection_timeout = self.mcp_timeout_spin.value()
        
        # AI tab
        if self.project_settings:
            self.project_settings.ai_inline_suggestions = self.ai_inline_check.isChecked()
            self.project_settings.ai_auto_complete = self.ai_autocomplete_check.isChecked()
        
        # Shortcuts tab
        self.shortcuts.new_file = self.shortcut_new.text()
        self.shortcuts.open_file = self.shortcut_open.text()
        self.shortcuts.save_file = self.shortcut_save.text()
        self.shortcuts.save_all = self.shortcut_save_all.text()
        self.shortcuts.git_commit = self.shortcut_git_commit.text()
        self.shortcuts.git_push = self.shortcut_git_push.text()
        self.shortcuts.git_pull = self.shortcut_git_pull.text()
        self.shortcuts.ai_chat = self.shortcut_ai_chat.text()
        self.shortcuts.ai_completion = self.shortcut_ai_completion.text()
        
        self.app_settings.update_shortcuts(self.shortcuts)
        
        # Accessibility tab
        if self.project_settings:
            self.project_settings.keyboard_navigation_enabled = self.keyboard_nav_check.isChecked()
            self.project_settings.focus_indicators_enabled = self.focus_indicators_check.isChecked()
            self.project_settings.screen_reader_mode = self.screen_reader_check.isChecked()
    
    def _restore_defaults(self) -> None:
        """Restore all settings to defaults"""
        self.app_settings = AppSettings()
        if self.project_settings:
            self.project_settings.reset_to_defaults()
        self.shortcuts = KeyboardShortcuts()
        self._load_settings()
    
    def accept(self) -> None:
        """Save settings and close dialog"""
        self._save_settings()
        self.settingsChanged.emit()
        super().accept()
