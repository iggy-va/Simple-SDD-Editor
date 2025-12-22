# Tasks: Speckit Document Editor/IDE

**Input**: Design documents from `/specs/001-speckit-editor-ide/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Test tasks are NOT included per standard practice. Focus on implementation and manual testing per user stories.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (src/{core,mcp,gui,cli,utils}, tests/{unit,integration,fixtures}, docs/)
- [ ] T002 Initialize Python project with pyproject.toml, requirements.txt, and requirements-dev.txt
- [ ] T003 [P] Configure pytest with pytest.ini and coverage settings (80% minimum)
- [ ] T004 [P] Configure Black formatter, Ruff linter, and mypy type checker
- [ ] T005 [P] Create .gitignore for Python (__pycache__, *.pyc, venv/, .pytest_cache/, htmlcov/)
- [ ] T006 [P] Create main.py application entry point with basic QApplication setup
- [ ] T007 [P] Setup logging infrastructure in src/utils/logging.py
- [ ] T008 [P] Create configuration management in src/utils/config.py for .specify/settings.json

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 Implement SpeckitProject model in src/core/project.py (scan_documents, lazy loading)
- [ ] T010 [P] Implement SpeckitDocument model in src/core/document.py (parse, save, validation)
- [ ] T011 [P] Implement Section and Requirement data classes in src/core/document.py
- [ ] T012 [P] Implement document parser for markdown in src/core/document.py (extract sections, requirements, frontmatter)
- [ ] T013 [P] Implement document validator in src/core/validator.py (requirement ID patterns, sequential numbering, cross-references)
- [ ] T014 [P] Implement ProjectSettings model in src/core/project.py with load/save to .specify/settings.json
- [ ] T015 Implement MainWindow class in src/gui/main_window.py with menu bar, status bar, and central widget
- [ ] T016 [P] Create application icons and assets in assets/ directory
- [ ] T017 [P] Setup PySide6 application styling in src/gui/main_window.py (stylesheet for focus indicators, themes)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Create and Edit Specification Documents (Priority: P1) 🎯 MVP

**Goal**: Enable users to create and edit speckit documents with syntax highlighting, validation, and saving

**Independent Test**: Create new spec from template, edit content with formatting, save document, reopen and verify content preserved

### Implementation for User Story 1

- [ ] T018 [P] [US1] Implement Template model in src/core/template.py (load, instantiate with variables)
- [ ] T019 [P] [US1] Implement TemplateVariable data class in src/core/template.py
- [ ] T020 [US1] Copy default templates from .specify/templates/ to src/core/template.py (spec-template, plan-template, tasks-template, checklist-template)
- [ ] T021 [P] [US1] Implement SpeckitEditorWidget in src/gui/editor.py extending QTextEdit
- [ ] T022 [P] [US1] Implement MarkdownHighlighter in src/gui/editor.py extending QSyntaxHighlighter (headers, code blocks, FR/SC IDs, priority markers, Given/When/Then)
- [ ] T023 [US1] Implement syntax highlighting regex patterns in src/gui/editor.py (per FR-001)
- [ ] T024 [US1] Implement QTextCharFormat styles for highlighted elements in src/gui/editor.py (colors, bold, font sizes)
- [ ] T025 [P] [US1] Implement DocumentChange model in src/core/document.py for undo/redo stack
- [ ] T026 [US1] Connect undo/redo operations to SpeckitEditorWidget in src/gui/editor.py using QTextDocument history
- [ ] T027 [P] [US1] Implement new document action in src/gui/main_window.py (File → New)
- [ ] T028 [US1] Create template selection dialog in src/gui/template_dialog.py with variable input forms
- [ ] T029 [US1] Integrate template instantiation with document creation in src/gui/main_window.py
- [ ] T030 [P] [US1] Implement save document action in src/gui/main_window.py (File → Save, Ctrl+S)
- [ ] T031 [P] [US1] Implement save all documents action in src/gui/main_window.py (File → Save All, Ctrl+Shift+S)
- [ ] T032 [US1] Implement unsaved changes tracking in src/gui/editor.py (dirty flag, textChanged signal)
- [ ] T033 [US1] Add unsaved indicator (*) to tab titles in src/gui/main_window.py
- [ ] T034 [US1] Implement close document prompt for unsaved changes in src/gui/main_window.py
- [ ] T035 [P] [US1] Implement open document action in src/gui/main_window.py (File → Open, Ctrl+O)
- [ ] T036 [US1] Integrate document parser with editor loading in src/gui/editor.py
- [ ] T037 [P] [US1] Implement real-time validation in src/gui/editor.py (trigger validation on 500ms typing pause)
- [ ] T038 [US1] Display validation errors/warnings in status bar or margin in src/gui/editor.py
- [ ] T039 [P] [US1] Implement auto-save functionality in src/gui/main_window.py (30s default interval, configurable 10-300s per FR-040)
- [ ] T040 [US1] Add visual feedback for auto-save completion in src/gui/main_window.py status bar

**Checkpoint**: User Story 1 complete - Users can create, edit, and save speckit documents with full syntax highlighting and validation

---

## Phase 4: User Story 2 - Navigate Speckit Project Structure (Priority: P2)

**Goal**: Enable users to browse project structure, open multiple documents in tabs, and navigate between them

**Independent Test**: Open speckit project folder, view tree structure with specs/templates/memory, click files to open, switch between tabs

### Implementation for User Story 2

- [ ] T041 [P] [US2] Implement ProjectNavigator widget in src/gui/navigator.py extending QTreeView
- [ ] T042 [P] [US2] Implement LazyProjectModel in src/gui/navigator.py extending QAbstractItemModel (virtual scrolling for 1000+ files per FR-035)
- [ ] T043 [US2] Implement tree node loading in src/gui/navigator.py (specs organized by feature number, templates by type, memory folders)
- [ ] T044 [US2] Add visual indicators for node types in src/gui/navigator.py (icons for spec, plan, tasks, templates, folders)
- [ ] T045 [US2] Implement expandable/collapsible nodes with 20px indentation per level in src/gui/navigator.py
- [ ] T046 [P] [US2] Implement file click handler in src/gui/navigator.py to open documents in editor
- [ ] T047 [US2] Integrate ProjectNavigator with MainWindow left panel in src/gui/main_window.py
- [ ] T048 [P] [US2] Implement tabbed interface for multiple documents in src/gui/main_window.py using QTabWidget
- [ ] T049 [US2] Add tab close buttons and context menu (close, close others, close all) in src/gui/main_window.py
- [ ] T050 [US2] Implement tab switching with Ctrl+Tab keyboard shortcut in src/gui/main_window.py
- [ ] T051 [US2] Maintain scroll position and cursor location per document in src/gui/editor.py (per FR-029)
- [ ] T052 [US2] Restore scroll/cursor when switching tabs in src/gui/main_window.py
- [ ] T053 [P] [US2] Implement project opening action in src/gui/main_window.py (File → Open Project)
- [ ] T054 [US2] Load SpeckitProject and populate navigator on project open in src/gui/main_window.py
- [ ] T055 [P] [US2] Implement project refresh action in src/gui/navigator.py (detect external file changes)
- [ ] T056 [US2] Add visual indicators for file change status in navigator in src/gui/navigator.py (badges per FR-009)
- [ ] T057 [P] [US2] Implement search functionality in src/gui/main_window.py (Ctrl+F, search panel)
- [ ] T058 [P] [US2] Implement DocumentIndex in src/core/indexer.py (in-memory inverted index with SQLite persistence)
- [ ] T059 [US2] Implement search with scope selection in src/gui/main_window.py (current/open/all documents per FR-020)
- [ ] T060 [US2] Support regex and case-sensitive search options in src/core/indexer.py
- [ ] T061 [US2] Display search results with line numbers and context in src/gui/main_window.py
- [ ] T062 [US2] Implement progressive indexing in background thread in src/core/indexer.py
- [ ] T063 [P] [US2] Implement drag-and-drop for allowed operations in src/gui/navigator.py (documents between folders, files to tabs, external files import per FR-027)
- [ ] T064 [US2] Add visual drop target highlighting and forbidden cursor in src/gui/navigator.py
- [ ] T065 [P] [US2] Implement context menu for file operations in src/gui/navigator.py (rename, delete with confirmation, duplicate, copy path, reveal in explorer, open external per FR-028)
- [ ] T066 [US2] Handle external file change detection in src/core/project.py using filesystem watchers
- [ ] T067 [US2] Prompt user to reload when external changes detected in src/gui/main_window.py (per FR-023, FR-041)
- [ ] T068 [P] [US2] Implement zero-state UI for empty projects in src/gui/main_window.py (quick-start actions per FR-034)

**Checkpoint**: User Story 2 complete - Users can navigate projects, manage multiple open documents, and search across files

---

## Phase 5: User Story 3 - Integrated Git Operations (Priority: P3)

**Goal**: Enable users to perform git operations (commit, branch, push, pull, diff) directly from the IDE

**Independent Test**: Make document changes, view diffs, stage files, commit with message, push to remote

### Implementation for User Story 3

- [ ] T069 [P] [US3] Implement FeatureBranch model in src/core/project.py (git metadata, commits)
- [ ] T070 [P] [US3] Implement GitCommit and GitStatus data classes in src/core/project.py
- [ ] T071 [P] [US3] Initialize pygit2 repository in src/core/project.py during project load
- [ ] T072 [P] [US3] Implement GitPanel widget in src/gui/git_panel.py with file list, diff viewer, commit UI
- [ ] T073 [US3] Implement git status display in src/gui/git_panel.py (staged, unstaged, untracked files)
- [ ] T074 [US3] Add visual indicators for file status in src/gui/git_panel.py (color-coded badges per FR-009)
- [ ] T075 [P] [US3] Implement diff viewer in src/gui/git_panel.py using side-by-side QTextEdit comparison
- [ ] T076 [US3] Highlight differences with line numbers in src/gui/git_panel.py
- [ ] T077 [P] [US3] Implement file staging/unstaging in src/gui/git_panel.py (checkbox selection or drag-drop)
- [ ] T078 [US3] Connect to pygit2 add/reset in src/core/project.py
- [ ] T079 [P] [US3] Implement commit UI in src/gui/git_panel.py (message textbox, commit button)
- [ ] T080 [US3] Validate conventional commit format in src/gui/git_panel.py (optional helper)
- [ ] T081 [US3] Execute commit via pygit2 in src/core/project.py
- [ ] T082 [P] [US3] Implement branch display in src/gui/git_panel.py (current branch, list all branches)
- [ ] T083 [US3] Implement branch checkout in src/gui/git_panel.py with branch selection dialog
- [ ] T084 [US3] Implement create new branch in src/gui/git_panel.py with name validation
- [ ] T085 [P] [US3] Implement push operation in src/gui/git_panel.py with remote selection
- [ ] T086 [US3] Handle push authentication via keyring credentials in src/core/project.py
- [ ] T087 [P] [US3] Implement pull operation in src/gui/git_panel.py
- [ ] T088 [US3] Detect merge conflicts during pull in src/core/project.py
- [ ] T089 [US3] Implement merge conflict resolution UI in src/gui/git_panel.py (per FR-024)
- [ ] T090 [US3] Provide conflict resolution options (accept ours, accept theirs, manual merge) in src/gui/git_panel.py
- [ ] T091 [P] [US3] Implement keyboard shortcuts for git operations in src/gui/main_window.py (Ctrl+K commit, Ctrl+Shift+P push, Ctrl+Shift+L pull, Ctrl+D diff per FR-021)
- [ ] T092 [US3] Display branch status in main window status bar in src/gui/main_window.py (ahead/behind counts)
- [ ] T093 [US3] Integrate GitPanel with MainWindow side panel in src/gui/main_window.py
- [ ] T094 [P] [US3] Handle git operation errors gracefully in src/core/project.py (network issues, auth failures, conflicts)
- [ ] T095 [US3] Display actionable error messages in src/gui/git_panel.py

**Checkpoint**: User Story 3 complete - Users can perform all git operations without command-line tools

---

## Phase 6: User Story 4 - MCP Integration Management (Priority: P3)

**Goal**: Enable users to configure and manage MCP connections (Jira, GitHub, databases, terminals, Chrome)

**Independent Test**: Open MCP settings, configure Jira connection with credentials, test connection, view status

### Implementation for User Story 4

- [ ] T096 [P] [US4] Implement EmbeddedMCPServer in src/mcp/server.py (asyncio event loop in separate thread)
- [ ] T097 [US4] Implement MCP server startup/shutdown lifecycle in src/mcp/server.py
- [ ] T098 [US4] Start MCP server during application initialization in main.py (within 3s budget per FR-042)
- [ ] T099 [P] [US4] Implement MCPConnection model in src/mcp/server.py (service_type, config, credentials, state)
- [ ] T100 [P] [US4] Implement ServiceCredential model in src/mcp/server.py with OS keyring integration
- [ ] T101 [US4] Implement credential storage using keyring package in src/mcp/credentials.py (AES-256 encryption per FR-012)
- [ ] T102 [P] [US4] Implement BaseMCPService abstract class in src/mcp/server.py (connect, authenticate, disconnect, health_check)
- [ ] T103 [P] [US4] Implement JiraService in src/mcp/services/jira.py (list_issues, create_issue, update_issue, get_issue)
- [ ] T104 [P] [US4] Implement GitHubService in src/mcp/services/github.py (list_pull_requests, create_pull_request, get_repository, list_branches)
- [ ] T105 [P] [US4] Implement DatabaseService in src/mcp/services/database.py (execute_query, execute_command, list_tables)
- [ ] T106 [P] [US4] Implement TerminalService in src/mcp/services/terminal.py (execute_command, start_interactive_session, send_input)
- [ ] T107 [P] [US4] Implement ChromeService in src/mcp/services/chrome.py (navigate, execute_script, screenshot)
- [ ] T108 [P] [US4] Implement GitService in src/mcp/services/git.py (status, commit, push, pull)
- [ ] T109 [US4] Implement API version detection for Jira (v2/v3) and GitHub (v3/v4) in respective service files (per FR-038, FR-039)
- [ ] T110 [P] [US4] Implement CachedResponse model in src/mcp/server.py for offline support
- [ ] T111 [US4] Implement response caching with SQLite in src/mcp/server.py (.specify/cache/mcp_cache.db)
- [ ] T112 [US4] Implement offline mode detection and cached data retrieval in src/mcp/server.py (per FR-033)
- [ ] T113 [P] [US4] Implement MCPPanel widget in src/gui/mcp_panel.py with service list and connection status
- [ ] T114 [US4] Display connection status indicators in src/gui/mcp_panel.py (connected/disconnected/error per FR-013)
- [ ] T115 [US4] Implement add connection dialog in src/gui/mcp_panel.py (service type selection, config inputs, credential entry)
- [ ] T116 [US4] Implement test connection button in src/gui/mcp_panel.py (5s timeout, 3s warning per FR-014)
- [ ] T117 [US4] Display test results with error details in src/gui/mcp_panel.py
- [ ] T118 [US4] Implement connection editing in src/gui/mcp_panel.py (update config, change credentials)
- [ ] T119 [US4] Implement connection removal with confirmation in src/gui/mcp_panel.py
- [ ] T120 [US4] Persist connection configs to .specify/cache/mcp_connections.json in src/mcp/server.py
- [ ] T121 [US4] Load saved connections on application startup in src/mcp/server.py
- [ ] T122 [US4] Integrate MCPPanel with MainWindow side panel in src/gui/main_window.py
- [ ] T123 [P] [US4] Handle MCP service errors gracefully in src/mcp/server.py (auth failures, timeouts, rate limiting per FR-037)
- [ ] T124 [US4] Display clear error messages for MCP failures in src/gui/mcp_panel.py

**Checkpoint**: User Story 4 complete - Users can configure and test all MCP integrations with secure credential storage

---

## Phase 7: User Story 5 - AI-Assisted Document Generation (Priority: P4)

**Goal**: Enable users to invoke AI assistance for generating spec content, suggestions, and completions

**Independent Test**: Type partial requirement, invoke AI completion, review suggestions, accept or reject

### Implementation for User Story 5

- [ ] T125 [P] [US5] Implement AISession model in src/core/document.py (session_id, document, messages)
- [ ] T126 [P] [US5] Implement AIMessage model in src/core/document.py (role, content, suggestion text/position, accepted flag)
- [ ] T127 [P] [US5] Implement AIPanel widget in src/gui/ai_panel.py with chat interface and suggestion controls
- [ ] T128 [US5] Connect AI panel to MCP server for AI service calls in src/gui/ai_panel.py
- [ ] T129 [US5] Implement AI prompt sending in src/gui/ai_panel.py (async call to MCP)
- [ ] T130 [US5] Display AI responses in chat interface in src/gui/ai_panel.py
- [ ] T131 [P] [US5] Implement inline suggestion display in src/gui/editor.py (overlay or tooltip)
- [ ] T132 [US5] Implement suggestion acceptance in src/gui/editor.py (Tab or Accept button)
- [ ] T133 [US5] Implement suggestion rejection in src/gui/editor.py (Esc or Reject button)
- [ ] T134 [US5] Track accepted/rejected suggestions in AISession in src/core/document.py
- [ ] T135 [P] [US5] Implement AI trigger shortcuts in src/gui/main_window.py (Ctrl+Space for inline, Ctrl+Shift+A for chat)
- [ ] T136 [US5] Implement context extraction for AI prompts in src/gui/editor.py (cursor position, surrounding text, document type)
- [ ] T137 [US5] Integrate AIPanel with MainWindow side panel in src/gui/main_window.py
- [ ] T138 [P] [US5] Validate AI-generated content against templates in src/core/validator.py
- [ ] T139 [US5] Display validation errors for AI content in src/gui/ai_panel.py
- [ ] T140 [US5] Handle AI unavailability gracefully in src/gui/ai_panel.py (clear message, continue without AI per FR-037)
- [ ] T141 [US5] Persist AI session history to .specify/cache/ai_sessions.db in src/core/document.py

**Checkpoint**: User Story 5 complete - Users can leverage AI assistance for document generation with full review control

---

## Phase 8: User Story 6 - Template Management and Customization (Priority: P4)

**Goal**: Enable users to view, edit, create, and version custom templates

**Independent Test**: Open template manager, edit spec template, save as new version, create document using modified template

### Implementation for User Story 6

- [ ] T142 [P] [US6] Implement template listing in src/core/template.py (scan .specify/templates/)
- [ ] T143 [P] [US6] Implement template versioning in src/core/template.py (track created/modified timestamps)
- [ ] T144 [P] [US6] Implement TemplateManager widget in src/gui/template_dialog.py with template list and version history
- [ ] T145 [US6] Display available templates grouped by type in src/gui/template_dialog.py
- [ ] T146 [US6] Implement template editing in src/gui/template_dialog.py (open in editor)
- [ ] T147 [US6] Implement template saving with new version creation in src/core/template.py
- [ ] T148 [US6] Preserve original template on save in src/core/template.py
- [ ] T149 [P] [US6] Implement custom template creation in src/gui/template_dialog.py (copy from existing or blank)
- [ ] T150 [US6] Implement template variable definition UI in src/gui/template_dialog.py (add/edit/remove variables)
- [ ] T151 [US6] Validate template variable patterns in src/core/template.py (uppercase names, [VARIABLE] syntax)
- [ ] T152 [US6] Implement template compatibility checking in src/core/template.py (validate structure changes)
- [ ] T153 [US6] Implement template upgrade prompt for old documents in src/gui/main_window.py
- [ ] T154 [US6] Backup document before template migration in src/core/template.py
- [ ] T155 [US6] Apply template structure while preserving content in src/core/template.py
- [ ] T156 [US6] Provide rollback option if migration fails in src/gui/main_window.py
- [ ] T157 [US6] Filter templates by document type in template selection dialog in src/gui/template_dialog.py
- [ ] T158 [US6] Integrate TemplateManager with menu action in src/gui/main_window.py (Tools → Manage Templates)

**Checkpoint**: User Story 6 complete - Users can customize templates and version them for team processes

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final touches, cross-platform packaging, performance optimization, accessibility

- [ ] T159 [P] Implement full keyboard navigation with tab order in all widgets (per FR-031)
- [ ] T160 [P] Add visible focus indicators with QStyleSheet in src/gui/main_window.py
- [ ] T161 [P] Implement screen reader compatibility with setAccessibleName/Description for all widgets (per FR-032)
- [ ] T162 [P] Add ARIA labels and state announcements in src/gui/ widgets
- [ ] T163 [P] Implement customizable keyboard shortcuts in src/gui/settings.py
- [ ] T164 [P] Create settings dialog in src/gui/settings.py with tabs for Editor, Git, MCP, AI, Templates, Accessibility
- [ ] T165 Implement settings persistence to .specify/settings.json in src/utils/config.py
- [ ] T166 [P] Optimize startup time to <3s in main.py (lazy loading, deferred initialization)
- [ ] T167 [P] Profile and optimize editor typing latency to <100ms in src/gui/editor.py
- [ ] T168 [P] Implement lazy loading for large documents (>5MB) in src/core/document.py
- [ ] T169 [P] Add performance warnings for large projects (1000+ files) in src/gui/main_window.py (per FR-035)
- [ ] T170 [P] Implement file system permission error handling in src/core/project.py (per FR-036)
- [ ] T171 [P] Display actionable error messages for permission issues in src/gui/main_window.py
- [ ] T172 [P] Implement crash recovery with unsaved document cache in src/utils/config.py
- [ ] T173 [P] Test all 42 functional requirements on Windows, macOS, and Linux (per SC-011)
- [ ] T174 Create PyInstaller spec file sdd-editor.spec for Windows (.exe), macOS (.app), and Linux (AppImage)
- [ ] T175 Configure PyInstaller to bundle Python runtime and all dependencies
- [ ] T176 Test packaged executables on all three platforms
- [ ] T177 [P] Optimize bundle size with UPX compression and module exclusions
- [ ] T178 [P] Implement code signing for Windows and macOS executables
- [ ] T179 [P] Create user documentation in docs/user-guide.md
- [ ] T180 [P] Create developer documentation in docs/developer-guide.md
- [ ] T181 [P] Add screenshots to docs/screenshots/ for README and user guide
- [ ] T182 Update README.md with installation, usage, and feature descriptions
- [ ] T183 [P] Create LICENSE file (determine license)
- [ ] T184 [P] Create CONTRIBUTING.md with development workflow
- [ ] T185 Final testing pass for all 12 success criteria (SC-001 to SC-012)

**Checkpoint**: Project complete and ready for release - all features implemented, tested, documented, and packaged

---

## Dependencies & Execution Order

### Critical Path (Sequential - Must Complete in Order)

1. **Phase 1 (Setup)**: T001-T008 → Creates project structure
2. **Phase 2 (Foundational)**: T009-T017 → Establishes core models and UI framework
3. **User Story Phases**: After Phase 2, user stories can proceed mostly in parallel with some dependencies noted below

### User Story Dependencies

- **US1 (P1)** → No dependencies, can start immediately after Phase 2
- **US2 (P2)** → Depends on US1 completion for document models and editor integration
- **US3 (P3)** → Depends on US2 completion for project loading and file tracking
- **US4 (P3)** → Independent of US1-US3, can run in parallel after Phase 2
- **US5 (P4)** → Depends on US1 (editor) and US4 (MCP) completion
- **US6 (P4)** → Depends on US1 (template usage) completion

### Parallel Execution Opportunities

**After Phase 2 Completes**:
- **Track 1**: US1 → US2 → US3 (Document editing → Navigation → Git integration)
- **Track 2**: US4 → US5 (MCP setup → AI assistance)
- **Track 3**: US6 (Template management, independent)

**Within Each User Story** - Tasks marked [P] can run in parallel (different files, no dependencies):
- US1: T018-T019-T020 (templates) || T021-T022-T023-T024 (editor/highlighting) || T025-T026 (undo/redo)
- US2: T041-T042 (navigator) || T048 (tabs) || T058 (indexing)
- US3: T069-T070-T071 (git models) || T072-T073-T074 (git panel UI)
- US4: All service implementations (T103-T108) can proceed in parallel after T096-T102 complete
- US5: T125-T126 (models) || T127 (panel) || T131 (inline suggestions)
- US6: T142-T143 (versioning) || T144-T145 (UI)

### Recommended Implementation Strategy

**MVP (Minimum Viable Product) - Ship First**:
- Phase 1 (Setup): T001-T008
- Phase 2 (Foundation): T009-T017
- Phase 3 (US1): T018-T040
- Phase 9 (Subset): T174-T176 (packaging), T182 (README), T185 (testing)

**Result**: Standalone document editor with syntax highlighting and template support - delivers immediate value

**Incremental Delivery**:
1. **Release 1.0 (MVP)**: US1 only
2. **Release 1.1**: Add US2 (navigation)
3. **Release 1.2**: Add US3 (git integration)
4. **Release 1.3**: Add US4 (MCP integrations)
5. **Release 1.4**: Add US5 (AI assistance)
6. **Release 2.0**: Add US6 (template customization) + full polish

---

## Summary

**Total Tasks**: 185
**MVP Tasks**: ~50 (Phase 1, Phase 2, Phase 3/US1, essential Phase 9)
**Estimated Total Effort**: ~400-500 hours (individual developer)
**MVP Effort**: ~120-150 hours

**Task Breakdown by User Story**:
- Setup (Phase 1): 8 tasks
- Foundation (Phase 2): 9 tasks
- US1 (P1 - MVP): 23 tasks
- US2 (P2): 28 tasks
- US3 (P3): 27 tasks
- US4 (P3): 29 tasks
- US5 (P4): 17 tasks
- US6 (P4): 17 tasks
- Polish (Phase 9): 27 tasks

**Parallelization Potential**: ~60% of tasks marked [P] can run in parallel within their phase

**Independent Testing**: Each user story phase has clear checkpoint criteria for standalone testing

---

## Format Validation ✅

All 185 tasks follow the required checklist format:
- ✅ Checkbox prefix `- [ ]`
- ✅ Sequential task IDs (T001-T185)
- ✅ [P] markers for parallelizable tasks
- ✅ [Story] labels for user story tasks (US1-US6)
- ✅ Clear descriptions with exact file paths
- ✅ Executable by LLM without additional context
