# a4 Frontmatter Schema

Consolidated frontmatter reference for the `a4/` workspace. Extracted from the spec-as-wiki+issues ADR (`plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md`) and the aligned spark skill SKILL.md files. This document is the **single source of truth for validators and skill authors**; the ADR remains the rationale source.

When the ADR and this document disagree, the ADR wins and this document should be updated to match.

## Scope

Every markdown file created by an a4 skill carries YAML frontmatter. Files split into three families:

| Family | Examples | Location |
|--------|----------|----------|
| **Wiki page** | `context.md`, `domain.md`, `architecture.md`, `actors.md`, `nfr.md`, `plan.md`, `bootstrap.md` | `a4/` root |
| **Issue** | use case, task, review item, decision, idea | `a4/usecase/`, `a4/task/`, `a4/review/`, `a4/decision/`, `a4/idea/` |
| **Spark** | brainstorm output | `a4/spark/` |

## Universal rules

These apply to every family.

### Ids

- Ids are **monotonically increasing integers, global to the workspace**. Unique across all issue folders in a given `a4/` (GitHub-issue semantics).
- Next id is computed as `max(existing ids in a4/) + 1` by `plugins/a4/scripts/allocate_id.py`.
- Wiki pages and spark files do **not** carry an `id:` field — they have no issue-tracker identity.

### Path references

Frontmatter fields that reference other files (`depends_on`, `implements`, `target`, `justified_by`, `supersedes`, `related`, `parent`, `promoted`) use the following format:

- **Plain strings.** No wikilink brackets — `usecase/3-search-history`, not `[[usecase/3-search-history]]`. Brackets break dataview parsing.
- **No `.md` extension.** Obsidian basename resolution handles it. Spark brainstorm files keep the `.brainstorm` suffix because it is part of the filename base, not the extension — e.g., `spark/2026-04-23-2119-caching-strategy.brainstorm`.
- **Folder-prefixed when cross-folder.** `usecase/3-search-history`, `task/5-render-markdown`, `review/6-missing-validation`, `decision/8-caching-strategy`, `spark/<base>`. Bare basename (`3-search-history`) resolves correctly because ids are globally unique, but folder-prefixed form is preferred for readability.
- **Wiki targets use bare basename.** `wiki_impact: [architecture, domain]`, not `wiki_impact: [architecture.md]`.

### Dates

- ISO format `YYYY-MM-DD`, unquoted. YAML-native date type so Obsidian dataview can sort and filter.
- All timestamp fields use the same format: `created`, `updated`, session timestamps on spark files.

### Empty collections

Empty lists may be written as `[]` or omitted entirely. Both are semantically equivalent. Prefer omission when the field is not expected to populate; prefer `[]` when the field is part of the type's shape and emptiness is noteworthy (e.g., `promoted: []` on a fresh brainstorm).

### Relationships are forward-only

The ADR fixes **one direction per relationship**. Reverse directions are derived by dataview queries, never stored.

| Forward (stored) | Reverse (derived) |
|------------------|-------------------|
| `depends_on` | `blocks` |
| `implements` | `implemented_by` |
| `justified_by` | `justifies` |
| `supersedes` | `superseded_by` |
| `parent` | `children` |
| `target` | (review backlinks) |
| `wiki_impact` | (wiki backlinks) |
| `promoted` | (spark → pipeline backlinks) |
| `related` | (symmetric; no reverse) |

### Unknown fields

Unknown fields are **not errors**. The validator in lenient mode reports them as informational only. Skills may carry additional fields (e.g., `tags`, `labels`, `milestone`) per the per-type tables below; anything outside the known set is treated as extension metadata.

### Status writers

`a4/` files are always written by an LLM via a skill or agent — never hand-edited by the user. Every status change on `usecase`, `task`, `review`, and `decision` files flows through the single writer at [`scripts/transition_status.py`](../scripts/transition_status.py), which validates the transition, writes `status:` + `updated:` + a `## Log` entry, and runs any cascade (task reset on UC `revising`, task/review discard cascade on UC `discarded`, supersedes-chain flip on UC `shipped`, supersedes-chain flip on decision `final`).

