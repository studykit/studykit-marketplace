# a4 — bug authoring

A bug at `a4/bug/<id>-<slug>.md` is a **defect fix** — production code change against expected behavior. Not throwaway.

After a4 v12.0.0 the four issue families (`task`, `bug`, `spike`, `research`) are sibling top-level folders that share the same lifecycle but each has its own authoring contract. Cross-family conventions for artifact directories live in `./artifacts.md`.

Companion to `./frontmatter-universals.md`, `./body-conventions.md`.

## Frontmatter contract (do not deviate)

```yaml
---
type: bug
id: <int — globally monotonic across the workspace>
title: "<short, human-readable phrase>"
status: open | pending | progress | complete | failing | discarded
implements: []         # list of paths, e.g. [usecase/3-search-history]
depends_on: []         # list of paths to other tasks
spec: []               # list of paths, e.g. [spec/8-caching-strategy]
related: []            # catchall for cross-references
artifacts: []          # artifact paths under artifacts/bug/<id>-<slug>/ (typically empty)
cycle: 1               # implementation cycle number
labels: []             # free-form tags
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `bug` |
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | human-readable |
| `status` | yes | enum | `open` \| `pending` \| `progress` \| `complete` \| `failing` \| `discarded` |
| `implements` | no | list of paths | use cases delivered (often empty for bug work that does not implement a UC) |
| `depends_on` | no | list of paths | other tasks this one needs first |
| `spec` | no | list of paths | specs governing this task |
| `artifacts` | no | list of strings | artifact paths under `artifacts/bug/<id>-<slug>/` (typically empty — repro/logs/screenshots only when worth keeping) |
| `cycle` | no | int | implementation cycle number |
| `labels` | no | list of strings | free-form tags |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | yes | date | `YYYY-MM-DD` |

- `title` is required and must not be a placeholder; the writer rejects `<title>`-shaped strings.
- `type: bug` is fixed for files under `a4/bug/`. There is no `kind:` field — the type *is* the kind.
- `implements:` lists `usecase/<id>-<slug>` paths the task delivers. Declare it when the bug traces to a UC's flow.
- `spec:` lists `spec/<id>-<slug>` paths backing the task. Declare it when the bug is a regression against a spec's expected behavior.
- `implements:` and `spec:` are **optional and orthogonal** — a bug may declare zero, one, or both. Empty anchors are common for cross-cutting fixes.
- `artifacts:` is artifact-only — paths must point under `artifacts/bug/<id>-<slug>/...`. The list is typically empty since the production fix lives in the project's source tree (documented in the body `## Files` section). See "Artifacts directory" below for when to use the artifact directory (repro repos, crash logs, screenshots).
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

Writer rules (bug-specific):

- **Allowed initial statuses on file create:** `open` (default — backlog), `pending` (queue-fill intent), `complete` (post-hoc documentation; fix already shipped).
- `progress` and `failing` are **writer-only** — never used as initial statuses. The writer produces them as a result of transitions.
- `open → progress` is allowed (e.g., a `task-implementer` spawned outside the batch loop). The `pending` step expresses queue intent; skip it when the queue is not the entry path.
- There is **no `pending → open` reverse** — once enqueued, a task cannot be returned to backlog.

### `complete` initial-status preflight

When the chosen initial status is `complete`, the fix is asserted to already be shipped. Verify before writing:

1. For each path in `artifacts:`, confirm it exists in the working tree. If any path is missing, halt and ask: (a) fix the path, or (b) downgrade to `pending` so the task enters the implement loop.
2. Required sections (`## Description`, `## Files`, `## Unit Test Strategy`, `## Acceptance Criteria`) must still be present per the body shape below — `complete` does not exempt the task from documentation.
3. If you want the post-hoc origin recorded, append a manual bullet to a `## Log` section (see `./body-conventions.md#log`):

   ```markdown
   ## Log

   - <YYYY-MM-DD> created at status: complete (post-hoc documentation; fix shipped prior to task authorship)
   ```

## Body shape

