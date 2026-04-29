# a4 — spike task authoring

A spike task at `a4/task/spike/<id>-<slug>.md` is a **time-boxed exploration to unblock a decision** (XP sense). PoC, investigation, benchmark — throwaway code. The accompanying code lives in the spike's artifact directory at `<project-root>/artifacts/task/spike/<id>-<slug>/`, **outside** the `a4/` workspace. For pure written investigation without throwaway code, use `kind: research` instead.

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
depends_on: []         # list of paths to other tasks
related: []            # catchall for cross-references
files: []              # paths under artifacts/task/spike/<id>-<slug>/ — never project source tree
labels: []             # free-form tags
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

- `title` is required and must not be a placeholder; the writer rejects `<title>`-shaped strings.
- `kind: spike` is fixed for files under `a4/task/spike/`. Every task must declare the kind explicitly.
- `implements:` is **not allowed** on spike (a4 v6.0.0) — spikes are exploratory, never UC deliverables. If a spike's outcome turns out to validate a UC, author a follow-up `feature` task with `implements: [usecase/<id>-<slug>]` and link the spike from its `## Description` body.
- `spec:` is **not allowed** on spike (a4 v6.0.0). Cite the triggering spec from the spike's `## Description` body via a markdown link — the frontmatter forward link is reserved for `feature` and `bug` tasks.
- `files:` paths must live under `artifacts/task/spike/<id>-<slug>/...` (or `artifacts/task/spike/archive/<id>-<slug>/...` after archive). **Never** point at the project's production source tree — production paths the task may *also* touch are documented in the body `## Files` section, not in frontmatter.
- `cycle:` is **not allowed** on spike (a4 v6.0.0); the spike either succeeds, fails (re-attempt without bumping), or is discarded — there is no multi-cycle implement loop for exploratory work.
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
- `complete` — Spike succeeded; hypothesis validated.
- `failing` — Spike could not validate the hypothesis on this iteration. Resumed via `failing → progress` (immediate retry) or deferred via `failing → pending` (re-attempt without a cycle bump — there is no `cycle:` on spike).
- `discarded` — Abandoned. Terminal. Reached via an explicit task-discard (a spike whose hypothesis is no longer worth testing).

Writer rules (task-specific):

- **Allowed initial statuses on file create:** `open` (default — backlog), `pending` (queue-fill intent), `complete` (post-hoc documentation; PoC already done).
- `progress` and `failing` are **writer-only** — never used as initial statuses. The writer produces them as a result of transitions.
- `open → progress` is allowed (e.g., a `task-implementer` spawned outside the batch loop).
- There is **no `pending → open` reverse** — once enqueued, a spike stays enqueued or moves forward / out.

### `complete` initial-status preflight

When the chosen initial status is `complete`, the spike is asserted to already be done. Verify before writing:

1. For each path in `files:`, confirm it exists under `artifacts/task/spike/<id>-<slug>/` (or `artifacts/task/spike/archive/<id>-<slug>/`). If any path is missing, halt and ask: (a) fix the path, or (b) downgrade to `pending` so the task enters the implement loop.
2. Required sections (`## Description`, `## Files`, `## Unit Test Strategy`, `## Acceptance Criteria`) must still be present per the body shape below — `complete` does not exempt the task from documentation.
3. If you want the post-hoc origin recorded, append a manual bullet to a `## Log` section (the section is optional and hand-maintained):

   ```markdown
   ## Log

   - <YYYY-MM-DD> created at status: complete (post-hoc documentation; PoC done prior to task authorship)
   ```

   `transition_status.py` does not touch `## Log`; the section is purely an author convenience.

## Body shape

(Heading form / link form / H1-forbidden are universal — see `./body-conventions.md`.)

**Required:**

- `## Description` — the question being explored and why a spike (vs. going straight to a feature task). State the hypothesis and the decision the spike's outcome will inform.
- `## Files` — action / path / change table. Artifact paths under `artifacts/task/spike/<id>-<slug>/` for files the spike creates; production source paths the spike may probe or temporarily touch may also appear here for reader context. (Frontmatter `files:` is artifact-only.)
- `## Unit Test Strategy` — may be a one-line "validate hypothesis via <method>" (benchmark, integration probe, sample-driven check). The section is still required.
- `## Acceptance Criteria` — checklist. AC source: **hypothesis + expected result, the spike's own body** — what observable outcome proves or refutes the question. The `## Acceptance Criteria` section must exist regardless.

