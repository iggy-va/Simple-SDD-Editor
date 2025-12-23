# Contributing to Speckit Editor

Thank you for your interest in contributing to Speckit Editor! This document provides guidelines and workflows for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Speckit Methodology](#speckit-methodology)

---

## Getting Started

### Prerequisites

- **Python 3.11+** (required for modern type hints)
- **Git 2.30+**
- **Virtual environment** (recommended)

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/iggy-va/Simple-SDD-Editor.git
cd Simple-SDD-Editor

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-qt pytest-cov black mypy

# Run tests to verify setup
python -m pytest tests/
```

---

## Development Workflow

This project follows the **Speckit methodology**. All features begin as specifications before implementation.

### For New Features

1. **Specify** - Define requirements and user stories
   ```bash
   # Create feature specification
   /speckit.specify "Feature description"
   ```

2. **Clarify** - Resolve ambiguities through Q&A
   ```bash
   /speckit.clarify
   ```

3. **Plan** - Create technical design
   ```bash
   /speckit.plan
   ```

4. **Generate Tasks** - Break down implementation
   ```bash
   /speckit.tasks
   ```

5. **Implement** - Build with AI guidance
   ```bash
   /speckit.implement
   ```

### For Bug Fixes

1. Create an issue describing the bug
2. Create a feature branch: `git checkout -b fix/issue-description`
3. Write a failing test that reproduces the bug
4. Fix the bug
5. Verify the test passes
6. Submit a pull request

---

## Code Standards

### Python Style

- **Formatter**: Black (line length 100)
- **Type Checker**: Mypy (strict mode)
- **Docstring Format**: Google style

```python
def example_function(param: str) -> bool:
    """Short description of function.
    
    Longer description if needed, explaining the function's
    purpose and behavior in detail.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When parameter is invalid
    """
    pass
```

### Code Organization

- **3-layer architecture**: Core → MCP → GUI
- **Dependency direction**: Always downward (GUI → MCP → Core)
- **Core layer**: Zero knowledge of GUI or MCP layers

```
┌─────────────────────────────────────┐
│     GUI Layer (PySide6)             │  ← User interactions
└─────────────┬───────────────────────┘
              │ (calls)
┌─────────────▼───────────────────────┐
│    MCP Integration Layer            │  ← External services
└─────────────┬───────────────────────┘
              │ (calls)
┌─────────────▼───────────────────────┐
│   Core Business Logic               │  ← Models, validation
└─────────────────────────────────────┘
```

### Format Code Before Committing

```bash
# Format with Black
black src/ tests/

# Check types
mypy src/

# Run linter
ruff check src/
```

---

## Testing

### Test Coverage Requirements

- **Unit tests**: 80%+ coverage for core business logic
- **Integration tests**: Critical user workflows
- **GUI tests**: pytest-qt for widget interactions

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/unit/test_document.py -v

# Run tests matching pattern
python -m pytest tests/ -k "test_validation"
```

### Writing Tests

```python
# tests/unit/test_example.py
import pytest
from src.core.document import SpeckitDocument

def test_create_document():
    """Test document creation."""
    doc = SpeckitDocument("Test", "spec")
    assert doc.name == "Test"
    assert doc.document_type == "spec"

@pytest.mark.parametrize("doc_type", ["spec", "plan", "tasks", "checklist"])
def test_valid_document_types(doc_type):
    """Test all valid document types."""
    doc = SpeckitDocument("Test", doc_type)
    assert doc.document_type == doc_type
```

---

## Commit Messages

We follow **Conventional Commits** for clear, semantic commit history.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### Examples

```bash
# Feature
git commit -m "feat(editor): Add syntax highlighting for issue references"

# Bug fix
git commit -m "fix(git): Resolve merge conflict detection error"

# Documentation
git commit -m "docs(readme): Update installation instructions"

# Breaking change
git commit -m "feat(api): Change document save format

BREAKING CHANGE: Document format version bumped to 2.0"
```

---

## Pull Request Process

### Before Submitting

1. ✅ All tests pass: `python -m pytest tests/`
2. ✅ Code formatted: `black src/ tests/`
3. ✅ Type checks pass: `mypy src/`
4. ✅ Coverage maintained: `pytest --cov=src`
5. ✅ Documentation updated (if applicable)
6. ✅ Commit messages follow Conventional Commits

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Closes #123

## Testing
- [ ] Added unit tests
- [ ] Added integration tests
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] Documentation updated
- [ ] No new warnings from type checker
```

### Review Process

1. Submit PR with clear description
2. Automated checks must pass (tests, linting, type checking)
3. At least one maintainer review required
4. Address review comments
5. Squash commits if requested
6. Maintainer will merge when approved

---

## Speckit Methodology

### Core Principles

1. **Specification First**: Features start as specs, not code
2. **Incremental Documentation**: Update docs after each user story
3. **Task-Driven Development**: Break work into trackable tasks
4. **Independent User Stories**: Each story deliverable independently
5. **Test-Driven When Requested**: Generate tests if spec requires

### File Structure

```
specs/
└── 001-feature-name/
    ├── spec.md          # Requirements and user stories
    ├── plan.md          # Technical design
    ├── tasks.md         # Task breakdown
    ├── data-model.md    # Entity relationships (optional)
    ├── contracts/       # API endpoints (optional)
    └── research.md      # Design decisions (optional)
```

### Task Format

Every task follows this checklist format:

```markdown
- [ ] T001 [TaskID] [P?] [Story?] Description with file path
```

Components:
- `- [ ]` - Markdown checkbox
- `T001` - Sequential task ID
- `[P]` - Optional parallel marker (different files, no dependencies)
- `[Story]` - User story label ([US1], [US2], etc.)
- Description with exact file path

---

## Questions?

- **Issues**: https://github.com/iggy-va/Simple-SDD-Editor/issues
- **Discussions**: https://github.com/iggy-va/Simple-SDD-Editor/discussions
- **Email**: Contact maintainers via GitHub

---

**Thank you for contributing to Speckit Editor!** 🚀
