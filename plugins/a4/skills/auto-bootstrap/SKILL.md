---
name: auto-bootstrap
description: "This skill should be used when the user needs to set up a development base from an architecture document — project structure, dependencies, build configuration, and test infrastructure for each tier. Common triggers include: 'bootstrap', 'set up the project', 'bootstrap the project', 'create the dev environment', 'set up testing'. Applicable after arch finalizes and before plan starts. Writes a4/bootstrap.md (wiki page) with the verified environment and commands."
argument-hint: <optional: pass no argument to use a4/architecture.md; passing a label archives the current bootstrap.md before writing a new one>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, WebSearch, WebFetch, TaskCreate, TaskUpdate, TaskList
---

# Project Bootstrap

> **Authoring contract:** `${CLAUDE_PLUGIN_ROOT}/references/bootstrap-authoring.md`. This skill is the sole writer for `a4/bootstrap.md`.

Takes the architecture in `a4/architecture.md` and sets up a working development base — project structure, dependencies, build configuration, and test infrastructure per tier. Runs autonomously. Produces `a4/bootstrap.md` as a wiki page that is the **single source of truth for Launch & Verify** per `${CLAUDE_PLUGIN_ROOT}/docs/wiki-authorship.md`. Both `/a4:run` and the `task-implementer` / `test-runner` agents read this file directly; `/a4:roadmap` only links to it.

## Workspace

Resolve `a4/` via `git rev-parse --show-toplevel`.

**Inputs:**

- `a4/architecture.md` — technology stack, components, external dependencies, test strategy (required for Full shape).
- `a4/usecase/*.md`, `a4/domain.md`, `a4/context.md` — reference-only context.

**Outputs:**

- `a4/bootstrap.md` — wiki page (`type: bootstrap`).
- `a4/archive/bootstrap-<YYYY-MM-DD>.md` — archived copy before iteration.
- `a4/review/<id>-<slug>.md` — per-issue review items.
- `a4/research/bootstrap-<label>.md` — research reports from `api-researcher`.

## What This Skill Does

1. Sets up project structure; installs dependencies; configures build.
2. Sets up test infrastructure per tier defined in `architecture.md` Test Strategy.
3. Verifies build / run / test runners / edit-build-test dev loop actually work.
4. Writes `a4/bootstrap.md` summarizing verified commands and results.
5. Emits review items for issues (environment-level fixable ones marked resolved after fix; architecture-level ones left open with `target: architecture`).
6. Runs the shared drift detector to surface wiki↔issue inconsistencies as additional review items.

## What This Skill Does NOT Do

- Implement any UC or feature logic.
- Write feature tests.
- Make architectural decisions — all decisions come from `architecture.md`.

## Workflow

### Step 0: Read sources

Read `a4/architecture.md`. Extract Technology Stack, Component structure, Test Strategy, External Dependencies. Optionally read `a4/context.md` and a small sample of `a4/usecase/*.md` to verify scope assumptions.

If `a4/bootstrap.md` already exists, archive it before proceeding: copy to `a4/archive/bootstrap-<YYYY-MM-DD-HHMM>.md`, then treat this run as **incremental**. Otherwise **fresh**.

### Steps

| Step | Focus | Procedure |
|------|-------|-----------|
| 1 | Codebase assessment (project state × pipeline shape) | `references/codebase-assessment.md` |
| 2 | Project structure + dependencies + build | `references/project-structure.md` |
| 3 | Test infrastructure per tier | `references/test-infrastructure.md` |
| 4 | Verification checklist | `references/verification.md` |
| 5 | Handle issues (architecture vs environment classification) | `references/issue-handling.md` |
| 6 | Write bootstrap.md (template + edit/write rule) | `references/bootstrap-md-template.md` |
| 7 | Drift detection | see below |
| 8 | Commit | `references/commit.md` |

### Step 7: Drift Detection

Before committing, run the shared drift detector against `a4/`:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/drift_detector.py" "$(git rev-parse --show-toplevel)/a4"
```

It deduplicates against existing open / in-progress / discarded `source: drift-detector` items, so re-running is safe. Findings target the affected wiki page (e.g., `target: architecture`) with `wiki_impact: [<wiki>]`, entering the unified review-item flow alongside Step 5 items. Use `--dry-run` to inspect before writing.

## Session Management

Runs autonomously. No user interaction during execution. On any verification failure that cannot be auto-fixed, the review items and `bootstrap.md` document the state — the user decides next steps after reading them.

## Next Step

After the commit lands, suggest:

> The dev environment is ready. Run `/a4:roadmap` to generate an implementation roadmap from the architecture and this bootstrap.

If any `target: architecture` review items are `status: open`:

> Architecture issues were flagged during bootstrap — run `/a4:arch iterate` first to address them, then re-run `/a4:auto-bootstrap`.

## Non-Goals

- Do not write per-topic / per-slug bootstrap files. `a4/bootstrap.md` is the single wiki page.
- Do not maintain `.bootstrap.r<N>.md` revision files. Archives go to `a4/archive/bootstrap-<date>.md`.
- Do not emit aggregated bootstrap reports separate from `bootstrap.md`. Issues are review items; the wiki page summarizes.
- Do not attempt to fix architecture issues. Flag them via review items with `target: architecture`.
