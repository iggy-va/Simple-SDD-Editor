#!/usr/bin/env python3
"""Speckit Editor - Main entry point"""

import sys
from PySide6.QtWidgets import QApplication


def main() -> int:
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Speckit Editor")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Speckit")
    
    # TODO: Initialize main window once implemented
    # from src.gui.main_window import MainWindow
    # window = MainWindow()
    # window.show()
    
    print("Speckit Editor - Development Build")
    print("Main window not yet implemented")
    
    return 0  # Exit immediately for now


if __name__ == "__main__":
    sys.exit(main())
