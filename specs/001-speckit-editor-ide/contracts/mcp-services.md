# MCP Service Contracts

**Feature**: 001-speckit-editor-ide | **Date**: 2025-12-22

## Purpose

Define the internal API contracts for MCP service integrations. These contracts specify how the editor communicates with Jira, GitHub, Git, databases, terminals, and Chrome via the embedded MCP server.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│            Speckit Editor GUI                   │
│  (PySide6 widgets, user interactions)           │
└───────────────────┬─────────────────────────────┘
                    │ async/await
                    ▼
┌─────────────────────────────────────────────────┐
│         MCP Integration Layer                   │
│  - Connection management                        │
│  - Credential storage (OS keyring)              │
│  - Response caching (offline support)           │
│  - Error handling & retries                     │
└───────────────────┬─────────────────────────────┘
                    │ in-process calls
                    ▼
┌─────────────────────────────────────────────────┐
│      Embedded MCP Server (asyncio)              │
│  - Service registry                             │
│  - Tool execution                               │
│  - Transport layer                              │
└───────────────────┬─────────────────────────────┘
                    │ HTTP/SSH/native APIs
                    ▼
┌─────────────────────────────────────────────────┐
│   External Services (Jira, GitHub, etc.)        │
└─────────────────────────────────────────────────┘
```

**Communication Pattern**:
1. GUI calls MCP integration layer method (e.g., `jira_service.create_issue(...)`)
2. Integration layer forwards to embedded MCP server via asyncio
3. MCP server executes tool (HTTP request, SSH command, etc.)
4. Response cached and returned to GUI
5. GUI updates UI with result

---

## Base Service Contract

All MCP services inherit from this base contract.

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ServiceConfig:
    """Base service configuration"""
    name: str                        # User-defined connection name
    service_type: str                # jira | github | database | terminal | chrome | git
    enabled: bool = True
    auto_connect: bool = False

@dataclass
class ServiceCredential:
    """Base credential structure"""
    credential_type: str             # token | username_password | ssh_key | oauth
    identifier: str                  # Keyring identifier
    expires_at: Optional[datetime]

@dataclass
class ServiceResponse:
    """Base service response"""
    success: bool
    data: Any
    error: Optional[str]
    cached: bool = False             # True if served from cache
    cached_at: Optional[datetime] = None

class BaseMCPService(ABC):
    def __init__(self, config: ServiceConfig):
        self.config = config
        self._connected = False
        self._authenticated = False
        
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to service"""
        pass
        
    @abstractmethod
    async def authenticate(self, credential: ServiceCredential) -> bool:
        """Authenticate with service"""
        pass
        
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from service"""
        pass
        
    @abstractmethod
    async def health_check(self) -> bool:
        """Check service availability"""
        pass
```

---

## 1. Jira Service Contract

### Configuration

```python
@dataclass
class JiraConfig(ServiceConfig):
    url: str                         # Jira instance URL (e.g., https://company.atlassian.net)
    project_key: str                 # Default project (e.g., "PROJ")
    api_version: str = "2"           # Jira REST API version (2 or 3)
```

### Methods

#### `list_issues`
Fetch issues from Jira project.

**Signature**:
```python
async def list_issues(
    self,
    project: Optional[str] = None,   # Override default project
    jql: Optional[str] = None,       # JQL query filter
    max_results: int = 50
) -> ServiceResponse[List[JiraIssue]]
```

**Request** (MCP tool call):
```json
{
  "tool": "jira/list_issues",
  "arguments": {
    "project": "PROJ",
    "jql": "status = Open",
    "max_results": 50
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "10001",
      "key": "PROJ-123",
      "summary": "Implement authentication",
      "status": "Open",
      "assignee": "user@example.com",
      "created": "2025-12-20T10:00:00Z",
      "updated": "2025-12-22T14:30:00Z"
    }
  ],
  "error": null,
  "cached": false
}
```

**Error Codes**:
- `401`: Authentication failed (invalid token)
- `403`: Insufficient permissions
- `404`: Project not found
- `500`: Jira server error

---

#### `create_issue`
Create new Jira issue.

