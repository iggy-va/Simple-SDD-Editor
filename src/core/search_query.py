"""Search query and result classes (stubs for tests)"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SearchQuery:
    """Search query parameters"""
    text: str
    case_sensitive: bool = False
    whole_word: bool = False
    regex: bool = False


@dataclass
class SearchResult:
    """Search result"""
    document_path: Path
    line_number: int
    column: int
    matched_text: str
    context_before: str = ""
    context_after: str = ""
