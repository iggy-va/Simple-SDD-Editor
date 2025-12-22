# Simple SDD Editor

A self-contained, cross-platform IDE for creating and managing Software Design Documents using the Speckit methodology.

## Project Status

**Current Version**: 0.2.0-alpha  
**Test Coverage**: 87% (117 passing tests)  
**MVP Status**: User Story 1 (P1) - ✅ Complete

### Implemented Features
- ✅ **US1 (P1)**: Create and edit specifications with auto-completion, validation, and templates
- ⏳ **US2 (P2)**: Project navigation (in development)  
- ⏳ **US3 (P3)**: Git integration (planned)
- ⏳ **US4 (P3)**: MCP integrations (planned)
- ⏳ **US5 (P4)**: AI assistance (planned)

## Project Description

Simple SDD Editor is a Python-based desktop application that provides an integrated environment for specification-driven development. It combines document editing, project management, version control, and AI assistance into a single, portable tool that runs identically on Windows, macOS, and Linux.

### Key Capabilities

- **Document-First Development**: Create specifications, plans, and task lists using structured templates
- **Built-in MCP Server**: Integrate with Jira, GitHub, databases, terminals, and Chrome without external tools
- **Git Integration**: Version control operations directly in the IDE
- **AI-Assisted Writing**: GitHub Copilot integration for generating and refining documentation
- **Zero External Dependencies**: Self-contained with automatic dependency management

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git installed and configured

### Installation

```bash
# Clone the repository
git clone https://github.com/iggy-va/Simple-SDD-Editor.git
cd Simple-SDD-Editor

# The editor manages its own dependencies
python src/main.py
```

### Starting a New Project

1. Launch the Simple SDD Editor
2. Select **File > New Speckit Project**
3. Choose a project directory
4. The editor creates the `.specify` structure with templates and scripts
5. Use **File > New Specification** to create your first feature spec

## Feature Guide

### Feature 1: Create and Edit Specification Documents (P1 - MVP) ✅ IMPLEMENTED

#### Status: Complete
- Auto-completion (Ctrl+Space for headings, IDs, keywords, variables)
- Real-time validation with visual feedback (squiggly underlines)
- Template-based document creation (spec, plan, tasks, checklist)
- File operations (New, Open, Save, Save All)
- Auto-save every 30 seconds with status feedback
- Syntax highlighting for Markdown + Speckit extensions

#### How It Works