(Heading form / link form / H1-forbidden are universal — see `./body-conventions.md`.)

**Required:**

- `## Description` — what's broken and why the fix matters. State the observed behavior and the expected behavior.
- `## Files` — action / path / change table. Lists production source paths the fix writes or modifies, plus any artifact paths under `artifacts/bug/<id>-<slug>/` when the task uses an artifact directory.
- `## Unit Test Strategy` — regression test scenarios + isolation strategy + test file paths. The bug must end with a test that fails before the fix and passes after.
- `## Acceptance Criteria` — checklist. AC source: **reproduction scenario + fixed criteria** (the regression test pinning the expected behavior). The `## Acceptance Criteria` section must exist regardless.

**Optional, emit only when there is content for them:**

- `## Interface Contracts` — contracts this task consumes or provides, with markdown links to `architecture.md` sections (e.g., `[architecture#SessionService](../architecture.md#sessionservice)`).
- `## Change Logs` — append-only audit trail when the task body is materially edited post-create (dated bullets with markdown links to the causing issue or spec).
- `## Log` — optional, hand-maintained status-transition narrative. See `./body-conventions.md#log`.
- `## Why Discarded` — populated by discard. Dated bullet (`<YYYY-MM-DD> — <reason text>`) appended when the discard reason deserves narrative capture.

Unknown H2 headings are tolerated.

## Artifacts directory (optional)

A bug task may have a sibling artifact directory at `<project-root>/artifacts/bug/<id>-<slug>/` when reproduction or evidence is itself worth keeping — minimal repro repos, crash logs, screenshots, traces:

```
<project-root>/
  a4/bug/<id>-<slug>.md             # task markdown — type: bug
  artifacts/bug/<id>-<slug>/        # repro, logs, screenshots (opt-in)
```

Optional — the production fix lives in the project's source tree (documented in body `## Files`), not here. Use the artifact directory only when reproduction artifacts have lasting value (a hard-to-reproduce data file, a heap dump that anchors the regression test). Frontmatter `artifacts:` lists artifact paths only.

No archive convention — closed bug tasks archive their markdown to `a4/archive/` independently; the artifact directory stays in place.

Cross-family conventions for the artifact directory — per-type expectations, the `artifacts:` artifact-only contract, what to keep vs. drop, ownership of curation, the project-repo (not scratch) status — live in `./artifacts.md` and apply to `type: bug` as written there.

## Common mistakes (bug-specific)

- **Required section missing** (`## Description`, `## Files`, `## Unit Test Strategy`, `## Acceptance Criteria`).
- **Wrong `type:` value or wrong folder.** A file under `a4/bug/` must declare `type: bug`. Mismatched declarations are a folder-routing error and should be re-located.
- **`kind:` field present** — `kind:` was retired with the v12 split. The folder + `type:` together encode the kind.
- **Production source paths in frontmatter `artifacts:`** — `artifacts:` is artifact-only. Production source belongs in the body `## Files` section.

(Universal body conventions — stray content above the first H2, malformed headings, sections nested inside other sections, H1 in body — are documented in `./body-conventions.md`.)

## Don't (bug-specific)

- **Don't put `implemented_by:` on a task or UC.** The field was retired (a4 v6.0.0); the reverse view of `task.implements:` is computed on demand.
- **Don't use `progress` or `failing` as an initial status.** They are writer-only, produced by transitions.
- **Don't reverse `pending → open`.** Once enqueued, a task stays enqueued or moves forward / out.
- **Don't manually flip cascade-driven statuses.** UC `discarded` → task `discarded` is the writer's job.
- **Don't write `kind:` in bug frontmatter.** The field was retired in a4 v12.0.0.
- **Don't ship a bug fix without a regression test.** The `## Unit Test Strategy` must include a scenario that pins the expected behavior; closing the task without it is the most common way the same bug returns.
- **Don't author a different issue family here.** Move tasks to `a4/task/`, spikes to `a4/spike/`, and research to `a4/research/` so the matching authoring contract applies.
