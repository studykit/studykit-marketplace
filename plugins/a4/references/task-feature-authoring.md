# a4 — feature task authoring

A feature task at `a4/task/feature/<id>-<slug>.md` is a **unit of regular implementation work** — new functionality, extension, or refactor. The default task kind in the Jira sense.

Lifecycle is identical across task kinds (`feature` / `bug` / `spike`). Tasks are produced by `/a4:task` (single ad-hoc) or `/a4:roadmap` (UC-batch); they are consumed by `/a4:run` (the implement + test loop) and the `task-implementer` agent.

Companion to [`./frontmatter-schema.md §Task`](./frontmatter-schema.md), `./spec-triggers.md`, `./body-conventions.md`.

## How to author — always via `/a4:task` or `/a4:roadmap`

Do **not** hand-craft a task file with `Write`. Always invoke the authoring skill so id allocation, slug derivation, frontmatter shape, body validation, `implements:` / `spec:` resolution, and the `implemented_by:` reverse-link refresh all run through the same code path.

- **`/a4:task`** — single ad-hoc feature task outside the UC-batch path. Use for a one-off feature that lands after the roadmap, or for post-hoc complete documentation of code already shipped.
- **`/a4:roadmap`** — batch generation of the full UC-driven task set in one go. Always writes new tasks at `pending` (queue-fill intent).
- **`/a4:task discard <id-or-slug> [reason]`** — explicit one-off discard. Flips `status: → discarded` via `transition_status.py` and appends an optional `<why-discarded>` body block. UC-cascade discards (when a UC flips to `discarded`) happen automatically — do not duplicate that path.

If you must read a task to answer a question, prefer `extract_section.py <file> <tag>` over loading the whole file.

## Frontmatter contract (do not deviate)

