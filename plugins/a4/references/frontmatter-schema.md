# a4 Frontmatter Schema

Consolidated frontmatter reference for the `a4/` workspace and the aligned spark skill SKILL.md files. This document is the **single source of truth for validators and skill authors**


## Scope

Every markdown file created by an a4 skill carries YAML frontmatter. Files split into three families:

| Family | Examples | Location |
|--------|----------|----------|
| **Wiki page** | `context.md`, `domain.md`, `architecture.md`, `actors.md`, `nfr.md`, `roadmap.md`, `bootstrap.md` | `a4/` root |
| **Issue** | use case, task, review item, spec, idea | `a4/usecase/`, `a4/task/`, `a4/review/`, `a4/spec/`, `a4/idea/` |
| **Spark** | brainstorm output | `a4/spark/` |

## Universal rules

These apply to every family.

### Ids

- Ids are **monotonically increasing integers, global to the workspace**. Unique across all issue folders in a given `a4/` (GitHub-issue semantics).
- Next id is computed as `max(existing ids in a4/) + 1` by `plugins/a4/scripts/allocate_id.py`.
- Wiki pages and spark files do **not** carry an `id:` field — they have no issue-tracker identity.

### Path references

Frontmatter fields that reference other files (`depends_on`, `implements`, `target`, `spec`, `supersedes`, `related`, `parent`, `promoted`) use the following format:

- **Plain strings.** No wikilink brackets — `usecase/3-search-history`, not `[[usecase/3-search-history]]`. Brackets break dataview parsing.
- **No `.md` extension.** Obsidian basename resolution handles it. Spark brainstorm files keep the `.brainstorm` suffix because it is part of the filename base, not the extension — e.g., `spark/2026-04-23-2119-caching-strategy.brainstorm`.
- **Folder-prefixed when cross-folder.** `usecase/3-search-history`, `task/5-render-markdown`, `review/6-missing-validation`, `spec/8-caching-strategy`, `spark/<base>`, `research/<slug>` (project-root `research/`, sibling of `a4/`). Bare basename (`3-search-history`) resolves correctly because ids are globally unique, but folder-prefixed form is preferred for readability.
- **Wiki targets use bare basename.** `wiki_impact: [architecture, domain]`, not `wiki_impact: [architecture.md]`.

### Dates

- ISO format `YYYY-MM-DD`, unquoted. YAML-native date type so Obsidian dataview can sort and filter.
- All timestamp fields use the same format: `created`, `updated`, session timestamps on spark files.

### Empty collections

Empty lists may be written as `[]` or omitted entirely. Both are semantically equivalent. Prefer omission when the field is not expected to populate; prefer `[]` when the field is part of the type's shape and emptiness is noteworthy (e.g., `promoted: []` on a fresh brainstorm).

### Relationships

The schema fixes **one direction per relationship** — the forward direction is the canonical source. Reverse directions are normally **derived on demand** (Obsidian dataview, grep, script back-scan) rather than stored.

**Stored-reverse exception.** A reverse direction may be stored as a frontmatter field when a script owns writes for it and a concrete consumer benefits from frontmatter-direct access. Two current cases:

- `usecase.implemented_by` — stored, auto-maintained by `scripts/refresh_implemented_by.py` (back-scan of `task.implements:`), consumed by the `usecase.ready → implementing` status gate in `transition_status.py` (which requires `implemented_by:` non-empty).
- `research.cited_by` — stored on the project-root research artifact, written atomically by `scripts/register_research_citation.py` alongside the forward `spec.research:` field. Consumed by the SessionStart staleness courtesy that reminds the user about uncited `status: final` research older than the configured threshold.

Hand-editing stored-reverse fields is forbidden.

Adding a new stored reverse link follows the same bar: a script must own writes, and there must be a concrete consumer (status gate, validator, hot query) that justifies bypassing derive-on-demand. Otherwise prefer derived.

| Forward (stored) | Reverse | Storage |
|------------------|---------|---------|
| `depends_on` | `blocks` | derived |
| `implements` | `implemented_by` | **stored — auto-maintained by `refresh_implemented_by.py`** |
| `supersedes` | `superseded_by` | derived |
| `parent` | `children` | derived |
| `target` | (review backlinks) | derived |
| `wiki_impact` | (wiki backlinks) | derived |
| `promoted` | (spark → pipeline backlinks) | derived |
| `spec.research` | `research.cited_by` | **stored — auto-maintained by `register_research_citation.py`** |
| `related` | (symmetric; no reverse) | — |

