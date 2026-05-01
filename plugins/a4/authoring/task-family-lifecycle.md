# a4 — task family lifecycle (shared)

> **Audience:** Workspace authors writing `<project-root>/a4/**/*.md` files (or LLMs editing them on the user's behalf). Not for a4 plugin contributors — implementation references live in `../dev/`.

The four task issue families (`task`, `bug`, `spike`, `research`) share **one** lifecycle, status enum, writer rules, and `complete` initial-status preflight. This file is the single source of truth; per-family authoring files cite it and add only family-specific deltas.

> `umbrella` is **not** part of the task family. It is a narrative-aggregation parent with its own lifecycle (`open | complete | discarded`), no implement loop, and no UC-cascade. See `./umbrella-authoring.md`.

## Status enum

`open | pending | progress | complete | failing | discarded`

## Lifecycle

```
open      → discarded | pending | progress | complete
pending   → discarded | progress
progress  → complete | discarded | failing | pending
complete  → discarded | pending
failing   → discarded | pending | progress
discarded → (terminal)
```

## Per-status meaning

- `open` — Backlog (kanban "todo"). Captured but not yet committed to the work queue. Not picked up by the implement loop; transition `open → pending` to enqueue.
- `pending` — In the work queue, awaiting an implementer. Default ready-set entry for the implement loop.
- `progress` — A `coder` agent (or investigator, for `research`) is working (or crashed mid-work — reset to `pending` on session resume).
- `complete` — Work succeeded against the family's success criterion (unit tests passed, hypothesis validated, investigation finalized). **Not** a forward-path terminal — UC `revising` cascade can return tasks to `pending` for re-implementation.
- `failing` — Work could not succeed on this iteration. Resumed via `failing → progress` (immediate retry, same cycle for families that carry `cycle:`) or deferred via `failing → pending` (next cycle, `cycle:` bumps where applicable).
- `discarded` — Abandoned. Terminal. Reached via UC `discarded` cascade or an explicit task-discard.

## Writer rules

- **Allowed initial statuses on file create:** `open` (default — backlog), `pending` (queue-fill intent), `complete` (post-hoc documentation; work already done).
- `progress` and `failing` are **writer-only** — never used as initial statuses. The writer produces them as a result of transitions.
- `open → progress` is allowed (e.g., a `coder` spawned outside the batch loop, or the user starts investigating directly). The `pending` step expresses queue intent; skip it when the queue is not the entry path.
- `open → complete` is allowed for post-hoc closure of backlog items finished outside the implement loop (work already done before the task entered the queue). Required body sections and the `complete` initial-status preflight still apply.
- There is **no `pending → open` reverse** — once enqueued, a task cannot be returned to backlog.
- UC-cascade automatic flips: when a UC flips to `discarded`, related tasks across the four families → `discarded`. When a UC flips to `revising`, tasks at `progress`/`failing` reset to `pending`; `open`/`pending`/`complete` tasks stay. Do not flip these by hand.

## `complete` initial-status preflight

When the chosen initial status is `complete`, the work is asserted to already be shipped/done. Verify before writing:

1. For families with `artifacts:`, confirm every listed path exists (under the project tree for `task`/`bug`/`research`; under `artifacts/spike/<id>-<slug>/` or its archive for `spike`). If any path is missing, halt and ask: (a) fix the path, or (b) downgrade to `pending` so the task enters the implement loop.
2. Required body sections (per the family's authoring contract) must still be present — `complete` does not exempt the task from documentation.
3. If you want the post-hoc origin recorded, append a manual bullet to a `## Log` section (see `./body-conventions.md#log`):

   ```markdown
   ## Log

   - <YYYY-MM-DD> created at status: complete (post-hoc documentation; <work> done prior to task authorship)
   ```

## Family-specific deltas

| Family | Notes |
|---|---|
| `task` | Default family; `cycle:` bumps on `failing → pending`; `complete` means unit tests passed. |
| `bug` | Same as task; `complete` means the regression test passes. |
| `spike` | No `cycle:` field (re-attempts do not bump a counter); `complete` means hypothesis validated; on close, user `git mv`s the artifact directory to `artifacts/spike/archive/<id>-<slug>/`. |
| `research` | No `cycle:`; `complete` means findings written and citable; failure paths are usually `failing → pending` for scope re-framing. |
