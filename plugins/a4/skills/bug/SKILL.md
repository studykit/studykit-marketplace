---
name: bug
description: "Log a tracked a4 bug fix task."
argument-hint: "[title or short description]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, TaskCreate, TaskUpdate, TaskList, WebSearch, WebFetch
---

# Single Bug Task Author

Writes one `a4/bug/<id>-<slug>.md` per the authoring contract at `${CLAUDE_PLUGIN_ROOT}/authoring/bug-authoring.md`. The bug family carries the same lifecycle as task/spike/research, but the body shape leans on reproduction + regression test. No special procedure beyond the contract; this skill is a thin wrapper.

Seed: **$ARGUMENTS**

## Context

- Project root: !`git rev-parse --show-toplevel 2>/dev/null || echo NOT_A_GIT_REPO`
- Today: !`date +%Y-%m-%d`

If the project root resolved to `NOT_A_GIT_REPO` or `a4/` is missing, abort. Ensure `<project-root>/a4/bug/` exists (`mkdir -p` if missing).

## Author

Allocate the next id immediately before writing; use it as `id:` and the filename prefix. Follow `${CLAUDE_PLUGIN_ROOT}/authoring/bug-authoring.md` for frontmatter, body shape, initial-status rules, and the `done` preflight. Write to `a4/bug/<id>-<slug>.md`. The body's `## Unit Test Strategy` must include a regression scenario that fails before the fix and passes after — closing a bug without that test is the most common reason the same bug returns. No commit; no implementation agent spawn.