### Unknown fields

Unknown fields are **not errors**. The validator in lenient mode reports them as informational only. Skills may carry additional fields (e.g., `tags`, `labels`, `milestone`) per the per-type tables below; anything outside the known set is treated as extension metadata.

### Status writers

`a4/` files are always written by an LLM via a skill or agent — never hand-edited by the user. Every status change on `usecase`, `task`, `review`, and `spec` files flows through the single writer at [`scripts/transition_status.py`](../scripts/transition_status.py), which validates the transition, writes `status:` + `updated:` + a `## Log` entry, and runs any cascade (task reset on UC `revising`, task/review discard cascade on UC `discarded`, supersedes-chain flip on UC `shipped`, supersedes-chain flip on spec `active`).

Listing who calls the writer for each value makes the invariant auditable.

| Family | Value | Caller |
|--------|-------|--------|
| usecase | `draft` | `/a4:usecase`, `/a4:auto-usecase`, `usecase-composer` (on create) |
| usecase | `ready` | `/a4:usecase` Step 6 ready-gate (user-confirmed "mark as ready"); also `revising → ready` at the end of a revising-edit session |
| usecase | `implementing` | `task-implementer` Step 1 (flips `ready → implementing` after pre-flight validation; refuses `draft`) |
| usecase | `revising` | `/a4:usecase` (user-triggered in-place spec edit), `task-implementer` (when semantic ambiguity surfaces mid-implementation and a review item is emitted) |
| usecase | `shipped` | `/a4:run` Step 5 (UC ship-review, user-confirmed after the implement + test loop). Cascade: `supersedes:` targets flip `shipped → superseded` inside the same script invocation |
| usecase | `superseded` | `transition_status.py` cascade — flipped automatically when a newer UC with `supersedes: [usecase/X]` reaches `shipped` |
| usecase | `discarded` | user-triggered via `/a4:usecase` (spec abandoned) or `/a4:roadmap` (direction rejected). Cascade: related tasks → `discarded`, open review items with `target: usecase/X` → `discarded` |
| usecase | `blocked` | `usecase-reviser` (on SPLIT), `task-implementer` (on implementation-time blocker detection) |
| task | `open` | `/a4:task` (on create — default backlog state). Not picked up by `/a4:run`; user must transition to `pending` to enqueue |
| task | `pending` | `/a4:roadmap` (on create — batch fill-queue intent), `/a4:task` (on create when user opts in over the default `open`), `/a4:run` (on revision reset, on `failing → pending` defer) |
| task | `progress` | `/a4:run` Step 2 (before `task-implementer` spawn); `task-implementer` when spawned outside `/a4:run` (flips `open → progress` or `pending → progress` directly); user-driven via `transition_status.py` when an LLM-conversation session starts work on a task without going through `/a4:run` |
| task | `complete` | `/a4:run` Step 2 (after agent returns success); `/a4:task` (on create, post-hoc documentation for already-implemented work) |
| task | `failing` | `/a4:run` Step 2 / 3 (after agent or test-runner failure) |
| task | `discarded` | `transition_status.py` cascade — when the UC this task implements flips to `discarded`. Direct calls are also permitted for explicit one-off task discards |
| review | `open` | reviewer agents, `drift_detector.py`, `task-implementer` (revising-trigger review items), defer paths in single-edit skills |
| review | `in-progress` | iterate flows (`/a4:usecase`, `/a4:arch`, `/a4:roadmap` iterate) |
| review | `resolved` | iterate flows + `usecase-reviser` (after fix lands) |
| review | `discarded` | `usecase-reviser`, `/a4:arch`, `/a4:usecase` iterate (when finding is incorrect); `transition_status.py` cascade when a target UC is `discarded` |
| spec | `draft` | `/a4:spec` (file is always born at `draft` when `/a4:spec` writes a new record) |
| spec | `active` | `/a4:spec` Step 6 — flips `draft → active` via `transition_status.py` once the spec is committed. Cascade: `supersedes:` targets flip `active → superseded` (or `deprecated → superseded`) inside the same script invocation |
| spec | `deprecated` | `/a4:spec` (user signals the spec is no longer the live source of truth but is not yet replaced; still readable for context) |
| spec | `superseded` | `transition_status.py` cascade — flipped automatically when a newer spec with `supersedes: [spec/X]` reaches `active` |
| idea | `open` | `/a4:idea` (capture mode) |
| idea | `promoted` | user-driven; `/a4:spec` / `/a4:usecase` / other consuming skills may write the pipeline target and this status together when the user confirms graduation |
| idea | `discarded` | `/a4:idea discard <id>` |
| brainstorm | `open` | `/a4:spark-brainstorm` (default wrap-up) |
| brainstorm | `promoted` | user-driven; set by hand when an idea from the brainstorm is graduated |
| brainstorm | `discarded` | `/a4:spark-brainstorm` (wrap-up status decision, from natural-language signals) |

