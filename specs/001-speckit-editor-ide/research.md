# Research: Speckit Editor Technical Decisions

**Feature**: 001-speckit-editor-ide | **Phase**: 0 (Research) | **Date**: 2025-12-22

## Purpose

Resolve technical unknowns and document technology choices before detailed design. Focuses on PySide6 best practices, MCP server implementation, cross-platform packaging, and performance optimization strategies.

---

## 1. PySide6 Architecture & Best Practices

### Decision: Use QTextEdit with QSyntaxHighlighter for Editor

**Rationale**:
- `QTextEdit` provides rich text editing with built-in undo/redo
- `QSyntaxHighlighter` enables real-time markdown syntax highlighting (FR-001)
- `QCompleter` can provide auto-completion for requirement IDs
- Native support for keyboard shortcuts and accessibility (FR-021, FR-031)

**Implementation Pattern**:
```python
class SpeckitEditorWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.highlighter = MarkdownHighlighter(self.document())
        self.setTabStopDistance(40)  # 4 spaces
        
class MarkdownHighlighter(QSyntaxHighlighter):
    def highlightBlock(self, text):
        # Apply QTextCharFormat for headers, code blocks, FR-XXX IDs, etc.
        pass
```

**Alternatives Considered**:
- ❌ QPlainTextEdit: Lacks rich text features needed for syntax highlighting
- ❌ Scintilla (QScintilla): External dependency violates Self-Contained principle
- ❌ Web-based editor (QtWebEngine): Memory overhead, security concerns

**References**:
- [Qt QTextEdit Documentation](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html)
- [QSyntaxHighlighter Guide](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QSyntaxHighlighter.html)

---

## 2. Embedded MCP Server Implementation

### Decision: Run MCP as Python Module with asyncio Event Loop

**Rationale**:
- MCP SDK provides Python implementation suitable for embedding
- Use asyncio for non-blocking service calls (FR-017 to FR-019)
- Spawn MCP server in separate thread with asyncio event loop
- Communicate via in-process queues (no network overhead)

**Implementation Pattern**:
```python
# src/mcp/server.py
import asyncio
from threading import Thread
from mcp.server import Server

class EmbeddedMCPServer:
    def __init__(self):
        self.server = Server("speckit-editor")
        self.loop = None
        self.thread = None
        
    def start(self):
        """Start MCP server in background thread"""
        self.thread = Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        
    def _run_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.server.run())
        
    async def call_service(self, service: str, method: str, **kwargs):
        """Call MCP service method from GUI thread"""
        return await self.server.call_tool(f"{service}/{method}", kwargs)
```

**Startup Sequence**:
1. GUI thread starts MCP server thread during application initialization
2. MCP server registers services (jira, github, git, databases, terminals, chrome)
3. Services load credentials from OS keyring
4. GUI polls server health status (< 3s startup budget from SC-001)

**Alternatives Considered**:
- ❌ External MCP server process: Violates Self-Contained principle, requires port management
- ❌ Synchronous MCP calls: Blocks GUI thread, violates <100ms responsiveness (SC-002)
- ❌ Multiprocessing instead of threading: Inter-process communication overhead

