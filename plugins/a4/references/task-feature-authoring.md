# a4 — feature task authoring

A feature task at `a4/task/feature/<id>-<slug>.md` is a **unit of regular implementation work** — new functionality, extension, or refactor. The default task kind in the Jira sense.

Lifecycle is identical across task kinds (`feature` / `bug` / `spike` / `research`).

Companion to [`./frontmatter-schema.md §Task`](./frontmatter-schema.md), `./body-conventions.md`.

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
files: []              # artifact paths under artifacts/task/feature/<id>-<slug>/ (typically empty)
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
- `files:` is artifact-only — paths must point under `artifacts/task/feature/<id>-<slug>/...`. The list is typically empty for feature work that ships only production source. Production source paths the task writes or modifies are documented in the body `<files>` section, not in this frontmatter field. See "Artifacts directory" below for when to use the artifact directory.
- `cycle` starts at `1`; bumped on `failing → pending` next-cycle defers.
- `implemented_by:` is **not** a task field — it is a UC reverse-link written by `refresh_implemented_by.py`. Do not put it on a task.

### `kind: feature` with empty `implements:` and `spec:` — smell check

A `feature` task with **both** anchors empty has no AC source. Either downgrade to `spike` (and move the file to `a4/task/spike/`) if the work is genuinely exploratory, or attach an anchor.

Empty anchors are not always a problem — small UI tweaks, single-property validations, and batch-generated features without a UC group can legitimately stay anchorless. The deeper signal is in the body: when the description implies a user-facing scope no existing UC covers, or an architectural choice no existing spec records, surface the gap as a review item with `kind: gap`, `target: usecase/` or `target: spec/` (omit `target:` for cross-cutting), `source: task`, body specifying which upstream artifact appears missing.

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

- `open` — Backlog (kanban "todo"). Captured but not yet committed to the work queue. Not picked up by the implement loop; transition `open → pending` to enqueue.
- `pending` — In the work queue, awaiting an implementer. Default ready-set entry for the implement loop.
- `progress` — A `task-implementer` agent is working (or crashed mid-work — reset to `pending` on session resume).
- `complete` — Unit tests passed. **Not** a forward-path terminal — UC `revising` cascade can return tasks to `pending` for re-implementation.
- `failing` — Unit tests red. Resumed via `failing → progress` (immediate retry, same cycle) or deferred via `failing → pending` (next cycle, `cycle:` bumps).
- `discarded` — Abandoned. Terminal. Reached via UC `discarded` cascade or an explicit task-discard.

Writer rules (task-specific):

- **Allowed initial statuses on file create:** `open` (default — backlog), `pending` (queue-fill intent), `complete` (post-hoc documentation; code already shipped). Batch-authored tasks (e.g., from a roadmap) use `pending`.
- `progress` and `failing` are **writer-only** — never used as initial statuses. The writer produces them as a result of transitions.
- `open → progress` is allowed (e.g., a `task-implementer` spawned outside the batch loop). The `pending` step expresses queue intent; skip it when the queue is not the entry path.
- There is **no `pending → open` reverse** — once enqueued, a task cannot be returned to backlog.
- UC-cascade automatic flips: when a UC flips to `discarded`, all related tasks → `discarded`. When a UC flips to `revising`, tasks at `progress`/`failing` reset to `pending`; `open`/`pending`/`complete` tasks stay. Do not flip these by hand.

### `complete` initial-status preflight

When the chosen initial status is `complete`, the work is asserted to already be shipped. Verify before writing:

1. For each path in `files:`, confirm it exists in the working tree. If any path is missing, halt and ask: (a) fix the path, or (b) downgrade to `pending` so the task enters the implement loop.
2. Required body sections (`<description>`, `<files>`, `<unit-test-strategy>`, `<acceptance-criteria>`) must still be present per the body shape below — `complete` does not exempt the task from documentation.
3. After writing the file, append an explicit `<log>` block recording the post-hoc origin (the writer never logged a `progress → complete` transition for this task):

   ```markdown
   <log>

   - <YYYY-MM-DD> created at status: complete (post-hoc documentation; code shipped prior to task authorship)

   </log>
   ```

   This is the **only** case where `<log>` is written directly — every subsequent entry must come from `transition_status.py`.

## Body shape

(Tag form / link form / H1-forbidden are universal — see `./body-conventions.md`.)

