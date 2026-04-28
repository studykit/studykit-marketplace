# a4 — spike task authoring

A spike task at `a4/task/spike/<id>-<slug>.md` is a **time-boxed exploration to unblock a decision** (XP sense). PoC, investigation, benchmark — throwaway code. The accompanying code lives at `<project-root>/spike/<id>-<slug>/`, **outside** the `a4/` workspace. For pure written investigation without throwaway code, use `kind: research` instead.

Lifecycle is identical across task kinds (`feature` / `bug` / `spike` / `research`).

Companion to [`./frontmatter-schema.md §Task`](./frontmatter-schema.md), `./body-conventions.md`.

## Frontmatter contract (do not deviate)

```yaml
---
type: task
id: <int — globally monotonic across the workspace>
title: "<short, human-readable phrase>"
kind: spike
status: open | pending | progress | complete | failing | discarded
implements: []         # usually empty for spike (exploratory)
depends_on: []         # list of paths to other tasks
spec: []               # populated when the spike is triggered by a spec's open questions
related: []            # catchall for cross-references
files: []              # paths under spike/<id>-<slug>/ — never project source tree
cycle: 1               # implementation cycle number
labels: []             # free-form tags
milestone: <optional>  # milestone name
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

- `title` is required and must not be a placeholder; the writer rejects `<title>`-shaped strings.
- `kind: spike` is fixed for files under `a4/task/spike/`. Every task must declare the kind explicitly.
- `implements:` is **usually empty** — a spike is exploratory, not a deliverable. Populate only when the PoC validates a hypothesis directly tied to a UC's flow.
- `spec:` lists `spec/<id>-<slug>` paths the spike investigates. Most spikes are spec-triggered; populate this when applicable.
- `files:` paths must live under `spike/<id>-<slug>/...` (or `spike/archive/<id>-<slug>/...` after archive). **Never** point at the project's production source tree — that would defeat the throwaway contract.
- `cycle` starts at `1`; bumped on `failing → pending` next-cycle defers.
- `implemented_by:` is **not** a task field — it is a UC reverse-link written by `refresh_implemented_by.py`. Do not put it on a task.

### Lifecycle and writer ownership

```
open      → discarded | pending | progress
pending   → discarded | progress
progress  → complete | discarded | failing | pending
complete  → discarded | pending
failing   → discarded | pending | progress
discarded → (terminal)
```

Per-status meaning:

- `open` — Backlog. Captured but not yet committed to the work queue. Not picked up by the implement loop; transition `open → pending` to enqueue.
- `pending` — In the work queue, awaiting an implementer.
- `progress` — A `task-implementer` agent is working (or crashed mid-work — reset to `pending` on session resume).
- `complete` — Spike succeeded; hypothesis validated.
- `failing` — Spike could not validate the hypothesis on this iteration. Resumed via `failing → progress` (immediate retry) or deferred via `failing → pending` (next cycle).
- `discarded` — Abandoned. Terminal. Reached via an explicit task-discard (a spike whose hypothesis is no longer worth testing).

Writer rules (task-specific):

- **Allowed initial statuses on file create:** `open` (default — backlog), `pending` (queue-fill intent), `complete` (post-hoc documentation; PoC already done).
- `progress` and `failing` are **writer-only** — never used as initial statuses. The writer produces them as a result of transitions.
- `open → progress` is allowed (e.g., a `task-implementer` spawned outside the batch loop).
- There is **no `pending → open` reverse** — once enqueued, a spike stays enqueued or moves forward / out.

### `complete` initial-status preflight

When the chosen initial status is `complete`, the spike is asserted to already be done. Verify before writing:

1. For each path in `files:`, confirm it exists under `spike/<id>-<slug>/` (or `spike/archive/<id>-<slug>/`). If any path is missing, halt and ask: (a) fix the path, or (b) downgrade to `pending` so the task enters the implement loop.
2. Required body sections (`<description>`, `<files>`, `<unit-test-strategy>`, `<acceptance-criteria>`) must still be present per the body shape below — `complete` does not exempt the task from documentation.
3. After writing the file, append an explicit `<log>` block recording the post-hoc origin:

   ```markdown
   <log>

   - <YYYY-MM-DD> created at status: complete (post-hoc documentation; PoC done prior to task authorship)

   </log>
   ```

   This is the **only** case where `<log>` is written directly — every subsequent entry must come from `transition_status.py`.

## Body shape

(Tag form / link form / H1-forbidden are universal — see `./body-conventions.md`.)

**Required:**

- `<description>` — the question being explored and why a spike (vs. going straight to a feature task). State the hypothesis and the decision the spike's outcome will inform.
- `<files>` — action / path / change table. Every path is under `spike/<id>-<slug>/`.
- `<unit-test-strategy>` — may be a one-line "validate hypothesis via <method>" (benchmark, integration probe, sample-driven check). The section is still required.
- `<acceptance-criteria>` — checklist. AC source: **hypothesis + expected result, the spike's own body** — what observable outcome proves or refutes the question. The `<acceptance-criteria>` section must exist regardless.

**Optional, emit only when there is content for them:**

- `<interface-contracts>` — contracts the spike consumes or proposes, with markdown links to `architecture.md` sections (e.g., `[architecture#SessionService](../../architecture.md#sessionservice)`). May be omitted for self-contained spikes.
- `<change-logs>` — append-only audit trail when the task body is materially edited post-create.
- `<log>` — append-only writer-owned status-transition trail (`YYYY-MM-DD — <from> → <to> — <reason>`). Starts absent — `status: pending` is the implicit creation entry, written by the writer on first transition. **Never write into `<log>` directly**, except for the documented post-hoc-`complete` case above.
- `<why-discarded>` — populated by discard. Dated bullet (`<YYYY-MM-DD> — <reason text>`) appended when the discard reason deserves narrative capture beyond the `<log>` line.

Unknown kebab-case tags are tolerated.

## Spike sidecar convention

For every spike task, accompanying PoC code lives at `<project-root>/spike/<id>-<slug>/`, parallel to (not inside) `a4/`:

```
<project-root>/
  a4/task/spike/<id>-<slug>.md   # task markdown — kind: spike
  spike/<id>-<slug>/             # PoC code, data, scratch notes
    *.py *.json ...
```

The `spike/` directory is part of the project repo (not scratch), is **not validated** by any a4 script (the markdown-only contract of `a4/` is preserved), and is opt-in. `feature`, `bug`, and `research` tasks have no sidecar — `feature` / `bug` `files:` paths point at production source, and `research` typically has no `files:` at all.

When a spike completes (or fails), the directory is manually `git mv`'d to `spike/archive/<id>-<slug>/` and the task's `files:` paths are updated. The move is **never automated**.

## Common mistakes (task-specific)

- **Required section missing** (`<description>`, `<files>`, `<unit-test-strategy>`, `<acceptance-criteria>`).
- **Missing `kind:` frontmatter field** → frontmatter validator error. `kind` has no default.
- **`kind:` value mismatched against folder** — a file under `a4/task/spike/` must declare `kind: spike`. Mismatched declarations are a folder-routing error and should be re-located.
- **`files:` paths under the project source tree, not under `spike/<id>-<slug>/`** — breaks the throwaway contract; the writer refuses.

(Universal body conventions — stray body content, attribute-bearing tags, same-tag nesting, H1 in body — are documented in `./body-conventions.md`.)

## Don't (spike-task-specific)

- **Don't put `implemented_by:` on a task.** It is a UC reverse-link, auto-maintained by `refresh_implemented_by.py` from `task.implements:`.
- **Don't use `progress` or `failing` as an initial status.** They are writer-only, produced by transitions.
- **Don't reverse `pending → open`.** Once enqueued, a spike stays enqueued or moves forward / out.
- **Don't omit `kind:`.** Every task declares `feature | spike | bug | research`.
- **Don't auto-delete or auto-archive `spike/<id>-<slug>/`** on discard. Archiving is a user-driven `git mv`.
- **Don't write production source from a spike.** `files:` paths staying under `spike/<id>-<slug>/` is the contract that keeps PoC code throwaway. If the spike's outcome warrants production work, follow up with a `kind: feature` task.
- **Don't author a `kind: feature` / `bug` / `research` task here.** Move them to the matching `a4/task/<kind>/` so the per-kind authoring contract applies.
