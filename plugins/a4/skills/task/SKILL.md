---
name: task
description: "This skill should be used when the user wants to author a task — a unit of regular implementation work (new functionality, extension, refactor). Common triggers: 'add a task', 'create a task', 'I need a task for', 'task for <UC>'. Optional implements: (UC paths) and/or spec: (spec paths); writes a4/task/<id>-<slug>.md. For bug/spike/research use the matching skill (/a4:bug, /a4:spike, /a4:research); to discard a task use /a4:discard."
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
- Next id: !`"${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4" 2>/dev/null || echo ALLOC_FAILED`

If the project root resolved to `NOT_A_GIT_REPO` or `a4/` is missing, abort. Ensure `<project-root>/a4/task/` exists (`mkdir -p` if missing).

## Author

Use the next id above as `id:` and the filename prefix. Follow `${CLAUDE_PLUGIN_ROOT}/authoring/task-authoring.md` for frontmatter, body shape, initial-status rules, and the `complete` preflight. Write to `a4/task/<id>-<slug>.md`. No commit; no implementation agent spawn.