**Required:**

- `<description>` — what and why.
- `<files>` — action / path / change table. Lists production source paths the task writes or modifies, plus any artifact paths under `artifacts/task/feature/<id>-<slug>/` when the task uses an artifact directory.
- `<unit-test-strategy>` — scenarios + isolation strategy + test file paths.
- `<acceptance-criteria>` — checklist. AC source:

  | Shape | AC source |
  |---|---|
  | `implements: [usecase/...]` | UC `<flow>` / `<validation>` / `<error-handling>` |
  | `spec: [spec/...]` (UC-less) | spec `decision:` frontmatter + relevant `architecture.md` section |

  AC source is a documentation convention. The `<acceptance-criteria>` section must exist regardless.

**Optional, emit only when there is content for them:**

- `<interface-contracts>` — contracts this task consumes or provides, with markdown links to `architecture.md` sections (e.g., `[architecture#SessionService](../../architecture.md#sessionservice)`). For UC-less work, link to the spec or relevant `architecture.md` section.
- `<change-logs>` — append-only audit trail when the task body is materially edited post-create (dated bullets with markdown links to the causing issue or spec).
- `<log>` — append-only writer-owned status-transition trail (`YYYY-MM-DD — <from> → <to> — <reason>`). Starts absent — `status: pending` is the implicit creation entry, written by the writer on first transition. **Never write into `<log>` directly**, except for the documented post-hoc-`complete` case above.
- `<why-discarded>` — populated by discard. Dated bullet (`<YYYY-MM-DD> — <reason text>`) appended when the discard reason deserves narrative capture beyond the `<log>` line.

Unknown kebab-case tags are tolerated.

## Artifacts directory (optional)

A feature task may have a sibling artifact directory at `<project-root>/artifacts/task/feature/<id>-<slug>/` when artifacts have evidentiary or comparative value — feature-comparison test samples, execution outputs, design mockups, migration dry-run results:

```
<project-root>/
  a4/task/feature/<id>-<slug>.md             # task markdown — kind: feature
  artifacts/task/feature/<id>-<slug>/        # comparison samples, outputs, mockups (opt-in)
```

Optional and the exception, not the default — most feature tasks have no artifact directory. Use it only when the artifacts themselves need to be preserved (before/after screenshots that anchor a UC's expected outcome, sample inputs/outputs proving a parser change). Production source the feature ships goes in the body `<files>` table; frontmatter `files:` lists artifact paths only.

No archive convention — closed feature tasks archive their markdown to `a4/archive/` independently; the artifact directory stays in place.

Cross-kind conventions for the artifact directory — what to keep vs. drop, ownership of curation, the project-repo (not scratch) status — live in [`./frontmatter-schema.md#task-artifacts-convention`](./frontmatter-schema.md#task-artifacts-convention) and apply to `kind: feature` as written there.

## Common mistakes (task-specific)

- **Required section missing** (`<description>`, `<files>`, `<unit-test-strategy>`, `<acceptance-criteria>`).
- **Missing `kind:` frontmatter field** → frontmatter validator error. `kind` has no default.
- **`kind:` value mismatched against folder** — a file under `a4/task/feature/` must declare `kind: feature`. Mismatched declarations are a folder-routing error and should be re-located.
- **Production source paths in frontmatter `files:`** — `files:` is artifact-only. Production source belongs in the body `<files>` section.

(Universal body conventions — stray body content, attribute-bearing tags, same-tag nesting, H1 in body — are documented in `./body-conventions.md`.)

## Don't (feature-task-specific)

- **Don't put `implemented_by:` on a task.** It is a UC reverse-link, auto-maintained by `refresh_implemented_by.py` from `task.implements:`.
- **Don't use `progress` or `failing` as an initial status.** They are writer-only, produced by transitions.
- **Don't reverse `pending → open`.** Once enqueued, a task stays enqueued or moves forward / out.
- **Don't manually flip cascade-driven statuses.** UC `discarded` → task `discarded`, UC `revising` → task `pending`-reset are the writer's job.
- **Don't omit `kind:`.** Every task declares `feature | spike | bug | research`.
- **Don't author a `kind: spike` / `bug` / `research` task here.** Move spikes to `a4/task/spike/`, bugs to `a4/task/bug/`, and research to `a4/task/research/` so the matching per-kind authoring contract applies.
