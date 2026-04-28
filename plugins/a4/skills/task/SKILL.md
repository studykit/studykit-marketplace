---
name: task
description: "This skill should be used when the user wants to author a single ad-hoc task outside the UC-batch path that /a4:roadmap takes, OR to discard an existing task. Common authoring triggers: 'add a task', 'create a task', 'spike on X', 'log a bug', 'I need a task for', 'one-off task'. Common discard triggers: 'discard task <id>', 'drop task <id>', 'abandon this task', 'task <id> is no longer needed'. Authoring required argument: kind (feature | spike | bug); optional implements: (UC paths) and/or spec: (spec paths); writes a4/task/<kind>/<id>-<slug>.md; for kind: spike also proposes a project-root spike/<id>-<slug>/ sidecar. Discard form: `discard <id-or-slug> [reason]`; flips status via transition_status.py and appends a `<why-discarded>` note. Single-task entry. Use /a4:roadmap for batch UC-driven generation; use /a4:run to drive the implement loop."
argument-hint: "kind=<feature|spike|bug> [title] | discard <id-or-slug> [reason]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, TaskCreate, TaskUpdate, TaskList
---

# Single Task Author + Discard

> **Authoring contracts:** per-kind authoring references — `${CLAUDE_PLUGIN_ROOT}/references/task-feature-authoring.md`, `${CLAUDE_PLUGIN_ROOT}/references/task-bug-authoring.md`, `${CLAUDE_PLUGIN_ROOT}/references/task-spike-authoring.md`. This skill orchestrates writing through those contracts.

Two modes:

- **Author** (default) — writes one `a4/task/<kind>/<id>-<slug>.md` (under `feature/`, `bug/`, or `spike/`) outside the UC-batch path. Co-exists with `/a4:roadmap` (batch UC-driven generation). Use when a spike is needed to unblock an architecture or decision question; a bug needs a tracked fix; a spec-justified feature needs implementation in a UC-less or partially-UC project; a new feature task lands after the initial roadmap was authored.
- **Discard** — `discard <id-or-slug> [reason]`. Flips an existing task's `status: → discarded` via `transition_status.py` and records the reason. Use when a task is abandoned independent of any UC cascade.

`/a4:run` is the agent loop that consumes files this skill produces. This skill never spawns implementation agents itself.

Seed: **$ARGUMENTS**

## Scope

- **In (author mode):** writing one task file at `status: pending`, allocating its id, resolving `implements:` / `spec:` references, proposing the `spike/<id>-<slug>/` sidecar for `kind: spike`, refreshing `implemented_by:` on referenced UCs.
- **In (discard mode):** flipping an existing task's `status: → discarded` via `transition_status.py`, appending an optional `<why-discarded>` note, advising on the spike sidecar (no auto-delete).
- **Out:** UC-batch generation (`/a4:roadmap`), implement / test loop (`/a4:run`), automated reviewer. No commit.

## Pre-flight

1. Resolve project root: `git rev-parse --show-toplevel`. If not a git repo, abort.
2. Verify `<project-root>/a4/` exists. If not, abort — this skill is workspace-scoped.
3. Ensure the kind subfolder exists: `<project-root>/a4/task/<kind>/`. Create with `mkdir -p` if missing.
4. **Mode dispatch.** Read the first whitespace-delimited token of `$ARGUMENTS`:
   - If the token is exactly `discard` (lowercase), this is **discard mode** — jump to "## Discard mode" below; skip Steps 1–8.
   - Otherwise this is **author mode** — continue with Step 5.
5. Parse `kind` from the argument or the recent conversation. **`kind` is required for author mode**; if absent or not one of `feature | spike | bug`, ask the user once which kind this task is.

## Author Mode Flow

Steps 1–8 procedure: `references/author-flow.md`. Covers capture intent → resolve implements/spec → compose body → spike sidecar proposal → allocate id + write → refresh implemented_by → spike sidecar create → hand-off.

For more single tasks, re-invoke `/a4:task`. If the user wants the task implemented immediately and no other ready tasks are pending, they may invoke `/a4:run` directly.

## Discard mode

Triggered when `$ARGUMENTS` starts with the token `discard`. Apply the procedure in `references/discard.md`: resolve the target task by id / `task/<id>-<slug>` / slug fragment (D1), confirm current status is `open | pending | progress | complete | failing` (D2), flip via `transition_status.py --to discarded` and append an optional `<why-discarded>` block (D3), advise on the spike sidecar without auto-deleting (D4), skip `refresh_implemented_by.py` since `implements:` did not change (D5), and report (D6). UC-cascade discards are handled automatically by `transition_status.py`.

## Commit Points

Per-mode subject formats and timing: `references/commit-points.md`.

## Wrap Up

**Author mode** — when the task file is written:

1. Summarize: task id / title / kind, `implements:` / `spec:` references (or "none — AC sourced from <X>"), whether the spike sidecar was created, files updated by `refresh_implemented_by.py`.
2. Suggest `/a4:run` as the next step.
3. Suggest `/a4:handoff` only if the broader session warrants a snapshot.

**Discard mode** — D6 in `references/discard.md` produces the summary. Do not suggest `/a4:run`. Suggest `/a4:handoff` only if the broader session warrants a snapshot.

## Non-Goals

- Do not run a reviewer agent. Single-task authorship is conversational.
- Do not author multiple tasks in one invocation. Re-invoke `/a4:task` per task. Use `/a4:roadmap` for the batch path.
- Do not discard multiple tasks in one invocation. UC-cascade discards happen automatically when the parent UC is discarded.
- Do not write `roadmap.md`. If the project has no roadmap and the user wants one, redirect to `/a4:roadmap`. Single tasks are valid without a roadmap.
- Do not flip task status beyond the initial `open` / `pending` / `complete` write (author mode) or the explicit `→ discarded` flip (discard mode).
- Do not auto-delete or auto-archive `spike/<id>-<slug>/` on discard.
- Do not delete the task file on discard.
