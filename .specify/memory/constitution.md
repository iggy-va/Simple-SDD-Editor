# SDD Editor Constitution

## Core Principles

### I. Self-Contained & Portable
The SDD Editor MUST be fully self-contained with zero external installation requirements. The editor MUST be distributed as standalone executables for Windows (.exe), macOS (.app), and Linux (AppImage/executable) that bundle Python runtime and all dependencies. Users MUST NOT be required to install Python or any other runtime. The editor MUST run identically on all platforms without platform-specific installations or configurations.

### II. Python-First Architecture
All core functionality built in Python with a modern GUI framework (candidates: PyQt6, PySide6, or Tkinter). Architecture separates concerns: Core logic → MCP integration layer → GUI layer. Each layer independently testable and loosely coupled.

### III. MCP Server Integration (NON-NEGOTIABLE)
The editor MUST include a built-in Model Context Protocol (MCP) server supporting:
- Jira integration (issue tracking, project management)
- Database connectivity (query, schema inspection)
- GitHub integration (repos, PRs, issues, workflows)
- Git operations (commit, branch, merge, history)
- Terminal execution (command running, output capture)
- Chrome automation (web scraping, testing, screenshots)

All integrations MUST be configurable, secure (credential management), and error-resilient.

### IV. CLI-GUI Parity
Every CLI command MUST have a GUI equivalent. Users can accomplish all tasks through either interface. GUI provides visual workflows; CLI provides scriptability and automation. Both interfaces call the same underlying core services.

### V. AI-Assisted Speckit Generation
GitHub Copilot (or compatible AI assistant) integration for generating speckit artifacts:
- Constitution templates
- Specification documents
- Plan generation from specs
- Task breakdown from plans
- Implementation guidance

AI assistance MUST be optional, reviewable, and editable by users before commitment.

### VI. Accessibility & 508 Compliance (NON-NEGOTIABLE)
The editor MUST comply with Section 508 of the Rehabilitation Act and WCAG 2.1 Level AA standards. This includes:
- Full keyboard navigation for all functionality without requiring a mouse
- Screen reader compatibility with ARIA labels and semantic markup
- Sufficient color contrast ratios (4.5:1 for normal text, 3:1 for large text, 7:1 for enhanced)
- Visible focus indicators for all interactive elements (minimum 2px outline with high contrast)
- No time-dependent interactions without alternatives or user control
- Accessible error messages and validation feedback announced to assistive technologies
- Support for assistive technologies (screen readers, voice control, screen magnification, alternative input devices)
- Resizable text without loss of functionality (up to 200% zoom)
- No content that causes seizures (no flashing >3 times per second)

Accessibility MUST NOT be an afterthought or "nice to have" feature - it is a core requirement equal in priority to functionality. All features MUST be designed with accessibility from the start, not retrofitted. Automated accessibility testing MUST be part of the CI/CD pipeline, and manual testing with screen readers MUST occur before each release.

## Technical Constraints

### Technology Stack
- **Language**: Python 3.11+ (for modern type hints, performance)
- **GUI Framework**: PySide6 (Qt for Python, LGPL licensed)
- **MCP Implementation**: Embedded Python module within editor process
- **Dependency Management**: pip + requirements.txt or Poetry for reproducible builds
- **Packaging**: PyInstaller or similar for standalone executables per platform

### Cross-Platform Requirements
- No platform-specific code in core logic (use abstraction layers)
- File paths use `pathlib` for OS-agnostic handling
- Process execution via `subprocess` with platform detection
- GUI layouts must be responsive and adapt to different screen sizes/DPI settings

### Security Standards
- Credentials stored using OS keyring (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- No plaintext passwords in configs or logs
- API tokens encrypted at rest
- User consent required for external network calls

### Performance Standards
- Application startup < 3 seconds
- GUI responsiveness maintained during long operations (async/threading)
- Document loading/saving < 1 second for typical SDD files (< 10MB)
- MCP operations timeout after 30 seconds with user notification

## Development Workflow

### Structure
```
sdd-editor/
├── src/
│   ├── core/          # Business logic (SDD parsing, validation)
│   ├── mcp/           # MCP server and integrations
│   ├── gui/           # GUI components and controllers
│   ├── cli/           # CLI interface
│   └── utils/         # Shared utilities
├── tests/             # Unit and integration tests
├── docs/              # Documentation
├── .specify/          # Speckit configuration
└── requirements.txt   # Dependencies
```

### Testing Requirements
- Unit tests for all core logic (pytest)
- Integration tests for MCP integrations (mock external services)
- GUI tests using pytest-qt for all completed GUI features
- **Minimum 90% code coverage for completed features only**
  - Coverage calculated only for modules/features marked as complete/implemented
  - Incomplete features excluded from coverage percentage until completion
  - Once a feature is marked complete, it must maintain 90% coverage
  - GUI tests required for all completed GUI features
- All tests must pass before commits to main branch
- Coverage reports generated and reviewed with each PR, gated by 90% for completed modules
- Uncovered code paths in completed features must be documented with justification
- Test stubs required for incomplete features to maintain passing test suite

### Version Control
- Git-based workflow with feature branches
- Commit messages follow Conventional Commits
- PRs require passing tests and code review
- Main branch always in releasable state

## Governance

### Decision Making
- Core principles in this constitution are immutable unless critical technical blockers arise
- Technology choices (GUI framework, specific libraries) subject to proof-of-concept validation
- Breaking changes require migration guide and backward compatibility period

### Amendment Process
1. Proposal documented with rationale
2. Team review and discussion
3. Vote and approval
4. Constitution updated with version bump
5. All affected documentation updated

### Compliance
- All features must align with constitution principles
- Trade-offs documented in architecture decision records (ADRs)
- Regular architecture reviews to ensure compliance

**Version**: 1.2.0 | **Ratified**: 2025-12-18 | **Last Amended**: 2025-12-22

---

## Amendment History

### v1.2.0 (2025-12-22)
**Addition**: Added Principle VI - Accessibility & 508 Compliance as a non-negotiable core principle. The editor must comply with Section 508 and WCAG 2.1 Level AA standards, including full keyboard navigation, screen reader support, color contrast requirements, and comprehensive assistive technology compatibility. Accessibility is now mandatory for all features with automated testing required in CI/CD pipeline.

### v1.1.0 (2025-12-22)
**Clarification**: Self-Contained principle now explicitly requires standalone executables (.exe, .app, AppImage) bundling Python runtime. Users must not need Python pre-installed. Packaging tools (PyInstaller) must create platform-native executables for Windows, macOS, and Linux.
