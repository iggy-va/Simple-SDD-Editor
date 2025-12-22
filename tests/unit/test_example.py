"""Sample unit test to verify pytest setup"""

import pytest


def test_sanity() -> None:
    """Sanity check: Python works"""
    assert 1 + 1 == 2


def test_imports() -> None:
    """Verify core dependencies importable"""
    import PySide6
    import pygit2
    import keyring
    import markdown
    
    assert PySide6 is not None
    assert pygit2 is not None
    assert keyring is not None
    assert markdown is not None


@pytest.mark.unit
def test_config_defaults() -> None:
    """Test ProjectSettings default values"""
    from src.utils.config import ProjectSettings
    
    settings = ProjectSettings()
    assert settings.tab_size == 4
    assert settings.auto_save_enabled is True
    assert settings.auto_save_interval == 30