Listing who calls the writer for each value makes the invariant auditable.

| Family | Value | Caller |
|--------|-------|--------|
| usecase | `draft` | `/a4:usecase`, `/a4:auto-usecase`, `usecase-composer` (on create) |
| usecase | `ready` | `/a4:usecase` Step 6 ready-gate (user-confirmed "mark as ready"); also `revising → ready` at the end of a revising-edit session |
| usecase | `implementing` | `task-implementer` Step 1 (flips `ready → implementing` after pre-flight validation; refuses `draft`) |
| usecase | `revising` | `/a4:usecase` (user-triggered in-place spec edit), `task-implementer` (when semantic ambiguity surfaces mid-implementation and a review item is emitted) |
| usecase | `shipped` | `/a4:plan` Step 2.5 (UC ship-review, user-confirmed after Phase 2). Cascade: `supersedes:` targets flip `shipped → superseded` inside the same script invocation |
| usecase | `superseded` | `transition_status.py` cascade — flipped automatically when a newer UC with `supersedes: [usecase/X]` reaches `shipped` |
| usecase | `discarded` | user-triggered via `/a4:usecase` (spec abandoned) or `/a4:plan` (direction rejected). Cascade: related tasks → `discarded`, open review items with `target: usecase/X` → `discarded` |
| usecase | `blocked` | `usecase-reviser` (on SPLIT), `task-implementer` (on implementation-time blocker detection) |
| task | `pending` | `/a4:plan` (on create + on revision reset) |
| task | `implementing` | `/a4:plan` Step 2.2 (before `task-implementer` spawn) |
| task | `complete` | `/a4:plan` Step 2.2 (after agent returns success) |
| task | `failing` | `/a4:plan` Step 2.2 / 2.3 (after agent or test-runner failure) |
| task | `discarded` | `transition_status.py` cascade — when the UC this task implements flips to `discarded`. Direct calls are also permitted for explicit one-off task discards |
| review | `open` | reviewer agents, `drift_detector.py`, `task-implementer` (revising-trigger review items), defer paths in single-edit skills |
| review | `in-progress` | iterate flows (`/a4:usecase`, `/a4:arch`, `/a4:plan` iterate) |
| review | `resolved` | iterate flows + `usecase-reviser` (after fix lands) |
| review | `discarded` | `usecase-reviser`, `/a4:arch`, `/a4:usecase` iterate (when finding is incorrect); `transition_status.py` cascade when a target UC is `discarded` |
| decision | `draft` | `/a4:decision` (file is always born at `draft` when `/a4:decision` writes a new record) |
| decision | `final` | `/a4:decision` Step 6 — flips `draft → final` via `transition_status.py` once the user signals commitment. Cascade: `supersedes:` targets flip `final → superseded` inside the same script invocation |
| decision | `superseded` | `transition_status.py` cascade — flipped automatically when a newer decision with `supersedes: [decision/X]` reaches `final` |
| idea | `open` | `/a4:idea` (capture mode) |
| idea | `promoted` | user-driven; `/a4:decision` / `/a4:usecase` / other consuming skills may write the pipeline target and this status together when the user confirms graduation |
| idea | `discarded` | `/a4:idea discard <id>` |
| brainstorm | `open` | `/a4:spark-brainstorm` (default wrap-up) |
| brainstorm | `promoted` | user-driven; set by hand when an idea from the brainstorm is graduated |
| brainstorm | `discarded` | `/a4:spark-brainstorm` (wrap-up status decision, from natural-language signals) |

Discovery principle: a derived status value is still materialized into the file when a writer can be assigned. `validate_status_consistency.py` remains the fallback safety net for the `promoted` values on `idea`/`brainstorm`, where no mechanical writer exists; for `superseded` on both `usecase` and `decision`, and for `discarded` on tasks/reviews cascaded from a discarded UC, the active writer `transition_status.py` writes the status so the file alone tells you whether the item is current.

