---
name: task
description: "This skill should be used when the user wants to author a single task — a unit of regular implementation work (new functionality, extension, refactor). Common triggers: 'add a task', 'create a task', 'I need a task for', 'one-off task', 'task for <UC>'. Optional implements: (UC paths) and/or spec: (spec paths); writes a4/task/<id>-<slug>.md. Single-task entry. For bug/spike/research use the matching skill (/a4:bug, /a4:spike, /a4:research); to discard a task use /a4:discard."
argument-hint: "[title or short description]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, TaskCreate, TaskUpdate, TaskList, WebSearch, WebFetch
---

# Single Task Author

> **Authoring contract:** `${CLAUDE_PLUGIN_ROOT}/authoring/task-authoring.md`. This skill orchestrates writing through that contract.

Writes one `a4/task/<id>-<slug>.md`. The `task` family is the default issue family — Jira's "Task" issue type alongside Bug / Spike / Research. Use when a spec-justified task needs implementation in a UC-less or partially-UC project, or when a new ad-hoc task lands after the initial breakdown was authored.

This skill never spawns implementation agents itself.

Seed: **$ARGUMENTS**

## Scope

- **In:** writing one task file at `status: pending` (or `complete` for post-hoc), allocating its id, resolving `implements:` / `spec:` references.
- **Out:** discard (`/a4:discard`), authoring tasks of other issue families (`/a4:bug`, `/a4:spike`, `/a4:research`). No commit.

## Pre-flight

1. Resolve project root: `git rev-parse --show-toplevel`. If not a git repo, abort.
2. Verify `<project-root>/a4/` exists. If not, abort — this skill is workspace-scoped.
3. Ensure `<project-root>/a4/task/` exists. Create with `mkdir -p` if missing.

## Author Flow

Steps procedure: `references/author-flow.md`. Covers capture intent → resolve implements/spec → compose body → allocate id + write → hand-off.

For more single tasks of the same family, re-invoke `/a4:task`.

## Commit Points

`references/commit-points.md`.

## Wrap Up

When the task file is written:

1. Summarize: task id / title, `implements:` / `spec:` references (or "none — AC sourced from <X>").
2. Suggest `/a4:handoff` only if the broader session warrants a snapshot.

## Non-Goals

- Do not run a reviewer agent. Single-task authorship is conversational.
- Do not author multiple tasks in one invocation. Re-invoke `/a4:task` per task.
- Do not author non-task issue families here — use `/a4:bug`, `/a4:spike`, or `/a4:research`.
- Do not write any wiki page; this skill writes a single `a4/task/<id>-<slug>.md` only.
- Do not flip task status beyond the initial `open` / `pending` / `complete` write.
