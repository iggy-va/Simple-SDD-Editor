# User Guide - Speckit Document Editor/IDE

**Version**: 1.0.0 | **Last Updated**: 2025-12-23

Welcome to the Speckit Editor - your complete IDE for creating, editing, and managing speckit documentation with AI assistance, git integration, and MCP service connectivity.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Creating and Editing Documents](#creating-and-editing-documents)
3. [Git Integration](#git-integration)
4. [MCP Service Integrations](#mcp-service-integrations)
5. [AI Assistant](#ai-assistant)
6. [Custom Templates](#custom-templates)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Installation

1. Download the Speckit Editor executable for your platform:
   - **Windows**: `Speckit Editor.exe`
   - **macOS**: `Speckit Editor.app`
   - **Linux**: `speckit-editor`

2. Run the application:
   - **Windows**: Double-click `Speckit Editor.exe`
   - **macOS**: Open `Speckit Editor.app`
   - **Linux**: `./speckit-editor` from terminal

No installation or external dependencies required - everything is bundled.

### First Launch

On first launch, the editor will:
1. Create a `.specify/` folder in your home directory for templates and settings
2. Initialize default templates (spec, plan, tasks, checklist)
3. Open with a welcome screen

### Opening a Project

**File → Open Project** (Ctrl+O)
- Navigate to a folder containing speckit documents (`.md` files)
- The editor will index all documents and display them in the file navigator

**Recent Projects**
- **File → Recent Projects** shows your 10 most recently opened projects
- Click to quickly reopen

---

## Creating and Editing Documents

### Opening and Navigating Projects

**Opening a Project**:

**File → Open Project** (Ctrl+O)
1. Browse to a folder containing speckit documents
2. The editor scans the folder for `.md` files
3. File navigator populates with your project structure
4. Recent files list shows your 10 most recently edited documents

**Project Structure**:

The file navigator (left sidebar) shows your project's folder hierarchy:

```text
my-feature-project/
├── specs/
│   ├── 001-auth/
│   │   ├── spec.md
│   │   ├── plan.md
│   │   └── tasks.md
│   └── 002-reporting/
│       ├── spec.md
│       └── plan.md
├── .specify/
│   ├── templates/
│   └── settings.json
└── README.md
```

**Navigation Features**:
- **Expand/Collapse folders**: Click arrow icon
- **Double-click file**: Opens in editor
- **Right-click file**: Context menu (rename, delete, duplicate, copy path, reveal in explorer)
- **Drag files** (optional): Move documents between folders
- **Search box**: Filter files by name (Ctrl+Shift+F)

### Using the File Navigator

**File Navigator Panel** (View → File Navigator or Ctrl+B)

**Opening Files**:
- **Double-click**: Open in new tab
- **Middle-click**: Open in background tab
- **Ctrl+Click**: Open in new split editor

**File Icons**:
- 📄 **Spec documents** (spec.md): Blue document icon
- 📋 **Plan documents** (plan.md): Orange document icon
- ✅ **Task documents** (tasks.md): Green checklist icon
- 📝 **Other markdown** (*.md): Gray document icon
- 📁 **Folders**: Yellow folder icon

**Context Menu** (right-click file):
- **Rename** (F2): Rename file (updates git status)
- **Delete** (Delete): Move to trash with confirmation
- **Duplicate**: Create copy with "- Copy" suffix
- **Copy Path**: Copy absolute path to clipboard
- **Copy Relative Path**: Copy workspace-relative path
- **Reveal in Explorer**: Open folder in OS file manager
- **Open External**: Open in default markdown editor

**File Status Indicators**:
- **● Green**: File has unsaved changes
- **M Orange**: Modified (git tracked)
- **A Green**: Added (git untracked)
- **D Red**: Deleted (git removed)
- **C Blue**: Conflicted (merge conflict)

### Managing Multiple Documents

**Tabbed Interface**:

All open documents appear as **tabs** at the top of the editor:

```text
[spec.md *] [plan.md] [tasks.md] [X]
```

**Tab Operations**:
- **Click tab**: Switch to that document
- **Middle-click tab**: Close tab
- **Ctrl+W**: Close active tab
- **Ctrl+Tab**: Next tab
- **Ctrl+Shift+Tab**: Previous tab
- **Ctrl+1 through Ctrl+9**: Jump to tab 1-9

**Tab Indicators**:
- **Asterisk** (`*`): Unsaved changes
- **Close icon** (X): Close tab (prompts if unsaved)

**Split Editors**:

View multiple documents side-by-side:

1. **View → Split Editor → Horizontal** (Ctrl+\\)
2. **View → Split Editor → Vertical** (Ctrl+Shift+\\)
3. Open different files in each split
4. Resize splits by dragging divider

**Use Cases for Splits**:
- View spec.md and tasks.md simultaneously
- Reference plan.md while editing spec.md
- Compare two versions of a document

**Close Split**: **View → Close Split** or drag divider to edge

### Searching Across Project

**Project-Wide Search** (Ctrl+Shift+F)

**Search Panel** (View → Search) allows searching across all project documents:

**1. Basic Search**:
- Enter search term: `authentication`
- Results show all matches across all files:
  ```text
  spec.md (5 matches)
    Line 42: ## User Authentication
    Line 87: FR-001: The system SHALL provide authentication
  
  plan.md (2 matches)
    Line 15: Authentication will use bcrypt
  ```

**2. Search Options**:
- **Match Case** (Aa): Case-sensitive search
- **Whole Word** (Ab|): Match complete words only
- **Regex** (.*): Use regular expressions

**Example Regex Search**:
- Pattern: `FR-\d{3}`
- Finds: FR-001, FR-042, FR-123 (all requirement IDs)

**3. Search and Replace**:
- Click **Replace** tab
- Enter find: `bcrypt`
- Enter replace: `argon2`
- **Replace**: Replace current match
- **Replace All**: Replace all matches across project (with confirmation)

**4. Search Filters**:
- **Files to include**: `specs/**/*.md` (only files in specs/ folder)
- **Files to exclude**: `**/drafts/**` (ignore drafts folder)

**5. Navigate Results**:
- Click result → jumps to that line in editor
- **Next Result** (F4): Jump to next match
- **Previous Result** (Shift+F4): Jump to previous match

**Quick Find in File** (Ctrl+F):

Search only the current document:
- Enter search term
- Press **Enter** to find next
- Press **Shift+Enter** to find previous
- **Esc** to close find bar

### Creating Documents from Templates

**File → New Document** (Ctrl+N)

1. The **Template Selection** dialog opens
2. Choose a template type:
   - **Specification** (`spec.md`) - Feature specifications with user stories, requirements, success criteria
   - **Implementation Plan** (`plan.md`) - Technical design, architecture, project structure
   - **Task Breakdown** (`tasks.md`) - Granular implementation tasks with dependencies
   - **Checklist** (`checklist.md`) - Simple checklists for workflows

3. Fill in template variables:
   - **Feature Name**: Name of the feature (e.g., "User Authentication")
   - **Branch Name**: Git branch for implementation (e.g., "001-user-auth")
   - **Date**: Today's date (auto-filled)
   - **Additional variables** depending on template

4. Click **Create** to instantiate the document

The editor creates a new document with the template content, variables substituted, and opens it in the editor.

### Editing with Syntax Highlighting

The editor provides **real-time syntax highlighting** for speckit markdown:

**Highlighted Elements**:
- **Headers** (`# Level 1`, `## Level 2`): Bold, blue (`#0066cc`)
- **Requirement IDs** (`FR-001`, `SC-005`, `TSK-042`): Bold, green (`#00aa00`)
- **Priority Markers** (`[P1]`, `[P2]`, `[P3]`): Orange (`#ff6600`)
- **Code Blocks** (```python): Monospace font, gray background
- **Gherkin Keywords** (`Given`, `When`, `Then`, `And`): Purple (`#9933cc`)
- **Task Checkboxes** (`- [ ]`, `- [x]`): Styled for readability

**Example**:
```markdown
# User Stories

## [P1] User Story 1: Create Account

**FR-001**: The system SHALL provide a registration form with email and password

**Acceptance Criteria**:

Given I am on the registration page
When I enter valid email and password
Then my account is created and I am logged in

- [x] Task 1: Implement registration form
- [ ] Task 2: Add email validation
```

All highlighted elements update **instantly as you type** with < 100ms latency.

### Understanding Validation Errors

The editor validates your document structure in real-time:

**Validation Rules**:
- **Spec documents**: Must contain "User Stories", "Functional Requirements", "Success Criteria" sections
- **Plan documents**: Must contain "Technology Stack", "Project Structure" sections  
- **Tasks documents**: Must have properly formatted task IDs (`T001`, `TSK-001`) and checkboxes (`- [ ]`)
- **Requirement IDs**: Must match patterns (`FR-NNN`, `SC-NNN`, `T-NNN`)
- **Template Variables**: All `${variable}` placeholders must be filled

**Validation Display**:
- **Green checkmark** (✅): Document is valid
- **Red error icon** (❌): Errors found (hover to see details)
- **Orange warning icon** (⚠️): Warnings found (non-blocking)

**Example Errors**:
```text
❌ Error (Line 15): Missing required section "Functional Requirements"
⚠️ Warning (Line 42): Requirement ID "REQ-001" should use format "FR-001"
💡 Suggestion: Add "Success Criteria" section after requirements
```

Click on an error to jump to the relevant line in the document.

### Saving and File Operations

**Save Document** (Ctrl+S)
- Saves the currently active document to disk
- Updates the file modification timestamp
- Removes the unsaved indicator (`*`) from the tab title

**Save All Documents** (Ctrl+Shift+S)
- Saves all open documents with unsaved changes
- Useful before committing to git

**Unsaved Changes Indicator**:
- Tabs with unsaved changes show an asterisk: `spec.md *`
- Closing a tab with unsaved changes prompts: "Save changes to spec.md?"

**File → Save As** (Ctrl+Shift+S)
- Save the current document with a new filename
- Useful for creating document variants

**Auto-Save**:
- Enabled by default (every 2 minutes)
- Configure in **Edit → Preferences → Editor → Auto-save interval**

---

## Git Integration

The Speckit Editor has **built-in git integration** - no need to switch to the command line for commits, branching, push/pull, or viewing diffs.

### Git Operations Overview

All git operations are accessible from the **Git Panel** (View → Git Panel or Ctrl+G).

**Supported Operations**:
- View changed files (staged, unstaged, untracked)
- View diffs for modified files
- Stage/unstage files
- Commit changes with messages
- Create and switch branches
- Push to remote
- Pull from remote
- View commit history
- Resolve merge conflicts (visual conflict editor)

### Committing Changes

**1. View Changed Files**

The Git Panel shows all changes in your project:
- **Unstaged Changes** (red): Files modified but not staged for commit
- **Staged Changes** (green): Files ready to be committed
- **Untracked Files** (gray): New files not yet tracked by git

**2. Stage Files**

**Option A: Stage individual files**
- Right-click file → **Stage File**
- Or click the **+** icon next to the filename

**Option B: Stage all changes**
- Click **Stage All** button at the top of the Git Panel

**3. Write Commit Message**

- Enter commit message in the text box at the top
- **Best Practice**: Use conventional commit format:
  - `feat: Add user authentication`
  - `fix: Resolve template variable substitution bug`
  - `docs: Update user guide with git integration`

**Optional**: Enable **Conventional Commits Validation** in settings to enforce this format.

**4. Commit**

- Click **Commit** button (or Ctrl+K)
- If commit message is empty, you'll be prompted to enter one
- Committed changes disappear from the changed files list

**Example Workflow**:
```text
1. Edit spec.md (appears in Unstaged Changes)
2. Click + next to spec.md (moves to Staged Changes)
3. Enter message: "feat: Add authentication requirements"
4. Click Commit
5. Changes are committed to current branch
```

### Branch Management

**Create New Branch**

1. Git Panel → **Branches** dropdown
2. Click **New Branch**
3. Enter branch name (e.g., `feature/user-auth`)
4. Branch is created and checked out automatically

**Switch Branches**

1. Git Panel → **Branches** dropdown
2. Select branch name from list
3. Editor switches to that branch (open documents reload)

**View Current Branch**

- Current branch shown in Git Panel header: `On branch: main`
- Status bar (bottom right) also shows current branch

### Push/Pull Operations

**Push to Remote** (Ctrl+Shift+K)

1. Git Panel → **Push** button
2. If remote requires authentication, credential dialog appears
3. Progress indicator shows upload status
4. Success notification: "Pushed 3 commits to origin/main"

**Pull from Remote** (Ctrl+Shift+P)

1. Git Panel → **Pull** button
2. If remote has new commits, they're downloaded and merged
3. If conflicts exist, the conflict resolver opens automatically

**Authentication**:
- Credentials stored securely in OS keyring
- SSH keys supported (reads from `~/.ssh/id_rsa` by default)
- Personal access tokens supported for GitHub/GitLab

### Viewing Diffs

**Diff Panel** shows line-by-line changes for the selected file:

1. Click any file in the changed files list
2. Diff appears in the right pane:
   - **Red lines** (with `-`): Removed lines
   - **Green lines** (with `+`): Added lines
   - **Gray lines**: Unchanged context

**Example Diff**:
```diff
  # User Stories
  
- ## User Story 1: Login
+ ## User Story 1: User Authentication
+ 
+ **FR-001**: The system SHALL provide a login form
  
  Given I am on the login page
```

**Navigation**:
- Click line numbers to jump to that line in the editor
- Use **Previous/Next Change** buttons to navigate between hunks

### Resolving Merge Conflicts

When a pull or merge creates conflicts, the **Conflict Resolver** opens automatically.

**Conflict Markers**:
```text
<<<<<<< HEAD (your changes)
FR-001: The system SHALL use bcrypt for password hashing
=======
FR-001: The system SHALL use argon2 for password hashing
>>>>>>> origin/main (incoming changes)
```

**Resolution Options**:
1. **Accept Yours**: Keep your version (local changes)
2. **Accept Theirs**: Use incoming version (remote changes)
3. **Accept Both**: Include both versions (manually edit afterward)
4. **Edit Manually**: Remove markers and write custom resolution

**Steps**:
1. Review conflicted sections (highlighted in yellow)
2. Click **Accept Yours**, **Accept Theirs**, or **Accept Both** for each conflict
3. OR manually edit the file to resolve
4. Click **Mark as Resolved**
5. Stage and commit the resolved file

**Example Resolution**:
```text
Original conflict:
<<<<<<< HEAD
FR-001: The system SHALL use bcrypt
=======
FR-001: The system SHALL use argon2
>>>>>>> origin/main

After choosing "Accept Both" and manual edit:
FR-001: The system SHALL use bcrypt or argon2 for password hashing
```

---

## MCP Service Integrations

The Speckit Editor includes **Model Context Protocol (MCP)** integrations for connecting to external services like Jira, GitHub, databases, terminals, and Chrome DevTools - all from within the editor.

### MCP Integrations Overview

**Supported Services**:
- **Jira**: Fetch issues, create tickets, update status
- **GitHub**: Search repos, create issues, view pull requests
- **Git**: Repository operations (commits, branches, push/pull)
- **Databases**: Query MySQL, PostgreSQL, SQLite
- **Terminal**: Execute shell commands
- **Chrome DevTools**: Inspect browser state, execute JavaScript

All integrations are **optional** - enable only what you need.

### Configuring Service Connections

**Open MCP Panel**: View → MCP Panel (or Ctrl+M)

**1. Add a New Connection**

Click **Add Connection** → Select service type:

**For Jira**:
- **Service Type**: Jira
- **Display Name**: "My Company Jira"
- **Server URL**: `https://yourcompany.atlassian.net`
- **Credentials**:
  - **Email**: your.email@company.com
  - **API Token**: Generate at https://id.atlassian.com/manage-profile/security/api-tokens
- Click **Test Connection** to verify
- Click **Save**

**For GitHub**:
- **Service Type**: GitHub
- **Display Name**: "GitHub Projects"
- **Credentials**:
  - **Personal Access Token**: Generate at https://github.com/settings/tokens
  - **Required Scopes**: `repo`, `read:user`
- Click **Test Connection**
- Click **Save**

**For Databases**:
- **Service Type**: Database (MySQL/PostgreSQL/SQLite)
- **Display Name**: "Dev Database"
- **Connection String**:
  - MySQL: `mysql://user:password@localhost:3306/dbname`
  - PostgreSQL: `postgresql://user:password@localhost:5432/dbname`
  - SQLite: `sqlite:///path/to/database.db`
- Click **Test Connection**
- Click **Save**

**2. Edit Existing Connection**

- Right-click connection → **Edit**
- Modify settings
- Click **Save**

**3. Delete Connection**

- Right-click connection → **Delete**
- Confirm deletion

### Managing Credentials Securely

**How Credentials Are Stored**:
- All credentials encrypted with **AES-256**
- Stored in your **OS keyring**:
  - **Windows**: Windows Credential Manager
  - **macOS**: Keychain
  - **Linux**: Secret Service (GNOME Keyring, KWallet)

**You control the data**:
- Credentials never sent to Speckit servers (no servers exist)
- API calls go directly from your machine to the service
- Offline mode uses cached data only (no network requests)

**Credential Management**:
- **Update Password**: MCP Panel → Right-click connection → **Update Credentials**
- **View Stored Credentials**: Not possible (encrypted, view-only via OS keyring tools)
- **Delete Credentials**: Delete the connection or use OS keyring manager

### Testing Connections

**Test Connection Button**:
- Verifies credentials are valid
- Checks network connectivity to service
- Returns detailed error if connection fails

**Example Test Results**:
```text
✅ Connection successful (142ms)
   - Authenticated as: user@company.com
   - API version: 8.20.0

❌ Connection failed: Invalid credentials
   - HTTP 401 Unauthorized
   - Verify API token is correct

❌ Connection failed: Network timeout
   - Could not reach server after 30s
   - Check firewall/VPN settings
```

**Test on Save**:
- Enable **Edit → Preferences → MCP → Test connection before saving** to automatically test when adding/editing connections

### Using MCP Services

**⚠️ Current Limitation**: The current release supports **connection management only**. Query execution, results viewing, and data insertion features are planned for the next release.

**What You Can Do Now**:
- Add and configure MCP connections (Jira, GitHub, databases, terminals, Chrome)
- Test connections to verify credentials and network access
- View connection status (connected, error, offline)
- Securely store credentials in OS keyring

**Planned Features** (Coming Soon):
- Execute queries (JQL for Jira, SQL for databases, shell commands for terminal)
- View results in formatted tables/lists
- Insert references into documents (e.g., link Jira issues)
- Real-time terminal output streaming
- In-document highlighting of linked issues with tooltips

**Workaround**: For now, use external tools (web browsers, command line) to interact with services, then manually reference data in your documents.

### Offline Mode

When internet is unavailable, the editor switches to **offline mode automatically**:

**Offline Behavior**:
- MCP services show **"Offline"** indicator
- Previously fetched data available from cache (24-hour TTL)
- New queries return: **"Offline - showing cached data from 2 hours ago"**
- All editing, validation, and git operations continue working

**Cache Management**:
- **Clear Cache**: MCP Panel → **Settings** → **Clear MCP Cache**
- **Cache Location**: `.specify/cache/mcp_cache.db`
- **Cache Size**: View in MCP Panel → **Settings** → **Storage Info**

**Force Online**:
- MCP Panel → **Settings** → **Force Online Mode** (attempts connection even if previously offline)

---

## AI Assistant

The Speckit Editor includes an **AI-powered assistant** to help you write specifications, plans, and task breakdowns faster with intelligent suggestions and content generation.

### Using AI Assistant

**Two Modes**:
1. **Quick Suggestions** (Ctrl+Space): Inline completion at cursor position
2. **Full Assistant** (Ctrl+Shift+A): Chat-based interaction in side panel

### Quick Suggestions (Ctrl+Space)

**Use Case**: Auto-complete the current section, requirement, or task

**How It Works**:
1. Position cursor where you want suggestions
2. Press **Ctrl+Space**
3. AI analyzes context and suggests next content
4. Preview appears as gray ghost text
5. Press **Tab** to accept, **Esc** to dismiss

**Example 1: Auto-complete User Story**
```markdown
## User Story 1: User Authentication

**As a** user
**I want to** |← Press Ctrl+Space here

AI suggests:
**I want to** log in securely with my email and password
**So that** I can access my personalized dashboard

Press Tab to accept suggestion.
```

**Example 2: Generate Requirements**
```markdown
## Functional Requirements

FR-001: The system SHALL |← Press Ctrl+Space here

AI suggests:
FR-001: The system SHALL provide a login form with email and password fields

FR-002: The system SHALL validate email format before submission

FR-003: The system SHALL hash passwords using bcrypt with salt rounds ≥ 12
```

**Context Awareness**:
- AI reads the **current document type** (spec, plan, tasks)
- Analyzes **surrounding content** (previous sections, requirement IDs)
- Suggests content matching **speckit conventions** (ID formats, Gherkin syntax, task checkboxes)

### Full AI Assistant Panel (Ctrl+Shift+A)

**Use Case**: Interactive conversation for complex content generation

**How It Works**:
1. Press **Ctrl+Shift+A** to open assistant panel
2. Type request in the chat box
3. AI responds with generated content
4. **Review** the content (highlighted in the editor)
5. **Accept** (insert into document), **Reject** (discard), or **Modify** (edit before inserting)

**Example Conversation**:
```text
You: Generate 5 functional requirements for user authentication with password reset

AI: Here are 5 functional requirements:

FR-001: The system SHALL provide a login form with email and password fields
FR-002: The system SHALL validate email format using RFC 5322 standard
FR-003: The system SHALL hash passwords using bcrypt with minimum 12 salt rounds
FR-004: The system SHALL provide a "Forgot Password" link on the login page
FR-005: The system SHALL send password reset emails with time-limited tokens (valid 1 hour)

[Review content above] [Accept] [Reject] [Modify]
```

Click **Accept** → Content inserted at cursor position in the document.

**Advanced Requests**:
- "Generate test scenarios for FR-001 through FR-005"
- "Create task breakdown for implementing user authentication"
- "Suggest database schema for user accounts with password reset tokens"

### Reviewing and Accepting AI Suggestions

**Review Workflow**:
1. AI generates content (shown in editor with **yellow highlight**)
2. Read through the generated content
3. Choose action:
   - **Accept** (Ctrl+Enter): Insert content at cursor position
   - **Reject** (Esc): Discard content, return to chat
   - **Modify** (Ctrl+E): Edit content before inserting

**Multi-Turn Refinement**:
```text
You: Generate FR-001 for user login

AI: FR-001: The system SHALL provide a login form

You: Too vague. Add details about fields and validation

AI: FR-001: The system SHALL provide a login form with:
- Email field (validated against RFC 5322)
- Password field (minimum 8 characters, masked input)
- "Remember Me" checkbox (optional)
- "Login" button (disabled until fields are valid)

You: Perfect! [Accept]
```

### Validating AI-Generated Content

The editor **automatically validates** all AI-generated content before insertion:

**Validation Checks**:
- **Template compliance**: Ensures content matches document type template (spec, plan, tasks)
- **Structure validation**: Verifies required sections exist (User Stories, Requirements, etc.)
- **ID format validation**: Checks requirement IDs follow conventions (`FR-NNN`, `SC-NNN`, `T-NNN`)
- **Checkbox format**: Validates task checkboxes (`- [ ]`, `- [x]`)
- **Variable substitution**: Ensures no unfilled `${variables}` remain

**Validation Results**:
```text
✅ Validation Passed (0 errors, 0 warnings)

or

❌ Validation Failed (2 errors, 1 warning)
   Error: Missing required section "Success Criteria"
   Error: Requirement ID "REQ-001" should use format "FR-001"
   Warning: Task T042 missing checkbox "- [ ]"
   
[Fix Issues] [Accept Anyway] [Reject]
```

**What Happens on Error**:
- **Fix Issues**: AI automatically corrects validation errors and re-validates
- **Accept Anyway**: Insert content despite errors (your choice to fix manually)
- **Reject**: Discard content, return to chat

**Why Validation Matters**:
- Ensures AI-generated content is immediately usable
- Prevents malformed documents that break tooling
- Saves time fixing formatting errors

### AI Session History

All AI interactions are **automatically saved** for later review:

**Viewing History**:
1. AI Panel → **History** tab
2. Sessions grouped by document and date:
   - **spec.md** - 2025-12-23 14:32 (3 exchanges)
   - **plan.md** - 2025-12-23 10:15 (7 exchanges)

3. Click session to view full conversation
4. **Replay**: Restore session context to continue conversation

**Search History**:
- AI Panel → **History** → Search bar
- Search by document name, date, or content
- Example: Search "authentication" to find all AI sessions about auth

**Export History**:
- Right-click session → **Export as Markdown**
- Saves conversation to `.specify/cache/ai_sessions/<session-id>.md`

**Privacy**:
- History stored locally in `.specify/cache/ai_sessions.db`
- Not sent to remote servers
- Delete sessions: Right-click → **Delete Session**

---

## Custom Templates

The Speckit Editor allows you to **create and manage custom templates** for your team's specific workflows, with version control and sharing capabilities.

### Creating Custom Templates

**Tools → Manage Templates** opens the **Template Manager**

**1. Create New Template**

Click **New Template**:
- **Template Name**: "API Specification Template"
- **Document Type**: Specification (spec.md)
- **Base Template**: Choose existing template to copy (optional)
- Click **Create**

**2. Edit Template Content**

The template opens in the editor with editable content:

```markdown
# ${feature_name} - API Specification

**Branch**: `${branch_name}` | **Date**: ${date}

## API Endpoints

### ${endpoint_1_name}

**Method**: ${endpoint_1_method}
**Path**: /api/v1/${endpoint_1_path}
**Description**: ${endpoint_1_description}

**Request**:
```json
${endpoint_1_request_body}
```

**Response**:
```json
${endpoint_1_response_body}
```

## Authentication

${auth_requirements}

## Rate Limiting

${rate_limit_details}
```

**3. Save Template**

- Click **Save** (Ctrl+S)
- Template saved to `.specify/templates/custom/api-specification-template.md`

### Template Variables and Metadata

**Variable Syntax**: `${variable_name}`

**Predefined Variables** (auto-filled):
- `${date}`: Current date (YYYY-MM-DD format)
- `${author}`: Git username or OS username
- `${project_name}`: Current project folder name

**Custom Variables**: Define any `${variable_name}` in your template
- When creating a document from template, user is prompted to fill in all custom variables
- Variables can have default values: `${feature_name:User Authentication}`

**Metadata Section** (optional, at top of template):
```markdown
---
template_type: specification
version: 2.1.0
author: your-team
tags: [api, rest, openapi]
---
```

**Using Metadata**:
- **Template Type**: Determines syntax highlighting and validation rules
- **Version**: Tracks template evolution (semantic versioning)
- **Tags**: Filter templates in selection dialog
- **Author**: Track template ownership

### Versioning Templates with Git

Templates are **just markdown files** - version them like any other document.

**1. Initialize Template Repository**

```bash
cd .specify/templates/
git init
git add .
git commit -m "Initial template commit"
git remote add origin https://github.com/yourteam/speckit-templates.git
git push -u origin main
```

**2. Track Changes**

When you edit a template:
- Changes appear in Git Panel
- Commit template changes: `git commit -m "feat: Add rate limiting section to API template"`
- Push to share with team: `git push`

**3. View Template History**

Right-click template in Template Manager → **View History**:
- Shows all commits that modified this template
- Click commit to view diff
- **Restore**: Right-click old version → **Restore this Version**

**Template Versioning Best Practices**:
- Use **semantic versioning** in metadata: `version: 2.1.0`
- **Breaking changes** (incompatible variables): Increment major version (2.x.x → 3.0.0)
- **New sections**: Increment minor version (2.1.x → 2.2.0)
- **Typo fixes**: Increment patch version (2.1.0 → 2.1.1)

### Sharing Templates Across Team

**Option 1: Git Repository** (Recommended)

1. **Create shared repo**:
   ```bash
   # Team member 1 (creates repo)
   cd .specify/templates/
   git remote add origin https://github.com/yourteam/templates.git
   git push -u origin main
   ```

2. **Team members clone**:
   ```bash
   # Team member 2+ (clones templates)
   cd .specify/
   rm -rf templates/  # Remove default templates
   git clone https://github.com/yourteam/templates.git
   ```

3. **Sync updates**:
   - Periodically run `git pull` in `.specify/templates/` to get team updates
   - Or enable **Edit → Preferences → Templates → Auto-sync on startup**

**Option 2: File Sharing** (Simple)

1. **Export templates**:
   - Template Manager → Select templates → **Export**
   - Saves as `.specify-templates.zip`

2. **Share file**:
   - Email, Slack, or shared drive

3. **Import templates**:
   - Template Manager → **Import** → Select `.specify-templates.zip`
   - Templates extracted to `.specify/templates/custom/`

**Team Conventions**:
- Agree on variable naming: `${feature_name}` vs `${feature-name}` vs `${FeatureName}`
- Document template usage in team wiki
- Use consistent metadata tags: `[api, rest, graphql, grpc]`

### Template Organization

**Default Structure**:
```text
.specify/templates/
├── default/                      # Built-in templates (read-only)
│   ├── spec-template.md
│   ├── plan-template.md
│   ├── tasks-template.md
│   └── checklist-template.md
│
└── custom/                       # Your team templates
    ├── api-spec-template.md
    ├── database-schema-template.md
    ├── deployment-plan-template.md
    └── release-checklist-template.md
```

**Organizing Large Template Libraries**:
```text
.specify/templates/custom/
├── backend/
│   ├── api-spec-template.md
│   └── database-migration-template.md
│
├── frontend/
│   ├── ui-spec-template.md
│   └── component-plan-template.md
│
└── infrastructure/
    ├── deployment-plan-template.md
    └── runbook-template.md
```

**Template Manager Filters**:
- **By Type**: Spec, Plan, Tasks, Checklist, Custom
- **By Tag**: `#api`, `#database`, `#frontend`
- **By Author**: Filter templates created by specific team members
- **Search**: Full-text search across template content

---

## Troubleshooting

### Document won't save

**Problem**: "Failed to save document: Permission denied"

**Solution**:
1. Check file permissions (should be writable)
2. Ensure no other application has the file open
3. Try **File → Save As** to save to a different location

### Syntax highlighting not working

**Problem**: Text appears plain without colors

**Solution**:
1. Verify file extension is `.md`
2. Check **Edit → Preferences → Editor → Enable syntax highlighting** is checked
3. Restart the editor

### Template variables not substituting

**Problem**: Document still shows `${feature_name}` after creation

**Solution**:
1. Re-create document from template (File → New Document)
2. Ensure you filled in all variable fields in the dialog
3. Check template file for syntax errors (variables must be `${var_name}`)

### Performance issues with large documents

**Problem**: Editor is slow when typing in large documents (> 5MB)

**Solution**:
1. Split large documents into smaller files
2. Disable syntax highlighting for very large files (**Edit → Preferences → Editor → Disable highlighting for files > 5MB**)
3. Close unused tabs to free memory

---

## Keyboard Shortcuts

### Document Editing
- **Ctrl+N**: New document
- **Ctrl+O**: Open project
- **Ctrl+S**: Save document
- **Ctrl+Shift+S**: Save all documents
- **Ctrl+W**: Close tab
- **Ctrl+Z**: Undo
- **Ctrl+Y**: Redo
- **Ctrl+F**: Find in document
- **Ctrl+H**: Find and replace

### Navigation
- **Ctrl+P**: Quick open file
- **Ctrl+Tab**: Next tab
- **Ctrl+Shift+Tab**: Previous tab
- **Ctrl+1-9**: Jump to tab 1-9

### Git Operations
- **Ctrl+K**: Git commit
- **Ctrl+Shift+K**: Git push
- **Ctrl+Shift+P**: Git pull

### AI Assistant
- **Ctrl+Space**: Quick AI suggestions
- **Ctrl+Shift+A**: Full AI assistant panel

### MCP Services
- **Ctrl+M**: Toggle MCP panel

---

## FAQ

**Q: Can I use the editor offline?**
A: Yes. Core editing, syntax highlighting, validation, and git operations work offline. MCP services and AI assistance require internet connectivity.

**Q: What file formats are supported?**
A: The editor works with Markdown (`.md`) files following the speckit convention. Plain text files (`.txt`) can be opened but won't have syntax highlighting.

**Q: Can I customize the syntax highlighting colors?**
A: Not yet. Custom color schemes are planned for a future release.

**Q: How do I report bugs or request features?**
A: Open an issue on the [GitHub repository](https://github.com/speckit/editor/issues) with details about the bug or feature request.

**Q: Is my data private?**
A: Yes. All documents are stored locally. MCP service credentials are encrypted in your OS keyring. AI assistance sends only the selected text, never entire documents.

---

## Additional Resources

- [Developer Guide](developer-guide.md) - For contributors and developers
- [GitHub Repository](https://github.com/speckit/editor) - Source code and issues
- [Speckit Documentation](https://speckit.dev/docs) - Methodology and conventions

---

**Need Help?** Open an issue on GitHub or email support@speckit.dev

**Version**: 1.0.0 | **Last Updated**: 2025-12-23