Discovery principle: a derived status value is still materialized into the file when a writer can be assigned. `validate_status_consistency.py` remains the fallback safety net for the `promoted` values on `idea`/`brainstorm`, where no mechanical writer exists; for `superseded` on both `usecase` and `spec`, and for `discarded` on tasks/reviews cascaded from a discarded UC, the active writer `transition_status.py` writes the status so the file alone tells you whether the item is current.

The `workspace-assistant` agent calls `transition_status.py` on behalf of the caller (typically the main session, when delegating to save context) and is therefore not listed as a separate caller in the table above — it executes only `(file, target_status)` pairs the caller has explicitly named, and never decides status on its own.

## Structural relationship fields

Shared across all issue types. Omit fields that are empty, or use `[]`.

| Field | Applies to | Points at | Meaning |
|-------|-----------|-----------|---------|
| `depends_on` | issue | issue | Items that must complete before this one (lifecycle blocker) |
| `implements` | task | usecase | Use cases delivered by this task |
| `target` | review | any issue or wiki | What this review item is about |
| `wiki_impact` | review, issue | wiki basename(s) | Wiki pages requiring update when this item resolves |
| `spec` | any issue | spec | Specs that govern this item |
| `supersedes` | spec, usecase | prior spec(s) / usecase(s) | This item replaces the referenced item(s) of the same family |
| `promoted` | spark/brainstorm, idea | spec, usecase, task, spark/brainstorm | Where this item's content graduated to (brainstorm: one-to-many ideas grow into pipeline artifacts; idea: a single captured thought becomes a concrete artifact) |
| `parent` | any issue | same-type issue | Parent in a decomposition hierarchy |
| `related` | any | any | Generic catchall for ties that don't fit other fields but warrant frontmatter-level searchability |

Soft references (see-also, mentions) are expressed as Obsidian wikilinks in body prose, not frontmatter. Backlinks surface them in Obsidian's UI without frontmatter maintenance.

## Wiki pages (`a4/<kind>.md`)

Minimal schema — no lifecycle, no id.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `kind` | yes | enum | `context` \| `domain` \| `architecture` \| `actors` \| `nfr` \| `roadmap` \| `bootstrap` |
| `updated` | yes | date | `YYYY-MM-DD` |

Example:

```yaml
---
kind: architecture
updated: 2026-04-24
---
```

The `kind` value must match the file basename (e.g., `kind: architecture` requires `architecture.md`). Cross-references live as Obsidian wikilinks in body prose plus the `## Changes` footnote section; they are **not** in frontmatter.

## Use case (`a4/usecase/<id>-<slug>.md`)

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | human-readable |
| `status` | yes | enum | `draft` \| `ready` \| `implementing` \| `revising` \| `shipped` \| `superseded` \| `discarded` \| `blocked` |
| `actors` | no | list of strings | actor names as defined in `actors.md` |
| `depends_on` | no | list of paths | other use cases this UC needs first |
| `spec` | no | list of paths | Specs governing this UC |
| `supersedes` | no | list of paths | prior use cases this UC replaces (see §Status writers) |
| `implemented_by` | no | list of paths | reverse link to tasks that implement this UC. **Auto-maintained** by `scripts/refresh_implemented_by.py` — never hand-write |
| `related` | no | list of paths | catchall |
| `labels` | no | list of strings | free-form tags |
| `milestone` | no | string | milestone name (e.g., `v1.0`) |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | yes | date | `YYYY-MM-DD` |

### UC lifecycle

Forward progression runs `draft → ready → implementing → shipped`, with `revising` as an in-place pause for spec edit, `blocked` as an off-path crosscutting state, and terminal sinks `superseded` and `discarded`.

