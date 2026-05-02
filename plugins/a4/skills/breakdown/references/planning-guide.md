# Planning Guide

Detailed procedures for deriving implementation tasks from upstream behavioral inputs (`a4/usecase/*.md`, `a4/spec/*.md`) grounded in the codebase.

## Task Derivation Strategy

There are three common approaches. Choose based on the behavioral material and codebase shape:

### 1. Component-First (Bottom-Up)

Best when the codebase has well-defined modules and the upstream specs decompose along the same lines.

1. Start with components (modules / services / packages) that have no dependencies on others (leaf nodes).
2. Build up layer by layer — data layer first, then services, then API / UI layers.
3. Each component becomes one or more tasks depending on complexity.

**When to use:** Data-heavy applications, backend services, systems with clear layered architecture, brownfield projects extending a layered system.

### 2. Feature-First (Vertical Slices)

Best when UCs / specs represent independent user-facing features that cut across multiple components.

1. Group UCs / specs into coherent features (e.g., "user authentication", "search filters").
2. Each feature becomes a task that touches all layers needed to deliver it.
3. Order by dependency: features that other features depend on come first.

**When to use:** Full-stack applications, feature-driven development, when users want incremental demos.

### 3. Hybrid

Mix both approaches: foundation tasks (shared schemas, utility services) first, then vertical feature slices.

**When to use:** Most real-world projects. Start with shared infrastructure, then slice by feature.

## Task Sizing Guidelines

A well-sized task should:
- Cover 1–5 related UCs or specs (or UC subsets — e.g., validation + error handling from a single UC).
- Touch 1–3 components.
- Be independently testable against `ci.md`'s `## How to run tests`.
- Result in a meaningful, working increment.
- Require roughly under ~500 lines of new or changed code.

### Splitting Large Tasks

Split when a task:
- Covers more than 5 UCs / specs across unrelated areas.
- Touches more than 3 components with no clear theme.
- Mixes schema creation with complex business logic.
- Would require both backend and frontend work that can be separated.

### Merging Small Tasks

Merge when a task:
- Contains only a single config file change.
- Is a trivial setup step always done alongside another task.
- Has no independent test value.

## Launch & Verify Source

`ci.md` is the single source of truth for test execution (per-tier commands, multi-tier run, test isolation flags, optional smoke scenario). `breakdown` does not author ci.md content and does not auto-detect commands. That work happened in `/a4:ci-setup` and was already verified there.

If `ci.md` is absent, the entry gate halts before reaching this step. If `ci.md` is stale (codebase no longer matches verify commands), re-run `/a4:ci-setup` rather than working around it here. The `breakdown-reviewer` flags task AC that disagrees with ci.md's commands as a finding.

## Dependency Analysis

### Finding Dependencies

For each task, check:
1. **Schema dependencies** — does this task use tables / entities created in another task?
2. **Service dependencies** — does this task call functions / APIs implemented in another task?
3. **Interface dependencies** — does this task implement one side of an interface contract defined in another task?
4. **Data dependencies** — does this task need seed data or migration from another task?

### Ordering Rules

1. **No forward references** — a task must not depend on anything built in a later task.
2. **Minimize depth** — prefer wider, flatter dependency trees over deep chains.
3. **Identify parallel opportunities** — tasks with no mutual dependencies can be implemented simultaneously.
4. **Foundation first** — shared schemas, utility functions, configuration changes always come first.

## Test Strategy Selection

| Task Type | Recommended Test Approach |
|-----------|--------------------------|
| Data model / schema | Integration tests against real DB (or in-memory DB) |
| Service / business logic | Unit tests with mocked dependencies |
| API endpoint | Integration tests with test client |
| UI component | Component tests (e.g., React Testing Library) |
| Cross-cutting flow | E2E tests |
| External service integration | Unit tests with mocked / stubbed external calls |

### Test Scenario Derivation

For each UC assigned to a task:
1. **Happy path** — derive from UC's Flow steps and Expected Outcome.
2. **Error cases** — derive from UC's Error handling field.
3. **Boundary cases** — derive from UC's Validation field.
4. **State transitions** — derive from Domain Model's state diagrams (if the UC involves stateful entities).

For each spec assigned to a task: derive scenarios from the `## Specification` body's invariants and from the spec's Acceptance section if present.

## Shared File Integration

When the file mapping shows 3+ tasks modifying the same file, that file is a **shared integration point**. Without explicit coordination, each task's coder agent adds its piece in isolation — message handlers get registered but components never get mounted, routes get defined but never wired to the app.

After completing all task file mappings, scan for shared integration points:

1. **Identify shared files** — any file appearing in 3+ tasks' `## Files` table.
2. **Define the integration pattern** — for each shared file, describe how the contributions from different tasks compose into a working whole.
3. **Inline the integration pattern in each contributing task's `## Description`** so each `coder` agent sees both its piece and the overall pattern.

Example pattern (inlined inside every contributing task's `## Description`):

```
Shared file: src/webview/main.ts
Integration pattern: Message handler registration + DOM component mounting.
This task's contribution: <task-specific piece>.
Other contributors: task/<id1> (initial setup), task/<id2> (ConversationView), task/<id3> (Sidebar).
```

This is included in the prompt for every coder agent that touches the file, so each agent knows both its contribution AND the overall integration pattern.

## File Mapping

### Deriving File Paths

Use the codebase observations from Step 2 (the codebase that ci-setup verified) to determine paths:

1. **Inspect the existing codebase** — directory structure, naming conventions, existing patterns.
2. **Follow framework conventions** — e.g., Next.js uses `app/` for routes, Django uses `<app>/models.py`.
3. **Be explicit** — `src/services/auth.service.ts` not "a service file."

When `architecture.md` suggests a file location that does not match the codebase, prefer the codebase. arch.md is reference-only and may drift — see `./verification.md` for the optional drift review.

### Change Scope for Existing Files

When modifying existing files, specify in `## Files`:

- **What is added** — new fields, methods, routes, imports.
- **What is modified** — changed function signatures, updated schemas.
- **What is removed** — deprecated code, replaced implementations.
