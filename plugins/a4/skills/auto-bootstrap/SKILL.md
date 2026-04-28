---
name: auto-bootstrap
description: "This skill should be used when the user needs to set up a development base from an architecture document — project structure, dependencies, build configuration, and test infrastructure for each tier. Common triggers include: 'bootstrap', 'set up the project', 'bootstrap the project', 'create the dev environment', 'set up testing'. Applicable after arch finalizes and before plan starts. Writes a4/bootstrap.md (wiki page) with the verified environment and commands."
argument-hint: <optional: pass no argument to use a4/architecture.md; passing a label archives the current bootstrap.md before writing a new one>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, WebSearch, WebFetch, TaskCreate, TaskUpdate, TaskList
---

# Project Bootstrap

> **Authoring contract:** the contract for `a4/bootstrap.md` — frontmatter, body sections (`<environment>` / `<launch>` / `<verify>`), why `<verify>` lives only here, common mistakes, "Don't" list — lives in [`references/bootstrap-authoring.md`](${CLAUDE_PLUGIN_ROOT}/references/bootstrap-authoring.md). This skill is the sole writer.

Takes the architecture in `a4/architecture.md` and sets up a working development base — project structure, dependencies, build configuration, and test infrastructure per tier. Runs autonomously. Produces `a4/bootstrap.md` as a wiki page that is the **single source of truth for Launch & Verify** (build / launch / test / smoke / isolation) per [`references/wiki-authorship.md`](${CLAUDE_PLUGIN_ROOT}/references/wiki-authorship.md). Both `/a4:run` and the `task-implementer` / `test-runner` agents read this file directly; `/a4:roadmap` only links to it.

## Workspace

Resolve `a4/` via `git rev-parse --show-toplevel`. Inputs:

- `a4/architecture.md` — technology stack, components, external dependencies, test strategy (required).
- `a4/usecase/*.md`, `a4/domain.md`, `a4/context.md` — reference-only context.

Outputs:

- `a4/bootstrap.md` — wiki page (`type: bootstrap`).
- `a4/archive/bootstrap-<YYYY-MM-DD>.md` — archived copy of the prior bootstrap.md before iteration (only when iterating).
- `a4/review/<id>-<slug>.md` — per-issue review items for unresolved environment or architecture problems.
- `a4/research/bootstrap-<label>.md` — research reports produced by the `api-researcher` agent when diagnosing issues.

## Bootstrap Wiki Schema

```yaml
---
type: bootstrap
updated: 2026-04-24
---
```

No lifecycle / revision / source SHA fields.

Body sections per `body_schemas/bootstrap.xsd`: required — `<environment>`, `<launch>`, `<verify>`. Optional — `<change-logs>`. The full template is in [`references/bootstrap-md-template.md`](references/bootstrap-md-template.md).

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

## Step 0: Read Sources

Read `a4/architecture.md`. Extract:

- **Technology Stack** — language, framework, platform.
- **Component structure** — component names + which need data stores.
- **Test Strategy** — per-tier tool selections with setup notes.
- **External Dependencies** — what needs to be installed or configured.

Optionally read `a4/context.md` and a small sample of `a4/usecase/*.md` to verify scope assumptions.

If `a4/bootstrap.md` already exists, archive it before proceeding: copy to `a4/archive/bootstrap-<YYYY-MM-DD-HHMM>.md`, then treat this run as **incremental**. Otherwise **fresh**.

## Step 1: Codebase Assessment

Two orthogonal axes determine the work scope here — both must be resolved.

**Axis 1 — project state (fresh vs incremental).**

- **No existing code** → fresh bootstrap (Step 2 onwards).
- **Existing code** → incremental. Identify what's already present (project structure, dependencies, build config, test setup). Only set up what's missing. Do not overwrite existing working configuration without cause.

**Axis 2 — pipeline shape (Full vs Minimal).** See [`references/pipeline-shapes.md`](${CLAUDE_PLUGIN_ROOT}/references/pipeline-shapes.md) for shape definitions.