**References**:
- [Model Context Protocol Specification](https://modelcontextprotocol.io/docs)
- [Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk)

---

## 3. Git Integration Strategy

### Decision: Use pygit2 (libgit2 bindings)

**Rationale**:
- Native C library (libgit2) for performance (SC-004: <5s git operations)
- Does NOT require git binary installation (Self-Contained principle)
- Supports commit, branch, push, pull, merge operations (FR-007 to FR-012)
- Cross-platform (Windows, macOS, Linux)

**Implementation Pattern**:
```python
import pygit2

class GitService:
    def __init__(self, repo_path: str):
        self.repo = pygit2.Repository(repo_path)
        
    def commit(self, message: str, files: List[str]):
        index = self.repo.index
        for file in files:
            index.add(file)
        tree = index.write_tree()
        signature = pygit2.Signature("User", "user@email.com")
        self.repo.create_commit('HEAD', signature, signature, message, tree, [self.repo.head.peel().id])
        
    def push(self, remote: str, branch: str, credentials):
        remote_obj = self.repo.remotes[remote]
        callbacks = pygit2.RemoteCallbacks(credentials=credentials)
        remote_obj.push([f'refs/heads/{branch}'], callbacks=callbacks)
```

**Credential Handling**:
- Retrieve from OS keyring via `keyring` package
- Support SSH keys (read from ~/.ssh) and HTTPS tokens
- Prompt user for credentials if not found (FR-036: permission errors)

**Alternatives Considered**:
- ❌ GitPython: Pure Python but slower, uses git binary subprocess calls
- ❌ Dulwich: Pure Python but limited merge support
- ❌ Subprocess git binary: Requires external git installation

**References**:
- [pygit2 Documentation](https://www.pygit2.org/)
- [libgit2 Library](https://libgit2.org/)

---

## 4. Cross-Platform Packaging

### Decision: PyInstaller with Platform-Specific Hooks

**Rationale**:
- Bundles Python interpreter + dependencies into single executable
- Supports PySide6 with built-in hooks
- Produces platform-native executables (.exe, .app, .AppImage)
- Handles Qt plugins and dynamic libraries automatically

**Build Configuration** (pyinstaller.spec):
```python
# sdd-editor.spec
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('.specify/templates', '.specify/templates')],  # Bundle templates
    hiddenimports=['PySide6', 'pygit2', 'keyring'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],  # Reduce bundle size
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Speckit-Editor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress executable
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI app, no console window
    icon='assets/icon.ico',
)

# macOS app bundle
app = BUNDLE(exe, name='Speckit-Editor.app', icon='assets/icon.icns', bundle_identifier='com.speckit.editor')
```

**Platform-Specific Considerations**:
- **Windows**: Sign executable with certificate for SmartScreen bypass
- **macOS**: Code signing + notarization for Gatekeeper approval
- **Linux**: AppImage format for distribution independence

**Size Optimization**:
- Exclude unused Qt modules (QtWebEngine, QtMultimedia)
- Use UPX compression (reduces 150MB bundle to ~80MB)
- Bundle only required Python stdlib modules

**Alternatives Considered**:
- ❌ Nuitka: Complex build process, debugging difficulties
- ❌ cx_Freeze: Less mature PySide6 support
- ❌ py2app/py2exe: Platform-specific, need separate tooling

**References**:
- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [PyInstaller + PySide6 Guide](https://doc.qt.io/qtforpython-6/deployment-pyinstaller.html)

---

## 5. Search & Indexing Strategy

### Decision: In-Memory Inverted Index with SQLite Persistence

**Rationale**:
- SC-003 requires <1s search across 50 documents
- In-memory index provides instant search (regex + case-sensitive from FR-020)
- SQLite persistence allows incremental updates (index only changed documents)
- Supports 1000+ documents (FR-035: capacity limits)

**Implementation Pattern**:
```python
import sqlite3
from typing import Dict, List, Set

class DocumentIndexer:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.index: Dict[str, Set[str]] = {}  # word -> set of doc paths
        self._load_index()
        
    def _load_index(self):
        """Load index from SQLite into memory on startup"""
        cursor = self.conn.execute("SELECT word, doc_path FROM index")
        for word, doc_path in cursor:
            self.index.setdefault(word, set()).add(doc_path)
            
    def index_document(self, path: str, content: str):
        """Index a document (incremental update)"""
        words = self._tokenize(content)
        for word in words:
            self.index.setdefault(word, set()).add(path)
            self.conn.execute("INSERT OR IGNORE INTO index VALUES (?, ?)", (word, path))
        self.conn.commit()
        
    def search(self, query: str, case_sensitive: bool, regex: bool) -> List[str]:
        """Search index, return matching document paths"""
        if regex:
            import re
            pattern = re.compile(query, 0 if case_sensitive else re.IGNORECASE)
            matches = [word for word in self.index if pattern.search(word)]
        else:
            matches = [query if case_sensitive else query.lower()]
            
        result_docs = set()
        for word in matches:
            result_docs.update(self.index.get(word, set()))
        return list(result_docs)
```

**Indexing Strategy**:
- Index on document open/save (incremental)
- Background re-indexing on project load (async, doesn't block GUI)
- Virtual scrolling for large result sets (FR-035)

**Alternatives Considered**:
- ❌ Whoosh/Xapian: External dependencies, violates Self-Contained
- ❌ Grep-style scanning: Too slow for 1000+ documents
- ❌ Elasticsearch: Requires external service, violates Self-Contained

**References**:
- [SQLite FTS5 Full-Text Search](https://www.sqlite.org/fts5.html)
- [Python sqlite3 Module](https://docs.python.org/3/library/sqlite3.html)

---

## 6. Syntax Highlighting Performance

### Decision: Incremental Highlighting with QSyntaxHighlighter

**Rationale**:
- QSyntaxHighlighter only re-highlights visible lines (Qt optimization)
- Use QTextDocument's block-based architecture (each line = block)
- Cache regex patterns to avoid recompilation

**Implementation Pattern**:
```python
import re
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor

class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        
        # Pre-compile regex patterns (performance optimization)
        self.patterns = {
            'header': re.compile(r'^#{1,6}\s+.+'),
            'code_block': re.compile(r'^```.*'),
            'fr_id': re.compile(r'\b(FR|SC|CHK)-\d{3}\b'),
            'priority': re.compile(r'\b(P1|P2|P3|P4)\b'),
            'bold': re.compile(r'\*\*(.+?)\*\*'),
            'italic': re.compile(r'\*(.+?)\*'),
        }
        
        # Define formats
        self.formats = {
            'header': self._create_format(QColor(33, 150, 243), bold=True, size=14),
            'fr_id': self._create_format(QColor(76, 175, 80), bold=True),
            # ... more formats
        }
        
    def highlightBlock(self, text: str):
        """Called by Qt for each visible text block"""
        for name, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), self.formats[name])
```

**Performance Characteristics**:
- Highlighting triggered only on visible lines (Qt viewport optimization)
- Typical 10MB file has ~100K lines, but only ~50 lines visible at once
- Regex matching on 50 lines takes <5ms (well under 100ms budget from SC-002)

**Alternatives Considered**:
- ❌ Full document re-highlighting: Too slow for large files
- ❌ Pygments library: External dependency, slower than native QSyntaxHighlighter
- ❌ Manual QTextCursor styling: More complex, no built-in incremental updates

**References**:
- [QSyntaxHighlighter Performance Tips](https://doc.qt.io/qt-6/qsyntaxhighlighter.html#details)

---

## 7. Accessibility Implementation

### Decision: Native Qt Accessibility APIs + Keyboard Navigation

**Rationale**:
- QWidget has built-in accessibility support (screen readers via IAccessible2/AT-SPI)
- Use `setAccessibleName()` and `setAccessibleDescription()` for all widgets (FR-031)
- Implement keyboard-only navigation with visible focus indicators (FR-032)
- Qt automatically exposes widget hierarchy to screen readers

**Implementation Pattern**:
```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set accessible names for screen readers
        self.editor = SpeckitEditorWidget()
        self.editor.setAccessibleName("Document Editor")
        self.editor.setAccessibleDescription("Edit speckit markdown documents")
        
        self.navigator = ProjectNavigator()
        self.navigator.setAccessibleName("Project Navigator")
        
        # Keyboard navigation
        self.editor.setFocusPolicy(Qt.StrongFocus)
        self.navigator.setFocusPolicy(Qt.StrongFocus)
        
        # Focus indicators (visible borders)
        self.setStyleSheet("""
            QWidget:focus {
                border: 2px solid #2196F3;
            }
        """)
        
    def keyPressEvent(self, event):
        """Implement keyboard shortcuts (FR-021)"""
        if event.matches(QKeySequence.Save):
            self.save_document()
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_P:
            self.navigator.setFocus()
```

**Screen Reader Support**:
- Windows: NVDA/JAWS via IAccessible2
- macOS: VoiceOver via NSAccessibility
- Linux: Orca via AT-SPI

**Keyboard Shortcuts** (FR-021):
| Action | Shortcut | Accessible Alternative |
|--------|----------|------------------------|
| Save | Ctrl+S | File menu → Save |
| New Document | Ctrl+N | File menu → New |
| Search | Ctrl+F | Edit menu → Find |
| Toggle Navigator | Ctrl+P | View menu → Project Navigator |
| Commit | Ctrl+K | Git menu → Commit |

**Alternatives Considered**:
- ❌ Custom accessibility implementation: Reinventing Qt's built-in support
- ❌ Web-based accessibility (ARIA): Requires QtWebEngine, memory overhead

**References**:
- [Qt Accessibility Overview](https://doc.qt.io/qt-6/accessible.html)
- [PySide6 Accessibility API](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QAccessible.html)

---

## 8. Offline Mode Strategy

### Decision: Cache MCP Service Responses in SQLite

**Rationale**:
- Core editing + git operations work offline (no MCP dependency from FR-033)
- Cache recent Jira issues, GitHub PRs, database queries in SQLite
- Display cached data with visual indicator ("Last updated: 2 hours ago")
- Queue MCP operations for retry when connection restored

**Implementation Pattern**:
```python
class OfflineCache:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        
    def cache_response(self, service: str, method: str, args: dict, response: dict):
        """Cache MCP service response"""
        key = f"{service}:{method}:{json.dumps(args, sort_keys=True)}"
        timestamp = datetime.now().isoformat()
        self.conn.execute(
            "INSERT OR REPLACE INTO cache VALUES (?, ?, ?)",
            (key, json.dumps(response), timestamp)
        )
        self.conn.commit()
        
    def get_cached(self, service: str, method: str, args: dict) -> Optional[dict]:
        """Retrieve cached response if available"""
        key = f"{service}:{method}:{json.dumps(args, sort_keys=True)}"
        cursor = self.conn.execute(
            "SELECT response, timestamp FROM cache WHERE key = ?",
            (key,)
        )
        row = cursor.fetchone()
        if row:
            return {'data': json.loads(row[0]), 'cached_at': row[1]}
        return None
```

**Offline Capabilities**:
- ✅ Document editing (syntax highlighting, validation)
- ✅ Git operations (commit, branch, merge) - local only
- ✅ Project navigation
- ✅ Template usage
- ❌ MCP service calls (Jira, GitHub, databases, terminals, Chrome) - cached data only

**Alternatives Considered**:
- ❌ No offline mode: Violates FR-033
- ❌ Full local data replication: Too complex, violates Self-Contained (requires sync logic)

---

## 9. Testing Strategy

### Decision: Three-Tier Testing with Mocking

**Rationale**:
- **Unit tests** (pytest): Test core logic (document parsing, validation) without GUI
- **GUI tests** (pytest-qt): Test PySide6 widgets with mock backend services
- **Integration tests**: Test MCP services with mock HTTP responses

**Test Architecture**:
```text
tests/
├── unit/
│   ├── test_document.py       # Test SpeckitDocument parsing
│   ├── test_validator.py      # Test requirement ID validation
│   └── test_indexer.py        # Test search indexing
│
├── integration/
│   ├── test_gui.py             # Test GUI interactions (pytest-qt)
│   ├── test_mcp_jira.py        # Test Jira service with mock responses
│   └── test_git.py             # Test git operations with temp repos
│
└── fixtures/
    ├── sample_spec.md
    ├── mock_jira_responses.json
    └── mock_github_responses.json
```

**Coverage Requirements**:
- Minimum 80% line coverage (constitution requirement)
- 100% coverage for core/validator.py (critical validation logic)
- GUI tests use qtbot fixture for widget interaction

**Mock Strategy**:
```python
# tests/integration/test_mcp_jira.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_jira_create_issue(mock_jira_service):
    """Test Jira issue creation with mock HTTP response"""
    mock_response = {'id': 'PROJ-123', 'key': 'PROJ-123'}
    
    with patch('mcp.services.jira.JiraClient.create_issue', new=AsyncMock(return_value=mock_response)):
        result = await mock_jira_service.create_issue(
            project='PROJ',
            summary='Test issue',
            description='Description'
        )
        assert result['key'] == 'PROJ-123'
```

**Alternatives Considered**:
- ❌ Manual testing only: Cannot ensure 80% coverage requirement
- ❌ Real API calls in tests: Flaky, slow, requires test credentials

**References**:
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-qt Guide](https://pytest-qt.readthedocs.io/)

---

## 10. Performance Optimization Strategy

### Decision: Lazy Loading + Virtual Scrolling + Background Indexing

**Rationale**:
- FR-035 requires support for 1000+ documents
- Lazy load documents only when opened (not on project load)
- Virtual scrolling for large trees (only render visible nodes)
- Background indexing doesn't block GUI (separate thread)

**Implementation Patterns**:

**Lazy Document Loading**:
```python
class SpeckitProject:
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.documents: Dict[str, Optional[SpeckitDocument]] = {}
        self._scan_project()  # Fast: only enumerate file paths
        
    def _scan_project(self):
        """Scan project structure (metadata only, no file reads)"""
        for path in Path(self.root_path).rglob('*.md'):
            self.documents[str(path)] = None  # Not loaded yet
            
    def get_document(self, path: str) -> SpeckitDocument:
        """Load document on-demand"""
        if self.documents[path] is None:
            self.documents[path] = SpeckitDocument.load(path)
        return self.documents[path]
```

**Virtual Scrolling for Tree View**:
```python
from PySide6.QtWidgets import QTreeView
from PySide6.QtCore import QAbstractItemModel

class ProjectNavigator(QTreeView):
    def __init__(self):
        super().__init__()
        self.setUniformRowHeights(True)  # Enable virtual scrolling optimization
        self.setModel(LazyProjectModel())
        
class LazyProjectModel(QAbstractItemModel):
    """Only load visible tree nodes"""
    def data(self, index, role):
        # Load node data only when visible in viewport
        if not index.isValid():
            return None
        # ... lazy loading logic
```

**Background Indexing**:
```python
from PySide6.QtCore import QThread, Signal

class IndexerThread(QThread):
    progress = Signal(int, int)  # current, total
    finished = Signal()
    
    def __init__(self, indexer: DocumentIndexer, documents: List[str]):
        super().__init__()
        self.indexer = indexer
        self.documents = documents
        
    def run(self):
        """Index documents in background thread"""
        for i, path in enumerate(self.documents):
            with open(path) as f:
                self.indexer.index_document(path, f.read())
            self.progress.emit(i + 1, len(self.documents))
        self.finished.emit()
```

**Performance Budget Validation**:
- SC-001: Application startup < 3s → Lazy loading + no upfront indexing
- SC-002: Typing latency < 100ms → Incremental syntax highlighting
- SC-003: Search < 1s → In-memory inverted index
- SC-004: Git operations < 5s → Native libgit2 (pygit2)

**Alternatives Considered**:
- ❌ Eager loading: Violates startup time budget for large projects
- ❌ Render all tree nodes: Memory exhaustion with 1000+ documents
- ❌ Synchronous indexing: Blocks GUI during project load

---

## Unresolved Questions

None. All technical decisions finalized. Proceed to Phase 1 (data-model.md, contracts/, quickstart.md).
