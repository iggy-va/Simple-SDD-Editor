# Developer Guide - Speckit Document Editor/IDE

**Version**: 1.0.0 | **Last Updated**: 2025-12-23

This guide explains the architecture, development setup, coding conventions, and contribution workflow for the Speckit Editor.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Development Setup](#development-setup)
4. [Code Conventions](#code-conventions)
5. [Testing Strategy](#testing-strategy)
6. [Build and Packaging](#build-and-packaging)
7. [Contributing](#contributing)

---

## Architecture Overview

The Speckit Editor uses a **3-layer architecture** to ensure testability, maintainability, and clear separation of concerns:

```text
┌─────────────────────────────────────────┐
│          GUI Layer (PySide6)            │  ← User interactions, Qt widgets
│  MainWindow, Editor, Panels, Dialogs   │
└─────────────┬───────────────────────────┘
              │ (calls)
┌─────────────▼───────────────────────────┐
│        MCP Integration Layer            │  ← External service integrations
│  Server, Services (Jira, GitHub, etc.)  │
└─────────────┬───────────────────────────┘
              │ (calls)
┌─────────────▼───────────────────────────┐
│       Core Business Logic Layer         │  ← Document models, validation
│  Document, Project, Validator, etc.     │
└─────────────────────────────────────────┘
```

### Layer Responsibilities

**Core Layer** (`src/core/`)
- **Purpose**: Pure business logic with zero UI or external dependencies
- **Components**:
  - `document.py`: SpeckitDocument model, parsing, serialization
  - `project.py`: SpeckitProject model, filesystem operations, git metadata
  - `validator.py`: Document validation (structure, IDs, references)
  - `template.py`: Template loading, variable substitution, instantiation
  - `indexer.py`: Full-text search indexing
- **Testing**: Unit tests only, no mocking required
- **Dependencies**: Standard library, dataclasses, regex, markdown

**MCP Layer** (`src/mcp/`)
- **Purpose**: Bridge between core logic and external services
- **Components**:
  - `server.py`: Embedded MCP server lifecycle management
  - `credentials.py`: OS keyring integration for secure credential storage
  - `services/`: Individual service implementations (Jira, GitHub, Git, databases, terminals, Chrome)
- **Testing**: Integration tests with mocked service responses
- **Dependencies**: python-mcp-sdk, keyring, requests, pygit2

**GUI Layer** (`src/gui/`)
- **Purpose**: User interface using PySide6 (Qt bindings)
- **Components**:
  - `main_window.py`: Application window, menu bar, status bar, docks
  - `editor.py`: Document editor with syntax highlighting (QTextEdit + QSyntaxHighlighter)
  - `navigator.py`: File tree navigator (QTreeWidget)
  - `git_panel.py`: Git operations panel (status, commit, branch, push/pull)
  - `mcp_panel.py`: MCP service connections panel
  - `ai_panel.py`: AI assistant panel (Ctrl+Space, Ctrl+Shift+A)
  - `template_dialog.py`: Template selection and variable input dialog
- **Testing**: pytest-qt for widget tests
- **Dependencies**: PySide6 (Qt6), core layer, MCP layer

### Design Principles

1. **Dependency Direction**: Always flows downward (GUI → MCP → Core). Core layer has zero knowledge of GUI or MCP.
2. **Testability**: Each layer independently testable without external dependencies.
3. **Loose Coupling**: Interfaces defined in core layer, implementations in MCP/GUI layers.
4. **Cross-Platform**: Platform-specific code isolated to packaging/build scripts only.

---

## Project Structure

```text
sdd-editor/
├── src/
│   ├── core/              # Business logic (zero external deps)
│   ├── mcp/               # MCP server integration
│   ├── gui/               # PySide6 widgets
│   ├── cli/               # CLI interface (optional)
│   └── utils/             # Shared utilities (config, logging)
│
├── tests/
│   ├── unit/              # Unit tests (core layer)
│   ├── integration/       # Integration tests (MCP + GUI)
│   └── fixtures/          # Test data (sample projects, mocks)
│
├── docs/
│   ├── user-guide.md      # User documentation
│   ├── developer-guide.md # This file
│   └── screenshots/       # Screenshots for README
│
├── .specify/              # Speckit metadata
│   ├── memory/            # Constitution and project context
│   ├── templates/         # Default templates (spec, plan, tasks)
│   └── cache/             # Local cache (MCP responses, AI sessions)
│
├── assets/                # Icons, images, resources
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── pyproject.toml         # Project metadata, tool configs
├── pytest.ini             # Pytest configuration
├── README.md              # Project overview
└── main.py                # Application entry point
```

### Key Files

- **main.py**: Application entry point. Initializes QApplication, loads MainWindow, starts event loop.
- **requirements.txt**: Runtime dependencies (PySide6, pygit2, keyring, markdown, python-mcp-sdk)
- **requirements-dev.txt**: Development dependencies (pytest, pytest-qt, pytest-mock, black, mypy)
- **pyproject.toml**: Build configuration, tool settings (black, mypy, setuptools)
- **pytest.ini**: Test configuration, coverage settings, markers

---

## Development Setup

### Prerequisites

- **Python 3.11+** (required for modern type hints, async/await)
- **Git 2.30+** (for version control and git integration testing)
- **Visual Studio Code** (recommended, with Python extension)

### Initial Setup

```bash
# Clone repository
git clone <repo-url>
cd sdd-editor

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests to verify setup
pytest tests/unit/ -v

# Launch application
python main.py
```

### IDE Configuration (VS Code)

Recommended extensions:
- Python (Microsoft)
- Pylance
- Black Formatter
- Mypy Type Checker
- Pytest IntelliSense

Workspace settings (`.vscode/settings.json`):
```json
{
  "python.linting.enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

### Running the Application

```bash
# Development mode (with verbose logging)
python main.py --debug

# Production mode
python main.py
```

---

## Code Conventions

### Style Guide

- **Formatting**: Black (line length 100)
- **Linting**: Mypy (strict mode)
- **Docstrings**: Google style

Example:
```python
def validate_requirement_id(req_id: str, document_type: str) -> ValidationResult:
    """Validate requirement ID format against document type rules.
    
    Args:
        req_id: Requirement identifier to validate (e.g., "FR-001")
        document_type: Document type ("spec", "plan", "tasks")
        
    Returns:
        ValidationResult with errors, warnings, and suggestions
        
    Raises:
        ValueError: If document_type is not recognized
    """
    if document_type not in ["spec", "plan", "tasks"]:
        raise ValueError(f"Unknown document type: {document_type}")
    
    # Implementation...
    return ValidationResult(errors=[], warnings=[], suggestions=[])
```

### Naming Conventions

- **Classes**: PascalCase (`SpeckitDocument`, `ValidationResult`)
- **Functions/Methods**: snake_case (`load_document`, `validate_structure`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_DOCUMENT_SIZE`, `DEFAULT_TIMEOUT`)
- **Private members**: Leading underscore (`_internal_state`, `_parse_header`)

### Type Hints

All public functions MUST have type hints:

```python
from typing import Optional, List, Dict
from dataclasses import dataclass

@dataclass
class ValidationError:
    line: int
    message: str
    severity: str  # "error" | "warning" | "info"

def validate_document(
    content: str,
    template: Optional[str] = None
) -> List[ValidationError]:
    """Validate document content against template."""
    errors: List[ValidationError] = []
    # Implementation...
    return errors
```

### Error Handling

- **Core layer**: Raise specific exceptions (`DocumentNotFoundError`, `InvalidTemplateError`)
- **MCP layer**: Catch external service errors, return error results (never crash)
- **GUI layer**: Display user-friendly error messages, log technical details

```python
# Core layer
class DocumentNotFoundError(Exception):
    """Raised when document file cannot be found."""
    pass

# MCP layer
def fetch_jira_issues(project_key: str) -> Result[List[JiraIssue], str]:
    try:
        response = requests.get(f"/jira/issues/{project_key}")
        return Ok(response.json())
    except requests.RequestException as e:
        return Err(f"Failed to fetch Jira issues: {e}")

# GUI layer
def on_fetch_clicked(self):
    result = self.mcp_server.fetch_jira_issues("PROJ")
    if result.is_err():
        QMessageBox.warning(self, "Jira Error", result.unwrap_err())
    else:
        self.display_issues(result.unwrap())
```

### File Organization

Each module should have clear sections:

```python
"""Module docstring explaining purpose."""

# Standard library imports
import os
from pathlib import Path
from typing import Optional, List

# Third-party imports
from PySide6.QtWidgets import QWidget
import pygit2

# Local imports
from src.core.document import SpeckitDocument
from src.utils.logging import get_logger

# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Type aliases
DocumentPath = Path

# Module-level logger
logger = get_logger(__name__)

# Classes
class MyClass:
    pass

# Functions
def my_function():
    pass
```

---

## Testing Strategy

### Test Organization

```text
tests/
├── unit/                  # Unit tests (no external deps)
│   ├── test_document.py   # Core document tests
│   ├── test_validator.py  # Validation logic tests
│   └── test_template.py   # Template tests
│
├── integration/           # Integration tests (mocked MCP, real GUI)
│   ├── test_gui.py        # GUI widget tests (pytest-qt)
│   ├── test_mcp.py        # MCP service tests (mocked responses)
│   └── test_git.py        # Git integration tests (real repos)
│
└── fixtures/              # Shared test data
    ├── sample_project/    # Example speckit project
    └── mock_responses/    # JSON responses for MCP mocks
```

### Running Tests

```bash
# All tests
pytest

# Unit tests only (fast)
pytest tests/unit/ -v

# Integration tests (slower)
pytest tests/integration/ -v

# With coverage report
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_validator.py -v

# Specific test function
pytest tests/unit/test_validator.py::test_validate_spec_structure -v
```

### Writing Tests

**Unit Test Example**:
```python
from src.core.validator import Validator, ValidationResult

def test_validate_requirement_id_valid():
    validator = Validator()
    result = validator.validate_requirement_id("FR-001", "spec")
    
    assert result.is_valid()
    assert len(result.errors) == 0

def test_validate_requirement_id_invalid_format():
    validator = Validator()
    result = validator.validate_requirement_id("INVALID", "spec")
    
    assert not result.is_valid()
    assert any("FR-NNN" in e.message for e in result.errors)
```

**Integration Test Example (pytest-qt)**:
```python
from PySide6.QtWidgets import QApplication
from src.gui.editor import SpeckitEditorWidget

def test_syntax_highlighting(qtbot):
    """Test that markdown headers are highlighted correctly."""
    editor = SpeckitEditorWidget()
    qtbot.addWidget(editor)
    
    # Set content with markdown header
    editor.setPlainText("# User Stories\n\nFR-001: Some requirement")
    
    # Get highlighted format at header position
    cursor = editor.textCursor()
    cursor.movePosition(cursor.Start)
    format = cursor.charFormat()
    
    # Verify header formatting applied
    assert format.fontWeight() == QFont.Bold
    assert format.foreground().color().name() == "#0066cc"
```

### Test Coverage Goals

- **Unit tests**: 80%+ coverage for core layer
- **Integration tests**: All user stories validated end-to-end
- **GUI tests**: Critical user workflows (create doc, save, git commit, AI assist)

### Mocking Strategy

- **External services**: Always mock (Jira, GitHub APIs)
- **File system**: Mock for unit tests, real filesystem for integration tests
- **Git operations**: Mock for unit tests, real git repos for integration tests
- **Qt widgets**: Use pytest-qt fixtures, real widgets (no mocking)

---

## Build and Packaging

### Prerequisites

**Required**:
- **Python 3.11 or 3.12** (recommended for stable packaging)
- **Python 3.14**: May work with PyInstaller 6.15.0 (test before production)
- PyInstaller 6.15.0: `pip install pyinstaller==6.15.0`
- Platform-specific tools:
  - Windows: Visual Studio Build Tools (for some dependencies)
  - macOS: Xcode Command Line Tools
  - Linux: Standard build tools (gcc, make)

### Development Builds

```bash
# Run from source (development)
python main.py

# Run with debug logging
python main.py --debug
```

### Production Builds

The project includes a pre-configured PyInstaller spec file (`speckit-editor.spec`) with optimized settings.

**Build using spec file** (recommended):
```bash
python -m PyInstaller speckit-editor.spec
```

This handles:
- Platform-specific executable formats (.exe, .app, binary)
- Template and asset bundling
- Hidden imports for PySide6, sqlite3
- Module exclusions (tkinter, matplotlib, etc.)
- UPX compression for smaller binaries

**Manual PyInstaller commands** (alternative):

**Windows**:
```bash
pyinstaller --name="Speckit Editor" \
            --windowed \
            --onefile \
            --icon=assets/icon.ico \
            --add-data=".specify;.specify" \
            --hidden-import=PySide6.QtCore \
            --hidden-import=PySide6.QtWidgets \
            main.py
```

**macOS**:
```bash
pyinstaller --name="Speckit Editor" \
            --windowed \
            --onefile \
            --icon=assets/icon.icns \
            --add-data=".specify:.specify" \
            --hidden-import=PySide6.QtCore \
            --hidden-import=PySide6.QtWidgets \
            main.py
```

**Linux**:
```bash
pyinstaller --name="speckit-editor" \
            --onefile \
            --add-data=".specify:.specify" \
            --hidden-import=PySide6.QtCore \
            --hidden-import=PySide6.QtWidgets \
            main.py
```

### Size Optimization

**UPX Compression** (enabled in spec file):
- Reduces binary size by 50-70%
- Install UPX: https://upx.github.io/
- PyInstaller auto-detects and uses UPX if available

**Module Exclusions** (already configured):
- Excluded: tkinter, matplotlib, numpy, pandas, IPython, jupyter
- Saves ~100MB in final binary

### Code Signing

**Windows**:
```powershell
# Sign executable with certificate
signtool sign /f certificate.pfx /p password /tr http://timestamp.digicert.com "dist/Speckit Editor.exe"
```

**macOS**:
```bash
# Sign application bundle
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" "dist/Speckit Editor.app"

# Notarize for Gatekeeper
xcrun notarytool submit "Speckit Editor.dmg" --apple-id your@email.com --password app-specific-password --wait
```

**Linux**:
```bash
# GPG signing (optional, recommended for distribution)
gpg --detach-sign --armor dist/speckit-editor
```

### Known Issues

**Python 3.14 Incompatibility**:
- **Issue**: PyInstaller 6.x + Python 3.14 + keyring module causes build failure
- **Error**: `ValueError: Target module 'distutils' already imported as ExcludedModule`
- **Workaround**: Use Python 3.11 or 3.12 for packaging
- **Status**: PyInstaller team aware, fix pending

### Testing Packaged Builds

**Smoke test checklist**:
1. Application launches without errors
2. Main window displays correctly
3. Can create new document
4. Can save and load files
5. Git integration works (commit, push, pull)
6. MCP panel accessible
7. Settings persist across restarts

**Full validation**:
- Run all test scenarios from `TEST_REPORT.md`
- Validate all 12 success criteria
- Test on clean system (no Python installed)

### Distribution

Executables are generated in `dist/`:
- **Windows**: `Speckit Editor.exe` (~25MB with UPX)
- **macOS**: `Speckit Editor.app` (~30MB with UPX)
- **Linux**: `speckit-editor` (~28MB with UPX)

---

## Contributing

### Workflow

1. **Create feature branch**: `git checkout -b feature/your-feature-name`
2. **Make changes**: Follow code conventions, write tests
3. **Run tests**: `pytest` (must pass 100%)
4. **Format code**: `black .`
5. **Type check**: `mypy src/`
6. **Commit**: Conventional commits (`feat:`, `fix:`, `docs:`, `test:`)
7. **Push**: `git push origin feature/your-feature-name`
8. **Pull request**: Submit PR with description and test results

### Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```text
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Examples:
- `feat(editor): Add markdown syntax highlighting`
- `fix(git): Handle merge conflicts in git panel`
- `docs(readme): Update installation instructions`
- `test(validator): Add tests for requirement ID validation`

### Code Review Checklist

Before submitting PR:
- [ ] All tests pass (`pytest`)
- [ ] Code formatted (`black .`)
- [ ] Type hints correct (`mypy src/`)
- [ ] Docstrings added (Google style)
- [ ] Manual testing performed
- [ ] No new warnings or errors

---

## Additional Resources

- [User Guide](user-guide.md) - End-user documentation
- [Project README](../README.md) - Overview and quick start
- [Speckit Constitution](../.specify/memory/constitution.md) - Design principles
- [Feature Spec](../specs/001-speckit-editor-ide/spec.md) - Functional requirements

---

**Maintainer**: Speckit Team | **License**: MIT
