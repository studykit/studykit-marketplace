# a4 Frontmatter Schema

Consolidated frontmatter reference for every file under the `a4/` workspace. This document is the **single source of truth for validators and authoring contracts**.

Body-side conventions (tag form, blank-line discipline, change-log and log section format, link form) live in `body-conventions.md`. The two should be read together.

## Scope

Every markdown file under `a4/` carries YAML frontmatter. Files split into three families:

| Family | Examples | Location |
|--------|----------|----------|
| **Wiki page** | `context.md`, `domain.md`, `architecture.md`, `actors.md`, `nfr.md`, `roadmap.md`, `bootstrap.md` | `a4/` root |
| **Issue** | use case, task, review item, spec, idea | `a4/usecase/`, `a4/task/<kind>/` (`feature`/`bug`/`spike`), `a4/review/`, `a4/spec/`, `a4/idea/` |
| **Spark** | brainstorm output | `a4/spark/` |

## Universal rules

These apply to every family.

### `type:` field — body root tag

Every markdown file declares a `type:` field in frontmatter. The value names the **body root tag** and resolves to a per-type XSD at `../scripts/body_schemas/<type>.xsd`. The XSD declares which `<tag>` sections are required vs optional in the body.

| Family | `type:` value | Body root tag |
|--------|--------------|---------------|
| Wiki — actors | `actors` | `<actors>` content |
| Wiki — architecture | `architecture` | `<architecture>` content |
| Wiki — bootstrap | `bootstrap` | `<bootstrap>` content |
| Wiki — context | `context` | `<context>` content |
| Wiki — domain | `domain` | `<domain>` content |
| Wiki — nfr | `nfr` | `<nfr>` content |
| Wiki — roadmap | `roadmap` | `<roadmap>` content |
| Issue — usecase | `usecase` | — |
| Issue — task | `task` | — |
| Issue — review | `review` | — |
| Issue — spec | `spec` | — |
| Issue — idea | `idea` | — |
| Issue — research (project-root) | `research` | — |
| Spark — brainstorm | `brainstorm` | — |

For wiki pages, `type:` doubles as the file-kind discriminator (e.g., `type: architecture` requires the file to be at `a4/architecture.md`). For issues and spark files, `type:` is the body schema selector — the file family is already implied by the folder.

Validator rules:

- Missing `type:` → `body-type-missing` (error).
- `type:` value with no matching XSD under `body_schemas/` → `body-type-unknown` (error).
- Wiki page `type:` not matching the file basename (e.g., `type: domain` in `architecture.md`) → frontmatter validator error.

### Body section tags

