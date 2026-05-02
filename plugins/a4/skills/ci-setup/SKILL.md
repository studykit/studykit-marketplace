---
name: ci-setup
description: "This skill should be used when the user needs the LLM to set up or update the CI / test environment — installing test runners (unit + integration), creating runner configuration, writing one minimal passing test per tier, wiring task entry points, and writing a4/ci.md as the test-execution reference. Common triggers include: 'set up testing', 'add integration tests', 'set up CI', 'write ci.md', 'update test environment'. Re-callable any time test infrastructure evolves."
argument-hint: "(no argument) — set up or update test environment against the current project state."
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, WebSearch, WebFetch, TaskCreate, TaskUpdate, TaskList
---

# CI / Test Environment Setup

Sets up unit + integration test infrastructure (runners, fixtures, sample tests, task entry points) and writes `a4/ci.md` — the project's reference for how the LLM (or a human) verifies any feature change. Runs autonomously. Re-callable: each invocation reconciles the test environment against the current repo state and rewrites `a4/ci.md` accordingly.

## Workspace

Resolve `a4/` and the project root via `git rev-parse --show-toplevel`.

**Inputs (all optional — read whichever exist for context):**

- `a4/architecture.md` — Test Strategy section (which tiers, which tools), when present.
- Existing test files / configs in the repo — when present, treat as ground truth; only set up what is missing.

**Outputs:**

- `a4/ci.md` — wiki page (`type: ci`). Required sections: `## How to run tests`, `## Test layout`. Other sections free-form.
- Test runner configuration files in the repo (e.g., `vitest.config.ts`, `pytest.ini`, `wdio.conf.ts`).
- One minimal passing test per tier installed.
- Task entry points wired (e.g., `npm test` / `npm run test:integration`).
- `a4/review/<id>-<slug>.md` — review items emitted when test setup uncovers architecture-level issues.
- `a4/research/ci-<label>.md` — research reports from `api-researcher` when an environment fix needs library / docs lookup.

## What This Skill Does

1. Identify which test tiers are needed (from `architecture.md` Test Strategy or, when absent, from project type plus user input — at minimum unit; add integration when the project has external boundaries).
2. Install test dependencies, create runner config, write one minimal passing test per tier, wire task entry points.
3. Verify each tier runs cleanly and tier isolation holds.
4. Write `a4/ci.md` with the verified commands, layout, and any tier-specific isolation notes.
5. Emit review items for architecture-level findings; auto-resolve environment-level ones when local fixes apply.

## What This Skill Does NOT Do

- Scaffold the project — that's `/a4:auto-scaffold`.
- Implement feature tests — only one minimal passing test per tier as a smoke check.
- Make architectural decisions about test strategy — when `architecture.md` is present, use its Test Strategy; when absent, derive a minimum + ask the user for the missing pieces.

## Workflow

### Step 0: Read sources

Read `a4/architecture.md` if present (Test Strategy section). Otherwise, derive scope from observed project state plus user input. Inspect existing test config and decide which tiers already exist.

### Steps

| Step | Focus | Procedure |
|------|-------|-----------|
| 1 | Test-tier assessment (which tiers, what's already present) | `references/tier-assessment.md` |
| 2 | Install runners + configs + minimal tests + task entry points | `references/test-infrastructure.md` |
| 3 | Per-tier execution + tier-isolation verification | `references/verification.md` |
| 4 | Issue handling (architecture vs environment) | `references/issue-handling.md` |
| 5 | Write `a4/ci.md` (template + edit/write rule) | `references/ci-md-template.md` |
| 6 | Commit | `references/commit.md` |

## Re-Run Behavior

`/a4:ci-setup` is idempotent against the current repo state. On re-run:

- Existing runner configs / sample tests are preserved unless the test strategy changed.
- `a4/ci.md` is **edited** (not overwritten) — only sections whose underlying state changed are rewritten, and a `## Change Logs` bullet records why.
- New tiers are added; obsolete tiers are removed and noted in `## Change Logs`.

## Session Management

Runs autonomously. No user interaction during execution. On any verification failure that cannot be auto-fixed, the review items document the state — the user decides next steps.

## Next Step

If any `target: architecture` review items are `status: open`:

> Architecture issues were flagged during ci-setup — run `/a4:arch iterate` first to address them, then re-run `/a4:ci-setup`.

## Non-Goals

- Do not write `a4/bootstrap.md` (the type was retired). `a4/ci.md` is the single test-environment wiki page.
- Do not write feature-level tests; only minimal smoke tests per tier.
- Do not attempt to fix architecture issues. Flag them via review items with `target: architecture`.
- Do not maintain archives or revision files — `## Change Logs` carries the history.
