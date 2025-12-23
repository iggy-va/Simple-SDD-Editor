"""Configuration management for Speckit Editor"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict, field


@dataclass
class KeyboardShortcuts:
    """Customizable keyboard shortcuts"""
    
    # File operations
    new_file: str = "Ctrl+N"
    open_file: str = "Ctrl+O"
    save_file: str = "Ctrl+S"
    save_all: str = "Ctrl+Shift+S"
    close_tab: str = "Ctrl+W"
    
    # Git operations
    git_commit: str = "Ctrl+K"
    git_push: str = "Ctrl+Shift+P"
    git_pull: str = "Ctrl+Shift+L"
    git_diff: str = "Ctrl+D"
    
    # AI operations
    ai_chat: str = "Ctrl+Shift+A"
    ai_completion: str = "Ctrl+Space"
    
    # Navigation
    next_tab: str = "Ctrl+Tab"
    prev_tab: str = "Ctrl+Shift+Tab"
    go_to_line: str = "Ctrl+G"
    find: str = "Ctrl+F"
    find_replace: str = "Ctrl+H"
    
    # Editor
    undo: str = "Ctrl+Z"
    redo: str = "Ctrl+Y"
    comment_toggle: str = "Ctrl+/"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "KeyboardShortcuts":
        """Create from dictionary"""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class AppSettings:
    """Application-wide settings (not project-specific)"""
    
    # Window settings
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False
    
    # Theme
    theme: str = "default"  # default | dark | light
    font_family: str = "Consolas"
    font_size: int = 11
    
    # Editor
    line_numbers: bool = True
    word_wrap: bool = False
    show_whitespace: bool = False
    
    # Behavior
    confirm_exit: bool = True
    restore_session: bool = True
    check_updates: bool = True
    
    # Performance
    max_file_size_mb: int = 10
    lazy_loading_threshold: int = 1000  # files
    
    # Keyboard shortcuts
    shortcuts: Dict[str, str] = field(default_factory=lambda: asdict(KeyboardShortcuts()))
    
    @classmethod
    def load(cls, settings_path: Path) -> "AppSettings":
        """Load settings from JSON file or create defaults"""
        if settings_path.exists():
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**data)
            except (json.JSONDecodeError, TypeError) as e:
                # Return defaults if file is corrupted
                return cls()
        return cls()
    
    def save(self, settings_path: Path) -> None:
        """Save settings to JSON file"""
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)
    
    def get_shortcuts(self) -> KeyboardShortcuts:
        """Get keyboard shortcuts object"""
        return KeyboardShortcuts.from_dict(self.shortcuts)
    
    def update_shortcuts(self, shortcuts: KeyboardShortcuts) -> None:
        """Update keyboard shortcuts"""
        self.shortcuts = shortcuts.to_dict()


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


class CrashRecovery:
    """Manage crash recovery cache for unsaved documents"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize crash recovery
        
        Args:
            cache_dir: Directory for crash recovery cache. Defaults to ~/.speckit/recovery
        """
        self.cache_dir = cache_dir or (Path.home() / ".speckit" / "recovery")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def save_unsaved_document(self, document_path: Path, content: str) -> None:
        """Save unsaved document content to recovery cache
        
        Args:
            document_path: Original path of the document
            content: Current content of the document
        """
        # Create cache file name from document path hash
        import hashlib
        path_hash = hashlib.md5(str(document_path.absolute()).encode()).hexdigest()
        cache_file = self.cache_dir / f"{path_hash}.recovery"
        
        # Save document info and content
        recovery_data = {
            "original_path": str(document_path.absolute()),
            "timestamp": str(Path.home()),  # Will be updated with actual timestamp
            "content": content
        }
        
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(recovery_data, f, indent=2)
        except Exception as e:
            # Don't fail if recovery save fails
            import logging
            logging.getLogger(__name__).warning(f"Failed to save recovery cache: {e}")
    
    def get_recoverable_documents(self) -> Dict[str, Dict[str, Any]]:
        """Get list of documents that can be recovered
        
        Returns:
            Dictionary mapping original paths to recovery data
        """
        recoverable = {}
        
        for cache_file in self.cache_dir.glob("*.recovery"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    original_path = data.get("original_path")
                    if original_path:
                        recoverable[original_path] = {
                            "cache_file": cache_file,
                            "content": data.get("content", ""),
                            "timestamp": data.get("timestamp")
                        }
            except Exception:
                # Skip corrupted recovery files
                continue
        
        return recoverable
    
    def recover_document(self, original_path: str) -> Optional[str]:
        """Recover document content from cache
        
        Args:
            original_path: Original path of the document
            
        Returns:
            Recovered content or None if not found
        """
        import hashlib
        path_hash = hashlib.md5(original_path.encode()).hexdigest()
        cache_file = self.cache_dir / f"{path_hash}.recovery"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("content")
        except Exception:
            return None
    
    def clear_recovery(self, original_path: str) -> None:
        """Clear recovery cache for a document
        
        Args:
            original_path: Original path of the document
        """
        import hashlib
        path_hash = hashlib.md5(original_path.encode()).hexdigest()
        cache_file = self.cache_dir / f"{path_hash}.recovery"
        
        if cache_file.exists():
            try:
                cache_file.unlink()
            except Exception:
                pass
    
    def clear_all(self) -> None:
        """Clear all recovery cache files"""
        for cache_file in self.cache_dir.glob("*.recovery"):
            try:
                cache_file.unlink()
            except Exception:
                pass