Body sections are column-0 `<tag>...</tag>` blocks (lowercase + kebab-case) with markdown content between the open and close lines. The set of allowed tags per `type:` is fixed by the XSD; required tags must appear, optional tags may appear, unknown tags are tolerated. See `body-conventions.md` for the full tag-form rules and [§Body sections per type](#body-sections-per-type) below for the per-type required/optional split.

### Ids

- Ids are **monotonically increasing integers, global to the workspace**. Unique across all issue folders in a given `a4/` (GitHub-issue semantics).
- Next id is computed as `max(existing ids in a4/) + 1` by `../scripts/allocate_id.py`.
- Wiki pages and spark files do **not** carry an `id:` field — they have no issue-tracker identity.

### Path references

Frontmatter fields that reference other files (`depends_on`, `implements`, `target`, `spec`, `supersedes`, `related`, `parent`, `promoted`) use the following format:

- **Plain strings.** No brackets — `usecase/3-search-history`, not `[usecase/3-search-history]`. Plain strings keep frontmatter machine-parseable.
- **No `.md` extension.** Spark brainstorm files keep the `.brainstorm` suffix because it is part of the filename base, not the extension — e.g., `spark/2026-04-23-2119-caching-strategy.brainstorm`.
- **Folder-prefixed when cross-folder.** `usecase/3-search-history`, `task/5-render-markdown`, `review/6-missing-validation`, `spec/8-caching-strategy`, `spark/<base>`, `research/<slug>` (project-root `research/`, sibling of `a4/`). Bare basename (`3-search-history`) resolves correctly because ids are globally unique, but folder-prefixed form is preferred for readability.
- **Wiki targets use bare basename.** `wiki_impact: [architecture, domain]`, not `wiki_impact: [architecture.md]`.

Body links use a different form — standard markdown `[text](relative/path.md)`. See `body-conventions.md`.

### Dates

- ISO format `YYYY-MM-DD`, unquoted. YAML-native date type.
- All timestamp fields use the same format: `created`, `updated`, session timestamps on spark files.

### Empty collections

Empty lists may be written as `[]` or omitted entirely. Both are semantically equivalent. Prefer omission when the field is not expected to populate; prefer `[]` when the field is part of the type's shape and emptiness is noteworthy (e.g., `promoted: []` on a fresh brainstorm).

### Relationships

The schema fixes **one direction per relationship** — the forward direction is the canonical source. Reverse directions are normally **derived on demand** (grep, script back-scan) rather than stored.

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

Every status change on `usecase`, `task`, `review`, and `spec` files flows through the single writer at [`../scripts/transition_status.py`](../scripts/transition_status.py), which validates the transition, writes `status:` + `updated:` + a `<log>` entry, and runs any cascade:

- Task reset on UC `revising` (tasks at `progress`/`failing` → `pending`).
- Task / review discard cascade on UC `discarded`.
- Supersedes-chain flip on UC `shipped` (predecessor UC: `shipped → superseded`).
- Supersedes-chain flip on spec `active` (predecessor spec: `active|deprecated → superseded`).

`status:` and `<log>` are **never hand-edited** after file creation. The fallback `validate_status_consistency.py` reports drift between `status:` and supporting cross-references for cases the writer cannot mechanically reach (`idea`/`brainstorm` `promoted`).

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

Soft references (see-also, mentions) are expressed as standard markdown links (`[text](relative/path.md)`) in body prose, not frontmatter.

## Wiki pages (`a4/<type>.md`)

Minimal schema — no lifecycle, no id.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | enum | `context` \| `domain` \| `architecture` \| `actors` \| `nfr` \| `roadmap` \| `bootstrap` |
| `updated` | yes | date | `YYYY-MM-DD` |

Example:

```yaml
---
type: architecture
updated: 2026-04-24
---
```

The `type` value must match the file basename (e.g., `type: architecture` requires `architecture.md`). Cross-references live as standard markdown links in body prose plus the `<change-logs>` section; they are **not** in frontmatter.

## Use case (`a4/usecase/<id>-<slug>.md`)

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `usecase` |
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
- **`revising` is in-place.** No new UC is created for the paused spec; the same file is edited, and a re-approval ready-gate flips `revising → ready`.
- **`ready → implementing` requires `implemented_by:` non-empty.** The UC must have at least one task declaring `implements: [usecase/<this>]`.
- **`implementing → shipped` requires every task in `implemented_by:` to be `complete`.** `transition_status.py` enforces this.

## Task (`a4/task/<kind>/<id>-<slug>.md`)

Jira "task" semantics — a unit of executable work. The `kind:` field distinguishes regular implementation, time-boxed exploration, and defect work; lifecycle is identical across kinds. The kind subfolder (`feature/`, `bug/`, `spike/`) is part of the file path. Reference forms in frontmatter (`implements`, `depends_on`, `target`, `implemented_by`, etc.) keep the bare `task/<id>-<slug>` shape (no kind segment) so refs stay stable when a task is moved between kinds.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `task` |
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
| `open` | Backlog (kanban "todo"). Captured but not yet committed to the work queue. Not picked up by the implement loop; transition `open → pending` to enqueue. |
| `pending` | In the work queue, awaiting an implementer. Default ready-set entry for the implement loop. |
| `progress` | A `task-implementer` agent is working (or crashed mid-work — reset to `pending` on session resume). |
| `complete` | Unit tests passed. Not a forward-path terminal — UC `revising` cascade can return tasks to `pending` for re-implementation. |
| `failing` | Unit tests red. Resumed via `failing → progress` (immediate retry, same cycle) or deferred via `failing → pending` (next cycle). |
| `discarded` | Abandoned. Terminal. Reached either via UC `discarded` cascade or an explicit task-discard. |

Allowed transitions:

```
open      → discarded | pending | progress
pending   → discarded | progress
progress  → complete | discarded | failing | pending
complete  → discarded | pending
failing   → discarded | pending | progress
discarded → (terminal)
```

`open → progress` is allowed when work is initiated outside the batch run loop — for example, a `task-implementer` spawned directly, or a session that starts implementing a backlog task without batch enqueue. The `pending` step exists to express batch-queue intent; skip it when the queue is not the entry path. There is no `pending → open` reverse — once enqueued, a task cannot be returned to backlog.

### Initial status policy

Three initial states are allowed on task file create:

- `open` (default) — backlog capture.
- `pending` — author intends the implement loop to pick it up immediately. Batch authoring (e.g., from a roadmap) writes new tasks at `pending`.
- `complete` — post-hoc documentation: code already shipped, task file added for traceability. The writer must verify every path in `files:` exists at create time and append an explicit `<log>` entry noting the post-hoc origin (since no `progress → complete` transition was logged by the writer).

`progress` and `failing` are never used as initial states; only the writer (`transition_status.py`) produces them as a result of transitions.

### Spike sidecar convention

For tasks with `kind: spike`, accompanying PoC code lives at project-root `spike/<id>-<slug>/`, parallel to (not inside) `a4/`:

```
<project-root>/
  a4/task/spike/<id>-<slug>.md  # task markdown — kind: spike
  spike/<id>-<slug>/            # PoC code, data, scratch notes
    *.py *.json ...
```

When a spike completes (or fails), the user manually `git mv`s the directory to `spike/archive/<id>-<slug>/` and updates the task's `files:` paths to match. `spike/archive/` is a sibling of active spike directories — self-contained under the `spike/` umbrella. The move is **never automated**; same-precedent reasoning as `idea/` promotion (deferred until manual cost surfaces as pain).

`feature` and `bug` tasks have no `spike/` sidecar; their `files:` paths point at the project's production source tree (outside both `a4/` and `spike/`).

The `spike/` directory:

- Is part of the project repo, not a temporary scratch area.
- Is not validated by any a4 script — the markdown-only contract of `a4/` is preserved.
- Is opt-in — projects without spike tasks have no `spike/` directory.

## Review item (`a4/review/<id>-<slug>.md`)

Unified conduit for findings, gaps, and questions. The `kind:` field distinguishes them; lifecycle is identical.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `review` |
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

**Close guard.** A review item with non-empty `wiki_impact` cannot cleanly transition to `resolved` unless each referenced wiki page records the change in its `<change-logs>` section with a markdown link to the causing issue (`target`). Enforcement is a warning with override — the drift detector re-surfaces violations.

## Spec (`a4/spec/<id>-<slug>.md`)

A spec is a **living specification** — the canonical, prescriptive description of a format, protocol, schema, renderer rule, CLI surface, or other artifact whose exact shape the project commits to. Specs are recorded into `a4/spec/<id>-<slug>.md` after the shape converges through conversation. Supporting research, when needed, is a portable artifact at project-root `./research/<slug>.md` and registered atomically via `scripts/register_research_citation.py`. Each citation is recorded in four places — the spec's `research:` frontmatter list and `<research>` body section, plus the research file's `cited_by:` frontmatter list and `<cited-by>` body section. Frontmatter representations stay queryable via plain-text scan; body sections preserve the in-context citation. The `related:` frontmatter field on a spec is **not** the right slot for research — `research` is the dedicated forward field; `related:` remains for cross-references between issue-family artifacts. A wiki nudge (updating `architecture.md` / `context.md` / `domain.md` / `actors.md` / `nfr.md` with a `<change-logs>` entry, or opening a review-item fallback) is performed at record time.

**Body structure.** Two sections are required: `<context>` (why this spec exists — the problem or scope it covers) and `<specification>` (the prescriptive content — grammar, fields, rules, examples). Both are mechanically enforced by `validate_body.py` against `body_schemas/spec.xsd`, which `transition_status.py` invokes on the `draft → active` flip. Beyond those two, additional sections may be added when the session content warrants them — common examples include `<decision-log>`, `<open-questions>`, `<rejected-alternatives>`, `<consequences>`, `<examples>`. See [§Body sections per type](#body-sections-per-type) for the full list.

**`<decision-log>` absorbs ADR-style notes.** The previous a4 model carried ADRs as a separate family; that role now lives inside the spec body as an optional `<decision-log>` section. Each entry is a short note (date + what was chosen + why), so the chain of design decisions that shaped a particular spec is co-located with the spec itself rather than scattered across decision records. Entries are append-only — earlier entries are never edited or removed; corrections are added as new entries that supersede the prior reasoning. This is the only sanctioned location for "decision rationale" content; do not introduce a separate `decisions/` slot, do not split decisions into their own files.

The spec body is **prescriptive**: it captures the chosen shape that downstream code, validators, and review items must conform to. Implementation tasks reference the spec via the forward `task.spec:` field; the reverse view is derived on demand and never rendered into the spec body. A `<migration-plan>` section is not used — migration work lives in `task/<id>-<slug>.md`.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `spec` |
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | spec title |
| `status` | yes | enum | `draft` \| `active` \| `deprecated` \| `superseded` |
| `decision` | no | string | one-line shape summary |
| `supersedes` | no | list of paths | prior specs replaced |
| `research` | no | list of paths | research artifacts informing this spec (`research/<slug>`); auto-maintained by `register_research_citation.py` together with the body `<research>` section |
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

Boundary with `review/`: **idea = independent possibility, captured raw; review = gap in current spec, bound to progress.** If ignoring the input blocks or degrades current spec work it is a review item; otherwise it is an idea.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `idea` |
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | human-readable one-liner |
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

Body is largely free — only optional sections per the XSD. Quick-capture ideas are typically empty or just a short `<notes>` block; longer ideas may add `<why-this-matters>`.

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

**Note on the former spark-decide slot.** Historically `a4/spark/<YYYY-MM-DD-HHmm>-<slug>.decide.md` was a separate "pre-pipeline decision" slot. It was retired in favor of direct `a4/spec/<id>-<slug>.md` records (with `<decision-log>` absorbing the rationale that previously lived in standalone decision records). No spark-family file carries `type: decide` anymore.

## Research artifact (project-root `research/<slug>.md`)

Research files live **outside** `a4/` — at project-root `research/` (sibling of `a4/`). They are portable, workspace-agnostic, and are **not** validated by `validate_frontmatter.py`. The convention below is documented here because `spec.research:` cites these files and `register_research_citation.py` writes their reverse-link.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `research` |
| `topic` | yes | string | research topic |
| `status` | yes | enum | `draft` \| `final` \| `standalone` \| `archived` |
| `mode` | yes | literal | `comparative` \| `single` |
| `options` | conditional | list of strings | required when `mode: comparative` |
| `cited_by` | no | list of paths | reverse link to citing specs; auto-maintained by `register_research_citation.py` |
| `tags` | no | list of strings | free-form |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | yes | date | `YYYY-MM-DD` (bumped by `register_research_citation.py` whenever it touches the file) |

Status semantics:

- `draft` — research is being authored.
- `final` — research is complete; may or may not have been cited yet.
- `standalone` — research is complete and intentionally not feeding any spec (terminal). The SessionStart staleness courtesy never nudges `standalone` files.
- `archived` — research is no longer relevant (terminal).

The staleness courtesy nudges only files at `status: final` with empty `cited_by:` and `updated:` older than a threshold; everything else is silent.

## Body sections per type

The XSDs at `../scripts/body_schemas/<type>.xsd` are the source of truth for the per-type body shape. The tables below mirror them. Each `<tag>` listed is a column-0 markdown section block; "required" tags must appear in every file of that type, "optional" tags may appear, and unknown tags are tolerated by the XSD's openContent (so authors can drop in `<benchmarks>` or any other supplemental block as needed).

Two universal optional sections appear on most types:

- **`<change-logs>`** — append-only audit trail of why this file was edited. Bullet entries dated `YYYY-MM-DD` with a markdown link to the causing issue or spec. See `body-conventions.md`. Replaces the prior `[^N]` footnote + `## Changes` mechanism.
- **`<log>`** — append-only status-transition trail written by `transition_status.py`. Bullet entries `YYYY-MM-DD — <from> → <to> — <reason>`. Authors should never write into `<log>` directly except for the documented post-hoc-`complete` task case.

### Wiki pages

| `type:` | Required tags | Optional tags |
|---|---|---|
| `actors` | `<roster>` | `<change-logs>` |
| `architecture` | `<components>`, `<overview>`, `<technology-stack>`, `<test-strategy>` | `<change-logs>`, `<component-diagram>`, `<external-dependencies>` |
| `bootstrap` | `<environment>`, `<launch>`, `<verify>` | `<change-logs>` |
| `context` | `<original-idea>`, `<problem-framing>` | `<change-logs>`, `<screens>` |
| `domain` | `<concepts>` | `<change-logs>`, `<relationships>`, `<state-transitions>` |
| `nfr` | `<requirements>` | `<change-logs>` |
| `roadmap` | `<plan>` | `<change-logs>` |

### Issues

| `type:` | Required tags | Optional tags |
|---|---|---|
| `usecase` | `<expected-outcome>`, `<flow>`, `<goal>`, `<situation>` | `<change-logs>`, `<dependencies>`, `<error-handling>`, `<log>`, `<validation>` |
| `task` | `<acceptance-criteria>`, `<description>`, `<files>`, `<unit-test-strategy>` | `<change-logs>`, `<interface-contracts>`, `<log>`, `<why-discarded>` |
| `review` | `<description>` | `<change-logs>`, `<log>` |
| `spec` | `<context>`, `<specification>` | `<change-logs>`, `<consequences>`, `<decision-log>`, `<examples>`, `<log>`, `<open-questions>`, `<rejected-alternatives>`, `<research>` |
| `idea` | (none) | `<change-logs>`, `<log>`, `<notes>`, `<why-this-matters>` |

### Spark + research

| `type:` | Required tags | Optional tags |
|---|---|---|
| `brainstorm` | `<ideas>` | `<change-logs>`, `<notes>` |
| `research` | `<context>` | `<change-logs>`, `<cited-by>`, `<findings>`, `<options>` |

`<xs:all>` ordering does not matter. Authors place sections in any order; the XSD only requires presence of required tags and absence of duplicates among declared tags. Adding new declared tags requires editing the relevant XSD by hand (no generator script — see [Hand-written XSDs](#hand-written-xsds) below).

## Hand-written XSDs

The XSDs under `../scripts/body_schemas/` are the authoritative schema. Each:

- Declares `vc:minVersion="1.1"` (XSD 1.1 features required — `xmlschema.XMLSchema11` in Python).
- Defines a single root element matching its `type:` value.
- Lists required and optional sections inside `<xs:all>` (children typed as `markdownContent`, mixed-content opaque to the schema).
- Wraps the children in `<xs:openContent mode="interleave">` with `<xs:any notQName="...">` listing every declared section name and `processContents="skip"` — so unknown tags pass while duplicates of declared tags are rejected.

Edit a section list by hand-editing the XSD. There is no generator script. The XSDs are intentionally short, so duplicating section enums in Python is unnecessary — `body_schemas.py` is a thin registry (`schema_path(type)`, `all_types()`) and that's all.

## Validator behavior

Two validators cover frontmatter and body in parallel:

- `../scripts/validate_frontmatter.py` — enforces this schema (frontmatter only).
- `../scripts/validate_body.py` — enforces the body XML structure against per-type XSDs.

Every rule violation is an error; both validators exit `2` on any violation and `0` on a clean run.

| Rule | Validator | Behavior |
|------|-----------|----------|
| Unknown frontmatter fields | frontmatter | **ignored** (the one point of leniency) |
| Missing required frontmatter field | frontmatter | error |
| Wrong type for a known field | frontmatter | error |
| Value outside enum for a known field | frontmatter | error |
| Path-reference format (brackets, `.md` extension) | frontmatter | error |
| `type` on wiki page disagrees with filename | frontmatter | error |
| `wiki_impact` entry not in the wiki-type enum | frontmatter | error |
| Id collision across issue folders | frontmatter | error |
| File in an issue/spark folder has no frontmatter | frontmatter | error |
| `body-type-missing` (no `type:` field) | body | error |
| `body-type-unknown` (no XSD for `type:` value) | body | error |
| `body-stray-content` (text outside any section block) | body | error |
| `body-tag-invalid` (open tag fails kebab-case rule) | body | error |
| `body-tag-unclosed` (EOF inside an open section) | body | error |
| `body-xsd` (XSD violation — missing required, unexpected duplicate) | body | error |

Hook scope is a separate concern — the validator reports; the caller decides whether to block, notify, or ignore.

### Cross-file status consistency

Several enum values are semantically derived from cross-file state rather than being chosen in isolation:

| Field | Derived value | Condition | Materialized by |
|-------|--------------|-----------|-----------------|
| `usecase.status` | `superseded` | A newer `usecase/*.md` with `supersedes: [<this>]` has `status: shipped` | `transition_status.py` cascade (fires during successor's `→ shipped` transition) |
| `usecase.implemented_by` | list of tasks | Tasks in `a4/task/*/*.md` (recursing through `feature/`/`bug/`/`spike/`) carry `implements: [usecase/<this>]` | `refresh_implemented_by.py` (back-scan; invoked from task-authoring writers and from `scripts/a4_hook.py session-start`). Emits the bare `task/<id>-<slug>` form (no kind segment) so refs stay stable across kind moves. |
| `task.status` | `discarded` | UC the task implements flips to `discarded` | `transition_status.py` cascade |
| `task.status` | `pending` (from `implementing`/`failing`) | UC the task implements flips to `revising` | `transition_status.py` cascade |
| `review.status` | `discarded` | UC named by `target:` flips to `discarded` | `transition_status.py` cascade |
| `spec.status` | `superseded` | Another `spec/*.md` declares `supersedes: [<this>]` and has `status: active` | `transition_status.py` cascade (fires during successor's `→ active` transition) |
| `idea.status` | `promoted` | Own `promoted:` list is non-empty | user-driven; `validate_status_consistency.py` surfaces drift |
| `spark/*.brainstorm.md` `status` | `promoted` | Own `promoted:` list is non-empty | user-driven; `validate_status_consistency.py` surfaces drift |

`../scripts/validate_status_consistency.py` reports either direction of mismatch (stale terminal status with no supporting cross-reference, or unflipped status despite supporting cross-reference). It is report-only — no file is mutated.

Two modes:

- **Workspace mode** (`<a4-dir>`) — scans all specs/ideas/brainstorms. Used at session start and during workspace validation.
- **File-scoped mode** (`<a4-dir> --file <path>`) — reports only mismatches in the connected component of the given file (idea/brainstorm: self-contained; spec: supersedes chain). Used on PostToolUse so ordinary edits do not re-surface unrelated legacy mismatches.

## Known deferred items

These are schema items deliberately left softened until a follow-up round.

1. **Issue `<log>` entry format.** Body-level `<log>` convention is referenced throughout but the exact entry format (prefix, timestamp granularity, author attribution) is not yet locked.
2. **Exact YAML grammar for path references.** Plain string is the current rule; whether to allow alternative forms (list-of-maps for typed references, etc.) is not yet decided.
3. **Stricter enums.** Several fields are currently open strings (`source` on review items) because the full value set has not been enumerated.

When these land, update this document **and** the validator simultaneously — the two must not drift.

## Cross-references

- **Body-level conventions:** `body-conventions.md` — tag form (column-0, kebab-case, no attributes), blank-line discipline, `<change-logs>` and `<log>` entry format, body link form (standard markdown).
- **XSDs (source of truth for body shape):** `../scripts/body_schemas/<type>.xsd`.
- **Body schema registry:** `../scripts/body_schemas.py` (`schema_path(type_)`, `all_types()`).
- **Id allocator:** `../scripts/allocate_id.py`.
- **Status model (canonical):** `../scripts/status_model.py` — per-family status enums, allowed transitions, terminal/in-progress/active classifications, kind enums. Imported by the writer, validators, workspace state, and search; the prose tables in this document mirror the same data.
- **Status transition writer:** `../scripts/transition_status.py` — single writer for usecase / task / review / spec status changes; runs cascades (revising task reset, discarded cascade, shipped → superseded chain, spec active → superseded chain). Body validation runs `validate_body.run()` on the relevant flips.
- **Implemented-by back-link refresher:** `../scripts/refresh_implemented_by.py` — back-scans `task.implements:` into `usecase.implemented_by:`.
- **Research citation registrar:** `../scripts/register_research_citation.py` — atomically records a research → spec citation in four places (spec frontmatter `research:`, spec body `<research>`, research frontmatter `cited_by:`, research body `<cited-by>`) and bumps the research file's `updated:`.
- **Drift detector (uses wiki / review schemas):** `../scripts/drift_detector.py`.
- **Cross-file status consistency validator:** `../scripts/validate_status_consistency.py` — reports mismatches between `status:` and the cross-file state that should derive it (superseded, promoted, discarded cascade).
- **Spark family scope:** brainstorm is the only spark-family schema validated here; research output lives outside `a4/` and is not validated by this schema.
