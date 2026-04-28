---
name: a4-task-spike-authoring
description: Authoring rules for a4 spike tasks. Auto-loaded when reading or editing anything under `a4/task/spike/`.
paths: ["a4/task/spike/**/*.md"]
---

# a4 — spike task authoring guide

A spike task at `a4/task/spike/<id>-<slug>.md` is a **time-boxed
exploration to unblock a decision** (XP sense). PoC, investigation,
benchmark — throwaway code. The accompanying code lives at
`<project-root>/spike/<id>-<slug>/`, **outside** the `a4/` workspace.

Lifecycle is identical across task kinds (`feature` / `bug` / `spike`).
Spike tasks are produced by `/a4:task` (single ad-hoc) and consumed by
`/a4:run` (the implement + test loop) and the `task-implementer` agent.

> **Workspace-wide policies** — writer-owned fields, id allocation,
> path-reference form, tag form, `<change-logs>` discipline, wiki
> authorship, cross-stage feedback, commit message form — live in
> [`a4-workspace-policies.md`](a4-workspace-policies.md) and load
> automatically alongside this rule. This rule covers the spike-task
> contract on top.

This rule is the working contract for any LLM about to read, draft, or
edit a spike task. The full schema and rationale live in
[`references/frontmatter-schema.md §Task`](../references/frontmatter-schema.md).

## How to author — always via `/a4:task`

Do **not** hand-craft a spike task file with `Write`. Always invoke
`/a4:task` so id allocation, slug derivation, frontmatter shape, body
validation, the spike sidecar prompt, and any `implements:` / `spec:`
resolution all run through the same code path. `/a4:roadmap` is
feature-only; spikes always come through the single-task path.

- **`/a4:task`** — single ad-hoc spike task. Use to unblock an
  architecture or decision question with a time-boxed PoC.
- **`/a4:task discard <id-or-slug> [reason]`** — explicit one-off
  discard. Flips `status: → discarded` via `transition_status.py` and
  appends an optional `<why-discarded>` body block.

If you must read a task to answer a question, prefer
`extract_section.py <file> <tag>` over loading the whole file (see
`a4-section-enum.md`).

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

- `title` is required and must not be a placeholder; the writer
  rejects `<title>`-shaped strings.
- `kind: spike` is fixed for files under `a4/task/spike/`. Every task
  must declare the kind explicitly.
- `implements:` is **usually empty** — a spike is exploratory, not a
  deliverable. Populate only when the PoC validates a hypothesis
  directly tied to a UC's flow.
- `spec:` lists `spec/<id>-<slug>` paths the spike investigates. Most
  spikes are spec-triggered; populate this when applicable.
- `files:` paths must live under `spike/<id>-<slug>/...` (or
  `spike/archive/<id>-<slug>/...` after archive). **Never** point at
  the project's production source tree — that would defeat the
  throwaway contract.
- `cycle` starts at `1`; bumped by `/a4:run` on `failing → pending`
  next-cycle defers.
- `implemented_by:` is **not** a task field — it is a UC reverse-link
  written by `refresh_implemented_by.py`. Do not put it on a task.

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

- `open` — Backlog (kanban "todo"). Captured but not yet committed to
  the work queue. Not picked up by `/a4:run`; user must transition
  `open → pending` to enqueue.
- `pending` — In the work queue, awaiting an implementer.
- `progress` — A `task-implementer` agent is working (or crashed
  mid-work — reset to `pending` on session resume by `/a4:run`).
- `complete` — Spike succeeded; hypothesis validated.
- `failing` — Spike could not validate the hypothesis on this
  iteration. Resumed via `failing → progress` (immediate retry, same
  cycle) or deferred via `failing → pending` (next cycle).
- `discarded` — Abandoned. Terminal. Reached via explicit
  `/a4:task discard` (a spike whose hypothesis is no longer worth
  testing).

Writer rules (task-specific; the universal "writer-owned fields" rule
is in `a4-workspace-policies.md` §1):