| Value | Meaning |
|-------|---------|
| `draft` | Spec is still being shaped; not ready for implementation. |
| `ready` | Spec is closed; ready to be picked up by an implementer. |
| `implementing` | Coding agent is actively working on the UC. |
| `revising` | Implementation paused for in-place spec edit. Re-enters `ready` on re-approval. Task `progress`/`failing` entries reset to `pending`; `open`/`pending`/`complete` tasks stay. |
| `shipped` | The running system reflects this use case. Forward-path terminal. |
| `superseded` | A newer UC declares `supersedes: [<this>]` and has shipped. Terminal. |
| `discarded` | Abandoned; direction was wrong or UC no longer needed. Terminal. Related tasks and open review items cascade to `discarded`. |
| `blocked` | Implementation-time blocker surfaced; crosscutting. Resolved via `blocked → ready` or `blocked → discarded`. |

Allowed transitions (forward path + escape paths):

```
draft        → discarded | ready
ready        → discarded | draft | implementing
implementing → blocked | discarded | revising | shipped
revising     → discarded | ready
blocked      → discarded | ready
shipped      → discarded | superseded
discarded    → (terminal)
superseded   → (terminal)
```

Notable rules:

- **`implementing → draft` is disallowed.** Once code has started, the UC cannot roll back to pre-spec-closed state. Use `implementing → revising` for in-place edit or `implementing → discarded` for abandonment.
- **`shipped` never returns to `implementing`/`draft`.** Post-ship requirement changes are modeled as either (a) a **new** UC with `supersedes: [usecase/<old>]` — when that new UC ships, the old one flips to `superseded`; or (b) `shipped → discarded` when the feature is being removed from the code.
- **`revising` is in-place.** No new UC is created for the paused spec; the same file is edited through `/a4:usecase`, and Step 6 ready-gate re-approves `revising → ready`.
- **`ready → implementing` requires `implemented_by:` non-empty.** The UC must have at least one task declaring `implements: [usecase/<this>]`.
- **`implementing → shipped` requires every task in `implemented_by:` to be `complete`.** `transition_status.py` enforces this.

## Task (`a4/task/<id>-<slug>.md`)

Jira "task" semantics — a unit of executable work. The `kind:` field distinguishes regular implementation, time-boxed exploration, and defect work; lifecycle is identical across kinds.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | human-readable |
| `kind` | yes | enum | `feature` \| `spike` \| `bug` |
| `status` | yes | enum | `open` \| `pending` \| `progress` \| `complete` \| `failing` \| `discarded` |
| `implements` | no | list of paths | use cases delivered (typically empty for `spike`) |
| `depends_on` | no | list of paths | other tasks this one needs first |
| `spec` | no | list of paths | Specs governing this task |
| `files` | no | list of strings | source paths the task writes or modifies. For `kind: spike`, points at `spike/<id>-<slug>/...` (or `spike/archive/<id>-<slug>/...` after archive); for `feature`/`bug`, points at the project's production source tree |
| `cycle` | no | int | implementation cycle number |
| `labels` | no | list of strings | free-form tags |
| `milestone` | no | string | milestone name |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | yes | date | `YYYY-MM-DD` |

### Kind semantics

| Value | Meaning |
|-------|---------|
| `feature` | Regular implementation — new functionality, extension, refactor. The default case. |
| `spike` | Time-boxed exploration to unblock a decision (XP sense). Throwaway code expected. PoC, investigation, benchmark. PoC code lives at project-root `spike/<id>-<slug>/`, **outside the `a4/` workspace**. |
| `bug` | Defect fix. Production code change, not throwaway. |

`kind` is **required** — every task must declare one. There is no implicit default. Existing task files predating this schema will fail validation until backfilled with an explicit `kind:` value.

### Task lifecycle

| Value | Meaning |
|-------|---------|
| `open` | Backlog (kanban "todo"). Captured but not yet committed to the work queue. Not picked up by `/a4:run`; user must transition `open → pending` to enqueue. |
| `pending` | In the work queue, awaiting an implementer. Default ready-set entry for `/a4:run`. |
| `progress` | A `task-implementer` agent is working (or crashed mid-work — reset to `pending` on session resume by `/a4:run`). |
| `complete` | Unit tests passed. Not a forward-path terminal — UC `revising` cascade can return tasks to `pending` for re-implementation. |
| `failing` | Unit tests red. Resumed via `failing → progress` (immediate retry, same cycle) or deferred via `failing → pending` (next cycle). |
| `discarded` | Abandoned. Terminal. Reached either via UC `discarded` cascade or explicit `/a4:task discard`. |

