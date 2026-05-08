---
name: auto-scaffold
description: "Scaffold project structure and a minimal entry point."
argument-hint: "(no argument) — scaffold against the current repo state. Idempotent for already-scaffolded projects."
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, WebSearch, WebFetch, TaskCreate, TaskUpdate, TaskList
---

# Project Scaffold

Performs the LLM-driven scaffold steps for a project — directory layout, package manifest, dependencies, build configuration, and a minimal running entry point. Runs autonomously. **Outputs are repo files only.** This skill does not author any wiki page; test environment setup and the `a4/ci.md` document are owned by `/a4:ci-setup`.

## Workspace

Resolve `a4/` and the project root via `git rev-parse --show-toplevel`.

**Inputs (all optional — read whichever exist for context):**

- `a4/architecture.md` — Technology Stack, Component structure, External Dependencies, when present.
- `a4/usecase/*.md`, `a4/domain.md`, `a4/context.md` — reference-only context to verify scope assumptions.
- Existing files in the repo — when present, treat as ground truth; only set up what is missing.

**Outputs:**

- Project files in the repo (e.g., `package.json`, `pyproject.toml`, `Cargo.toml`, build config, source directory layout, minimal entry point).
- `a4/review/<id>-<slug>.md` — review items emitted when scaffold uncovers architecture-level issues that the user should address via `/a4:arch iterate`.
- `a4/research/scaffold-<label>.md` — research reports from `api-researcher` when an environment fix needs library / docs lookup.

## What This Skill Does

1. Assess project state (fresh vs incremental).
2. Set up project structure; install dependencies; configure build.
3. Create a minimal entry point — a **running** application (web app dev server serves a page; CLI prints `--help`; API health check returns 200; etc.).
4. Verify build / run / dev loop work.
5. Emit review items for architecture-level findings; auto-resolve environment-level findings when the fix is local.

## What This Skill Does NOT Do

- Set up test infrastructure or write tests — that's `/a4:ci-setup`.
- Write `a4/ci.md` or any other wiki page.
- Implement any UC or feature logic.
- Make architectural decisions — when `architecture.md` is present, all decisions come from it; when absent, scaffold derives the minimum needed from the observed repo state plus user input.

## Workflow

### Step 0: Read sources

Read `a4/architecture.md` if present. Otherwise, derive scope from existing repo files plus the running prompt. No archive step — scaffold is idempotent against the current repo state.

### Steps

| Step | Focus | Procedure |
|------|-------|-----------|
| 1 | Project-state assessment (fresh vs incremental) | `references/codebase-assessment.md` |
| 2 | Project structure + dependencies + build | `references/project-structure.md` |
| 3 | Build / run / dev-loop verification | `references/verification.md` |
| 4 | Issue handling (architecture vs environment) | `references/issue-handling.md` |
| 5 | Commit | `references/commit.md` |

## Session Management

Runs autonomously. No user interaction during execution. On any verification failure that cannot be auto-fixed, the review items document the state — the user decides next steps after reading them.

## Next Step

If any `target: architecture` review items are `status: open`:

> Architecture issues were flagged during scaffold — run `/a4:arch iterate` first to address them, then re-run `/a4:auto-scaffold` (idempotent) and `/a4:ci-setup` to set up the test environment.

If scaffold succeeded with no open architecture issues:

> Scaffold complete. Next, run `/a4:ci-setup` to set up the test environment and write `a4/ci.md`.

## Non-Goals

- Do not write any other wiki page.
- Do not install test runners or write tests.
- Do not attempt to fix architecture issues. Flag them via review items with `target: architecture`.
- Do not maintain archives or revision files.
