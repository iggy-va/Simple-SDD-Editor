"""Theme management for Speckit Editor"""

from enum import Enum
from typing import Dict


class Theme(Enum):
    """Available themes"""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class ThemeManager:
    """Manages application themes and stylesheets"""
    
    @staticmethod
    def get_stylesheet(theme: Theme) -> str:
        """Get stylesheet for specified theme
        
        Args:
            theme: Theme to generate stylesheet for
            
        Returns:
            Complete QSS stylesheet string
        """
        if theme == Theme.DARK:
            return ThemeManager._get_dark_theme()
        elif theme == Theme.LIGHT:
            return ThemeManager._get_light_theme()
        else:  # SYSTEM - use light for now
            return ThemeManager._get_light_theme()
    
    @staticmethod
    def _get_light_theme() -> str:
        """Light theme stylesheet (white background, black text)"""
        return """
        /* Base colors */
        QMainWindow, QWidget {
            background-color: #ffffff;
            color: #000000;
        }
        
        /* Text inputs */
        QTextEdit, QPlainTextEdit, QLineEdit {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            selection-background-color: #0078d4;
            selection-color: #ffffff;
        }
        
        /* Tree views and lists */
        QTreeView, QListView {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            alternate-background-color: #f9f9f9;
        }
        
        QTreeView::item:selected, QListView::item:selected {
            background-color: #0078d4;
            color: #ffffff;
        }
        
        QTreeView::item:hover, QListView::item:hover {
            background-color: #e5f3ff;
        }
        
        /* Labels */
        QLabel {
            color: #000000;
            background-color: transparent;
        }
        
        /* Tabs */
        QTabWidget::pane {
            border: 1px solid #cccccc;
            background-color: #ffffff;
        }
        
        QTabBar::tab {
            background-color: #f0f0f0;
            color: #000000;
            border: 1px solid #cccccc;
            border-bottom: none;
            padding: 6px 12px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: #ffffff;
            color: #000000;
            border-bottom: 1px solid #ffffff;
        }
        
        QTabBar::tab:hover {
            background-color: #e0e0e0;
        }
        
        /* Buttons */
        QPushButton {
            background-color: #f0f0f0;
            color: #000000;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 6px 12px;
        }
        
        QPushButton:hover {
            background-color: #e5e5e5;
        }
        
        QPushButton:pressed {
            background-color: #d0d0d0;
        }
        
        QPushButton:disabled {
            background-color: #f5f5f5;
            color: #999999;
        }
        
        /* Menus */
        QMenuBar {
            background-color: #f0f0f0;
            color: #000000;
            border-bottom: 1px solid #cccccc;
        }
        
        QMenuBar::item {
            background-color: transparent;
            color: #000000;
            padding: 4px 8px;
        }
        
        QMenuBar::item:selected {
            background-color: #e0e0e0;
        }
        
        QMenu {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
        }
        
        QMenu::item {
            padding: 4px 20px;
        }
        
        QMenu::item:selected {
            background-color: #0078d4;
            color: #ffffff;
        }
        
        /* Status bar */
        QStatusBar {
            background-color: #f0f0f0;
            color: #000000;
            border-top: 1px solid #cccccc;
        }
        
        /* Dialogs */
        QDialog {
            background-color: #ffffff;
            color: #000000;
        }
        
        QFormLayout QLabel {
            color: #000000;
        }
        
        /* Checkboxes and Radio buttons */
        QCheckBox, QRadioButton {
            color: #000000;
        }
        
        /* Scroll bars */
        QScrollBar:vertical {
            background-color: #f0f0f0;
            width: 12px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #cccccc;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #999999;
        }
        
        /* Focus indicators (accessibility) */
        *:focus {
            outline: 2px solid #0078d4;
            outline-offset: 2px;
        }
        """
    
    @staticmethod
    def _get_dark_theme() -> str:
        """Dark theme stylesheet (dark background, light text)"""
        return """
        /* Base colors */
        QMainWindow, QWidget {
            background-color: #1e1e1e;
            color: #d4d4d4;
        }
        
        /* Text inputs */
        QTextEdit, QPlainTextEdit, QLineEdit {
            background-color: #252526;
            color: #d4d4d4;
            border: 1px solid #3e3e42;
            selection-background-color: #264f78;
            selection-color: #ffffff;
        }
        
        /* Tree views and lists */
        QTreeView, QListView {
            background-color: #252526;
            color: #d4d4d4;
            border: 1px solid #3e3e42;
            alternate-background-color: #2d2d30;
        }
        
        QTreeView::item:selected, QListView::item:selected {
            background-color: #264f78;
            color: #ffffff;
        }
        
        QTreeView::item:hover, QListView::item:hover {
            background-color: #2a2d2e;
        }
        
        /* Labels */
        QLabel {
            color: #d4d4d4;
            background-color: transparent;
        }
        
        /* Tabs */
        QTabWidget::pane {
            border: 1px solid #3e3e42;
            background-color: #1e1e1e;
        }
        
        QTabBar::tab {
            background-color: #2d2d30;
            color: #d4d4d4;
            border: 1px solid #3e3e42;
            border-bottom: none;
            padding: 6px 12px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: #1e1e1e;
            color: #d4d4d4;
            border-bottom: 1px solid #1e1e1e;
        }
        
        QTabBar::tab:hover {
            background-color: #323233;
        }
        
        /* Buttons */
        QPushButton {
            background-color: #333333;
            color: #d4d4d4;
            border: 1px solid #3e3e42;
            border-radius: 4px;
            padding: 6px 12px;
        }
        
        QPushButton:hover {
            background-color: #3e3e42;
        }
        
        QPushButton:pressed {
            background-color: #4e4e52;
        }
        
        QPushButton:disabled {
            background-color: #2d2d30;
            color: #656565;
        }
        
        /* Menus */
        QMenuBar {
            background-color: #2d2d30;
            color: #d4d4d4;
            border-bottom: 1px solid #3e3e42;
        }
        
        QMenuBar::item {
            background-color: transparent;
            color: #d4d4d4;
            padding: 4px 8px;
        }
        
        QMenuBar::item:selected {
            background-color: #3e3e42;
        }
        
        QMenu {
            background-color: #252526;
            color: #d4d4d4;
            border: 1px solid #3e3e42;
        }
        
        QMenu::item {
            padding: 4px 20px;
        }
        
        QMenu::item:selected {
            background-color: #264f78;
            color: #ffffff;
        }
        
        /* Status bar */
        QStatusBar {
            background-color: #2d2d30;
            color: #d4d4d4;
            border-top: 1px solid #3e3e42;
        }
        
        /* Dialogs */
        QDialog {
            background-color: #1e1e1e;
            color: #d4d4d4;
        }
        
        QFormLayout QLabel {
            color: #d4d4d4;
        }
        
        /* Checkboxes and Radio buttons */
        QCheckBox, QRadioButton {
            color: #d4d4d4;
        }
        
        /* Scroll bars */
        QScrollBar:vertical {
            background-color: #1e1e1e;
            width: 12px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #424242;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #4e4e4e;
        }
        
        /* Focus indicators (accessibility) */
        *:focus {
            outline: 2px solid #0078d4;
            outline-offset: 2px;
        }
        """
