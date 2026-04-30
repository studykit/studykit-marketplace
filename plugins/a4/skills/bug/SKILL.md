---
name: bug
description: "This skill should be used when the user wants to log a single bug task — a tracked defect fix against expected behavior. Common triggers: 'log a bug', 'create a bug task', 'open a bug for X', 'track this regression', 'file a bug'. Optional implements: (UC paths the bug traces to) and/or spec: (spec paths whose expected behavior the bug violates); writes a4/bug/<id>-<slug>.md. Single-task entry. For batch UC-driven generation use /a4:roadmap; for the implement loop use /a4:run; for feature/spike/research use the matching skill (/a4:feature, /a4:spike, /a4:research); to discard a task use /a4:discard."
argument-hint: "[title or short description]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, TaskCreate, TaskUpdate, TaskList, WebSearch, WebFetch
---

# Single Bug Task Author

> **Authoring contract:** `${CLAUDE_PLUGIN_ROOT}/references/bug-authoring.md`. This skill orchestrates writing through that contract.

Writes one `a4/bug/<id>-<slug>.md`. Use when a defect needs a tracked fix; the task lifecycle is identical to feature/spike/research, but the body shape leans on reproduction + regression test.

`/a4:run` is the agent loop that consumes files this skill produces. This skill never spawns implementation agents itself.

Seed: **$ARGUMENTS**

## Scope

- **In:** writing one bug task file at `status: pending` (or `complete` for post-hoc), allocating its id, resolving optional `implements:` / `spec:` references.
- **Out:** UC-batch generation (`/a4:roadmap`), implement / test loop (`/a4:run`), discard (`/a4:discard`), authoring tasks of other families (`/a4:feature`, `/a4:spike`, `/a4:research`). No commit.

## Pre-flight

1. Resolve project root: `git rev-parse --show-toplevel`. If not a git repo, abort.
2. Verify `<project-root>/a4/` exists. If not, abort — this skill is workspace-scoped.
3. Ensure `<project-root>/a4/bug/` exists. Create with `mkdir -p` if missing.

## Author Flow

Steps procedure: `references/author-flow.md`. Covers capture intent (observed vs expected behavior, regression test scope) → resolve implements/spec → compose body → allocate id + write → hand-off.

## Commit Points

`references/commit-points.md`.

## Wrap Up

When the task file is written:

1. Summarize: task id / title, observed vs expected behavior, `implements:` / `spec:` references (or "none").
2. Suggest the next step: `pending` → `/a4:run` (which spawns a `task-implementer` to write the regression test, then the fix).
3. Suggest `/a4:handoff` only if the broader session warrants a snapshot.

## Non-Goals

- Do not run a reviewer agent.
- Do not author multiple bugs in one invocation. Re-invoke `/a4:bug` per bug.
- Do not author non-bug tasks here — use `/a4:feature`, `/a4:spike`, or `/a4:research`.
- Do not flip task status beyond the initial `open` / `pending` / `complete` write.
- Do not ship the fix here — the implement loop (`/a4:run`) covers regression-test-then-fix.
