# a4 — bug task authoring

A bug task at `a4/task/bug/<id>-<slug>.md` is a **defect fix** — production code change against expected behavior. Not throwaway.

Lifecycle is identical across task kinds (`feature` / `bug` / `spike` / `research`).

Companion to [`./frontmatter-schema.md §Task`](./frontmatter-schema.md), `./body-conventions.md`.

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
files: []              # artifact paths under artifacts/task/bug/<id>-<slug>/ (typically empty)
cycle: 1               # implementation cycle number
labels: []             # free-form tags
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

- `title` is required and must not be a placeholder; the writer rejects `<title>`-shaped strings.
- `kind: bug` is fixed for files under `a4/task/bug/`. Every task must declare the kind explicitly.
- `implements:` lists `usecase/<id>-<slug>` paths the task delivers. Declare it when the bug traces to a UC's flow.
- `spec:` lists `spec/<id>-<slug>` paths backing the task. Declare it when the bug is a regression against a spec's expected behavior.
- `implements:` and `spec:` are **optional and orthogonal** — a bug may declare zero, one, or both. Empty anchors are common for cross-cutting fixes.
- `files:` is artifact-only — paths must point under `artifacts/task/bug/<id>-<slug>/...`. The list is typically empty since the production fix lives in the project's source tree (documented in the body `## Files` section). See "Artifacts directory" below for when to use the artifact directory (repro repos, crash logs, screenshots).
- `cycle` starts at `1`; bumped on `failing → pending` next-cycle defers.
- `implemented_by:` is **not** a frontmatter field on any artifact — the UC ↔ task reverse view is derived on demand from `task.implements:`. Do not place an `implemented_by:` field on tasks or UCs.

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
2. Required sections (`## Description`, `## Files`, `## Unit Test Strategy`, `## Acceptance Criteria`) must still be present per the body shape below — `complete` does not exempt the task from documentation.
3. If you want the post-hoc origin recorded, append a manual bullet to a `## Log` section (the section is optional and hand-maintained):

   ```markdown
   ## Log

   - <YYYY-MM-DD> created at status: complete (post-hoc documentation; fix shipped prior to task authorship)
   ```

   `transition_status.py` does not touch `## Log`; the section is purely an author convenience.

## Body shape

(Heading form / link form / H1-forbidden are universal — see `./body-conventions.md`.)

**Required:**

- `## Description` — what's broken and why the fix matters. State the observed behavior and the expected behavior.
- `## Files` — action / path / change table. Lists production source paths the fix writes or modifies, plus any artifact paths under `artifacts/task/bug/<id>-<slug>/` when the task uses an artifact directory.
- `## Unit Test Strategy` — regression test scenarios + isolation strategy + test file paths. The bug must end with a test that fails before the fix and passes after.
- `## Acceptance Criteria` — checklist. AC source: **reproduction scenario + fixed criteria** (the regression test pinning the expected behavior). The `## Acceptance Criteria` section must exist regardless.

**Optional, emit only when there is content for them:**

- `## Interface Contracts` — contracts this task consumes or provides, with markdown links to `architecture.md` sections (e.g., `[architecture#SessionService](../../architecture.md#sessionservice)`).
- `## Change Logs` — append-only audit trail when the task body is materially edited post-create (dated bullets with markdown links to the causing issue or spec).
- `## Log` — optional, hand-maintained status-transition narrative (`YYYY-MM-DD — <from> → <to> — <reason>`). `transition_status.py` flips `status:` and bumps `updated:` but does **not** touch `## Log`; append a bullet by hand if you want the transition recorded in the body.
- `## Why Discarded` — populated by discard. Dated bullet (`<YYYY-MM-DD> — <reason text>`) appended when the discard reason deserves narrative capture.

Unknown H2 headings are tolerated.

## Artifacts directory (optional)

A bug task may have a sibling artifact directory at `<project-root>/artifacts/task/bug/<id>-<slug>/` when reproduction or evidence is itself worth keeping — minimal repro repos, crash logs, screenshots, traces:

```
<project-root>/
  a4/task/bug/<id>-<slug>.md             # task markdown — kind: bug
  artifacts/task/bug/<id>-<slug>/        # repro, logs, screenshots (opt-in)
```

Optional — the production fix lives in the project's source tree (documented in body `## Files`), not here. Use the artifact directory only when reproduction artifacts have lasting value (a hard-to-reproduce data file, a heap dump that anchors the regression test). Frontmatter `files:` lists artifact paths only.

No archive convention — closed bug tasks archive their markdown to `a4/archive/` independently; the artifact directory stays in place.

Cross-kind conventions for the artifact directory — per-kind expectations, the `task.files:` artifact-only contract, what to keep vs. drop, ownership of curation, the project-repo (not scratch) status — live in [`task-artifacts.md`](./task-artifacts.md) and apply to `kind: bug` as written there.

## Common mistakes (task-specific)

- **Required section missing** (`## Description`, `## Files`, `## Unit Test Strategy`, `## Acceptance Criteria`).
- **Missing `kind:` frontmatter field** → frontmatter validator error. `kind` has no default.
- **`kind:` value mismatched against folder** — a file under `a4/task/bug/` must declare `kind: bug`. Mismatched declarations are a folder-routing error and should be re-located.
- **Production source paths in frontmatter `files:`** — `files:` is artifact-only. Production source belongs in the body `## Files` section.

(Universal body conventions — stray content above the first H2, malformed headings, sections nested inside other sections, H1 in body — are documented in `./body-conventions.md`.)

## Don't (bug-task-specific)

- **Don't put `implemented_by:` on a task or UC.** The field was retired (a4 v6.0.0); the reverse view of `task.implements:` is computed on demand.
- **Don't use `progress` or `failing` as an initial status.** They are writer-only, produced by transitions.
- **Don't reverse `pending → open`.** Once enqueued, a task stays enqueued or moves forward / out.
- **Don't manually flip cascade-driven statuses.** UC `discarded` → task `discarded` is the writer's job.
- **Don't omit `kind:`.** Every task declares `feature | spike | bug | research`.
- **Don't ship a bug fix without a regression test.** The `## Unit Test Strategy` must include a scenario that pins the expected behavior; closing the task without it is the most common way the same bug returns.
- **Don't author a `kind: feature` / `spike` / `research` task here.** Move them to the matching `a4/task/<kind>/` so the per-kind authoring contract applies.
