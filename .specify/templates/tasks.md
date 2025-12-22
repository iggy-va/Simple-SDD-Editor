---
description: Task breakdown template for implementation
version: 1.0.0
author: Speckit Editor
---

# Implementation Tasks: {{feature_name}}

**Feature ID**: {{feature_id}}
**Total Estimated Tasks**: {{task_count}}

## Task Organization

Tasks are organized by implementation phase and user story.

### Legend

- `[P]` - Can be parallelized with other [P] tasks
- `[US#]` - Associated with User Story number
- `[ ]` - Not started
- `[x]` - Completed

---

## Phase 1: {{phase_1_name}}

**Goal**: {{phase_1_goal}}

**Independent Test**: {{phase_1_test}}

### Tasks

- [ ] T001 [P] {{task_1_description}}
- [ ] T002 [P] {{task_2_description}}
- [ ] T003 {{task_3_description}}

**Checkpoint**: {{phase_1_checkpoint}}

---

## Phase 2: {{phase_2_name}}

**Goal**: {{phase_2_goal}}

**Independent Test**: {{phase_2_test}}

### Tasks

- [ ] T004 [P] [US1] {{task_4_description}}
- [ ] T005 [US1] {{task_5_description}}
- [ ] T006 [US1] {{task_6_description}}

**Checkpoint**: {{phase_2_checkpoint}}

---

## Progress Tracking

| Phase | Tasks | Completed | % Complete |
|-------|-------|-----------|------------|
| Phase 1 | {{phase_1_tasks}} | 0 | 0% |
| Phase 2 | {{phase_2_tasks}} | 0 | 0% |
| **Total** | {{total_tasks}} | 0 | 0% |

---

**Created**: {{date}}
**Last Updated**: {{date}}