**Signature**:
```python
async def create_issue(
    self,
    project: str,
    summary: str,
    description: str,
    issue_type: str = "Task",
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    labels: Optional[List[str]] = None
) -> ServiceResponse[JiraIssue]
```

**Request**:
```json
{
  "tool": "jira/create_issue",
  "arguments": {
    "project": "PROJ",
    "summary": "Implement feature X",
    "description": "Full description...",
    "issue_type": "Story",
    "priority": "High",
    "labels": ["backend", "api"]
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "10002",
    "key": "PROJ-124",
    "self": "https://company.atlassian.net/rest/api/2/issue/10002"
  },
  "error": null
}
```

---

#### `update_issue`
Update existing Jira issue.

**Signature**:
```python
async def update_issue(
    self,
    issue_key: str,
    fields: Dict[str, Any]           # Fields to update
) -> ServiceResponse[bool]
```

**Request**:
```json
{
  "tool": "jira/update_issue",
  "arguments": {
    "issue_key": "PROJ-123",
    "fields": {
      "status": "In Progress",
      "assignee": "new-user@example.com"
    }
  }
}
```

---

#### `get_issue`
Fetch single issue by key.

**Signature**:
```python
async def get_issue(self, issue_key: str) -> ServiceResponse[JiraIssue]
```

---

### Data Models

```python
@dataclass
class JiraIssue:
    id: str
    key: str
    summary: str
    description: str
    status: str
    issue_type: str
    priority: Optional[str]
    assignee: Optional[str]
    reporter: str
    labels: List[str]
    created: datetime
    updated: datetime
    self: str                        # API URL for issue
```

---

## 2. GitHub Service Contract

### Configuration

```python
@dataclass
class GitHubConfig(ServiceConfig):
    api_url: str = "https://api.github.com"  # GitHub API endpoint
    owner: str                       # Repository owner (user/org)
    repo: str                        # Repository name
    api_version: str = "v3"          # v3 (REST) or v4 (GraphQL)
```

### Methods

#### `list_pull_requests`
Fetch pull requests from repository.

**Signature**:
```python
async def list_pull_requests(
    self,
    state: str = "open",             # open | closed | all
    sort: str = "created",           # created | updated | popularity
    direction: str = "desc",         # asc | desc
    max_results: int = 50
) -> ServiceResponse[List[PullRequest]]
```

**Request**:
```json
{
  "tool": "github/list_pull_requests",
  "arguments": {
    "state": "open",
    "sort": "updated",
    "direction": "desc",
    "max_results": 20
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "number": 42,
      "title": "Add authentication feature",
      "state": "open",
      "user": "octocat",
      "created_at": "2025-12-20T10:00:00Z",
      "updated_at": "2025-12-22T14:30:00Z",
      "html_url": "https://github.com/owner/repo/pull/42"
    }
  ],
  "error": null
}
```

---

#### `create_pull_request`
Create new pull request.

**Signature**:
```python
async def create_pull_request(
    self,
    title: str,
    head: str,                       # Branch to merge from
    base: str,                       # Branch to merge into
    body: Optional[str] = None,
    draft: bool = False
) -> ServiceResponse[PullRequest]
```

**Request**:
```json
{
  "tool": "github/create_pull_request",
  "arguments": {
    "title": "feat: add offline mode",
    "head": "001-speckit-editor-ide",
    "base": "main",
    "body": "Implements offline mode with caching...",
    "draft": false
  }
}
```

---

#### `get_repository`
Fetch repository metadata.

**Signature**:
```python
async def get_repository(self) -> ServiceResponse[Repository]
```

---

#### `list_branches`
List repository branches.

**Signature**:
```python
async def list_branches(self) -> ServiceResponse[List[Branch]]
```

---

### Data Models

```python
@dataclass
class PullRequest:
    number: int
    title: str
    state: str                       # open | closed
    user: str
    head: str                        # Source branch
    base: str                        # Target branch
    created_at: datetime
    updated_at: datetime
    merged_at: Optional[datetime]
    html_url: str

@dataclass
class Repository:
    name: str
    full_name: str
    owner: str
    description: str
    default_branch: str
    html_url: str
    clone_url: str

@dataclass
class Branch:
    name: str
    commit_sha: str
    protected: bool
```

