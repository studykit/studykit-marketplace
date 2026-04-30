# a4 — task authoring

A task at `a4/task/<id>-<slug>.md` is a **unit of regular implementation work** — new functionality, extension, or refactor. The default issue family in the Jira sense (equivalent to Jira's "Task" issue type alongside Bug / Story / Epic).

After a4 v12.0.0 the four issue families (`task`, `bug`, `spike`, `research`) are sibling top-level folders that share the same lifecycle but each has its own authoring contract. Cross-family conventions for artifact directories live in [`./artifacts.md`](./artifacts.md).

Companion to [`./frontmatter-schema.md §Task`](./frontmatter-schema.md), `./body-conventions.md`.

## Frontmatter contract (do not deviate)

```yaml
---
type: task
id: <int — globally monotonic across the workspace>
title: "<short, human-readable phrase>"
status: open | pending | progress | complete | failing | discarded
implements: []         # list of paths, e.g. [usecase/3-search-history]
depends_on: []         # list of paths to other tasks
spec: []               # list of paths, e.g. [spec/8-caching-strategy]
related: []            # catchall for cross-references
artifacts: []          # artifact paths under artifacts/task/<id>-<slug>/ (typically empty)
cycle: 1               # implementation cycle number
labels: []             # free-form tags
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

- `title` is required and must not be a placeholder; the writer rejects `<title>`-shaped strings.
- `type: task` is fixed for files under `a4/task/`. There is no `kind:` field — the type *is* the kind.
- `implements:` lists `usecase/<id>-<slug>` paths the task delivers. Declare it whenever the project is UC-driven.
- `spec:` lists `spec/<id>-<slug>` paths backing the task. Declare it in UC-less projects (the spec's `## Specification` body + relevant `architecture.md` section becomes the AC source).
- `implements:` and `spec:` are **optional and orthogonal** — a task may declare zero, one, or both. See the smell check below for the zero-anchor case.
- `artifacts:` is artifact-only — paths must point under `artifacts/task/<id>-<slug>/...`. The list is typically empty for task work that ships only production source. Production source paths the task writes or modifies are documented in the body `## Files` section, not in this frontmatter field. See "Artifacts directory" below for when to use the artifact directory.
- `cycle` starts at `1`; bumped on `failing → pending` next-cycle defers.
- `implemented_by:` is **not** a frontmatter field on any artifact — the UC ↔ task reverse view is derived on demand from `<task-family>.implements:`. Do not place an `implemented_by:` field on tasks or UCs.

### `type: task` with empty `implements:` and `spec:` — smell check

A task with **both** anchors empty has no AC source. Either downgrade to `spike` (and move the file to `a4/spike/`, changing `type:` to `spike`) if the work is genuinely exploratory, or attach an anchor.

Empty anchors are not always a problem — small UI tweaks, single-property validations, and batch-generated tasks without a UC group can legitimately stay anchorless. The deeper signal is in the body: when the description implies a user-facing scope no existing UC covers, or an architectural choice no existing spec records, surface the gap as a review item with `kind: gap`, `target: usecase/` or `target: spec/` (omit `target:` for cross-cutting), `source: task`, body specifying which upstream artifact appears missing.

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
- UC-cascade automatic flips: when a UC flips to `discarded`, all related tasks across the four issue families → `discarded`. When a UC flips to `revising`, tasks at `progress`/`failing` reset to `pending`; `open`/`pending`/`complete` tasks stay. Do not flip these by hand.

### `complete` initial-status preflight

When the chosen initial status is `complete`, the work is asserted to already be shipped. Verify before writing:

1. For each path in `artifacts:`, confirm it exists in the working tree. If any path is missing, halt and ask: (a) fix the path, or (b) downgrade to `pending` so the task enters the implement loop.
2. Required sections (`## Description`, `## Files`, `## Unit Test Strategy`, `## Acceptance Criteria`) must still be present per the body shape below — `complete` does not exempt the task from documentation.
3. If you want the post-hoc origin recorded, append a manual bullet to a `## Log` section (the section is optional and hand-maintained):

   ```markdown
   ## Log

   - <YYYY-MM-DD> created at status: complete (post-hoc documentation; code shipped prior to task authorship)
   ```

   `transition_status.py` does not touch `## Log`; the section is purely an author convenience.

## Body shape

(Heading form / link form / H1-forbidden are universal — see `./body-conventions.md`.)

**Required:**

- `## Description` — what and why.
- `## Files` — action / path / change table. Lists production source paths the task writes or modifies, plus any artifact paths under `artifacts/task/<id>-<slug>/` when the task uses an artifact directory.
- `## Unit Test Strategy` — scenarios + isolation strategy + test file paths.
- `## Acceptance Criteria` — checklist. AC source:

  | Shape | AC source |
  |---|---|
  | `implements: [usecase/...]` | UC `## Flow` / `## Validation` / `## Error Handling` |
  | `spec: [spec/...]` (UC-less) | spec `## Specification` body + relevant `architecture.md` section |

  AC source is a documentation convention. The `## Acceptance Criteria` section must exist regardless.

**Optional, emit only when there is content for them:**

- `## Interface Contracts` — contracts this task consumes or provides, with markdown links to `architecture.md` sections (e.g., `[architecture#SessionService](../architecture.md#sessionservice)`). For UC-less work, link to the spec or relevant `architecture.md` section.
- `## Change Logs` — append-only audit trail when the task body is materially edited post-create (dated bullets with markdown links to the causing issue or spec).
- `## Log` — optional, hand-maintained status-transition narrative (`YYYY-MM-DD — <from> → <to> — <reason>`). `transition_status.py` flips `status:` and bumps `updated:` but does **not** touch `## Log`; append a bullet by hand if you want the transition recorded in the body.
- `## Why Discarded` — populated by discard. Dated bullet (`<YYYY-MM-DD> — <reason text>`) appended when the discard reason deserves narrative capture.

Unknown H2 headings are tolerated.

## Artifacts directory (optional)

A task may have a sibling artifact directory at `<project-root>/artifacts/task/<id>-<slug>/` when artifacts have evidentiary or comparative value — comparison test samples, execution outputs, design mockups, migration dry-run results:

```
<project-root>/
  a4/task/<id>-<slug>.md             # task markdown — type: task
  artifacts/task/<id>-<slug>/        # comparison samples, outputs, mockups (opt-in)
```

Optional and the exception, not the default — most tasks have no artifact directory. Use it only when the artifacts themselves need to be preserved (before/after screenshots that anchor a UC's expected outcome, sample inputs/outputs proving a parser change). Production source the task ships goes in the body `## Files` table; frontmatter `artifacts:` lists artifact paths only.

No archive convention — closed tasks archive their markdown to `a4/archive/` independently; the artifact directory stays in place.

Cross-family conventions for the artifact directory — per-type expectations, the `artifacts:` artifact-only contract, what to keep vs. drop, ownership of curation, the project-repo (not scratch) status — live in [`./artifacts.md`](./artifacts.md) and apply to `type: task` as written there.

## Common mistakes (task-specific)

- **Required section missing** (`## Description`, `## Files`, `## Unit Test Strategy`, `## Acceptance Criteria`).
- **Wrong `type:` value or wrong folder.** A file under `a4/task/` must declare `type: task`. Mismatched declarations are a folder-routing error and should be re-located.
- **`kind:` field present** — `kind:` was retired with the v12 split. The folder + `type:` together encode the kind.
- **Production source paths in frontmatter `artifacts:`** — `artifacts:` is artifact-only. Production source belongs in the body `## Files` section.

(Universal body conventions — stray content above the first H2, malformed headings, sections nested inside other sections, H1 in body — are documented in `./body-conventions.md`.)

## Don't (task-specific)

- **Don't put `implemented_by:` on a task or UC.** The field was retired (a4 v6.0.0); the reverse view of `task.implements:` is computed on demand.
- **Don't use `progress` or `failing` as an initial status.** They are writer-only, produced by transitions.
- **Don't reverse `pending → open`.** Once enqueued, a task stays enqueued or moves forward / out.
- **Don't manually flip cascade-driven statuses.** UC `discarded` → task `discarded`, UC `revising` → task `pending`-reset are the writer's job.
- **Don't write `kind:` in task frontmatter.** The field was retired in a4 v12.0.0.
- **Don't author a different issue family here.** Move spikes to `a4/spike/`, bugs to `a4/bug/`, and research to `a4/research/` so the matching authoring contract applies.
