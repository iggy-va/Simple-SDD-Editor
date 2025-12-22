"""Tests for logging module"""

import pytest
from pathlib import Path
from src.utils.logging import setup_logging, get_logger
import logging


def test_get_logger():
    """Test getting logger instance"""
    logger = get_logger("test_module")
    assert logger is not None
    assert logger.name == "test_module"


def test_setup_logging_default():
    """Test logging setup with defaults"""
    setup_logging()
    logger = get_logger("test")
    assert logger is not None


def test_setup_logging_with_file(tmp_path):
    """Test logging setup with file output"""
    log_file = tmp_path / "test.log"
    setup_logging(log_level="INFO", log_file=log_file)
    
    logger = get_logger("test_file")
    logger.info("Test message")
    
    assert log_file.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