---

## 3. Database Service Contract

### Configuration

```python
@dataclass
class DatabaseConfig(ServiceConfig):
    db_type: str                     # postgresql | mysql | sqlite | mongodb
    host: str
    port: int
    database: str
    username: Optional[str] = None
    ssl_enabled: bool = False
```

### Methods

#### `execute_query`
Execute SQL query (SELECT).

**Signature**:
```python
async def execute_query(
    self,
    query: str,
    params: Optional[Dict[str, Any]] = None,
    max_rows: int = 100
) -> ServiceResponse[QueryResult]
```

**Request**:
```json
{
  "tool": "database/execute_query",
  "arguments": {
    "query": "SELECT * FROM users WHERE status = :status LIMIT :limit",
    "params": {"status": "active", "limit": 10},
    "max_rows": 100
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "columns": ["id", "name", "email", "status"],
    "rows": [
      [1, "Alice", "alice@example.com", "active"],
      [2, "Bob", "bob@example.com", "active"]
    ],
    "row_count": 2
  },
  "error": null
}
```

---

#### `execute_command`
Execute SQL command (INSERT, UPDATE, DELETE).

**Signature**:
```python
async def execute_command(
    self,
    command: str,
    params: Optional[Dict[str, Any]] = None
) -> ServiceResponse[CommandResult]
```

**Request**:
```json
{
  "tool": "database/execute_command",
  "arguments": {
    "command": "UPDATE users SET status = :status WHERE id = :id",
    "params": {"status": "inactive", "id": 5}
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "affected_rows": 1
  },
  "error": null
}
```

---

#### `list_tables`
List database tables.

**Signature**:
```python
async def list_tables(self) -> ServiceResponse[List[str]]
```

---

### Data Models

```python
@dataclass
class QueryResult:
    columns: List[str]
    rows: List[List[Any]]
    row_count: int

@dataclass
class CommandResult:
    affected_rows: int
```

---

## 4. Terminal Service Contract

### Configuration

```python
@dataclass
class TerminalConfig(ServiceConfig):
    shell: str = "bash"              # bash | zsh | powershell | cmd
    working_directory: Optional[str] = None
    environment: Optional[Dict[str, str]] = None
```

### Methods

#### `execute_command`
Execute shell command.

**Signature**:
```python
async def execute_command(
    self,
    command: str,
    timeout: int = 30,               # Seconds
    capture_output: bool = True
) -> ServiceResponse[CommandOutput]
```

**Request**:
```json
{
  "tool": "terminal/execute_command",
  "arguments": {
    "command": "git status",
    "timeout": 10,
    "capture_output": true
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "stdout": "On branch main\nYour branch is up to date...",
    "stderr": "",
    "exit_code": 0
  },
  "error": null
}
```

---

#### `start_interactive_session`
Start interactive terminal session.

**Signature**:
```python
async def start_interactive_session(self) -> ServiceResponse[str]  # Returns session ID
```

---

#### `send_input`
Send input to interactive session.

**Signature**:
```python
async def send_input(self, session_id: str, input: str) -> ServiceResponse[str]
```

---

### Data Models

```python
@dataclass
class CommandOutput:
    stdout: str
    stderr: str
    exit_code: int
```

---

## 5. Chrome Service Contract

### Configuration

```python
@dataclass
class ChromeConfig(ServiceConfig):
    debug_port: int = 9222           # Chrome DevTools port
    auto_launch: bool = False        # Launch Chrome with debugging enabled
    user_data_dir: Optional[str] = None
```

### Methods

#### `navigate`
Navigate to URL.

**Signature**:
```python
async def navigate(self, url: str, wait_until: str = "load") -> ServiceResponse[bool]
```

**Request**:
```json
{
  "tool": "chrome/navigate",
  "arguments": {
    "url": "https://example.com",
    "wait_until": "networkidle"
  }
}
```

---

#### `execute_script`
Execute JavaScript in page.

**Signature**:
```python
async def execute_script(self, script: str) -> ServiceResponse[Any]
```

**Request**:
```json
{
  "tool": "chrome/execute_script",
  "arguments": {
    "script": "document.querySelector('h1').textContent"
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": "Welcome to Example",
  "error": null
}
```

