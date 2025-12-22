# CLI API Contract

**Feature**: 001-speckit-editor-ide | **Date**: 2025-12-22

## Purpose

Define the command-line interface contract for the Speckit Editor. This contract ensures CLI-GUI parity (FR-014) and enables scripting/automation of speckit workflows.

---

## Command Structure

All commands follow the pattern:
```bash
speckit-editor <command> [options] [arguments]
```

**Exit Codes**:
- `0`: Success
- `1`: General error (invalid arguments, file not found, etc.)
- `2`: Validation error (spec/plan invalid structure)
- `3`: Git error (merge conflict, authentication failure, etc.)
- `4`: MCP error (service unavailable, connection timeout, etc.)

---

## Commands

### 1. Project Management

#### `init`
Initialize a new speckit project.

**Syntax**:
```bash
speckit-editor init [--path <directory>] [--template <name>]
```

**Options**:
- `--path <directory>`: Project directory (default: current directory)
- `--template <name>`: Constitution template to use (default: `default`)

**Output**:
```
Created speckit project at: /path/to/project
- .specify/memory/constitution.md
- .specify/templates/
- .specify/scripts/
- README.md
```

**Exit Code**: `0` on success, `1` if directory already contains `.specify/`

**Example**:
```bash
speckit-editor init --path ./my-project --template minimal
```

---

#### `validate`
Validate project structure and documents.

**Syntax**:
```bash
speckit-editor validate [--path <directory>] [--strict]
```

**Options**:
- `--path <directory>`: Project root (default: current directory)
- `--strict`: Treat warnings as errors (exit code 2 if any warnings)

**Output**:
```
Validating project: /path/to/project
✓ Constitution: valid
✓ specs/001-editor-ide/spec.md: valid
✗ specs/002-api/spec.md: 2 errors, 1 warning
  - Error: Duplicate requirement ID FR-005 (line 42)
  - Error: Broken reference to SC-999 (line 87)
  - Warning: Non-sequential IDs (FR-003 → FR-005)

Validation failed: 2 errors, 1 warning
```

**Exit Code**: 
- `0` if valid (no errors)
- `2` if errors found
- `2` if `--strict` and warnings found

**Example**:
```bash
speckit-editor validate --strict
```

---

### 2. Feature Workflow

#### `specify`
Generate feature specification from template.

**Syntax**:
```bash
speckit-editor specify --id <feature-id> [--template <name>] [--interactive]
```

**Options**:
- `--id <feature-id>`: Three-digit feature ID (e.g., `001`)
- `--template <name>`: Spec template to use (default: `spec-template`)
- `--interactive`: Prompt for template variables interactively

**Output**:
```
Creating feature specification: 001
Template: spec-template.md
Variables:
  - FEATURE_ID: 001
  - FEATURE_NAME: [Enter value]: Speckit Editor IDE
  - PRIORITY: [Enter P1-P4]: P1

Generated: specs/001-speckit-editor-ide/spec.md
Created branch: 001-speckit-editor-ide
```

**Exit Code**: `0` on success, `1` if feature ID already exists

**Example**:
```bash
speckit-editor specify --id 003 --interactive
```

---

#### `clarify`
Run clarification workflow on feature specification.

**Syntax**:
```bash
speckit-editor clarify --feature <feature-id>
```

**Options**:
- `--feature <feature-id>`: Feature to clarify (e.g., `001`)

**Output**:
```
Clarifying feature: 001-speckit-editor-ide
Reading: specs/001-speckit-editor-ide/spec.md

Found 3 NEEDS CLARIFICATION markers:
1. [Line 42] GUI framework choice
2. [Line 87] MCP server architecture
3. [Line 123] Offline mode strategy

Please update spec.md to resolve these clarifications.
Run `speckit-editor clarify --feature 001` again when ready.
```

**Exit Code**: 
- `0` if no clarifications needed
- `2` if clarifications pending

**Example**:
```bash
speckit-editor clarify --feature 001
```

---

#### `plan`
Generate implementation plan from specification.

**Syntax**:
```bash
speckit-editor plan --feature <feature-id>
```

**Options**:
- `--feature <feature-id>`: Feature to plan (e.g., `001`)

**Output**:
```
Generating plan: 001-speckit-editor-ide
Constitution check: PASSED
Generated:
  - specs/001-speckit-editor-ide/plan.md
  - specs/001-speckit-editor-ide/research.md
  - specs/001-speckit-editor-ide/data-model.md
  - specs/001-speckit-editor-ide/contracts/
  - specs/001-speckit-editor-ide/quickstart.md
```