```yaml
---
type: task
id: <int — globally monotonic across the workspace>
title: "<short, human-readable phrase>"
kind: feature
status: open | pending | progress | complete | failing | discarded
implements: []         # list of paths, e.g. [usecase/3-search-history]
depends_on: []         # list of paths to other tasks
spec: []               # list of paths, e.g. [spec/8-caching-strategy]
related: []            # catchall for cross-references
files: []              # source paths the task writes or modifies
cycle: 1               # implementation cycle number
labels: []             # free-form tags
milestone: <optional>  # milestone name
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

- `title` is required and must not be a placeholder; the writer rejects `<title>`-shaped strings.
- `kind: feature` is fixed for files under `a4/task/feature/`. Every task must declare the kind explicitly.
- `implements:` lists `usecase/<id>-<slug>` paths the task delivers. Declare it whenever the project is UC-driven.
- `spec:` lists `spec/<id>-<slug>` paths backing the task. Declare it in UC-less projects (the spec's `decision:` + relevant `architecture.md` section becomes the AC source).
- `implements:` and `spec:` are **optional and orthogonal** — a task may declare zero, one, or both. See the smell check below for the zero-anchor case.
- `files:` paths point at the project's production source tree.
- `cycle` starts at `1`; bumped by `/a4:run` on `failing → pending` next-cycle defers.
- `implemented_by:` is **not** a task field — it is a UC reverse-link written by `refresh_implemented_by.py`. Do not put it on a task.

### `kind: feature` with empty `implements:` and `spec:` — smell check

A `feature` task with **both** anchors empty has no AC source. The authoring skill asks where the AC will be drawn from; downgrade to `spike` (and move the file to `a4/task/spike/`) if the work is genuinely exploratory, or attach an anchor.

Empty anchors are not always a problem — small UI tweaks, single-property validations, and roadmap-auto-generated features without a UC group can legitimately stay anchorless. The deeper signal is in the body: when the description implies a user-facing scope no existing UC covers, or an architectural choice no existing spec records, this is **content-aware upward propagation** per `./spec-triggers.md`. Surface the gap as a review item with `kind: gap`, `target: usecase/` or `target: spec/` (omit `target:` for cross-cutting), `source: task`, body specifying which upstream artifact appears missing. The user resolves by authoring the upstream and re-linking, or closing the review with `discarded` + rationale.

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

- `open` — Backlog (kanban "todo"). Captured but not yet committed to the work queue. Not picked up by `/a4:run`; user must transition `open → pending` to enqueue.
- `pending` — In the work queue, awaiting an implementer. Default ready-set entry for `/a4:run`.
- `progress` — A `task-implementer` agent is working (or crashed mid-work — reset to `pending` on session resume by `/a4:run`).
- `complete` — Unit tests passed. **Not** a forward-path terminal — UC `revising` cascade can return tasks to `pending` for re-implementation.
- `failing` — Unit tests red. Resumed via `failing → progress` (immediate retry, same cycle) or deferred via `failing → pending` (next cycle, `/a4:run` bumps `cycle:`).
- `discarded` — Abandoned. Terminal. Reached either via UC `discarded` cascade or explicit `/a4:task discard`.

Writer rules (task-specific):

- **Allowed initial statuses on file create:** `open` (default — backlog), `pending` (`/a4:run` queue-fill intent), `complete` (post-hoc documentation; code already shipped). `/a4:roadmap` always uses `pending`.
- `progress` and `failing` are **writer-only** — never used as initial statuses. The writer produces them as a result of transitions.
- `open → progress` is allowed (e.g., `task-implementer` spawned outside `/a4:run`). The `pending` step expresses queue intent; skip it when the queue is not the entry path.
- There is **no `pending → open` reverse** — once enqueued, a task cannot be returned to backlog.
- UC-cascade automatic flips: when a UC flips to `discarded`, all related tasks → `discarded`. When a UC flips to `revising`, tasks at `progress`/`failing` reset to `pending`; `open`/`pending`/`complete` tasks stay. Do not flip these by hand.

### `complete` initial-status preflight

When the chosen initial status is `complete`, the work is asserted to already be shipped. The skill verifies before writing:

1. For each path in `files:`, confirm it exists in the working tree. If any path is missing, halt and ask: (a) fix the path, or (b) downgrade to `pending` so the task enters the implement loop.
2. Required body sections (`<description>`, `<files>`, `<unit-test-strategy>`, `<acceptance-criteria>`) must still be present per `body_schemas/task.xsd` — `complete` does not exempt the task from documentation.
3. After writing the file, append an explicit `<log>` block recording the post-hoc origin (the writer never logged a `progress → complete` transition for this task):

   ```markdown
   <log>

   - <YYYY-MM-DD> created at status: complete (post-hoc documentation; code shipped prior to task authorship)

   </log>
   ```

   This is the **only** case where a skill writes into `<log>` directly — every subsequent entry must come from `transition_status.py`.

## Body shape

(Tag form / link form / H1-forbidden are universal — see `./body-conventions.md`.)

**Required (enforced by `../scripts/body_schemas/task.xsd`):**

- `<description>` — what and why.
- `<files>` — action / path / change table. Paths point at the project's production source tree.
- `<unit-test-strategy>` — scenarios + isolation strategy + test file paths.
- `<acceptance-criteria>` — checklist. AC source:

  | Shape | AC source |
  |---|---|
  | `implements: [usecase/...]` | UC `<flow>` / `<validation>` / `<error-handling>` |
  | `spec: [spec/...]` (UC-less) | spec `decision:` frontmatter + relevant `architecture.md` section |

  Validators do not enforce source-by-shape — this is a documentation convention. The `<acceptance-criteria>` section must exist regardless.

**Optional, emit only when the conversation produced content for them:**

- `<interface-contracts>` — contracts this task consumes or provides, with markdown links to `architecture.md` sections (e.g., `[architecture#SessionService](../../architecture.md#sessionservice)`). For UC-less work, link to the spec or relevant `architecture.md` section.
- `<change-logs>` — append-only audit trail when the task body is materially edited post-create (dated bullets with markdown links to the causing issue or spec).
- `<log>` — append-only writer-owned status-transition trail (`YYYY-MM-DD — <from> → <to> — <reason>`). Starts absent — `status: pending` is the implicit creation entry, written by the writer on first transition. **Never write into `<log>` directly**, except for the documented post-hoc-`complete` case above.
- `<why-discarded>` — populated by discard mode. Dated bullet (`<YYYY-MM-DD> — <reason text>`) appended when the user supplied a reason explicit enough to deserve narrative capture beyond the `<log>` line.

Unknown kebab-case tags are tolerated by the XSD's openContent.

## Common mistakes the validator catches (task-specific)

- **Required section missing** (`<description>`, `<files>`, `<unit-test-strategy>`, `<acceptance-criteria>`) → `body-xsd`.
- **Missing `kind:` frontmatter field** → frontmatter validator error. `kind` has no default.
- **`kind:` value mismatched against folder** — a file under `a4/task/feature/` must declare `kind: feature`. Mismatched declarations are a folder-routing error and should be re-located.

(Universal validator catches — stray body content, attribute-bearing tags, same-tag nesting, H1 in body — are documented in `./body-conventions.md`.)

To validate manually before commit:

```bash
uv run "../scripts/validate_body.py" \
  "<project-root>/a4" --file task/feature/<id>-<slug>.md
```

## Don't (feature-task-specific)

- **Don't put `implemented_by:` on a task.** It is a UC reverse-link, auto-maintained by `refresh_implemented_by.py` from `task.implements:`.
- **Don't use `progress` or `failing` as an initial status.** They are writer-only, produced by transitions.
- **Don't reverse `pending → open`.** Once enqueued, a task stays enqueued or moves forward / out.
- **Don't manually flip cascade-driven statuses.** UC `discarded` → task `discarded`, UC `revising` → task `pending`-reset are the writer's job.
- **Don't author multiple tasks in one `/a4:task` invocation.** Re-invoke per task; use `/a4:roadmap` for the batch path.
- **Don't write `roadmap.md` from `/a4:task`.** If the project has no roadmap and the user wants one, redirect to `/a4:roadmap`.
- **Don't omit `kind:`.** Every task declares `feature | spike | bug`.
- **Don't author a `kind: spike` or `kind: bug` task here.** Move spikes to `a4/task/spike/` and bugs to `a4/task/bug/` so the per-kind authoring rule auto-loads.

## After authoring

`/a4:task` author mode runs `refresh_implemented_by.py` (when `implements:` is non-empty) to update the UC reverse-links and suggests `/a4:run` as the next step. The skill does not commit; the file (and any UC files updated by the refresh) is left in the working tree for the user to commit.

`/a4:task discard` flips status, optionally appends `<why-discarded>`, and reports — also without committing.
