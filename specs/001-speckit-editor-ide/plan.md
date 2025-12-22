# Implementation Plan: Speckit Document Editor/IDE

**Branch**: `001-speckit-editor-ide` | **Date**: 2025-12-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-speckit-editor-ide/spec.md`

## Summary

Build a cross-platform desktop IDE for speckit document management with embedded MCP server integration. The editor provides document editing with syntax highlighting, project navigation, git integration, MCP service connectivity (Jira, GitHub, databases, terminals, Chrome), AI assistance, and template management. Architecture uses PySide6 for GUI, embedded Python MCP module, and layered design (core → MCP → GUI) for testability and loose coupling.

## Technical Context

**Language/Version**: Python 3.11+ (for modern type hints, async/await, performance)
**Primary Dependencies**:
- PySide6 (Qt 6.x) - GUI framework (LGPL license)
- pygit2 or GitPython - Git operations  
- keyring - OS credential management
- markdown - Document parsing
- python-mcp-sdk - MCP server implementation
- pytest + pytest-qt - Testing framework

**Storage**: Local filesystem for documents, OS keyring for credentials, SQLite for local index/cache
**Testing**: pytest (unit), pytest-qt (GUI), pytest-mock (MCP integration tests)
**Target Platform**: Windows 10+, macOS 11+, Linux (Ubuntu 20.04+)
**Project Type**: Desktop application (single executable per platform)
**Performance Goals**:
- Application startup < 3 seconds
- Document editor typing latency < 100ms
- Search across 50 documents < 1 second
- Git operations < 5 seconds for typical repos

**Constraints**:
- Zero external installation beyond Python runtime
- Offline-capable core functionality
- AES-256 credential encryption
- Cross-platform parity (100% feature coverage)
- Memory footprint < 500MB with 20 open documents

**Scale/Scope**:
- Support projects with 1000+ documents
- Handle documents up to 10MB
- Up to 20 concurrent open documents
- 6 MCP integration types (Jira, GitHub, databases, terminals, Chrome, Git)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Constitution Check

Verified compliance with `.specify/memory/constitution.md` (v1.0.0):

| Principle | Requirement | Status | Evidence |
|-----------|-------------|--------|----------|
| Self-Contained | Zero external installations | ✅ PASS | PyInstaller bundles all dependencies; PySide6 embeds Qt runtime; no external database or web servers |
| Python-First | Python 3.11+ core implementation | ✅ PASS | Pure Python architecture; PySide6 for GUI (Python bindings); all business logic in Python modules |
| MCP Integration | Embedded MCP server | ✅ PASS | MCP server runs as Python module within editor process; supports 6 services (Jira, GitHub, Git, databases, terminals, Chrome) per FR-017 to FR-019 |
| CLI-GUI Parity | Feature parity across interfaces | ✅ PASS | FR-013 (execute commands via GUI), FR-014 (CLI interface), FR-015 (AI assist through GUI), all speckit commands accessible via both |
| AI-Assisted Generation | Copilot integration | ✅ PASS | FR-015 (AI-assisted spec generation), FR-016 (inline suggestions), leverages embedded MCP server for AI connectivity |

**Technical Constraints Compliance**:
- PySide6 GUI framework: ✅ Specified in Technical Context
- Embedded MCP architecture: ✅ Confirmed in clarifications (Session 2025-12-22)
- Python 3.11+ minimum: ✅ Specified in Technical Context
- Cross-platform requirement: ✅ Target platforms Windows/macOS/Linux specified
- Testing requirements (pytest, 80% coverage): ✅ Specified in Technical Context
- Security requirements (OS keyring, AES-256): ✅ Specified in Technical Context

**Gate Status**: ✅ **APPROVED** - All constitution principles satisfied, proceed with planning.

## Project Structure

### Documentation (this feature)

```text
specs/001-speckit-editor-ide/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
sdd-editor/
├── src/
│   ├── core/                 # Business logic layer (document parsing, validation)
│   │   ├── __init__.py
│   │   ├── document.py       # SpeckitDocument, parsing logic
│   │   ├── project.py        # SpeckitProject, filesystem operations
│   │   ├── validator.py      # Requirement ID validation, spec structure checks
│   │   ├── indexer.py        # Document search indexing
│   │   └── template.py       # Template management
│   │
│   ├── mcp/                  # MCP integration layer
│   │   ├── __init__.py
│   │   ├── server.py         # MCP server lifecycle management
│   │   ├── services/         # Service-specific implementations
│   │   │   ├── jira.py       # Jira integration
│   │   │   ├── github.py     # GitHub integration
│   │   │   ├── git.py        # Git operations
│   │   │   ├── database.py   # Database connections
│   │   │   ├── terminal.py   # Terminal execution
│   │   │   └── chrome.py     # Chrome DevTools
│   │   └── credentials.py    # Keyring-based credential management
│   │
│   ├── gui/                  # PySide6 GUI layer
│   │   ├── __init__.py
│   │   ├── main_window.py    # Main application window
│   │   ├── editor.py         # Document editor widget (syntax highlighting)
│   │   ├── navigator.py      # Project tree navigator widget
│   │   ├── git_panel.py      # Git operations panel
│   │   ├── mcp_panel.py      # MCP service connections panel
│   │   ├── ai_panel.py       # AI assistance panel
│   │   ├── template_dialog.py # Template selection dialog
│   │   └── settings.py       # Settings/preferences dialog
│   │
│   ├── cli/                  # Command-line interface
│   │   ├── __init__.py
│   │   ├── main.py           # CLI entry point
│   │   └── commands.py       # Speckit command implementations
│   │
│   └── utils/                # Shared utilities
│       ├── __init__.py
│       ├── config.py         # Configuration management
│       ├── logging.py        # Logging setup
│       └── packaging.py      # PyInstaller helpers
│
├── tests/
│   ├── unit/                 # Unit tests (pytest)
│   │   ├── test_document.py
│   │   ├── test_validator.py
│   │   └── test_template.py
│   │
│   ├── integration/          # Integration tests (pytest-qt, mock MCP)
│   │   ├── test_gui.py
│   │   ├── test_mcp_services.py
│   │   └── test_git_integration.py
│   │
│   └── fixtures/             # Test data
│       ├── sample_project/
│       └── mock_responses/
│
├── docs/                     # User documentation
│   ├── user-guide.md
│   ├── developer-guide.md
│   └── screenshots/
│
├── .specify/                 # Speckit metadata (already exists)
│   ├── memory/
│   │   └── constitution.md
│   ├── templates/
│   └── scripts/
│
├── requirements.txt          # Python dependencies
├── requirements-dev.txt      # Development dependencies
├── pyproject.toml            # Project metadata (setuptools/black/mypy config)
├── pytest.ini                # Pytest configuration
├── README.md                 # Project README
└── main.py                   # Application entry point
```

**Structure Decision**: Single desktop project with three-layer architecture (core → mcp → gui). This structure enables:
- **Testability**: Core business logic testable without GUI dependencies
- **Loose Coupling**: MCP layer can be mocked for integration tests
- **CLI-GUI Parity**: Both interfaces consume same core/mcp modules
- **Cross-Platform**: Platform-specific code isolated to packaging layer only

## Complexity Tracking

No constitution violations detected. All complexity justified by functional requirements:
- **Three-layer architecture** (core/mcp/gui): Required by FR-013/FR-014 (CLI-GUI parity) and testability
- **Six MCP services**: Required by FR-017 to FR-019 (Jira, GitHub, Git, databases, terminals, Chrome)
- **Embedded MCP server**: Required by Self-Contained principle, simpler than external MCP server process