- **Allowed initial statuses on file create:** `open` (default —
  backlog), `pending` (`/a4:run` queue-fill intent), `complete`
  (post-hoc documentation; PoC already done).
- `progress` and `failing` are **writer-only** — never used as initial
  statuses. The writer produces them as a result of transitions.
- `open → progress` is allowed (e.g., `task-implementer` spawned
  outside `/a4:run`).
- There is **no `pending → open` reverse** — once enqueued, a spike
  stays enqueued or moves forward / out.

### `complete` initial-status preflight

When the chosen initial status is `complete`, the spike is asserted
to already be done. The skill verifies before writing:

1. For each path in `files:`, confirm it exists under
   `spike/<id>-<slug>/` (or `spike/archive/<id>-<slug>/`). If any
   path is missing, halt and ask: (a) fix the path, or (b) downgrade
   to `pending` so the task enters the implement loop.
2. Required body sections (`<description>`, `<files>`,
   `<unit-test-strategy>`, `<acceptance-criteria>`) must still be
   present per `body_schemas/task.xsd` — `complete` does not exempt
   the task from documentation.
3. After writing the file, append an explicit `<log>` block recording
   the post-hoc origin:

   ```markdown
   <log>

   - <YYYY-MM-DD> created at status: complete (post-hoc documentation; PoC done prior to task authorship)

   </log>
   ```

   This is the **only** case where a skill writes into `<log>`
   directly — every subsequent entry must come from
   `transition_status.py`.

## Body shape

(Tag form / link form / H1-forbidden are universal — see
`a4-workspace-policies.md` §4.)

**Required (enforced by `body_schemas/task.xsd`):**

- `<description>` — the question being explored and why a spike (vs.
  going straight to a feature task). State the hypothesis and the
  decision the spike's outcome will inform.
- `<files>` — action / path / change table. Every path is under
  `spike/<id>-<slug>/`.
- `<unit-test-strategy>` — may be a one-line "validate hypothesis via
  <method>" (benchmark, integration probe, sample-driven check). The
  XSD still requires the section.
- `<acceptance-criteria>` — checklist. AC source: **hypothesis +
  expected result, the spike's own body** — what observable outcome
  proves or refutes the question.

  Validators do not enforce AC source — this is a documentation
  convention. The `<acceptance-criteria>` section must exist
  regardless.

**Optional, emit only when the conversation produced content for them:**

- `<interface-contracts>` — contracts the spike consumes or proposes,
  with markdown links to `architecture.md` sections (e.g.,
  `[architecture#SessionService](../../architecture.md#sessionservice)`).
  May be omitted for self-contained spikes.
- `<change-logs>` — append-only audit trail when the task body is
  materially edited post-create.
- `<log>` — append-only writer-owned status-transition trail
  (`YYYY-MM-DD — <from> → <to> — <reason>`). Starts absent —
  `status: pending` is the implicit creation entry, written by the
  writer on first transition. **Never write into `<log>` directly**,
  except for the documented post-hoc-`complete` case above.
- `<why-discarded>` — populated by discard mode. Dated bullet
  (`<YYYY-MM-DD> — <reason text>`) appended when the user supplied a
  reason explicit enough to deserve narrative capture beyond the
  `<log>` line.

Unknown kebab-case tags are tolerated by the XSD's openContent.

## Spike sidecar convention

For every spike task, accompanying PoC code lives at
`<project-root>/spike/<id>-<slug>/`, parallel to (not inside) `a4/`:

```
<project-root>/
  a4/task/spike/<id>-<slug>.md   # task markdown — kind: spike
  spike/<id>-<slug>/             # PoC code, data, scratch notes
    *.py *.json ...
```

The `spike/` directory is part of the project repo (not scratch), is
**not validated** by any a4 script (the markdown-only contract of
`a4/` is preserved), and is opt-in. `feature` and `bug` tasks have no
sidecar — their `files:` paths point at production source.

