---
name: discard
description: "Discard a tracked a4 task, bug, spike, or research item."
argument-hint: "<id-or-slug> [reason]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, TaskCreate, TaskUpdate, TaskList
---

# Single Task Discard

Discard one task at `a4/<type>/<id>-<slug>.md` (where `<type>` is one of `task`, `bug`, `spike`, `research`). Flips `status:` → `discarded` by editing the frontmatter directly and records the reason in an optional `## Why Discarded` body block.

Seed: **$ARGUMENTS**

## Scope

- **In:** flipping an existing task's `status: → discarded` by editing the frontmatter directly, appending an optional `## Why Discarded` note, advising on the spike artifact directory (no auto-delete).
- **Out:** UC-cascade discards (handled automatically by the PostToolUse cascade hook when a UC flips to `discarded`), authoring (use `/a4:task` / `/a4:bug` / `/a4:spike` / `/a4:research`), implement / test loop (`/a4:auto-coding`). No commit.

## Pre-flight

1. Resolve project root: `git rev-parse --show-toplevel`. If not a git repo, abort.
2. Verify `<project-root>/a4/` exists. If not, abort — this skill is workspace-scoped.
3. Parse `$ARGUMENTS` as `<id-or-slug> [reason]`. If empty, abort with the usage hint:

   > `/a4:discard <id-or-slug> [reason]` — provide a task id, slug fragment, or `<type>/<id>-<slug>` path.

## Procedure

Apply the steps in `references/discard.md`: resolve the target task by id / `<type>/<id>-<slug>` / slug fragment (D1), confirm current status is `open | queued | progress | holding | done | failing` (D2), append an optional `## Why Discarded` block first and then edit `status:` to `discarded` (D3), advise on the spike artifact directory without auto-deleting (D4), and report (D5).

## Commit Points

Commit subject:

```
#<task-id> docs(a4): discard <type> <slug>
```

Suggest the commit when the user confirms; do not auto-commit.

## Wrap Up

After the discard is applied, summarize: task id, type, title, the reason, and any UC links the user may want to revisit. Do not suggest `/a4:auto-coding`. Suggest `/a4:handoff` only if the broader session warrants a snapshot.

## Non-Goals

- Do not delete the task file.
- Do not auto-delete or auto-archive the spike artifact directory.
- Do not discard multiple tasks in one invocation. UC-cascade discards happen automatically when the parent UC is discarded.
- Do not author replacement tasks here — use the matching `/a4:<type>` skill.
