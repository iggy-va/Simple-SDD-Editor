# Developer Quickstart: Speckit Editor

**Feature**: 001-speckit-editor-ide | **Date**: 2025-12-22

## Purpose

Get developers up and running with the Speckit Editor codebase in under 30 minutes. This guide covers environment setup, running the application, running tests, and making your first code contribution.

---

## Prerequisites

- **Python**: 3.11 or higher
- **Git**: 2.30 or higher
- **OS**: Windows 10+, macOS 11+, or Linux (Ubuntu 20.04+)
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 500MB free space

---

## Step 1: Clone Repository

```bash
git clone https://github.com/iggy-va/Simple-SDD-Editor.git
cd Simple-SDD-Editor
```

**Verify structure**:
```bash
ls -la
# Expected output:
# .specify/
# specs/
# README.md
# (src/ directory will be created during development)
```

---

## Step 2: Create Virtual Environment

**macOS/Linux**:
```bash
python3.11 -m venv venv
source venv/bin/activate
```

**Windows**:
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Verify activation**:
```bash
which python  # Should show venv/bin/python (or venv\Scripts\python.exe on Windows)
python --version  # Should show Python 3.11+
```

---

## Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

**requirements.txt** (core dependencies):
```text
PySide6>=6.6.0
pygit2>=1.13.0
keyring>=24.0.0
markdown>=3.5.0
python-mcp-sdk>=0.1.0
httpx>=0.25.0
```

**requirements-dev.txt** (development dependencies):
```text
pytest>=7.4.0
pytest-qt>=4.2.0
pytest-asyncio>=0.21.0
pytest-mock>=3.12.0
pytest-cov>=4.1.0
black>=23.12.0
mypy>=1.7.0
ruff>=0.1.8
```

**Verify installation**:
```bash
python -c "import PySide6; print(PySide6.__version__)"
# Expected: 6.6.x

pytest --version
# Expected: pytest 7.4.x
```

---

## Step 4: Run Application (Development Mode)

Since implementation hasn't started yet, we'll create a minimal skeleton:

**Create `main.py` (temporary skeleton)**:
```python
#!/usr/bin/env python3
"""Speckit Editor - Main entry point"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Speckit Editor v0.1.0-dev")
        self.setGeometry(100, 100, 800, 600)
        
        label = QLabel("Speckit Editor - Development Build", self)
        label.move(300, 250)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

**Run the application**:
```bash
python main.py
```

**Expected**: Empty window with title "Speckit Editor v0.1.0-dev" appears.

---

## Step 5: Run Tests

**Create test directory structure**:
```bash
mkdir -p tests/{unit,integration,fixtures}
```

**Create sample test** (`tests/unit/test_example.py`):
```python
"""Sample test to verify pytest setup"""

def test_sanity():
    """Sanity check: Python works"""
    assert 1 + 1 == 2

def test_imports():
    """Verify core dependencies importable"""
    import PySide6
    import pygit2
    import keyring
    import markdown
    assert True
```

**Run tests**:
```bash
pytest tests/ -v

# Expected output:
# tests/unit/test_example.py::test_sanity PASSED
# tests/unit/test_example.py::test_imports PASSED
# ======================== 2 passed in 0.5s ========================
```

**Run with coverage**:
```bash
pytest tests/ --cov=src --cov-report=term-missing

