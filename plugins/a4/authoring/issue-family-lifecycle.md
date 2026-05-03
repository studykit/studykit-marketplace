# a4 — issue family lifecycle (shared)

The four issue families (`task`, `bug`, `spike`, `research`) share **one** lifecycle, status enum, writer rules, and `done` initial-status preflight. This file is the single source of truth; per-family authoring files cite it and add only family-specific deltas.

> `umbrella` is **not** part of the issue family. It is a narrative-aggregation parent with its own lifecycle (`open | done | discarded`), no implement loop, and no UC-cascade. See `./umbrella-authoring.md`.

## Status enum

`open | queued | progress | holding | done | failing | discarded`

## Lifecycle

```
open      → discarded | queued | progress | done
queued    → discarded | progress
progress  → done | discarded | failing | queued | holding
holding   → progress | discarded
done      → discarded | queued
failing   → discarded | queued | progress
discarded → (terminal)
```

## Per-status meaning

- `open` — Backlog (kanban "todo"). Captured but not yet committed to the work queue. Not picked up by the implement loop; transition `open → queued` to enqueue.
- `queued` — In the work queue, awaiting an implementer. Default ready-set entry for the implement loop.
- `progress` — A `coder` agent (or investigator, for `research`) is working (or crashed mid-work — reset to `queued` on session resume).
- `holding` — Work was started but is **temporarily paused by an explicit human or agent decision** (e.g., blocking dependency surfaced, awaiting an external answer, scope of the in-flight work needs broader thought before resuming). Distinct from `failing` (the iteration ran and did not succeed) and from `queued` (work has not started yet). Not picked up by the implement loop — resume requires a manual `holding → progress` flip.
- `done` — Work succeeded against the family's success criterion (unit tests passed, hypothesis validated, investigation finalized). **Not** a forward-path terminal — UC `revising` cascade can return tasks to `queued`.
- `failing` — Work could not succeed on this iteration. Resumed via `failing → progress` (immediate retry, same cycle for families that carry `cycle:`) or deferred via `failing → queued` (next cycle, `cycle:` bumps where applicable).
- `discarded` — Abandoned. Terminal. Reached via UC `discarded` cascade or an explicit task-discard.

## Writer rules

- **Allowed initial statuses on file create:** `open` (default — backlog), `queued` (queue-fill intent), `done` (post-hoc documentation; work already done).
- `progress`, `holding`, and `failing` are **writer-only** — never used as initial statuses. The writer produces them as a result of transitions on a file already in the workspace.
- `open → progress` is allowed (e.g., a `coder` spawned outside the batch loop, or the user starts investigating directly). The `queued` step expresses queue intent; skip it when the queue is not the entry path.
- `open → done` is allowed for post-hoc closure of backlog items finished outside the implement loop. Required body sections and the `done` initial-status preflight still apply.
- There is **no `queued → open` reverse** — once enqueued, a task cannot be returned to backlog.
- `holding` is reachable only from `progress` (i.e., work that was actually started, then paused). Reaching `holding` from any other state is illegal — if work has not begun yet, leave the file at `open` / `queued`. Resume via `holding → progress`; abandon via `holding → discarded`. There is no automatic exit; a paused task stays paused until a writer flips it.
- UC-cascade automatic flips: when a UC flips to `discarded`, related tasks across the four families → `discarded`. When a UC flips to `revising`, tasks at `progress`/`failing` reset to `queued`; `open`/`queued`/`holding`/`done` tasks stay. (`holding` is exempt because the pause carries explicit human stewardship.) Do not flip these by hand.
- **Flip `status:` when starting work.** Before the first source edit, flip to `progress` (`queued → progress`, or `open → progress` if the queue step was skipped, or `holding → progress` when resuming). The writer is whoever is doing the work; `status:` is never auto-flipped.

## `done` initial-status preflight

When the chosen initial status is `done`, the work is asserted to already be shipped/done. Verify before writing:

1. For families with `artifacts:`, confirm every listed path exists (under the project tree for `task`/`bug`/`research`; under `artifacts/spike/<id>-<slug>/` or its archive for `spike`). If any path is missing, halt and ask: (a) fix the path, or (b) downgrade to `queued` so the task enters the implement loop.
2. Required body sections (per the family's authoring contract) must still be present — `done` does not exempt the task from documentation.
3. If you want the post-hoc origin recorded, append a manual bullet to a `## Log` section (see `./issue-body.md#log`):

   ```markdown
   ## Log

   - <YYYY-MM-DD HH:mm> authored at status: done (post-hoc documentation; <work> done prior to task authorship at <YYYY-MM-DD>)
   ```

## Family-specific deltas

| Family | Notes |
|---|---|
| `task` | Default family; `cycle:` bumps on `failing → queued`; `done` means unit tests passed. |
| `bug` | Same as task; `done` means the regression test passes. |
| `spike` | No `cycle:` field (re-attempts do not bump a counter); `done` means hypothesis validated; on close, user `git mv`s the artifact directory to `artifacts/spike/archive/<id>-<slug>/`. |
| `research` | No `cycle:`; `done` means findings written and citable; failure paths are usually `failing → queued` for scope re-framing. |