**Exit Code**: 
- `0` on success
- `2` if constitution check fails

**Example**:
```bash
speckit-editor plan --feature 001
```

---

#### `tasks`
Break plan into implementation tasks.

**Syntax**:
```bash
speckit-editor tasks --feature <feature-id>
```

**Options**:
- `--feature <feature-id>`: Feature to generate tasks for (e.g., `001`)

**Output**:
```
Generating tasks: 001-speckit-editor-ide
Reading: specs/001-speckit-editor-ide/plan.md

Generated: specs/001-speckit-editor-ide/tasks.md
Tasks breakdown:
  - TSK-001: Setup project structure (2 hours)
  - TSK-002: Implement document parser (4 hours)
  - TSK-003: Build editor widget (8 hours)
  ... (25 more tasks)
  
Total estimated effort: 120 hours
```

**Exit Code**: `0` on success, `1` if plan.md not found

**Example**:
```bash
speckit-editor tasks --feature 001
```

---

### 3. Document Operations

#### `open`
Open document(s) in GUI editor.

**Syntax**:
```bash
speckit-editor open <file-path> [<file-path>...]
```

**Arguments**:
- `<file-path>`: Path to markdown document(s)

**Output**: Launches GUI with specified documents open in tabs.

**Exit Code**: `0` on success, `1` if file not found

**Example**:
```bash
speckit-editor open specs/001-editor-ide/spec.md specs/001-editor-ide/plan.md
```

---

#### `search`
Search documents for text or requirement IDs.

**Syntax**:
```bash
speckit-editor search <query> [--regex] [--case-sensitive] [--scope <scope>]
```

**Arguments**:
- `<query>`: Search query (text or requirement ID)

**Options**:
- `--regex`: Treat query as regex pattern
- `--case-sensitive`: Case-sensitive search
- `--scope <scope>`: Search scope (`all`, `specs`, `plans`, `tasks`)

**Output**:
```
Searching for: "authentication"
Scope: all documents

Results (3 matches):
1. specs/001-editor-ide/spec.md:42
   ... user authentication via MCP service integration ...
   
2. specs/002-api/spec.md:87
   ... OAuth authentication flow for GitHub integration ...
   
3. specs/002-api/plan.md:123
   ... authentication strategy using OS keyring ...
```

**Exit Code**: `0` if matches found, `1` if no matches

**Example**:
```bash
speckit-editor search "FR-\d{3}" --regex --scope specs
```

---

### 4. Git Integration

#### `commit`
Commit staged changes with conventional commit message.

**Syntax**:
```bash
speckit-editor commit --type <type> --scope <scope> --message <message> [--breaking]
```

