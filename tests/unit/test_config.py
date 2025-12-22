"""Tests for config module"""

import pytest
from pathlib import Path
from src.utils.config import ProjectSettings
import json


def test_settings_defaults():
    """Test default settings values"""
    settings = ProjectSettings()
    assert settings.tab_size == 4
    assert settings.auto_save_enabled is True
    assert settings.syntax_highlighting_enabled is True


def test_settings_save_and_load(tmp_path):
    """Test saving and loading settings"""
    settings_path = tmp_path / "settings.json"
    
    settings = ProjectSettings(tab_size=2, auto_save_interval=60)
    settings.save(settings_path)
    
    loaded = ProjectSettings.load(settings_path)
    assert loaded.tab_size == 2
    assert loaded.auto_save_interval == 60


def test_settings_load_nonexistent(tmp_path):
    """Test loading from nonexistent file returns defaults"""
    settings_path = tmp_path / "missing.json"
    settings = ProjectSettings.load(settings_path)
    assert settings.tab_size == 4


def test_settings_load_corrupted(tmp_path):
    """Test loading from corrupted file returns defaults"""
    settings_path = tmp_path / "corrupt.json"
    settings_path.write_text("invalid json{{{")
    
    settings = ProjectSettings.load(settings_path)
    assert settings.tab_size == 4


def test_settings_reset_to_defaults():
    """Test resetting settings to defaults"""
    settings = ProjectSettings(tab_size=8, auto_save_enabled=False)
    settings.reset_to_defaults()
    
    assert settings.tab_size == 4
    assert settings.auto_save_enabled is True


def test_settings_all_preferences():
    """Test all preference fields are accessible"""
    settings = ProjectSettings()
    
    # Editor preferences
    assert isinstance(settings.tab_size, int)
    assert isinstance(settings.auto_save_enabled, bool)
    assert isinstance(settings.auto_save_interval, int)
    assert isinstance(settings.syntax_highlighting_enabled, bool)
    
    # Git preferences
    assert isinstance(settings.git_auto_fetch, bool)
    assert isinstance(settings.commit_message_template, str)
    assert isinstance(settings.conventional_commits, bool)
    
    # MCP preferences
    assert isinstance(settings.mcp_auto_connect, bool)
    assert isinstance(settings.mcp_connection_timeout, int)
    
    # AI preferences
    assert isinstance(settings.ai_inline_suggestions, bool)
    assert isinstance(settings.ai_auto_complete, bool)
    
    # Search preferences
    assert isinstance(settings.search_case_sensitive, bool)
    assert isinstance(settings.search_regex_enabled, bool)
    assert isinstance(settings.search_default_scope, str)
    
    # Accessibility
    assert isinstance(settings.keyboard_navigation_enabled, bool)
    assert isinstance(settings.screen_reader_mode, bool)
    assert isinstance(settings.focus_indicators_enabled, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