# Expected: 0% coverage (no src/ yet, but pytest-cov works)
```

---

## Step 6: Code Quality Checks

**Format code** (Black):
```bash
black main.py tests/
# Expected: All done! ✨ 🍰 ✨
```

**Lint code** (Ruff):
```bash
ruff check main.py tests/
# Expected: No issues found (or list of fixable issues)
```

**Type check** (mypy):
```bash
mypy main.py --strict
# Expected: Success (or type errors to fix)
```

---

## Step 7: Understanding Project Structure

```text
Simple-SDD-Editor/
├── .specify/                    # Speckit metadata
│   ├── memory/
│   │   └── constitution.md      # Project constitution (read first!)
│   ├── templates/               # Document templates
│   └── scripts/                 # PowerShell helper scripts
│
├── specs/                       # Feature specifications
│   └── 001-speckit-editor-ide/
│       ├── spec.md              # Requirements (read second!)
│       ├── plan.md              # Implementation plan (this feature)
│       ├── research.md          # Technical decisions
│       ├── data-model.md        # Data structures
│       ├── contracts/           # API contracts
│       │   ├── cli-api.md
│       │   └── mcp-services.md
│       └── quickstart.md        # This file
│
├── src/                         # Source code (to be created)
│   ├── core/                    # Business logic
│   ├── mcp/                     # MCP integration
│   ├── gui/                     # PySide6 GUI
│   ├── cli/                     # Command-line interface
│   └── utils/                   # Shared utilities
│
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── fixtures/                # Test data
│
├── docs/                        # User documentation
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
├── pytest.ini                   # Pytest configuration
├── pyproject.toml               # Project metadata
├── main.py                      # Application entry point
└── README.md                    # User-facing documentation
```

---

## Step 8: Development Workflow

### 8.1 Create Feature Branch

```bash
git checkout -b 001-speckit-editor-ide
```

### 8.2 Make Changes

1. **Understand requirement**: Read `specs/001-speckit-editor-ide/spec.md`
2. **Check data model**: Review `specs/001-speckit-editor-ide/data-model.md`
3. **Write failing test**: Add test to `tests/unit/test_*.py`
4. **Implement feature**: Add code to `src/`
5. **Make test pass**: Run `pytest` until green
6. **Refactor**: Improve code quality

### 8.3 Pre-Commit Checks

```bash
# Format
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/ --strict

# Run tests
pytest tests/ --cov=src --cov-report=term-missing

# Verify coverage >= 80%
```

### 8.4 Commit Changes

**Use conventional commit format**:
```bash
git add src/core/document.py tests/unit/test_document.py
git commit -m "feat(001): implement document parser

- Parse markdown into sections
- Extract requirements (FR/SC/CHK IDs)
- Validate requirement numbering
- Add unit tests (coverage: 85%)

Implements: FR-001, FR-002
Tests: test_document.py"
```

**Commit message structure**:
```
<type>(<scope>): <short summary>

<detailed description>

<references>
```

**Types**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

### 8.5 Push to Remote

```bash
git push origin 001-speckit-editor-ide
```

### 8.6 Create Pull Request

Go to GitHub and create PR from `001-speckit-editor-ide` → `main`.

---

## Step 9: Common Development Tasks

### Run Specific Test

```bash
pytest tests/unit/test_document.py::test_parse_sections -v
```

### Run Tests in Watch Mode

```bash
pytest-watch tests/
```

### Debug with Breakpoints

Add to code:
```python
import pdb; pdb.set_trace()
```

Run test:
```bash
pytest tests/unit/test_document.py --pdb
```

### Profile Performance

```bash
python -m cProfile -o profile.stats main.py
python -m pstats profile.stats
# (Pstats) sort cumtime
# (Pstats) stats 10
```

### Generate Documentation

```bash
# Generate API docs (future)
sphinx-build -b html docs/ docs/_build/
```

---

## Step 10: Troubleshooting

### Issue: PySide6 fails to import

**Error**: `ImportError: cannot import name 'QApplication' from 'PySide6.QtWidgets'`

**Solution**:
```bash
pip uninstall PySide6
pip install PySide6 --no-cache-dir
```

---

### Issue: pygit2 installation fails

**Error**: `fatal error: git2.h: No such file or directory`

**Solution** (install libgit2 first):

**macOS**:
```bash
brew install libgit2
pip install pygit2
```

**Ubuntu**:
```bash
sudo apt-get install libgit2-dev
pip install pygit2
```

**Windows**: Use pre-built wheel:
```bash
pip install pygit2 --only-binary :all:
```

---

### Issue: Keyring backend not available

**Error**: `keyring.errors.NoKeyringError: No recommended backend was available`

**Solution** (Linux):
```bash
sudo apt-get install gnome-keyring
```

**Workaround** (development only):
```bash
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
```

---

### Issue: Tests fail with Qt platform plugin error

**Error**: `qt.qpa.plugin: Could not load the Qt platform plugin "xcb"`

**Solution** (Linux):
```bash
sudo apt-get install libxcb-xinerama0
export QT_QPA_PLATFORM=offscreen  # For headless CI
```

---

## Step 11: IDE Setup

### VS Code (Recommended)

**Install extensions**:
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Black Formatter (ms-python.black-formatter)
- Ruff (charliermarsh.ruff)

**Workspace settings** (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

**Run configuration** (`.vscode/launch.json`):
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Speckit Editor",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/main.py",
      "console": "integratedTerminal"
    },
    {
      "name": "Python: Current Test",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-v"]
    }
  ]
}
```

