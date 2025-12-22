#!/usr/bin/env python3
"""Speckit Editor - Main entry point"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from src.gui import MainWindow
from src.utils.logging import setup_logging

# Setup logging
setup_logging()


def main() -> int:
    """Main application entry point"""
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("Speckit Editor")
    app.setOrganizationName("Speckit")
    app.setApplicationVersion("0.1.0")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
