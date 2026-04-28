# a4 — bug task authoring

A bug task at `a4/task/bug/<id>-<slug>.md` is a **defect fix** — production code change against expected behavior. Not throwaway.

Lifecycle is identical across task kinds (`feature` / `bug` / `spike`).

Companion to [`./frontmatter-schema.md §Task`](./frontmatter-schema.md), `./body-conventions.md`.

## Reading a task

If only a specific section is needed to answer a question, prefer `extract_section.py <file> <tag>` over loading the whole file.

## Frontmatter contract (do not deviate)

```yaml
---
type: task
id: <int — globally monotonic across the workspace>
title: "<short, human-readable phrase>"
kind: bug
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
- `kind: bug` is fixed for files under `a4/task/bug/`. Every task must declare the kind explicitly.
- `implements:` lists `usecase/<id>-<slug>` paths the task delivers. Declare it when the bug traces to a UC's flow.
- `spec:` lists `spec/<id>-<slug>` paths backing the task. Declare it when the bug is a regression against a spec's expected behavior.
- `implements:` and `spec:` are **optional and orthogonal** — a bug may declare zero, one, or both. Empty anchors are common for cross-cutting fixes.
- `files:` paths point at the project's production source tree.
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
- `complete` — Unit tests passed. The fix is in.
- `failing` — Unit tests red. Resumed via `failing → progress` (immediate retry) or deferred via `failing → pending` (next cycle, `cycle:` bumps).
- `discarded` — Abandoned. Terminal.

Writer rules (task-specific):

- **Allowed initial statuses on file create:** `open` (default — backlog), `pending` (queue-fill intent), `complete` (post-hoc documentation; fix already shipped).
- `progress` and `failing` are **writer-only** — never used as initial statuses. The writer produces them as a result of transitions.
- `open → progress` is allowed (e.g., a `task-implementer` spawned outside the batch loop). The `pending` step expresses queue intent; skip it when the queue is not the entry path.
- There is **no `pending → open` reverse** — once enqueued, a task cannot be returned to backlog.

### `complete` initial-status preflight

When the chosen initial status is `complete`, the fix is asserted to already be shipped. Verify before writing:

1. For each path in `files:`, confirm it exists in the working tree. If any path is missing, halt and ask: (a) fix the path, or (b) downgrade to `pending` so the task enters the implement loop.
2. Required body sections (`<description>`, `<files>`, `<unit-test-strategy>`, `<acceptance-criteria>`) must still be present per `body_schemas/task.xsd` — `complete` does not exempt the task from documentation.
3. After writing the file, append an explicit `<log>` block recording the post-hoc origin (the writer never logged a `progress → complete` transition for this task):

   ```markdown
   <log>

   - <YYYY-MM-DD> created at status: complete (post-hoc documentation; fix shipped prior to task authorship)

   </log>
   ```

   This is the **only** case where `<log>` is written directly — every subsequent entry must come from `transition_status.py`.

## Body shape

(Tag form / link form / H1-forbidden are universal — see `./body-conventions.md`.)

**Required (enforced by `../scripts/body_schemas/task.xsd`):**

- `<description>` — what's broken and why the fix matters. State the observed behavior and the expected behavior.
- `<files>` — action / path / change table. Paths point at the project's production source tree.
- `<unit-test-strategy>` — regression test scenarios + isolation strategy + test file paths. The bug must end with a test that fails before the fix and passes after.
- `<acceptance-criteria>` — checklist. AC source: **reproduction scenario + fixed criteria** (the regression test pinning the expected behavior).

  Validators do not enforce AC source — this is a documentation convention. The `<acceptance-criteria>` section must exist regardless.

**Optional, emit only when there is content for them:**

- `<interface-contracts>` — contracts this task consumes or provides, with markdown links to `architecture.md` sections (e.g., `[architecture#SessionService](../../architecture.md#sessionservice)`).
- `<change-logs>` — append-only audit trail when the task body is materially edited post-create (dated bullets with markdown links to the causing issue or spec).
- `<log>` — append-only writer-owned status-transition trail (`YYYY-MM-DD — <from> → <to> — <reason>`). Starts absent — `status: pending` is the implicit creation entry, written by the writer on first transition. **Never write into `<log>` directly**, except for the documented post-hoc-`complete` case above.
- `<why-discarded>` — populated by discard. Dated bullet (`<YYYY-MM-DD> — <reason text>`) appended when the discard reason deserves narrative capture beyond the `<log>` line.

Unknown kebab-case tags are tolerated by the XSD's openContent.

## Common mistakes the validator catches (task-specific)

- **Required section missing** (`<description>`, `<files>`, `<unit-test-strategy>`, `<acceptance-criteria>`) → `body-xsd`.
- **Missing `kind:` frontmatter field** → frontmatter validator error. `kind` has no default.
- **`kind:` value mismatched against folder** — a file under `a4/task/bug/` must declare `kind: bug`. Mismatched declarations are a folder-routing error and should be re-located.

(Universal validator catches — stray body content, attribute-bearing tags, same-tag nesting, H1 in body — are documented in `./body-conventions.md`.)

To validate manually before commit:

```bash
uv run "../scripts/validate_body.py" \
  "<project-root>/a4" --file task/bug/<id>-<slug>.md
```

## Don't (bug-task-specific)

- **Don't put `implemented_by:` on a task.** It is a UC reverse-link, auto-maintained by `refresh_implemented_by.py` from `task.implements:`.
- **Don't use `progress` or `failing` as an initial status.** They are writer-only, produced by transitions.
- **Don't reverse `pending → open`.** Once enqueued, a task stays enqueued or moves forward / out.
- **Don't manually flip cascade-driven statuses.** UC `discarded` → task `discarded` is the writer's job.
- **Don't omit `kind:`.** Every task declares `feature | spike | bug`.
- **Don't ship a bug fix without a regression test.** The `<unit-test-strategy>` must include a scenario that pins the expected behavior; closing the task without it is the most common way the same bug returns.
- **Don't author a `kind: feature` or `kind: spike` task here.** Move features to `a4/task/feature/` and spikes to `a4/task/spike/` so the matching per-kind authoring contract applies.
