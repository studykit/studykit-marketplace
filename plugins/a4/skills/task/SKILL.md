---
name: task
description: "This skill should be used when the user wants to author a single task — a unit of regular implementation work (new functionality, extension, refactor) — outside the UC-batch path that /a4:roadmap takes. Common triggers: 'add a task', 'create a task', 'I need a task for', 'one-off task', 'task for <UC>'. Optional implements: (UC paths) and/or spec: (spec paths); writes a4/task/<id>-<slug>.md. Single-task entry. For batch UC-driven generation use /a4:roadmap; for the implement loop use /a4:run; for bug/spike/research use the matching skill (/a4:bug, /a4:spike, /a4:research); to discard a task use /a4:discard."
argument-hint: "[title or short description]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, TaskCreate, TaskUpdate, TaskList, WebSearch, WebFetch
---

# Single Task Author

> **Authoring contract:** `${CLAUDE_PLUGIN_ROOT}/authoring/task-authoring.md`. This skill orchestrates writing through that contract.

Writes one `a4/task/<id>-<slug>.md` outside the UC-batch path. The `task` family is the default issue family — Jira's "Task" issue type alongside Bug / Spike / Research. Co-exists with `/a4:roadmap` (batch UC-driven generation). Use when a spec-justified task needs implementation in a UC-less or partially-UC project, or when a new task lands after the initial roadmap was authored.

`/a4:run` is the agent loop that consumes files this skill produces. This skill never spawns implementation agents itself.

Seed: **$ARGUMENTS**

## Scope

- **In:** writing one task file at `status: pending` (or `complete` for post-hoc), allocating its id, resolving `implements:` / `spec:` references.
- **Out:** UC-batch generation (`/a4:roadmap`), implement / test loop (`/a4:run`), discard (`/a4:discard`), authoring tasks of other issue families (`/a4:bug`, `/a4:spike`, `/a4:research`). No commit.

## Pre-flight

1. Resolve project root: `git rev-parse --show-toplevel`. If not a git repo, abort.
2. Verify `<project-root>/a4/` exists. If not, abort — this skill is workspace-scoped.
3. Ensure `<project-root>/a4/task/` exists. Create with `mkdir -p` if missing.

## Author Flow

Steps procedure: `references/author-flow.md`. Covers capture intent → resolve implements/spec → compose body → allocate id + write → hand-off.

For more single tasks of the same family, re-invoke `/a4:task`. If the user wants the task implemented immediately and no other ready tasks are pending, they may invoke `/a4:run` directly.

## Commit Points

`references/commit-points.md`.

## Wrap Up

When the task file is written:

1. Summarize: task id / title, `implements:` / `spec:` references (or "none — AC sourced from <X>").
2. Suggest the next step: `pending` → `/a4:run`.
3. Suggest `/a4:handoff` only if the broader session warrants a snapshot.

## Non-Goals

- Do not run a reviewer agent. Single-task authorship is conversational.
- Do not author multiple tasks in one invocation. Re-invoke `/a4:task` per task. Use `/a4:roadmap` for the batch path.
- Do not author non-task issue families here — use `/a4:bug`, `/a4:spike`, or `/a4:research`.
- Do not write `roadmap.md`. If the project has no roadmap and the user wants one, redirect to `/a4:roadmap`.
- Do not flip task status beyond the initial `open` / `pending` / `complete` write.