When a spike completes (or fails), the user manually `git mv`s the
directory to `spike/archive/<id>-<slug>/` and updates the task's
`files:` paths. The move is **never automated** — same precedent as
`idea/` promotion.

## Common mistakes the validator catches (task-specific)

- **Required section missing** (`<description>`, `<files>`,
  `<unit-test-strategy>`, `<acceptance-criteria>`) → `body-xsd`.
- **Missing `kind:` frontmatter field** → frontmatter validator
  error. `kind` has no default.
- **`kind:` value mismatched against folder** — a file under
  `a4/task/spike/` must declare `kind: spike`. Mismatched
  declarations are a folder-routing error and should be re-located.
- **`files:` paths under the project source tree, not under
  `spike/<id>-<slug>/`** — breaks the throwaway contract; the writer
  refuses.

(Universal validator catches — stray body content, attribute-bearing
tags, same-tag nesting, H1 in body — are documented in
`a4-workspace-policies.md` §4.)

To validate manually before commit:

```bash
uv run "../scripts/validate_body.py" \
  "<project-root>/a4" --file task/spike/<id>-<slug>.md
```

## Don't (spike-task-specific)

(Universal Don'ts — hand-editing writer-owned fields, inventing ids,
bracketing frontmatter paths, H1 in body, deleting review files —
are in `a4-workspace-policies.md` §10.)

- **Don't put `implemented_by:` on a task.** It is a UC reverse-link,
  auto-maintained by `refresh_implemented_by.py` from `task.implements:`.
- **Don't use `progress` or `failing` as an initial status.** They
  are writer-only, produced by transitions.
- **Don't reverse `pending → open`.** Once enqueued, a spike stays
  enqueued or moves forward / out.
- **Don't author multiple tasks in one `/a4:task` invocation.**
  Re-invoke per task.
- **Don't omit `kind:`.** Every task declares `feature | spike | bug`.
- **Don't auto-delete or auto-archive `spike/<id>-<slug>/`** on
  discard. Archiving is a user-driven `git mv`.
- **Don't write production source from a spike.** `files:` paths
  staying under `spike/<id>-<slug>/` is the contract that keeps PoC
  code throwaway. If the spike's outcome warrants production work,
  follow up with a `kind: feature` task.
- **Don't author a `kind: feature` or `kind: bug` task here.** Move
  features to `a4/task/feature/` and bugs to `a4/task/bug/` so the
  per-kind authoring rule auto-loads.

## After authoring

`/a4:task` author mode runs `refresh_implemented_by.py` (when
`implements:` is non-empty), optionally creates the
`spike/<id>-<slug>/` sidecar (after user confirmation), and suggests
`/a4:run` as the next step. The skill does not commit; the file is
left in the working tree for the user to commit.

`/a4:task discard` flips status, optionally appends `<why-discarded>`,
advises on the spike sidecar without auto-deleting, and reports —
also without committing.

## Cross-references

- [`references/frontmatter-schema.md §Task`](../references/frontmatter-schema.md) —
  full field schema, kind semantics, lifecycle, initial-status policy,
  spike sidecar convention, and validator behavior.
- [`references/body-conventions.md`](../references/body-conventions.md) —
  tag form, blank-line discipline, link form,
  `<change-logs>` / `<log>` rules.
- [`a4-task-feature-authoring.md`](a4-task-feature-authoring.md) —
  feature-task contract (regular implementation work).
- [`a4-task-bug-authoring.md`](a4-task-bug-authoring.md) — bug-task
  contract (reproduction + fixed criteria).
- [`skills/task/SKILL.md`](../skills/task/SKILL.md) —
  the authoring skill itself; this rule complements it for read/edit
  contexts where the skill is not invoked.
- [`skills/task/references/discard.md`](../skills/task/references/discard.md) —
  the discard procedure (D1–D6) loaded by `/a4:task discard`.
- `body_schemas/task.xsd` — the source of truth for required vs
  optional sections; the `a4-section-enum` rule's bullet block is
  generated from it.