---

### PyCharm

**Configure interpreter**:
1. File → Settings → Project → Python Interpreter
2. Add Interpreter → Existing Environment → Select `venv/bin/python`

**Configure pytest**:
1. File → Settings → Tools → Python Integrated Tools
2. Default test runner: pytest

**Configure Black**:
1. File → Settings → Tools → External Tools
2. Add → Name: Black, Program: `$ProjectFileDir$/venv/bin/black`, Arguments: `$FilePath$`

---

## Step 12: Next Steps

After completing this quickstart, you should:

1. **Read the constitution**: `.specify/memory/constitution.md` (understand project principles)
2. **Read the spec**: `specs/001-speckit-editor-ide/spec.md` (understand requirements)
3. **Read the data model**: `specs/001-speckit-editor-ide/data-model.md` (understand entities)
4. **Pick a task**: Once `tasks.md` is generated, pick TSK-001 and implement it
5. **Ask questions**: Open GitHub issue or discussion if stuck

---

## Step 13: Helpful Commands Cheatsheet

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Run application
python main.py

# Run all tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html in browser

# Format code
black src/ tests/

# Lint code
ruff check src/ tests/ --fix

# Type check
mypy src/ --strict

# Pre-commit checks (all)
black src/ tests/ && ruff check src/ tests/ && mypy src/ && pytest tests/ --cov=src

# Commit with conventional format
git commit -m "feat(001): <description>"

# Push to feature branch
git push origin 001-speckit-editor-ide

# View git log (pretty)
git log --oneline --graph --decorate

# Clean cache files
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name '*.pyc' -delete
```

---

## Step 14: Learning Resources

**PySide6**:
- [Official Documentation](https://doc.qt.io/qtforpython-6/)
- [Qt for Python Tutorial](https://doc.qt.io/qtforpython-6/tutorials/index.html)

**pygit2**:
- [pygit2 Documentation](https://www.pygit2.org/)
- [libgit2 Examples](https://libgit2.org/docs/guides/101-samples/)

**MCP**:
- [Model Context Protocol Docs](https://modelcontextprotocol.io/docs)
- [Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk)

**Testing**:
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-qt Guide](https://pytest-qt.readthedocs.io/)

**Python Best Practices**:
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [Type Hints (PEP 484)](https://peps.python.org/pep-0484/)

---

## Step 15: Getting Help

**Stuck? Try these resources**:

1. **Check the docs**: Read `specs/001-speckit-editor-ide/*.md` files
2. **Search issues**: [GitHub Issues](https://github.com/iggy-va/Simple-SDD-Editor/issues)
3. **Ask in discussions**: [GitHub Discussions](https://github.com/iggy-va/Simple-SDD-Editor/discussions)
4. **Review test examples**: Look at existing tests for patterns
5. **Check data model**: `data-model.md` defines all entities

**Reporting bugs**:
1. Search existing issues first
2. Provide minimal reproducible example
3. Include Python version, OS, error traceback
4. Tag with appropriate label (bug, question, enhancement)

---

## Success Criteria

You've successfully completed the quickstart when you can:

- ✅ Clone repository and activate virtual environment
- ✅ Install all dependencies without errors
- ✅ Run skeleton application (GUI window appears)
- ✅ Run tests (all pass)
- ✅ Format, lint, and type-check code
- ✅ Create conventional commit and push to feature branch
- ✅ Understand project structure (constitution → spec → plan → code)

**Estimated completion time**: 20-30 minutes

---

## What's Next?

Once implementation begins, this quickstart will evolve to include:

- **Running specific features**: How to test document editor, git integration, MCP services
- **Debugging MCP**: How to inspect MCP server calls
- **Performance profiling**: How to identify bottlenecks
- **Packaging builds**: How to create PyInstaller executables

For now, focus on:
1. Understanding the requirements (`spec.md`)
2. Understanding the architecture (`plan.md`, `data-model.md`)
3. Setting up your development environment (this guide)
4. Waiting for task breakdown (`tasks.md` - generated by `/speckit.tasks`)

**Welcome to the Speckit Editor project! 🎉**