## Structural relationship fields

Shared across all issue types. Omit fields that are empty, or use `[]`.

| Field | Applies to | Points at | Meaning |
|-------|-----------|-----------|---------|
| `depends_on` | issue | issue | Items that must complete before this one (lifecycle blocker) |
| `implements` | task | usecase | Use cases delivered by this task |
| `target` | review | any issue or wiki | What this review item is about |
| `wiki_impact` | review, issue | wiki basename(s) | Wiki pages requiring update when this item resolves |
| `justified_by` | any issue | decision | Decisions that justify this item |
| `supersedes` | decision, usecase | prior decision(s) / usecase(s) | This item replaces the referenced item(s) of the same family |
| `promoted` | spark/brainstorm, idea | decision, usecase, task, spark/brainstorm | Where this item's content graduated to (brainstorm: one-to-many ideas grow into pipeline artifacts; idea: a single captured thought becomes a concrete artifact) |
| `parent` | any issue | same-type issue | Parent in a decomposition hierarchy |
| `related` | any | any | Generic catchall for ties that don't fit other fields but warrant frontmatter-level searchability |

Soft references (see-also, mentions) are expressed as Obsidian wikilinks in body prose, not frontmatter. Backlinks surface them in Obsidian's UI without frontmatter maintenance.

## Wiki pages (`a4/<kind>.md`)

Minimal schema — no lifecycle, no id.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `kind` | yes | enum | `context` \| `domain` \| `architecture` \| `actors` \| `nfr` \| `plan` \| `bootstrap` |
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
| `justified_by` | no | list of paths | decisions justifying this UC |
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
| `revising` | Implementation paused for in-place spec edit. Re-enters `ready` on re-approval. Task `implementing`/`failing` entries reset to `pending`; `complete` tasks stay. |
| `shipped` | The running system reflects this use case. Forward-path terminal. |
| `superseded` | A newer UC declares `supersedes: [<this>]` and has shipped. Terminal. |
| `discarded` | Abandoned; direction was wrong or UC no longer needed. Terminal. Related tasks and open review items cascade to `discarded`. |
| `blocked` | Implementation-time blocker surfaced; crosscutting. Resolved via `blocked → ready` or `blocked → discarded`. |

Allowed transitions (forward path + escape paths):

```
draft → ready | discarded
ready → draft | implementing | discarded
implementing → shipped | revising | discarded | blocked
revising → ready | discarded
blocked → ready | discarded
shipped → superseded | discarded
superseded → (terminal)
discarded → (terminal)
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
| `status` | yes | enum | `pending` \| `implementing` \| `complete` \| `failing` \| `discarded` |
| `implements` | no | list of paths | use cases delivered (typically empty for `spike`) |
| `depends_on` | no | list of paths | other tasks this one needs first |
| `justified_by` | no | list of paths | decisions justifying this task |
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

Source: `plugins/a4/spec/2026-04-24-experiments-slot.decide.md`.

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

## Decision (`a4/decision/<id>-<slug>.md`)

ADR stored as an issue — the canonical decision slot from the wiki+issues duality. Decisions are recorded by `/a4:decision` into `a4/decision/<id>-<slug>.md` after the user and LLM converge on a choice through conversation. Supporting research, when needed, is produced separately by `/a4:research` as a portable artifact at project-root `./research/<slug>.md` and cited in the decision's **body prose** as `[[research/<slug>]]` Obsidian wikilinks (not in `related:` frontmatter — research lives outside the `a4/` workspace and is not an issue-family artifact). The wiki nudge (updating `architecture.md` / `context.md` / `domain.md` / `actors.md` / `nfr.md` with footnote markers, or opening a review-item fallback) is performed by `/a4:decision` at record time.

**Body structure.** Two sections are required: `## Context` (why this decision was needed) and `## Decision` (the chosen option with rationale). Both are mechanically enforced by `transition_status.py` on the `draft → final` flip. Beyond those two, additional sections may be added when the session content warrants them — common examples include `## Options Considered`, `## Rejected Alternatives`, `## Next Steps`, `## Consequences`, `## Migration Plan`, `## Open Questions`. Use headed sections (`##` or `###`) only; no free-form prose outside a section.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | decision title |
| `status` | yes | enum | `draft` \| `final` \| `superseded` |
| `framework` | no | string | decision framework used (e.g., `weighted-scoring`, `analysis-driven`) |
| `decision` | no | string | one-line decision summary |
| `supersedes` | no | list of paths | prior decisions replaced |
| `related` | no | list of paths | catchall |
| `tags` | no | list of strings | free-form |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | no | date | `YYYY-MM-DD` (bump when the decision is revised) |