**Options**:
- `--type <type>`: Commit type (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`)
- `--scope <scope>`: Commit scope (e.g., `001`, `gui`, `mcp`)
- `--message <message>`: Commit message description
- `--breaking`: Mark as breaking change (adds `!` after type)

**Output**:
```
Staged files:
  - specs/001-editor-ide/spec.md
  - specs/001-editor-ide/plan.md

Commit message:
feat(001): add MCP integration requirements

Created commit: a1b2c3d
```

**Exit Code**: `0` on success, `3` if git error (no staged files, merge conflict, etc.)

**Example**:
```bash
speckit-editor commit --type feat --scope 001 --message "add offline mode requirements"
```

---

#### `branch`
Manage feature branches.

**Syntax**:
```bash
speckit-editor branch <action> [--feature <feature-id>] [--name <branch-name>]
```

**Actions**:
- `list`: List all feature branches
- `create`: Create new feature branch
- `checkout`: Switch to feature branch
- `delete`: Delete feature branch

**Options**:
- `--feature <feature-id>`: Feature ID (for `create`, `checkout`, `delete`)
- `--name <branch-name>`: Branch name (for `create`)

**Output** (list):
```
Feature branches:
* 001-speckit-editor-ide (current)
  002-api-integration
  003-deployment
```

**Output** (create):
```
Created branch: 002-api-integration
Switched to branch: 002-api-integration
```

**Exit Code**: `0` on success, `3` if git error

**Example**:
```bash
speckit-editor branch create --feature 002 --name "api-integration"
speckit-editor branch list
speckit-editor branch checkout --feature 001
```

---

### 5. MCP Integration

#### `mcp`
Manage MCP service connections.

**Syntax**:
```bash
speckit-editor mcp <action> [--service <service-type>] [options]
```

**Actions**:
- `list`: List configured MCP connections
- `add`: Add new MCP connection
- `test`: Test connection to MCP service
- `remove`: Remove MCP connection

**Options** (for `add`):
- `--service <service-type>`: Service type (`jira`, `github`, `database`, `terminal`, `chrome`, `git`)
- `--name <name>`: Connection name
- `--config <json>`: Service configuration as JSON

**Output** (list):
```
MCP Connections:
✓ Jira - Company JIRA (connected)
✓ GitHub - Personal Account (connected)
✗ Database - PostgreSQL Dev (disconnected)
```

**Output** (add):
```
Adding MCP connection: Jira
Name: Company JIRA
Config: {"url": "https://company.atlassian.net", "project": "PROJ"}
Credentials: [Enter API token]: ********

Testing connection... ✓
Connection added successfully.
```

**Exit Code**: 
- `0` on success
- `4` if connection test fails

**Example**:
```bash
speckit-editor mcp add --service jira --name "Company JIRA" --config '{"url": "https://company.atlassian.net"}'
speckit-editor mcp list
speckit-editor mcp test --service jira --name "Company JIRA"
```

---

### 6. Template Management

#### `template`
Manage document templates.

**Syntax**:
```bash
speckit-editor template <action> [--name <template-name>] [options]
```

**Actions**:
- `list`: List available templates
- `create`: Create new custom template
- `edit`: Edit existing template
- `delete`: Delete template

**Options**:
- `--name <template-name>`: Template name
- `--type <type>`: Template type (`spec`, `plan`, `tasks`, `checklist`, `custom`)
- `--from <source>`: Copy from existing template

**Output** (list):
```
Available templates:
- spec-template.md (spec)
- plan-template.md (plan)
- tasks-template.md (tasks)
- checklist-template.md (checklist)
- my-custom-template.md (custom)
```

**Output** (create):
```
Creating template: my-custom-template
Type: custom
Variables:
  - [Enter variable name, blank to finish]: PROJECT_NAME
  - [Enter variable name, blank to finish]: AUTHOR
  - [Enter variable name, blank to finish]: 

Created: .specify/templates/my-custom-template.md
```

**Exit Code**: `0` on success, `1` if template not found

**Example**:
```bash
speckit-editor template list
speckit-editor template create --name "api-spec" --type spec --from spec-template
```

---

## API Versioning

**CLI Version**: `1.0.0`

**Compatibility Promise**:
- Major version bump (e.g., `1.x` → `2.x`): Breaking changes to command syntax
- Minor version bump (e.g., `1.0` → `1.1`): New commands/options, backward compatible
- Patch version bump (e.g., `1.0.0` → `1.0.1`): Bug fixes, no API changes

**Version Check**:
```bash
speckit-editor --version
```
Output: `Speckit Editor CLI v1.0.0`

---

## Error Handling

All commands output errors to `stderr` and return non-zero exit codes.

**Error Format**:
```
Error: <error-type>
<error-message>
<optional-suggestion>
```

**Example**:
```bash
$ speckit-editor validate
Error: Invalid project structure
.specify/memory/constitution.md not found
Suggestion: Run `speckit-editor init` to initialize project
```

---

## Configuration

CLI reads configuration from:
1. `.specify/settings.json` (project-level)
2. `~/.speckit/config.json` (user-level)
3. Environment variables (highest priority)

**Environment Variables**:
- `SPECKIT_PROJECT_ROOT`: Override project root path
- `SPECKIT_TEMPLATE_DIR`: Custom template directory
- `SPECKIT_LOG_LEVEL`: Logging verbosity (`DEBUG`, `INFO`, `WARN`, `ERROR`)

**Example**:
```bash
export SPECKIT_LOG_LEVEL=DEBUG
speckit-editor validate
```

---

## Testing Contract

All CLI commands must be testable via:
1. **Unit tests**: Mock filesystem, git, MCP services
2. **Integration tests**: Test with real git repository, sample projects
3. **Smoke tests**: End-to-end workflow (init → specify → plan → tasks)

**Test Coverage Requirement**: 80% minimum (per constitution)

---

## Future Extensions

Potential future commands (not in v1.0):
- `speckit-editor export`: Export spec/plan to PDF, HTML, etc.
- `speckit-editor metrics`: Project metrics (requirement count, test coverage, etc.)
- `speckit-editor sync`: Sync MCP data (Jira issues, GitHub PRs) to local cache
- `speckit-editor ai`: Direct AI interaction via CLI (non-interactive mode)

---

## References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [POSIX CLI Conventions](https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap12.html)
