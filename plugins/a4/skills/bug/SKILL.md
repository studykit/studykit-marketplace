---
name: bug
description: "This skill should be used when the user wants to log a single bug task — a tracked defect fix against expected behavior. Common triggers: 'log a bug', 'create a bug task', 'open a bug for X', 'track this regression', 'file a bug'. Optional implements: (UC paths the bug traces to) and/or spec: (spec paths whose expected behavior the bug violates); writes a4/bug/<id>-<slug>.md. Single-task entry. For batch UC/spec-driven generation use /a4:breakdown; for the implement loop use /a4:auto-coding; for task/spike/research use the matching skill (/a4:task, /a4:spike, /a4:research); to discard a task use /a4:discard."
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
- Allocated id: !`"${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4" 2>/dev/null || echo ALLOC_FAILED`

If the project root resolved to `NOT_A_GIT_REPO` or `a4/` is missing, abort. Ensure `<project-root>/a4/bug/` exists (`mkdir -p` if missing).

## Author

Use the allocated id above as `id:` and the filename prefix. Follow `${CLAUDE_PLUGIN_ROOT}/authoring/bug-authoring.md` for frontmatter, body shape, initial-status rules, and the `done` preflight. Write to `a4/bug/<id>-<slug>.md`. The body's `## Unit Test Strategy` must include a regression scenario that fails before the fix and passes after — closing a bug without that test is the most common reason the same bug returns. No commit; no implementation agent spawn.