Allowed transitions:

```
open      → discarded | pending | progress
pending   → discarded | progress
progress  → complete | discarded | failing | pending
complete  → discarded | pending
failing   → discarded | pending | progress
discarded → (terminal)
```

`open → progress` is allowed when work is initiated outside `/a4:run` — for example, a `task-implementer` spawned directly, or an LLM-conversation session that starts implementing a backlog task without batch enqueue. The `pending` step exists to express `/a4:run` queue intent; skip it when the queue is not the entry path. There is no `pending → open` reverse — once enqueued, a task cannot be returned to backlog.

### Initial status policy

`/a4:task` allows three initial states on file create:

- `open` (default) — backlog capture.
- `pending` — author intends `/a4:run` to pick it up immediately.
- `complete` — post-hoc documentation: code already shipped, task file added for traceability. Skill must verify every path in `files:` exists at create time and append an explicit `## Log` entry noting the post-hoc origin (since no `progress → complete` transition was logged by the writer).

`/a4:roadmap` always writes new tasks at `pending` — batch generation reflects "fill the queue right now" intent.

`progress` and `failing` are never used as initial states; only the writer (`transition_status.py`) produces them as a result of transitions.

### Spike sidecar convention

For tasks with `kind: spike`, accompanying PoC code lives at project-root `spike/<id>-<slug>/`, parallel to (not inside) `a4/`:

```
<project-root>/
  a4/task/<id>-<slug>.md       # task markdown — kind: spike
  spike/<id>-<slug>/           # PoC code, data, scratch notes
    *.py *.json ...
```

When a spike completes (or fails), the user manually `git mv`s the directory to `spike/archive/<id>-<slug>/` and updates the task's `files:` paths to match. `spike/archive/` is a sibling of active spike directories — self-contained under the `spike/` umbrella. The move is **never automated**; same-precedent reasoning as `idea/` promotion (deferred until manual cost surfaces as pain).

`feature` and `bug` tasks have no `spike/` sidecar; their `files:` paths point at the project's production source tree (outside both `a4/` and `spike/`).

The `spike/` directory:

- Is part of the project repo, not a temporary scratch area.
- Is not validated by any a4 script — the markdown-only contract of `a4/` is preserved.
- Is opt-in — projects without spike tasks have no `spike/` directory.

Source: `plugins/a4/spec/archive/2026-04-24-experiments-slot.decide.md`.

## Review item (`a4/review/<id>-<slug>.md`)

Unified conduit for findings, gaps, and questions. The `kind:` field distinguishes them; lifecycle is identical.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `id` | yes | int | monotonic global integer |
| `kind` | yes | enum | `finding` \| `gap` \| `question` |
| `status` | yes | enum | `open` \| `in-progress` \| `resolved` \| `discarded` |
| `target` | no | path | what this review is about (omit for cross-cutting) |
| `source` | yes | enum \| string | `self` \| `drift-detector` \| `<reviewer-agent-name>` (e.g., `usecase-reviewer-r2`) |
| `wiki_impact` | no | list of wiki basenames | wiki pages needing update when this resolves |
| `priority` | no | enum | `high` \| `medium` \| `low` |
| `labels` | no | list of strings | free-form; drift-detector uses `drift:<kind>` and `drift-cause:<slug>` |
| `milestone` | no | string | milestone name |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | yes | date | `YYYY-MM-DD` |

**Close guard.** A review item with non-empty `wiki_impact` cannot cleanly transition to `resolved` unless each referenced wiki page contains a footnote whose `## Changes` payload wikilinks the causing issue (`target`). Enforcement is a warning with override — the drift detector re-surfaces violations.

## Spec (`a4/spec/<id>-<slug>.md`)

A spec is a **living specification** — the canonical, prescriptive description of a format, protocol, schema, renderer rule, CLI surface, or other artifact whose exact shape the project commits to. Specs are recorded by `/a4:spec` into `a4/spec/<id>-<slug>.md` after the user and LLM converge on the shape through conversation. Supporting research, when needed, is produced separately by `/a4:research` as a portable artifact at project-root `./research/<slug>.md` and registered atomically via `scripts/register_research_citation.py`. Each citation is recorded in four places — the spec's `research:` frontmatter list and `## Research` body section, plus the research file's `cited_by:` frontmatter list and `## Cited By` body section. Frontmatter representations are queryable via dataview; body prose preserves the in-context citation. The `related:` frontmatter field on a spec is **not** the right slot for research — `research` is the dedicated forward field; `related:` remains for cross-references between issue-family artifacts. The wiki nudge (updating `architecture.md` / `context.md` / `domain.md` / `actors.md` / `nfr.md` with footnote markers, or opening a review-item fallback) is performed by `/a4:spec` at record time.