Decisions enter at `draft` while the rationale is still being written, move to `final` via `transition_status.py` once the user signals commitment, and later to `superseded` automatically via `transition_status.py` cascade when a newer decision with `supersedes: [decision/<this-id>-<slug>]` reaches `final`. There is no direct `draft → superseded` path — supersession presumes the predecessor was live (`final`).

## Idea (`a4/idea/<id>-<slug>.md`)

Pre-pipeline quick-capture slot — Jira-issue-style "Idea / Suggestion" with the minimum fields needed to participate in the issue family.

Boundary with `review/`: **idea = independent possibility, captured raw; review = gap in current spec, bound to progress.** If ignoring the input blocks or degrades current spec work it is a review item; otherwise it is an idea. See `plugins/a4/spec/2026-04-24-idea-slot.decide.md` for the full rationale.

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

**Deliberately excluded fields** (see ADR Rejected Alternatives for full rationale):

- `priority` — ideas are pre-prioritization; prioritization attaches to the graduation target.
- `source` — ideas are effectively always `self`; no information content.
- `target` — ideas are independent of other artifacts by definition; a `target` would blur the boundary with `review/`.
- `kind` — only one kind of idea (unlike `review/` which unifies finding/gap/question).
- `milestone` — ideas are not scheduled.

Body is free-form; no required sections. Captured via `/a4:idea <line>` the body is typically just the H1; longer ideas may add `## Why this matters` or `## Notes` sections.

Source: `plugins/a4/skills/idea/SKILL.md` and `plugins/a4/spec/2026-04-24-idea-slot.decide.md`.

## Spark brainstorm (`a4/spark/<YYYY-MM-DD-HHmm>-<slug>.brainstorm.md`)

Pre-pipeline idea capture. Lifecycle tracks whether ideas graduated into pipeline artifacts.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `brainstorm` |
| `pipeline` | yes | literal | `spark` |
| `topic` | yes | string | session topic |
| `status` | yes | enum | `open` \| `promoted` \| `discarded` |
| `promoted` | no | list of paths | populated when `status → promoted` (e.g., `[decision/<id>-<slug>, usecase/<id>-<slug>]`) |
| `tags` | no | list of strings | free-form |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | yes | date | `YYYY-MM-DD` |

Source: `plugins/a4/skills/spark-brainstorm/SKILL.md` lines 91–100.

**Note on the former spark-decide slot.** Historically `a4/spark/<YYYY-MM-DD-HHmm>-<slug>.decide.md` was a separate "pre-pipeline decision" slot. It was retired in favor of direct `a4/decision/<id>-<slug>.md` records. The `/a4:spark-decide` skill was first split into `/a4:research` (investigation at project-root `./research/<slug>.md`) and `/a4:decision-review` (reviewer pass + wiki nudge on a hand-authored decision file); the latter was subsequently retired when it emerged that the review agent assumed a research-grounded decision shape and did not serve simpler, conversation-derived decisions. The current shape is: `/a4:research` (optional) → `/a4:research-review` (optional) → conversation → `/a4:decision` (records the decision + performs the wiki nudge). No spark-family file carries `type: decide` anymore.

## Validator behavior

The validator at `plugins/a4/scripts/validate_frontmatter.py` enforces this schema. Every rule violation is an error; the process exits `2` on any violation and `0` on a clean run.