**Optional, emit only when there is content for them:**

- `## Interface Contracts` — contracts the spike consumes or proposes, with markdown links to `architecture.md` sections (e.g., `[architecture#SessionService](../../architecture.md#sessionservice)`). May be omitted for self-contained spikes.
- `## Change Logs` — append-only audit trail when the task body is materially edited post-create.
- `## Log` — optional, hand-maintained status-transition narrative (`YYYY-MM-DD — <from> → <to> — <reason>`). `transition_status.py` flips `status:` and bumps `updated:` but does **not** touch `## Log`; append a bullet by hand if you want the transition recorded in the body.
- `## Why Discarded` — populated by discard. Dated bullet (`<YYYY-MM-DD> — <reason text>`) appended when the discard reason deserves narrative capture.

Unknown H2 headings are tolerated.

## Artifacts directory

For every spike task, accompanying PoC code lives at `<project-root>/artifacts/task/spike/<id>-<slug>/`, parallel to (not inside) `a4/`:

```
<project-root>/
  a4/task/spike/<id>-<slug>.md             # task markdown — kind: spike
  artifacts/task/spike/<id>-<slug>/        # PoC code, data, scratch notes
    *.py *.json ...
```

Spike-specific notes:

- The directory is the spike's primary deliverable while exploration is underway. Most active spikes have one.
- When the spike completes (or fails), `git mv` it to `artifacts/task/spike/archive/<id>-<slug>/` and update `files:` paths to match. The move is **never automated**.

Cross-kind conventions for the artifact directory — per-kind expectations, the `task.files:` artifact-only contract, what to keep vs. drop, ownership of curation, the project-repo (not scratch) status — live in [`task-artifacts.md`](./task-artifacts.md) and apply to `kind: spike` as written there.

## Common mistakes (task-specific)

- **Required section missing** (`## Description`, `## Files`, `## Unit Test Strategy`, `## Acceptance Criteria`).
- **Missing `kind:` frontmatter field** — `kind` is required and has no default.
- **`kind:` value mismatched against folder** — a file under `a4/task/spike/` must declare `kind: spike`. Mismatched declarations are a folder-routing error and should be re-located.
- **`files:` paths under the project source tree, not under `artifacts/task/spike/<id>-<slug>/`** — breaks the throwaway contract; production source paths belong in the body `## Files` section.

(Universal body conventions — stray content above the first H2, malformed headings, sections nested inside other sections, H1 in body — are documented in `./body-conventions.md`.)

## Don't (spike-task-specific)

- **Don't put `implements:`, `cycle:`, or `spec:` on a spike.** All three are forbidden on `kind: spike` (a4 v6.0.0). Spikes are exploratory; if the outcome warrants UC delivery, author a follow-up `kind: feature` task that declares `implements:` and `spec:` as needed.
- **Don't put `implemented_by:` on a task or UC.** The field was retired (a4 v6.0.0); the reverse view of `task.implements:` is computed on demand.
- **Don't use `progress` or `failing` as an initial status.** They are writer-only, produced by transitions.
- **Don't reverse `pending → open`.** Once enqueued, a spike stays enqueued or moves forward / out.
- **Don't omit `kind:`.** Every task declares `feature | spike | bug | research`.
- **Don't auto-delete or auto-archive `artifacts/task/spike/<id>-<slug>/`** on discard. Archiving is a user-driven `git mv`.
- **Don't write production source from a spike.** `files:` paths staying under `artifacts/task/spike/<id>-<slug>/` is the contract that keeps PoC code throwaway. If the spike's outcome warrants production work, follow up with a `kind: feature` task.
- **Don't author a `kind: feature` / `bug` / `research` task here.** Move them to the matching `a4/task/<kind>/` so the per-kind authoring contract applies.