**Body structure.** Two sections are required: `## Context` (why this spec exists — the problem or scope it covers) and `## Specification` (the prescriptive content — grammar, fields, rules, examples). Both are mechanically enforced by `transition_status.py` on the `draft → active` flip. Beyond those two, additional sections may be added when the session content warrants them — common examples include `## Decision Log`, `## Open Questions`, `## Rejected Alternatives`, `## Consequences`, `## Examples`. Use headed sections (`##` or `###`) only; no free-form prose outside a section.

**`## Decision Log` absorbs ADR-style notes.** The previous a4 model carried ADRs as a separate family; that role now lives inside the spec body as an optional `## Decision Log` section. Each entry is a short note (date + what was chosen + why), so the chain of design decisions that shaped a particular spec is co-located with the spec itself rather than scattered across decision records. Entries are append-only — earlier entries are never edited or removed; corrections are added as new entries that supersede the prior reasoning. This is the only sanctioned location for "decision rationale" content; do not introduce a separate `decisions/` slot, do not split decisions into their own files.

The spec body is **prescriptive**: it captures the chosen shape that downstream code, validators, and review items must conform to. Implementation tasks reference the spec via the forward `task.spec:` field; the reverse view is derived on demand and never rendered into the spec body. Sections such as `## Migration Plan` are not used — migration work lives in `task/<id>-<slug>.md`.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | spec title |
| `status` | yes | enum | `draft` \| `active` \| `deprecated` \| `superseded` |
| `decision` | no | string | one-line shape summary |
| `supersedes` | no | list of paths | prior specs replaced |
| `research` | no | list of paths | research artifacts informing this spec (`research/<slug>`); auto-maintained by `register_research_citation.py` together with the body `## Research` section |
| `related` | no | list of paths | catchall |
| `labels` | no | list of strings | free-form tags |
| `tags` | no | list of strings | free-form (alias of `labels`; either is accepted) |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | no | date | `YYYY-MM-DD` (bump when the spec is revised) |

### Spec lifecycle

| Value | Meaning |
|-------|---------|
| `draft` | Spec is being authored; shape is not yet committed. |
| `active` | Spec is live; downstream code and validators must conform. |
| `deprecated` | Spec is no longer the live source of truth — preserved for context, but new work should not target it. May or may not have a successor yet. |
| `superseded` | A newer spec declares `supersedes: [<this>]` and has reached `active`. Terminal. |

Allowed transitions:

```
draft      → active | deprecated
active     → deprecated | superseded
deprecated → superseded
superseded → (terminal)
```

Notable rules:

- **`draft → superseded` is disallowed** — supersession presumes the predecessor was at one point live (`active` or `deprecated`).
- **`active → superseded` requires a newer spec at `active`** with `supersedes: [spec/<this>]`. The flip is automatic via `transition_status.py` cascade during the successor's `→ active` transition.
- **`deprecated` is opt-in retirement** — used when the user wants to mark a spec as no longer authoritative even before a successor exists. Useful for retiring formats whose replacement is still under design.
- **No reverse path from `deprecated → active`** — once retired, a new spec must be authored to revive the shape (typically with `supersedes:` pointing back to clarify lineage).

## Idea (`a4/idea/<id>-<slug>.md`)

Pre-pipeline quick-capture slot — Jira-issue-style "Idea / Suggestion" with the minimum fields needed to participate in the issue family.

Boundary with `review/`: **idea = independent possibility, captured raw; review = gap in current spec, bound to progress.** If ignoring the input blocks or degrades current spec work it is a review item; otherwise it is an idea. See `plugins/a4/spec/archive/2026-04-24-idea-slot.decide.md` for the full rationale.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | human-readable one-liner (becomes H1) |
| `status` | yes | enum | `open` \| `promoted` \| `discarded` |
| `promoted` | no | list of paths | populated when `status → promoted` (e.g., `[usecase/5-search, spark/2026-04-24-1730-idea-x.brainstorm]`) |
| `related` | no | list of paths | soft links to other artifacts |
| `labels` | no | list of strings | free-form tags |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | yes | date | `YYYY-MM-DD` |

