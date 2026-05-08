---
name: task
description: "Author a regular a4 implementation task."
argument-hint: "[title or short description]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, TaskCreate, TaskUpdate, TaskList, WebSearch, WebFetch
---

# Task Author

Writes `a4/task/<id>-<slug>.md` per the authoring contract at `${CLAUDE_PLUGIN_ROOT}/authoring/task-authoring.md`. The `task` family is the default issue family — Jira's "Task" issue type alongside Bug / Spike / Research. No special procedure beyond the contract; this skill is a thin wrapper.

Seed: **$ARGUMENTS**

## Context

- Project root: !`git rev-parse --show-toplevel 2>/dev/null || echo NOT_A_GIT_REPO`
- Today: !`date +%Y-%m-%d`

If the project root resolved to `NOT_A_GIT_REPO` or `a4/` is missing, abort. Ensure `<project-root>/a4/task/` exists (`mkdir -p` if missing).

## Author

Allocate the next id immediately before writing; use it as `id:` and the filename prefix. Follow `${CLAUDE_PLUGIN_ROOT}/authoring/task-authoring.md` for frontmatter, body shape, initial-status rules, and the `done` preflight. Write to `a4/task/<id>-<slug>.md`. No commit; no implementation agent spawn.