Body-side conventions (wiki-page footnote format, body wikilink resolution) are enforced by a sibling script `plugins/a4/scripts/validate_body.py`; see [obsidian-conventions.md](./obsidian-conventions.md) for the rules covered there.

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
| `usecase.implemented_by` | list of tasks | Tasks in `a4/task/*.md` carry `implements: [usecase/<this>]` | `refresh_implemented_by.py` (back-scan; called at end of `/a4:plan` Phase 1 and from the `scripts/a4_hook.py session-start` SessionStart hook) |
| `task.status` | `discarded` | UC the task implements flips to `discarded` | `transition_status.py` cascade |
| `task.status` | `pending` (from `implementing`/`failing`) | UC the task implements flips to `revising` | `transition_status.py` cascade |
| `review.status` | `discarded` | UC named by `target:` flips to `discarded` | `transition_status.py` cascade |
| `decision.status` | `superseded` | Another `decision/*.md` declares `supersedes: [<this>]` and has `status: final` | `transition_status.py` cascade (fires during successor's `→ final` transition) |
| `idea.status` | `promoted` | Own `promoted:` list is non-empty | user-driven; `validate_status_consistency.py` surfaces drift |
| `spark/*.brainstorm.md` `status` | `promoted` | Own `promoted:` list is non-empty | user-driven; `validate_status_consistency.py` surfaces drift |

`plugins/a4/scripts/validate_status_consistency.py` reports either direction of mismatch (stale terminal status with no supporting cross-reference, or unflipped status despite supporting cross-reference). It is report-only — no file is mutated.

Two modes:

- **Workspace mode** (`<a4-dir>`) — scans all decisions/ideas/brainstorms. Used by the SessionStart hook and `/a4:validate`.
- **File-scoped mode** (`<a4-dir> --file <path>`) — reports only mismatches in the connected component of the given file (idea/brainstorm: self-contained; decision: supersedes chain). Used by the PostToolUse hook so ordinary edits do not re-surface unrelated legacy mismatches.

## Known deferred items

These are ADR items that this schema deliberately leaves softened until a follow-up round.

1. **Issue comment/log section format.** Body-level `## Log` convention is referenced in the ADR but the exact entry format (prefix, timestamp granularity, author attribution) is not yet locked.
2. **Exact YAML grammar for path references.** Plain string is the current rule; whether to allow alternative forms (list-of-maps for typed references, etc.) is not yet decided.
3. **Stricter enums.** Several fields are currently open strings (`framework`, `source` on review items) because the full value set has not been enumerated.

When these land, update this document **and** the validator simultaneously — the two must not drift.

## Cross-references

- **ADR (authority):** `plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md` §Frontmatter schema (lines ~132–225).
- **Body-level conventions:** `plugins/a4/references/obsidian-conventions.md` — wikilink syntax, footnote audit trail, Wiki Update Protocol.
- **Dataview patterns:** `plugins/a4/references/obsidian-dataview.md` — canonical INDEX.md blocks and reverse-derived relationship views.
- **Id allocator:** `plugins/a4/scripts/allocate_id.py`.
- **Status transition writer:** `plugins/a4/scripts/transition_status.py` — single writer for usecase / task / review / decision status changes; runs cascades (revising task reset, discarded cascade, shipped → superseded chain, decision final → superseded chain).
- **Implemented-by back-link refresher:** `plugins/a4/scripts/refresh_implemented_by.py` — back-scans `task.implements:` into `usecase.implemented_by:`.
- **Drift detector (uses wiki / review schemas):** `plugins/a4/scripts/drift_detector.py`.
- **Cross-file status consistency validator:** `plugins/a4/scripts/validate_status_consistency.py` — reports mismatches between `status:` and the cross-file state that should derive it (superseded, promoted, discarded cascade).
- **Spark schemas (origin):** `plugins/a4/skills/spark-brainstorm/SKILL.md` (brainstorm is the only spark-family schema; `/a4:research` output lives outside `a4/` and is not validated by this schema).