---

#### `screenshot`
Capture page screenshot.

**Signature**:
```python
async def screenshot(self, full_page: bool = False) -> ServiceResponse[bytes]
```

---

## 6. Git Service Contract

### Configuration

```python
@dataclass
class GitConfig(ServiceConfig):
    repository_path: str             # Path to git repository
    user_name: Optional[str] = None
    user_email: Optional[str] = None
```

### Methods

#### `status`
Get repository status.

**Signature**:
```python
async def status(self) -> ServiceResponse[GitStatus]
```

**Response**:
```json
{
  "success": true,
  "data": {
    "branch": "001-speckit-editor-ide",
    "staged_files": ["specs/001/spec.md"],
    "unstaged_files": ["README.md"],
    "untracked_files": [],
    "ahead": 2,
    "behind": 0
  },
  "error": null
}
```

---

#### `commit`
Create commit.

**Signature**:
```python
async def commit(self, message: str, files: List[str]) -> ServiceResponse[str]  # Returns commit SHA
```

---

#### `push`
Push commits to remote.

**Signature**:
```python
async def push(self, remote: str = "origin", branch: Optional[str] = None) -> ServiceResponse[bool]
```

---

#### `pull`
Pull commits from remote.

**Signature**:
```python
async def pull(self, remote: str = "origin", branch: Optional[str] = None) -> ServiceResponse[bool]
```

---

### Data Models

```python
@dataclass
class GitStatus:
    branch: str
    staged_files: List[str]
    unstaged_files: List[str]
    untracked_files: List[str]
    ahead: int                       # Commits ahead of remote
    behind: int                      # Commits behind remote
```

---

## Error Handling

All services use standardized error responses:

```python
@dataclass
class ServiceError:
    code: str                        # Error code (e.g., "AUTH_FAILED", "TIMEOUT")
    message: str                     # Human-readable message
    details: Optional[Dict[str, Any]]  # Additional error context
    recoverable: bool                # Can retry operation

# Common error codes:
ERROR_CODES = {
    "AUTH_FAILED": "Authentication failed",
    "TIMEOUT": "Operation timed out",
    "CONNECTION_FAILED": "Failed to connect to service",
    "RATE_LIMITED": "Rate limit exceeded",
    "NOT_FOUND": "Resource not found",
    "PERMISSION_DENIED": "Insufficient permissions",
    "INVALID_INPUT": "Invalid input parameters",
    "SERVER_ERROR": "Service returned error",
}
```

---

## Caching Strategy

All services implement caching for offline support:

```python
class CachePolicy:
    enabled: bool = True
    ttl: int = 3600                  # Time-to-live in seconds
    max_size: int = 100              # Max cached items
    invalidate_on_write: bool = True # Clear cache on write operations
```

**Cache Key Format**: `{service_type}:{method}:{args_hash}`

**Cache Storage**: SQLite database (`.specify/cache/mcp_cache.db`)

---

## Testing Contracts

All MCP services must include:

1. **Unit tests**: Mock HTTP/SSH responses
2. **Integration tests**: Test with real services (optional, requires credentials)
3. **Contract tests**: Validate request/response schemas

**Mock Examples**:
```python
# tests/integration/test_jira_service.py
@pytest.mark.asyncio
async def test_list_issues(mock_jira_service):
    mock_response = [
        {"id": "1", "key": "PROJ-123", "summary": "Test issue"}
    ]
    
    with patch('httpx.AsyncClient.get', new=AsyncMock(return_value=mock_response)):
        result = await mock_jira_service.list_issues(project="PROJ")
        assert result.success
        assert len(result.data) == 1
        assert result.data[0].key == "PROJ-123"
```

---

## Versioning

**Contract Version**: `1.0.0`

**Breaking Changes** (require major version bump):
- Remove method
- Change method signature (required parameters)
- Change response data structure

**Non-Breaking Changes** (minor version bump):
- Add new method
- Add optional parameters
- Add new fields to response (backward compatible)

---

## References

- [Model Context Protocol Specification](https://modelcontextprotocol.io/docs)
- [Jira REST API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [GitHub REST API](https://docs.github.com/en/rest)