**Deliberately excluded fields** (see the prior decision archive for full rationale):

- `priority` — ideas are pre-prioritization; prioritization attaches to the graduation target.
- `source` — ideas are effectively always `self`; no information content.
- `target` — ideas are independent of other artifacts by definition; a `target` would blur the boundary with `review/`.
- `kind` — only one kind of idea (unlike `review/` which unifies finding/gap/question).
- `milestone` — ideas are not scheduled.

Body is free-form; no required sections. Captured via `/a4:idea <line>` the body is typically just the H1; longer ideas may add `## Why this matters` or `## Notes` sections.

Source: `plugins/a4/skills/idea/SKILL.md` and `plugins/a4/spec/archive/2026-04-24-idea-slot.decide.md`.

## Spark brainstorm (`a4/spark/<YYYY-MM-DD-HHmm>-<slug>.brainstorm.md`)

Pre-pipeline idea capture. Lifecycle tracks whether ideas graduated into pipeline artifacts.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `brainstorm` |
| `pipeline` | yes | literal | `spark` |
| `topic` | yes | string | session topic |
| `status` | yes | enum | `open` \| `promoted` \| `discarded` |
| `promoted` | no | list of paths | populated when `status → promoted` (e.g., `[spec/<id>-<slug>, usecase/<id>-<slug>]`) |
| `tags` | no | list of strings | free-form |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | yes | date | `YYYY-MM-DD` |

Source: `plugins/a4/skills/spark-brainstorm/SKILL.md` lines 91–100.

**Note on the former spark-decide slot.** Historically `a4/spark/<YYYY-MM-DD-HHmm>-<slug>.decide.md` was a separate "pre-pipeline decision" slot. It was retired in favor of direct `a4/spec/<id>-<slug>.md` records (with `## Decision Log` absorbing the rationale that previously lived in standalone decision records). The current shape is: `/a4:research` (optional) → `/a4:research-review` (optional) → conversation → `/a4:spec` (records the spec + performs the wiki nudge). No spark-family file carries `type: decide` anymore.

## Research artifact (project-root `research/<slug>.md`)

Research files live **outside** `a4/` — at project-root `research/` (sibling of `a4/`). They are portable, workspace-agnostic, and are **not** validated by `validate_frontmatter.py`. The convention below is documented here because `spec.research:` cites these files and `register_research_citation.py` writes their reverse-link.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `topic` | yes | string | research topic |
| `status` | yes | enum | `draft` \| `final` \| `standalone` \| `archived` |
| `mode` | yes | literal | `comparative` \| `single` |
| `options` | conditional | list of strings | required when `mode: comparative` |
| `cited_by` | no | list of paths | reverse link to citing ADRs; auto-maintained by `register_research_citation.py` |
| `tags` | no | list of strings | free-form |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | yes | date | `YYYY-MM-DD` (bumped by `register_research_citation.py` whenever it touches the file) |

Status semantics:

- `draft` — research is being authored.
- `final` — research is complete; may or may not have been cited yet.
- `standalone` — research is complete and intentionally not feeding any spec (terminal). The SessionStart staleness courtesy never nudges `standalone` files.
- `archived` — research is no longer relevant (terminal).

The staleness courtesy nudges only files at `status: final` with empty `cited_by:` and `updated:` older than a threshold; everything else is silent.

## Validator behavior

The validator at `plugins/a4/scripts/validate_frontmatter.py` enforces this schema. Every rule violation is an error; the process exits `2` on any violation and `0` on a clean run.

Body-side conventions (wiki-page footnote format, body wikilink resolution) are enforced by a sibling script `plugins/a4/scripts/validate_body.py`; see [obsidian-conventions.md](${CLAUDE_PLUGIN_ROOT}/references/obsidian-conventions.md) for the rules covered there.

| Rule | Behavior |
|------|----------|
| Unknown fields | **ignored** (the one point of leniency) |
| Missing required field | error |
| Wrong type for a known field | error |
| Value outside enum for a known field | error |
| Path-reference format (wikilink brackets, `.md` extension) | error |
| `kind` on wiki page disagrees with filename | error |
| `wiki_impact` entry not in the wiki-kind enum | error |
| Id collision across issue folders | error |
| File in an issue/spark folder has no frontmatter | error |

Hook scope is a separate concern — the validator reports; the caller (hook, skill, manual invocation) decides whether to block, notify, or ignore.

### Cross-file status consistency

