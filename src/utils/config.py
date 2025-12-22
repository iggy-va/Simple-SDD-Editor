"""Configuration management for Speckit Editor"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class ProjectSettings:
    """Project-specific configuration"""
    
    # Editor preferences
    tab_size: int = 4
    auto_save_enabled: bool = True
    auto_save_interval: int = 30  # seconds (10-300 range)
    syntax_highlighting_enabled: bool = True
    
    # Git preferences
    git_auto_fetch: bool = False
    commit_message_template: str = ""
    conventional_commits: bool = True
    
    # MCP preferences
    mcp_auto_connect: bool = False
    mcp_connection_timeout: int = 10  # seconds
    
    # AI preferences
    ai_inline_suggestions: bool = True
    ai_auto_complete: bool = False
    
    # Search preferences
    search_case_sensitive: bool = False
    search_regex_enabled: bool = False
    search_default_scope: str = "current"  # current | open | all
    
    # Accessibility
    keyboard_navigation_enabled: bool = True
    screen_reader_mode: bool = False
    focus_indicators_enabled: bool = True
    
    @classmethod
    def load(cls, settings_path: Path) -> "ProjectSettings":
        """Load settings from JSON file or create defaults"""
        if settings_path.exists():
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**data)
            except (json.JSONDecodeError, TypeError):
                # Return defaults if file is corrupted
                return cls()
        return cls()
    
    def save(self, settings_path: Path) -> None:
        """Save settings to JSON file"""
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to default values"""
        defaults = ProjectSettings()
        for key, value in asdict(defaults).items():
            setattr(self, key, value)
