# Task Generation Principles

**Version**: 1.0.0  
**Created**: 2025-12-23  
**Purpose**: Rules for generating tasks.md from spec.md and plan.md

---

## Core Principles

### 1. Incremental Documentation Principle

**Rule**: README.md and user-facing documentation MUST be updated incrementally after each user story completes.

**What to Update After Each User Story**:
- `docs/user-guide.md` - Add section documenting the story's features
- `README.md` - Update feature status table (USX: ✅ Complete)
- `README.md` - Update test coverage numbers
- `README.md` - Add links to new documentation sections

**Anti-Pattern**: Deferring all documentation to "Phase 9" or "final polish"

**Rationale**:
- README is the public interface - stale README = misleading repository
- Documentation written immediately after implementation is more accurate
- Incremental docs enable earlier feedback and user adoption
- Waiting until end risks forgetting implementation details

**Implementation**:
```markdown
### Documentation for User Story 1

- [ ] T0XX [P] [Simple] [US1] Document US1 features in docs/user-guide.md
  - Feature overview
  - How to use X
  - Understanding Y
  - Troubleshooting Z
- [ ] T0XX [P] [Simple] [US1] Update README.md for US1 completion
  - Update feature status (US1: ✅ Complete)
  - Update test coverage numbers
  - Add link to US1 documentation
```

**Exception**: Final README polish (screenshots, FAQ, advanced troubleshooting) can be deferred to final phase.

---

### 2. Task Organization by User Story

**Rule**: Tasks MUST be grouped by user story to enable independent implementation and testing.

**Structure**:
```markdown
## Phase 3: User Story 1 (P1)

### Tests for User Story 1 (optional)
### Implementation for User Story 1
### Documentation for User Story 1

**Checkpoint**: US1 complete and documented
```

**Rationale**: Each user story should be deliverable as an independent increment.

---

### 3. Test Tasks Are Optional

**Rule**: Only generate test tasks if explicitly requested in the specification or if TDD approach is specified.

**Default**: Implementation tasks only (no test generation)

**When to Include Tests**:
- Spec explicitly mentions "test-driven development" or "TDD"
- Spec has section titled "Testing Strategy" with specific test requirements
- User explicitly requests tests in feature description

**Test Task Format** (when included):
```markdown
### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T0XX [P] [US1] Contract test for [endpoint] in tests/contract/test_[name].py
- [ ] T0XX [P] [US1] Integration test for [user journey] in tests/integration/test_[name].py
```

---

### 4. Setup and Foundational Tasks

**Rule**: Separate setup (Phase 1) from foundational (Phase 2) tasks.

**Phase 1 - Setup**: Project scaffolding, zero dependencies
- Create project structure
- Initialize package managers
- Configure linters/formatters
- Setup CI/CD basics

**Phase 2 - Foundational**: Core infrastructure that BLOCKS all user stories
- Core models/entities used by ALL stories
- Authentication/authorization framework
- Database schema and migrations
- API routing and middleware
- Error handling and logging
- Configuration management

**Critical Rule**: Mark Phase 2 with warning:
```markdown
## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete
```

---

### 5. Parallel Task Marking

**Rule**: Mark tasks with `[P]` if they can run in parallel (different files, no dependencies).

**Criteria for [P]**:
- ✅ Different files
- ✅ No shared state
- ✅ No dependency on incomplete tasks
- ❌ Same file (even different functions)
- ❌ Depends on another incomplete task
- ❌ Requires integration with incomplete component

**Example**:
```markdown
- [ ] T010 [P] [US1] Create User model in src/models/user.py
- [ ] T011 [P] [US1] Create Post model in src/models/post.py
- [ ] T012 [US1] Implement UserService in src/services/user_service.py (depends on T010)
```

---

### 6. Task ID Sequential Numbering

**Rule**: Task IDs MUST be sequential (T001, T002, T003...) without gaps or suffixes.