Several enum values are semantically derived from cross-file state rather than being chosen in isolation:

| Field | Derived value | Condition | Materialized by |
|-------|--------------|-----------|-----------------|
| `usecase.status` | `superseded` | A newer `usecase/*.md` with `supersedes: [<this>]` has `status: shipped` | `transition_status.py` cascade (fires during successor's `→ shipped` transition) |
| `usecase.implemented_by` | list of tasks | Tasks in `a4/task/*.md` carry `implements: [usecase/<this>]` | `refresh_implemented_by.py` (back-scan; called at end of `/a4:roadmap` Step 3 and from `/a4:task` Step 6, plus the `scripts/a4_hook.py session-start` SessionStart hook) |
| `task.status` | `discarded` | UC the task implements flips to `discarded` | `transition_status.py` cascade |
| `task.status` | `pending` (from `implementing`/`failing`) | UC the task implements flips to `revising` | `transition_status.py` cascade |
| `review.status` | `discarded` | UC named by `target:` flips to `discarded` | `transition_status.py` cascade |
| `spec.status` | `superseded` | Another `spec/*.md` declares `supersedes: [<this>]` and has `status: active` | `transition_status.py` cascade (fires during successor's `→ active` transition) |
| `idea.status` | `promoted` | Own `promoted:` list is non-empty | user-driven; `validate_status_consistency.py` surfaces drift |
| `spark/*.brainstorm.md` `status` | `promoted` | Own `promoted:` list is non-empty | user-driven; `validate_status_consistency.py` surfaces drift |

`plugins/a4/scripts/validate_status_consistency.py` reports either direction of mismatch (stale terminal status with no supporting cross-reference, or unflipped status despite supporting cross-reference). It is report-only — no file is mutated.

Two modes:

- **Workspace mode** (`<a4-dir>`) — scans all specs/ideas/brainstorms. Used by the SessionStart hook and `/a4:validate`.
- **File-scoped mode** (`<a4-dir> --file <path>`) — reports only mismatches in the connected component of the given file (idea/brainstorm: self-contained; spec: supersedes chain). Used by the PostToolUse hook so ordinary edits do not re-surface unrelated legacy mismatches.

## Known deferred items

These are schema items deliberately left softened until a follow-up round.

1. **Issue comment/log section format.** Body-level `## Log` convention is referenced throughout but the exact entry format (prefix, timestamp granularity, author attribution) is not yet locked.
2. **Exact YAML grammar for path references.** Plain string is the current rule; whether to allow alternative forms (list-of-maps for typed references, etc.) is not yet decided.
3. **Stricter enums.** Several fields are currently open strings (`source` on review items) because the full value set has not been enumerated.

When these land, update this document **and** the validator simultaneously — the two must not drift.

## Cross-references

- **Body-level conventions:** `plugins/a4/references/obsidian-conventions.md` — wikilink syntax, footnote audit trail, Wiki Update Protocol.
- **Id allocator:** `plugins/a4/scripts/allocate_id.py`.
- **Status model (canonical):** `plugins/a4/scripts/status_model.py` — per-family status enums, allowed transitions, terminal/in-progress/active classifications, kind enums. Imported by the writer, validators, workspace state, and search; the prose tables in this document mirror the same data.
- **Status transition writer:** `plugins/a4/scripts/transition_status.py` — single writer for usecase / task / review / spec status changes; runs cascades (revising task reset, discarded cascade, shipped → superseded chain, spec active → superseded chain).
- **Implemented-by back-link refresher:** `plugins/a4/scripts/refresh_implemented_by.py` — back-scans `task.implements:` into `usecase.implemented_by:`.
- **Research citation registrar:** `plugins/a4/scripts/register_research_citation.py` — atomically records a research → spec citation in four places (spec frontmatter `research:`, spec body `## Research`, research frontmatter `cited_by:`, research body `## Cited By`) and bumps the research file's `updated:`.
- **Drift detector (uses wiki / review schemas):** `plugins/a4/scripts/drift_detector.py`.
- **Cross-file status consistency validator:** `plugins/a4/scripts/validate_status_consistency.py` — reports mismatches between `status:` and the cross-file state that should derive it (superseded, promoted, discarded cascade).
- **Spark schemas (origin):** `plugins/a4/skills/spark-brainstorm/SKILL.md` (brainstorm is the only spark-family schema; `/a4:research` output lives outside `a4/` and is not validated by this schema).