The editor provides a rich text interface for creating and editing markdown documents that follow speckit templates. It automatically:
- Loads template structure with required sections (FR-017, FR-018)
- Provides 40+ auto-completions via Ctrl+Space (FR-001)
  - Section headings (## Summary, ## Technical Context, etc.)
  - Requirement IDs (FR-001, SC-001, NFR-001)
  - BDD keywords (**Given**, **When**, **Then**)
  - Template variables ([FEATURE_NAME], [DATE], [AUTHOR])
- Validates content in real-time with 500ms debounce (FR-026)
  - Red squiggly underlines for errors
  - Yellow squiggly underlines for warnings
  - Status bar shows validation summary
- Supports both [VARIABLE] and {{variable}} template formats
- Highlights syntax elements:
  - Headers with appropriate sizing
  - Requirement IDs in bold cyan
  - Priority markers (P1-P4) in red
  - Code blocks and inline code
  - BDD keywords in purple
- Provides syntax highlighting for markdown
- Validates document structure in real-time
- Tracks unsaved changes
- Auto-saves at configurable intervals

#### Example 1: Creating a New Specification (Success)

```
1. Click File → New Document (Ctrl+N)
2. Template dialog shows: spec, plan, tasks, checklist
3. Select "spec" template
4. Enter variables:
   - Feature Name: "User Authentication"
   - Feature ID: "002"
   - Author: (auto-filled from git config)
5. Click OK
6. Editor opens with template:
   - Syntax highlighting active (headers in blue, FR-IDs in cyan)
   - Auto-completion ready (Ctrl+Space)
7. Type "## R" → Press Ctrl+Space → Select "## Requirements"
8. Type "FR-" → Auto-complete suggests FR-001, FR-002...
9. Validation runs after 500ms typing pause
10. Status bar: "✓ Valid"
11. Press Ctrl+S → File saved to specs/002-user-auth/spec.md
```

**Result**: ✅ New specification created with auto-completion and validation

#### Example 2: Real-Time Validation (Success)

```
1. Open specs/001-speckit-editor-ide/spec.md
2. Scroll to line 45, type "FR-999" (invalid sequencing)
3. After 500ms pause:
   - Red squiggly underline appears under "FR-999"
   - Status bar: "✗ 1 errors, 0 warnings"
4. Correct to "FR-043"
5. Squiggly disappears
6. Status bar: "✓ Valid"
7. Tab shows "*" for unsaved changes
8. Auto-save triggers after 30s → "*" clears
9. Status bar: "Auto-saved 1 document(s)"
```

**Result**: ✅ Validation catches errors, auto-save works seamlessly

#### Example 3: Invalid Template Structure (Failure)

```
1. Edit spec.md externally, delete "## Requirements"
2. Return to IDE, file watcher detects change
3. Prompt: "File changed externally. Reload?"
4. Click "Reload"
5. Validation runs:
   - Red squiggly under entire affected section
   - Status bar: "✗ 1 errors, 0 warnings"
6. Hover over error or check validation message:
   - "Missing mandatory section: Requirements"
```

**Result**: ❌ Document fails validation
**Why It Fails**: Speckit spec template requires "Requirements" section. Editor detects violation and highlights the issue for correction.

---

### Feature 2: Navigate Speckit Project Structure (P2)

#### How It Works

The IDE displays your project in a hierarchical tree view showing:
- `.specify/` - Templates and configuration
- `specs/` - All feature specifications organized by number
- Each spec folder contains: `spec.md`, `plan.md`, `tasks.md`, checklists
- Multiple tabs allow switching between open documents

#### Example 1: Browsing Project Structure (Success)

```
1. Open a speckit project folder
2. Project Tree displays:
   └── specs/
       ├── 001-speckit-editor-ide/
       │   ├── spec.md
       │   └── checklists/requirements.md
       └── 002-user-auth/
           └── spec.md
3. Click on 001-speckit-editor-ide/spec.md
4. Document opens in editor tab
```

**Result**: ✅ Full project structure visible, documents open correctly

#### Example 2: Multi-Document Navigation (Success)

```
1. Open specs/001-speckit-editor-ide/spec.md (Tab 1)
2. Open specs/002-user-auth/spec.md (Tab 2)
3. Scroll to line 50 in Tab 1
4. Switch to Tab 2, scroll to line 30
5. Switch back to Tab 1
6. Editor automatically scrolls to line 50 (preserved position)
```

**Result**: ✅ Scroll positions and state preserved across tab switches

#### Example 3: Missing Specs Directory (Failure)

```
1. Select "Open Speckit Project"
2. Choose a directory without .specify/ folder
3. Project tree attempts to load
4. Error displayed: "Not a valid speckit project"
5. Help message: "Initialize with: /speckit.specify or create .specify/ manually"
```

**Result**: ❌ Project fails to load
**Why It Fails**: The editor requires `.specify/` structure with templates and scripts. A directory without this structure isn't recognized as a speckit project. User must initialize the project properly first.

---

### Feature 3: Integrated Git Operations (P3)

#### How It Works

The Source Control panel shows:
- Modified, staged, and untracked files
- Current branch and commit history
- Visual diff viewer for changes
- Commit, push, pull, merge operations
- Branch creation and switching

#### Example 1: Committing Changes (Success)

```
1. Edit specs/001-speckit-editor-ide/spec.md
2. Save file
3. Open Source Control panel
4. See "spec.md" listed under "Changes"
5. Click checkbox to stage
6. Enter commit message: "feat(001): add edge cases"
7. Click Commit
8. File moves to commit history
```

**Result**: ✅ Changes committed to current branch

#### Example 2: Viewing Diff Before Commit (Success)

```
1. Modify spec.md by adding a new requirement
2. In Source Control, click "Show Diff" next to spec.md
3. Split view shows:
   - Left: Original with "FR-030"
   - Right: Modified with "FR-030" and "FR-031" (new)
   - Additions highlighted in green
4. Review changes
5. Stage and commit
```

**Result**: ✅ Visual diff helps review changes before committing

#### Example 3: Push Without Remote Configured (Failure)

```
1. Initialize a new speckit project locally
2. Create and commit a spec.md
3. Click "Push" in Source Control panel
4. Error: "No remote repository configured"
5. Instructions shown: "Add remote with: git remote add origin <url>"
```

**Result**: ❌ Push operation fails
**Why It Fails**: Git requires a remote repository URL to push to. A newly initialized local repository has no remote configured. User must add origin URL first using git config or the editor's remote management settings.

---

### Feature 4: MCP Integration Management (P3)

#### How It Works

MCP (Model Context Protocol) Settings allow connecting to:
- **Jira**: Fetch issues, update status, link to specs
- **GitHub**: View PRs, issues, workflows
- **Databases**: Query schemas, run read-only queries
- **Terminals**: Execute commands, capture output
- **Chrome**: Automate browser testing, screenshots

Credentials are stored securely in OS keyring (Windows Credential Manager, macOS Keychain, Linux Secret Service).

#### Example 1: Configuring Jira Integration (Success)

```
1. Open Settings > MCP Integrations
2. Select "Jira"
3. Enter:
   - URL: https://yourcompany.atlassian.net
   - Email: user@company.com
   - API Token: [from Jira API tokens page]
4. Click "Test Connection"
5. Success message: "Connected to Jira (23 projects found)"
6. Click Save
7. Credentials stored in Windows Credential Manager
```

**Result**: ✅ Jira connected, credentials secured

#### Example 2: Linking GitHub Issues in Spec (Success)

```
1. Configure GitHub integration with personal access token
2. Open spec.md
3. Type: "Implements #42" in a requirement
4. GitHub integration detects issue reference
5. Hover over "#42" shows tooltip:
   - Issue title
   - Status: Open
   - Assigned to: iggy-va
6. Click opens issue in browser
```

**Result**: ✅ Live GitHub issue data embedded in documentation

#### Example 3: Expired API Token (Failure)

```
1. Jira integration previously configured
2. API token expires after 90 days
3. Open spec with Jira issue reference
4. Editor attempts to fetch issue data
5. Error notification: "Jira authentication failed"
6. Prompt: "Re-authenticate to continue"
7. MCP status shows: Jira (Disconnected - Auth Required)
```

**Result**: ❌ Integration fails to fetch data
**Why It Fails**: API tokens have expiration dates for security. When expired, the integration loses access. User must generate a new token and update credentials. The editor detects this gracefully and prompts for re-auth instead of silently failing.

---

### Feature 5: AI-Assisted Document Generation (P4)

#### How It Works

GitHub Copilot integration provides:
- Context-aware suggestions as you type
- Generate complete sections from brief prompts
- Suggest acceptance criteria from requirements
- Auto-complete Given/When/Then scenarios
- All suggestions require user review and approval

#### Example 1: Generating Acceptance Criteria (Success)

```
1. In spec.md, write requirement:
   "FR-015: System MUST validate email format"
2. Move to Acceptance Scenarios section
3. Press Ctrl+Space to invoke AI
4. AI suggests:
   Given: User enters "invalid-email"
   When: Form is submitted
   Then: Error shown "Invalid email format"
5. Review, accept suggestion
6. Criteria added to document
```

**Result**: ✅ Valid acceptance scenario generated from requirement

#### Example 2: Completing User Story (Success)

```
1. Type: "### User Story 5 - Password Reset"
2. AI suggests complete story structure:
   - Description of password reset flow
   - Why this priority: P2 reasoning
   - 4 acceptance scenarios covering happy/error paths
3. Review suggestions
4. Modify priority from P2 to P3
5. Accept modified version
```

**Result**: ✅ Comprehensive user story created with human oversight

#### Example 3: AI Generates Invalid Structure (Failure)

```
1. Ask AI to generate a user story
2. AI provides story without priority marker
3. Try to save document
4. Validation error: "User Story 3 missing required (Priority: PX) marker"
5. AI suggestion not automatically applied
6. User must fix structure or regenerate
```

**Result**: ❌ Invalid structure rejected
**Why It Fails**: AI suggestions are not guaranteed to follow template structure perfectly. The editor's validation layer catches format violations before they're saved. This prevents malformed documents from being committed. User must review and correct AI output to match template requirements.

---

### Feature 6: Template Management and Customization (P4)

#### How It Works

Template Manager allows viewing and editing:
- `spec-template.md` - Feature specifications
- `plan-template.md` - Technical design plans
- `tasks-template.md` - Implementation task lists
- `checklist-template.md` - Quality checklists

Changes create new template versions. Existing documents can be upgraded to new versions while preserving content.

#### Example 1: Editing Spec Template (Success)

```
1. Open Template Manager
2. Select "spec-template.md" (version 1.0)
3. Add new section: "## Security Considerations"
4. Save as version 1.1
5. Create new spec using File > New Specification
6. New spec includes "Security Considerations" section
7. Old specs still use version 1.0 until upgraded
```

**Result**: ✅ Template versioning preserves backward compatibility

#### Example 2: Upgrading Document to New Template (Success)

```
1. Open old spec created with template v1.0
2. Notification bar: "Template v1.2 available"
3. Click "Show Changes"
4. Diff shows: v1.2 adds "## Dependencies" section
5. Click "Upgrade"
6. Editor merges new sections, preserves existing content
7. Document now uses v1.2 structure
```

**Result**: ✅ Seamless upgrade with content preservation

#### Example 3: Removing Mandatory Section from Template (Failure)

```
1. Open Template Manager
2. Edit spec-template.md
3. Delete "## Requirements *(mandatory)*" section
4. Try to save
5. Error: "Cannot remove mandatory sections"
6. List shown: User Scenarios, Requirements, Success Criteria
7. Save blocked, template unchanged
```

**Result**: ❌ Template modification rejected
**Why It Fails**: Speckit enforces mandatory sections to ensure all specifications meet minimum quality standards. Removing "Requirements" would allow incomplete specs to be created. The editor protects template integrity by preventing deletion of mandatory sections, ensuring consistency across all documentation.

---

## Project Status

**Current Phase**: Implementation In Progress - Phase 2 Foundation Complete

- ✅ Constitution v1.1.0 ratified (standalone executable requirement)
- ✅ Feature 001 specification completed (42 requirements, 12 success criteria)
- ✅ Requirements quality validated (88-item checklist, 78% complete)
- ✅ Implementation plan completed (research, data model, contracts, quickstart)
- ✅ Task breakdown completed (185 tasks organized by 6 user stories)
- ✅ **Phase 1 Setup complete** (T001-T008: project structure, dependencies, configuration)
- ✅ **Phase 2 Foundation complete** (T009-T017: core models, parser, validator, GUI foundation)
  - Core business logic: SpeckitProject, SpeckitDocument, FeatureBranch
  - Document parsing: Sections, Requirements, frontmatter
  - Validation: DocumentValidator, ProjectValidator with error/warning tracking
  - Search: DocumentIndex with inverted index and requirement lookup
  - Git integration: Repository detection, branch scanning, timestamp extraction
  - GUI: MainWindow with menus, tabs, status bar, PySide6 styling
  - Tests: 128 tests (117 unit + 11 integration) with 91% coverage
  - Coverage by module: project 92%, document 91%, search 90%, validator 90%, config 100%, logging 100%
- 🔄 Next: Phase 3 (US1 - Document Editing MVP)

## Contributing

This project follows the Speckit methodology. All features begin as specifications and follow the workflow:
1. `/speckit.specify` - Define feature requirements
2. `/speckit.clarify` - Resolve ambiguities
3. `/speckit.plan` - Create technical design
4. `/speckit.tasks` - Break down implementation
5. `/speckit.implement` - Build with guidance

## License

[To be determined]

## Links

- [Constitution](.specify/memory/constitution.md) - Project principles and technical constraints
- [Feature 001 Specification](specs/001-speckit-editor-ide/spec.md) - Requirements and success criteria
- [Feature 001 Plan](specs/001-speckit-editor-ide/plan.md) - Implementation plan and architecture
- [Feature 001 Tasks](specs/001-speckit-editor-ide/tasks.md) - Implementation task breakdown (185 tasks, 6 user stories)
- [Research](specs/001-speckit-editor-ide/research.md) - Technology decisions
- [Data Model](specs/001-speckit-editor-ide/data-model.md) - Domain entities
- [Quickstart](specs/001-speckit-editor-ide/quickstart.md) - Developer onboarding
- GitHub: https://github.com/iggy-va/Simple-SDD-Editor