**Anti-Pattern**: T001, T002, T002a, T002b, T003

**Rationale**: Sequential IDs are easier to reference, search, and track.

**When Adding Tasks**: Renumber all subsequent tasks to maintain sequence.

---

### 7. Checkpoint After Each User Story

**Rule**: Each user story phase MUST end with a checkpoint describing what should be functional.

**Format**:
```markdown
**Checkpoint**: User Story 1 complete - Users can [specific capability]. All tests passing. Documentation updated.
```

**Checkpoint Should Verify**:
- Feature functionality
- Independent testability
- Documentation completeness
- Integration status (if applicable)

---

### 8. Phase 9 (Polish) Scope

**Rule**: Phase 9 should only contain cross-cutting concerns and final polish, NOT initial documentation.

**Phase 9 Includes**:
- Polish and consolidate incremental documentation
- Add screenshots to docs/screenshots/
- Final README polish (FAQ, troubleshooting, advanced guides)
- Code cleanup and refactoring
- Performance optimization across stories
- Security hardening
- Final testing pass

**Phase 9 Does NOT Include**:
- Initial user guide creation (done incrementally)
- Initial developer guide creation (done in Phase 2)
- Initial README updates (done after each story)

---

## Task Generation Workflow

1. **Read spec.md**: Extract user stories with priorities (P1, P2, P3...)
2. **Read plan.md**: Extract tech stack, architecture, project structure
3. **Read data-model.md** (if exists): Map entities to user stories
4. **Read contracts/** (if exists): Map endpoints to user stories
5. **Generate Phase 1**: Setup tasks
6. **Generate Phase 2**: Foundational tasks with ⚠️ warning
7. **Generate Phase 3+**: One phase per user story in priority order
   - Tests (if requested)
   - Implementation
   - **Documentation** (user guide + README update)
   - Checkpoint
8. **Generate Phase N**: Polish and cross-cutting concerns
9. **Add Dependencies section**: Show execution order and parallel opportunities

---

## Example: Complete User Story Phase

```markdown
## Phase 3: User Story 1 - User Authentication (Priority: P1)

**Goal**: Enable users to register, login, and manage their account

**Independent Test**: Create account, login, logout, view profile

### Implementation for User Story 1

- [ ] T015 [P] [US1] Create User model in src/models/user.py
- [ ] T016 [P] [US1] Create Session model in src/models/session.py
- [ ] T017 [US1] Implement AuthService in src/services/auth_service.py (password hashing, token generation)
- [ ] T018 [US1] Implement /register endpoint in src/api/auth.py
- [ ] T019 [US1] Implement /login endpoint in src/api/auth.py
- [ ] T020 [US1] Implement /logout endpoint in src/api/auth.py
- [ ] T021 [Simple] [US1] Add validation for email format and password strength

### Documentation for User Story 1

- [ ] T022 [P] [Simple] [US1] Document US1 features in docs/user-guide.md
  - Creating an account
  - Logging in and out
  - Password requirements
  - Troubleshooting login issues
- [ ] T023 [P] [Simple] [US1] Update README.md for US1 completion
  - Update feature status (US1: ✅ Complete)
  - Update test coverage numbers
  - Add link to authentication documentation

**Checkpoint**: User Story 1 complete - Users can register, login, and logout. All authentication flows tested. Documentation updated.
```

---

## Enforcement

These principles MUST be followed by:
- `/speckit.tasks` command when generating tasks.md
- AI agents when proposing task additions/modifications
- Human developers when manually updating tasks.md

**Violations to Flag**:
- Documentation tasks deferred to Phase 9
- README not updated after user stories
- Non-sequential task IDs (gaps, suffixes)
- Missing checkpoints
- Missing ⚠️ warning on Phase 2
- Incorrect [P] marking (same file, has dependencies)

---

**Last Updated**: 2025-12-23  
**Next Review**: When task generation patterns change