- **Full shape** (`architecture.md` is the input) — extract Technology Stack, Component structure, Test Strategy, External Dependencies from `architecture.md` per Step 0 and execute against that. This is the canonical case.
- **Minimal shape** (`architecture.md` may be absent) — when invoked directly without architecture authoring (e.g., a brownfield single-change project entering through `/a4:task`), derive build / launch / test commands from the observed project state plus minimal user input. Produce a `bootstrap.md` that captures the verified L&V commands; do not back-fill an `architecture.md`. The bootstrap wiki page itself is the only required anchor in Minimal shape.

The two axes combine: greenfield + Full is the canonical greenfield bootstrap; brownfield + Full is the incremental case after `/a4:arch` has run; brownfield + Minimal is the single-change case where `architecture.md` does not exist.

## Step 2: Project Structure

Based on the Technology Stack and Component structure:

1. Create directory structure following framework conventions.
2. Initialize project files (`package.json`, `pyproject.toml`, `Cargo.toml`, etc.).
3. Install dependencies from Technology Stack + External Dependencies.
4. Configure build (`tsconfig`, `vite.config`, `esbuild`, etc.).
5. Create a minimal entry point: a **running** application, not just a compile target. Web app → dev server serves a page. VS Code extension → extension activates + panel opens. CLI → `--help` prints usage. API → health check returns 200.

## Step 3: Test Infrastructure

For each tier in Test Strategy:

1. Install test dependencies (runner + assertion lib + plugins).
2. Create test configuration file (`vitest.config.ts`, `.vscode-test.js`, `wdio.conf.ts`, etc.).
3. Write one minimal passing test per tier (unit: import + assert true; integration: verify host environment reachable; E2E: launch app + verify main view loads).
4. Add package scripts (`test`, `test:integration`, `test:e2e`) or equivalent.
5. Verify tier isolation — tests in one tier do not interfere with others.

Use Test Strategy's **setup notes** from `architecture.md`. Apply specific flags — e.g., `--disable-extensions` for VS Code, temp user-data-dir for Electron.

## Step 4: Verification

Run each check and record the outcome:

- **Build** — build command exits 0.
- **Run** — launch command starts the app without error; clean up.
- **Unit tests** — unit runner exits 0 with at least one passing test.
- **Integration tests** — integration runner exits 0 with at least one passing test.
- **E2E tests** *(if applicable)* — E2E runner exits 0 with at least one passing test.
- **Dev loop** — trivial source edit → rebuild → tests re-run successfully.

## Step 5: Handle Issues

For each Step 4 verification failure: classify as architecture vs environment, run the `api-researcher` agent before attempting any environment fix (no guessing), then emit a review item using one of the three templates. Diagnosis taxonomy, agent procedure, and the architecture / environment-auto-fixed / environment-unresolved review-item YAML templates are in [`references/issue-handling.md`](references/issue-handling.md). Read that file when a verification step fails.

## Step 6: Write bootstrap.md

Use the markdown scaffold in [`references/bootstrap-md-template.md`](references/bootstrap-md-template.md). The body has three required tag sections — `<environment>`, `<launch>`, `<verify>` — plus an optional `<change-logs>`. Fresh run uses `Write`; incremental run uses `Edit` to touch only the changed sections plus a new `<change-logs>` bullet (typically citing `[architecture](architecture.md)`).

## Step 7: Drift Detection

Before committing, run the shared drift detector against `a4/`. It scans every wiki page's `<change-logs>` plus every issue file's frontmatter and emits one review item per detected drift (stale links, close-guard violations, missing wiki pages):

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/drift_detector.py" "$(git rev-parse --show-toplevel)/a4"
```

The detector deduplicates against existing open / in-progress / discarded `source: drift-detector` items, so re-running is safe. Findings target the affected wiki page (e.g., `target: architecture`) with `wiki_impact: [<wiki>]` set, so they enter the unified review-item flow alongside the architecture/environment items emitted in Step 5. Use `--dry-run` to inspect findings before writing.

## Step 8: Commit

Stage `a4/bootstrap.md`, any emitted review items (including any from Step 7's drift detection), research reports, and all bootstrap-configured project files (package.json, test config, sample tests, etc.). Single commit:

```
bootstrap: <fresh | iterate>

- Build: PASS | FAIL
- Test tiers: N/M passing
- Dev loop: PASS | FAIL
- Issues: <open-archive-count> open
```

Never skip hooks, amend, or force-push.

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
