# a4 Frontmatter Schema

Consolidated frontmatter reference for every file under the `a4/` workspace. This document is the **single source of truth for validators and authoring contracts**.

Body-side conventions (heading form, blank-line discipline, change-log and log section format, link form) live in `body-conventions.md`. The two should be read together.

## Scope

Every markdown file under `a4/` carries YAML frontmatter. Files split into three families:

| Family | Examples | Location |
|--------|----------|----------|
| **Wiki page** | `context.md`, `domain.md`, `architecture.md`, `actors.md`, `nfr.md`, `roadmap.md`, `bootstrap.md` | `a4/` root |
| **Issue** | use case, task, review item, spec, idea | `a4/usecase/`, `a4/task/<kind>/` (`feature`/`bug`/`spike`/`research`), `a4/review/`, `a4/spec/`, `a4/idea/` |
| **Spark** | brainstorm output | `a4/spark/` |

## Universal rules

These apply to every family.

### `type:` field

Every markdown file declares a `type:` field in frontmatter. The value selects the per-type reference XSD at `../scripts/body_schemas/<type>.xsd`, which documents which body sections are required vs optional. **Reference-only**: no runtime validator consumes the XSDs; authoring contracts under `plugins/a4/references/` are the binding source. The XSD element names use lowercase kebab-case (an XML grammar artifact); the body itself uses Title Case H2 headings (`## Heading`) per `body-conventions.md`.

| Family | `type:` value |
|--------|--------------|
| Wiki — actors | `actors` |
| Wiki — architecture | `architecture` |
| Wiki — bootstrap | `bootstrap` |
| Wiki — context | `context` |
| Wiki — domain | `domain` |
| Wiki — nfr | `nfr` |
| Wiki — roadmap | `roadmap` |
| Issue — usecase | `usecase` |
| Issue — task | `task` |
| Issue — review | `review` |
| Issue — spec | `spec` |
| Issue — idea | `idea` |
| Spark — brainstorm | `brainstorm` |

For wiki pages, `type:` doubles as the file-kind discriminator (e.g., `type: architecture` requires the file to be at `a4/architecture.md`). For issues and spark files, `type:` is the body schema selector — the file family is already implied by the folder.

Validator rules:

- Missing `type:` → frontmatter validator error.
- Wiki page `type:` not matching the file basename (e.g., `type: domain` in `architecture.md`) → frontmatter validator error.

### Body section headings

Body sections are column-0 H2 markdown headings in Title Case with spaces (`## Context`, `## Specification`, `## Change Logs`, …). The recommended set per `type:` is documented in the per-type authoring contracts under `plugins/a4/references/`. Authoring contracts list required and optional sections; unknown Title Case headings are tolerated. See `body-conventions.md` for the full heading-form rules (including the kebab-case → Title Case mapping that aligns XSD element names with body headings) and [§Body sections per type](#body-sections-per-type) below for the per-type required/optional split.

### Ids

- Ids are **monotonically increasing integers, global to the workspace**. Unique across all issue folders in a given `a4/` (GitHub-issue semantics).
- Next id is computed as `max(existing ids in a4/) + 1` by `../scripts/allocate_id.py`.
- Wiki pages and spark files do **not** carry an `id:` field — they have no issue-tracker identity.

### Path references

Frontmatter fields that reference other files (`depends_on`, `implements`, `target`, `spec`, `supersedes`, `related`, `parent`, `promoted`) use the following format:

- **Plain strings.** No brackets — `usecase/3-search-history`, not `[usecase/3-search-history]`. Plain strings keep frontmatter machine-parseable.
- **No `.md` extension.** Spark brainstorm files keep the `.brainstorm` suffix because it is part of the filename base, not the extension — e.g., `spark/2026-04-23-2119-caching-strategy.brainstorm`.
- **Folder-prefixed when cross-folder.** `usecase/3-search-history`, `task/5-render-markdown`, `review/6-missing-validation`, `spec/8-caching-strategy`, `spark/<base>`. Bare basename (`3-search-history`) resolves correctly because ids are globally unique, but folder-prefixed form is preferred for readability.
- **Wiki targets use bare basename.** A review item naming a wiki page writes `target: [architecture, domain]`, not `target: [architecture.md]`. Issue-folder paths and wiki basenames may be mixed in a single `target:` list.

Body links use a different form — standard markdown `[text](relative/path.md)`. See `body-conventions.md`.

### Dates

- ISO format `YYYY-MM-DD`, unquoted. YAML-native date type.
- All timestamp fields use the same format: `created`, `updated`, session timestamps on spark files.

### Empty collections

Empty lists may be written as `[]` or omitted entirely. Both are semantically equivalent. Prefer omission when the field is not expected to populate; prefer `[]` when the field is part of the type's shape and emptiness is noteworthy (e.g., `promoted: []` on a fresh brainstorm).

### Relationships

The schema fixes **one direction per relationship** — the forward direction is the canonical source. Reverse directions are **derived on demand** (grep, script back-scan) rather than stored. There is currently no stored-reverse field; if a future need arises (a status gate, validator, or hot query that justifies bypassing derive-on-demand), a script must own writes for the field and the rationale must be documented here before the field is introduced.

| Forward (stored) | Reverse | Storage |
|------------------|---------|---------|
| `depends_on` | `blocks` | derived |
| `implements` | (UC → tasks) | derived |
| `supersedes` | `superseded_by` | derived |
| `parent` | `children` | derived |
| `target` | (review backlinks; wiki-page backlinks) | derived |
| `promoted` | (spark → pipeline backlinks) | derived |
| `related` | (symmetric; no reverse) | — |

### Unknown fields

Unknown fields are **not errors**. The validator in lenient mode reports them as informational only. Skills may carry additional fields (e.g., `tags`, `labels`) per the per-type tables below; anything outside the known set is treated as extension metadata.

### Status writers

Every status change on `usecase`, `task`, `review`, and `spec` files flows through the single writer at [`../scripts/transition_status.py`](../scripts/transition_status.py), which validates the transition and writes `status:` + `updated:`, then runs any cascade:

- Task reset on UC `revising` (tasks at `progress`/`failing` → `pending`).
- Task / review discard cascade on UC `discarded`.
- Supersedes-chain flip on UC `shipped` (predecessor UC: `shipped → superseded`).
- Supersedes-chain flip on spec `active` (predecessor spec: `active|deprecated → superseded`).

`transition_status.py` does **not** touch the body's optional `## Log` section — that section is hand-maintained when an author wants a body-level audit trail. `status:` is **never hand-edited** after file creation. The fallback `validate_status_consistency.py` reports drift between `status:` and supporting cross-references for cases the writer cannot mechanically reach (`idea`/`brainstorm` `promoted`).

## Structural relationship fields

Shared across all issue types. Omit fields that are empty, or use `[]`.

| Field | Applies to | Points at | Meaning |
|-------|-----------|-----------|---------|
| `depends_on` | task | task | Tasks that must complete before this one (lifecycle blocker) |
| `implements` | task | usecase | Use cases delivered by this task |
| `target` | review | any issue path(s) and/or wiki basename(s) | What this review item is about and which wiki pages must record the resolution; mixed lists are allowed |
| `spec` | task (`feature` / `bug` only) | spec | Specs that govern this task |
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

The `type` value must match the file basename (e.g., `type: architecture` requires `architecture.md`). Cross-references live as standard markdown links in body prose plus the `## Change Logs` section; they are **not** in frontmatter.

## Use case (`a4/usecase/<id>-<slug>.md`)

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `usecase` |
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | human-readable |
| `status` | yes | enum | `draft` \| `ready` \| `implementing` \| `revising` \| `shipped` \| `superseded` \| `discarded` \| `blocked` |
| `actors` | no | list of strings | actor names as defined in `actors.md` |
| `supersedes` | no | list of paths | prior use cases this UC replaces (see §Status writers) |
| `related` | no | list of paths | catchall |
| `labels` | no | list of strings | free-form tags |
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
- **`ready → implementing` and `implementing → shipped` carry no mechanical task gate.** The writer flips `status:` regardless of whether tasks declaring `implements: [usecase/<this>]` exist or are complete. Authors decide when a UC has enough work staged or has truly shipped; `/a4:run` and roadmap surfaces are the load-bearing checks, not the writer.

## Task (`a4/task/<kind>/<id>-<slug>.md`)

Jira "task" semantics — a unit of executable work. The `kind:` field distinguishes regular implementation, time-boxed exploration, defect work, and investigation; lifecycle is identical across kinds. The kind subfolder (`feature/`, `bug/`, `spike/`, `research/`) is part of the file path. Reference forms in frontmatter (`implements`, `depends_on`, `target`, etc.) keep the bare `task/<id>-<slug>` shape (no kind segment) so refs stay stable when a task is moved between kinds.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `task` |
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | human-readable |
| `kind` | yes | enum | `feature` \| `spike` \| `bug` \| `research` |
| `status` | yes | enum | `open` \| `pending` \| `progress` \| `complete` \| `failing` \| `discarded` |
| `implements` | no | list of paths | use cases delivered. **Forbidden on `kind: spike`** (spikes are exploratory, never UC deliverables). Typically empty for `kind: research` as well. |
| `depends_on` | no | list of paths | other tasks this one needs first |
| `spec` | no | list of paths | Specs governing this task. **Allowed only on `kind: feature` and `kind: bug`** (a4 v6.0.0); forbidden on `spike` / `research` (cite via body markdown links instead). |
| `files` | no | list of strings | artifact paths under `artifacts/task/<kind>/<id>-<slug>/`. For `kind: spike`, paths may also point under `artifacts/task/spike/archive/<id>-<slug>/...` once archived. Empty list is allowed for any kind; the typical default for `kind: research` (the body is the deliverable). Production source paths the task writes or modifies are documented in the body `## Files` section, **not** in this frontmatter field. |
| `mode` | conditional | enum | `comparative` \| `single` — required when `kind: research` |
| `options` | conditional | list of strings | option names — required when `kind: research` and `mode: comparative` |
| `cycle` | no | int | implementation cycle number. **Allowed only on `kind: feature` and `kind: bug`** (a4 v6.0.0); forbidden on `spike` / `research`. |
| `labels` | no | list of strings | free-form tags |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | yes | date | `YYYY-MM-DD` |

### Kind semantics

| Value | Meaning |
|-------|---------|
| `feature` | Regular implementation — new functionality, extension, refactor. The default case. |
| `spike` | Time-boxed exploration to unblock a decision (XP sense). Throwaway code expected. PoC, investigation, benchmark. PoC code lives at project-root `artifacts/task/spike/<id>-<slug>/`, **outside the `a4/` workspace**. |
| `bug` | Defect fix. Production code change, not throwaway. |
| `research` | Investigation of a technical topic or comparison of alternatives. Output is the task body itself (sources, findings, options). No code is produced. Typically cited by a follow-up `feature` or `spec` via `task.spec:` or via a body link. |

`kind` is **required** — every task must declare one. There is no implicit default. Existing task files predating this schema will fail validation until backfilled with an explicit `kind:` value.

### Task lifecycle

| Value | Meaning |
|-------|---------|
| `open` | Backlog (kanban "todo"). Captured but not yet committed to the work queue. Not picked up by the implement loop; transition `open → pending` to enqueue. |
| `pending` | In the work queue, awaiting an implementer. Default ready-set entry for the implement loop. |
| `progress` | A `task-implementer` agent (or, for `kind: research`, an investigator) is working (or crashed mid-work — reset to `pending` on session resume). |
| `complete` | Unit tests passed (for `feature`/`bug`), hypothesis validated (for `spike`), or investigation finalized (for `research`). Not a forward-path terminal — UC `revising` cascade can return tasks to `pending` for re-implementation. |
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
- `complete` — post-hoc documentation: code already shipped, task file added for traceability. The writer must verify every path in `files:` exists at create time. If the author wants the post-hoc origin recorded in the body, append a manual bullet to the optional `## Log` section. For `kind: research`, a task may be authored directly at `complete` when the investigation is captured in one shot.

`progress` and `failing` are never used as initial states; only the writer (`transition_status.py`) produces them as a result of transitions.

### Task artifacts convention

Each task may have a sibling **artifact directory** at project-root `artifacts/task/<kind>/<id>-<slug>/`, parallel to (not inside) `a4/`:

```
<project-root>/
  a4/task/<kind>/<id>-<slug>.md         # task markdown
  artifacts/task/<kind>/<id>-<slug>/    # artifact directory (opt-in)
    *.py *.json *.png *.csv ...
```

Per-kind expectations:

| kind | Typical contents | Strength |
|---|---|---|
| `spike` | PoC code, benchmark raw, scratch scripts | Primary use — most active spikes have one |
| `research` | Comparison raw data, charts, evaluation scripts, downloaded sources | Recommended when the investigation produces ancillary artifacts |
| `feature` | Test samples, execution outputs for feature comparison, design mockups, migration dry-run results | Optional — only when artifacts have evidentiary or comparative value |
| `bug` | Reproduction repos, crash logs, screenshots, traces | Optional — only when reproduction or evidence is itself worth keeping |

Frontmatter `task.files:` lists artifact paths only — production source paths the task writes or modifies belong in the body `## Files` section, not in frontmatter. For `kind: spike`, `files:` may also point under `artifacts/task/spike/archive/<id>-<slug>/` once the directory has been archived.

When a spike completes (or fails), the user manually `git mv`s the directory to `artifacts/task/spike/archive/<id>-<slug>/` and updates the task's `files:` paths to match. The archive convention applies to `spike` only; `feature`, `bug`, and `research` artifact directories are not archived (closed task markdown moves to `a4/archive/` independently). The move is **never automated**; same-precedent reasoning as `idea/` promotion (deferred until manual cost surfaces as pain).

The `artifacts/` directory:

- Is part of the project repo, not a temporary scratch area.
- Is not validated by any a4 script — the markdown-only contract of `a4/` is preserved.
- Is opt-in — projects without artifact-bearing tasks have no `artifacts/` directory.

#### Artifact directory curation

The artifact directory is part of the project repo, not scratch. Commit intentionally — only what carries value beyond the current session.

- **Keep:** comparison results, reproducible data/scripts, evidence cited from the task body, decision-supporting raw output.
- **Drop:** regenerable build outputs, machine-specific caches, large binaries not referenced from the body, secrets/API keys.

Curation is user-driven. There is no automated cleanup. When a spike's exploration ends, manually `git mv` the directory to `artifacts/task/spike/archive/<id>-<slug>/`.

## Review item (`a4/review/<id>-<slug>.md`)

Unified conduit for findings, gaps, and questions. The `kind:` field distinguishes them; lifecycle is identical.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `review` |
| `id` | yes | int | monotonic global integer |
| `kind` | yes | enum | `finding` \| `gap` \| `question` |
| `status` | yes | enum | `open` \| `in-progress` \| `resolved` \| `discarded` |
| `target` | no | list of paths | issue paths (e.g., `usecase/3-search`) and/or wiki basenames (e.g., `architecture`) this review is about. May mix both. Empty list / omitted is allowed for cross-cutting items. |
| `source` | yes | enum \| string | `self` \| `drift-detector` \| `<reviewer-agent-name>` (e.g., `usecase-reviewer-r2`) |
| `priority` | no | enum | `high` \| `medium` \| `low` |
| `labels` | no | list of strings | free-form; drift-detector uses `drift:<kind>` and `drift-cause:<slug>` |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | yes | date | `YYYY-MM-DD` |

**Close guard.** When `target:` contains one or more wiki basenames, the review cannot cleanly transition to `resolved` unless each referenced wiki page records the change in its `## Change Logs` section with a markdown link to the review item itself. Enforcement is a warning with override — the drift detector re-surfaces violations.

## Spec (`a4/spec/<id>-<slug>.md`)

A spec is a **living specification** — the canonical, prescriptive description of a format, protocol, schema, renderer rule, CLI surface, or other artifact whose exact shape the project commits to. Specs are recorded into `a4/spec/<id>-<slug>.md` after the shape converges through conversation. Supporting investigation, when needed, lives in a sibling `kind: research` task at `a4/task/research/<id>-<slug>.md` and is referenced from the spec body via standard markdown links. A wiki nudge (updating `architecture.md` / `context.md` / `domain.md` / `actors.md` / `nfr.md` with a `## Change Logs` entry, or opening a review-item fallback) is performed at record time.

**Body structure.** Two sections are typically present: `## Context` (why this spec exists — the problem or scope it covers) and `## Specification` (the prescriptive content — grammar, fields, rules, examples). Beyond those two, additional sections may be added when the session content warrants them — common examples include `## Decision Log`, `## Open Questions`, `## Rejected Alternatives`, `## Consequences`, `## Examples`. See [§Body sections per type](#body-sections-per-type) for the full list.

**`## Decision Log` absorbs ADR-style notes.** The previous a4 model carried ADRs as a separate family; that role now lives inside the spec body as an optional `## Decision Log` section. Each entry is a short note (date + what was chosen + why), so the chain of design decisions that shaped a particular spec is co-located with the spec itself rather than scattered across decision records. Entries are append-only — earlier entries are never edited or removed; corrections are added as new entries that supersede the prior reasoning. This is the only sanctioned location for "decision rationale" content; do not introduce a separate `decisions/` slot, do not split decisions into their own files.

The spec body is **prescriptive**: it captures the chosen shape that downstream code, validators, and review items must conform to. Implementation tasks reference the spec via the forward `task.spec:` field; the reverse view is derived on demand and never rendered into the spec body. A `## Migration Plan` section is not used — migration work lives in `task/<id>-<slug>.md`.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `spec` |
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | spec title |
| `status` | yes | enum | `draft` \| `active` \| `deprecated` \| `superseded` |
| `supersedes` | no | list of paths | prior specs replaced |
| `related` | no | list of paths | catchall (use this slot for soft cross-references including any informing research task) |
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

Body is largely free — only optional sections per the authoring contract. Quick-capture ideas are typically empty or just a short `## Notes` section; longer ideas may add `## Why This Matters`.

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

**Note on the former spark-decide slot.** Historically `a4/spark/<YYYY-MM-DD-HHmm>-<slug>.decide.md` was a separate "pre-pipeline decision" slot. It was retired in favor of direct `a4/spec/<id>-<slug>.md` records (with `## Decision Log` absorbing the rationale that previously lived in standalone decision records). No spark-family file carries `type: decide` anymore.

## Body sections per type

The per-type authoring contracts under `plugins/a4/references/` are the source of truth for the body shape. The reference XSDs at `../scripts/body_schemas/<type>.xsd` mirror them for human readers but are no longer consumed by any runtime validator. The tables below summarise the recommended split. Each entry is a Title Case H2 heading (`## Heading`); "required" headings should appear in every file of that type, "optional" headings may appear, and unknown Title Case headings are tolerated.

Two universal optional sections appear on most types:

- **`## Change Logs`** — append-only audit trail of why this file was edited. Bullet entries dated `YYYY-MM-DD` with a markdown link to the causing issue or spec. See `body-conventions.md`. Replaces the prior `[^N]` footnote + `## Changes` mechanism.
- **`## Log`** — optional, hand-maintained status-transition trail. Bullet entries `YYYY-MM-DD — <from> → <to> — <reason>` are a common shape. `transition_status.py` flips `status:` and bumps `updated:` but does **not** write to `## Log`; append bullets manually if you want a body audit trail.

### Wiki pages

| `type:` | Required sections | Optional sections |
|---|---|---|
| `actors` | `## Roster` | `## Change Logs` |
| `architecture` | `## Components`, `## Overview`, `## Technology Stack`, `## Test Strategy` | `## Change Logs`, `## Component Diagram`, `## External Dependencies` |
| `bootstrap` | `## Environment`, `## Launch`, `## Verify` | `## Change Logs` |
| `context` | `## Original Idea`, `## Problem Framing` | `## Change Logs`, `## Screens` |
| `domain` | `## Concepts` | `## Change Logs`, `## Relationships`, `## State Transitions` |
| `nfr` | `## Requirements` | `## Change Logs` |
| `roadmap` | `## Plan` | `## Change Logs` |

### Issues

| `type:` | Kind | Required sections | Optional sections |
|---|---|---|---|
| `usecase` | — | `## Expected Outcome`, `## Flow`, `## Goal`, `## Situation` | `## Change Logs`, `## Dependencies`, `## Error Handling`, `## Log`, `## Validation` |
| `task` | `feature`, `spike`, `bug` | `## Acceptance Criteria`, `## Description`, `## Files`, `## Unit Test Strategy` | `## Change Logs`, `## Interface Contracts`, `## Log`, `## Why Discarded` |
| `task` | `research` | `## Context` | `## Change Logs`, `## Findings`, `## Options`, `## Log`, `## Why Discarded` |
| `review` | — | `## Description` | `## Change Logs`, `## Log` |
| `spec` | — | `## Context`, `## Specification` | `## Change Logs`, `## Consequences`, `## Decision Log`, `## Examples`, `## Log`, `## Open Questions`, `## Rejected Alternatives` |
| `idea` | — | (none) | `## Change Logs`, `## Log`, `## Notes`, `## Why This Matters` |

### Spark

| `type:` | Required sections | Optional sections |
|---|---|---|
| `brainstorm` | `## Ideas` | `## Change Logs`, `## Notes` |

Section ordering does not matter. Authors place sections in any order; the contract only requires presence of required headings. Adding a new section is a documentation change in the per-type authoring reference; the reference XSDs may be updated in parallel for human reference.

## Reference XSDs

The XSDs under `../scripts/body_schemas/` are **reference material only** — no runtime validator parses them. They:

- Declare `vc:minVersion="1.1"` (XSD 1.1 features).
- Define a single root element matching the `type:` value (or, for `task`, a single `task` root that covers all kinds).
- List required and optional sections inside `<xs:all>` (children typed as `markdownContent`).
- Wrap the children in `<xs:openContent mode="interleave">` to permit unknown elements (the XML reflection of the body's "unknown Title Case headings tolerated" rule).

Edit a section list by hand-editing both the per-type authoring contract under `plugins/a4/references/` and the matching XSD so the two stay in sync.

## Validator behavior

One validator covers frontmatter; body shape is documentation-only.

- `../scripts/validate_frontmatter.py` — enforces this schema (frontmatter only).

Every rule violation is an error; the validator exits `2` on any violation and `0` on a clean run.

| Rule | Behavior |
|------|----------|
| Unknown frontmatter fields | **ignored** (the one point of leniency) |
| Missing required frontmatter field | error |
| Wrong type for a known field | error |
| Value outside enum for a known field | error |
| Path-reference format (brackets, `.md` extension) | error |
| `type` on wiki page disagrees with filename | error |
| Id collision across issue folders | error |
| File in an issue/spark folder has no frontmatter | error |

Hook scope is a separate concern — the validator reports; the caller decides whether to block, notify, or ignore.

### Cross-file status consistency

Several enum values are semantically derived from cross-file state rather than being chosen in isolation:

| Field | Derived value | Condition | Materialized by |
|-------|--------------|-----------|-----------------|
| `usecase.status` | `superseded` | A newer `usecase/*.md` with `supersedes: [<this>]` has `status: shipped` | `transition_status.py` cascade (fires during successor's `→ shipped` transition) |
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

1. **Issue `## Log` entry format.** Body-level `## Log` is hand-maintained when authors choose to populate it; the exact entry format (prefix, timestamp granularity, author attribution) is not yet locked.
2. **Exact YAML grammar for path references.** Plain string is the current rule; whether to allow alternative forms (list-of-maps for typed references, etc.) is not yet decided.
3. **Stricter enums.** Several fields are currently open strings (`source` on review items) because the full value set has not been enumerated.
4. **`task.files:` artifact-path enforcement.** The artifact-only contract on `task.files:` is documented (this round) but not yet enforced by `validate_frontmatter.py`. Pending validator work: per-kind prefix check (`artifacts/task/<kind>/<id>-<slug>/...` for `spike` is required, optional for the other kinds; `spike` paths may also start with `artifacts/task/spike/archive/<id>-<slug>/`), plus a task-id-vs-path consistency check (the `<id>-<slug>` segment must match the file's own id and slug). Until then, frontmatter `files:` paths that still point at production source or a foreign id are tolerated.
5. **`research` `complete` initial-status preflight.** The path-existence check on `files:` (already enforced for `spike` and `feature`/`bug`) needs extension to `research` — when `research` is authored at `status: complete` with non-empty `files:`, every artifact path must exist under `artifacts/task/research/<id>-<slug>/` before the writer accepts the file.

When these land, update this document **and** the validator simultaneously — the two must not drift.

## Cross-references

- **Body-level conventions:** `body-conventions.md` — heading form (column-0 H2, Title Case, kebab → Title Case mapping), blank-line discipline, `## Change Logs` and `## Log` entry format, body link form (standard markdown).
- **Reference XSDs:** `../scripts/body_schemas/<type>.xsd` — documentation of recommended body shape; not consumed by any runtime validator.
- **Id allocator:** `../scripts/allocate_id.py`.
- **Status model (canonical):** `../scripts/status_model.py` — per-family status enums, allowed transitions, terminal/in-progress/active classifications, kind enums. Imported by the writer, validators, workspace state, and search; the prose tables in this document mirror the same data.
- **Status transition writer:** `../scripts/transition_status.py` — single writer for usecase / task / review / spec status changes; runs cascades (revising task reset, discarded cascade, shipped → superseded chain, spec active → superseded chain).
- **Drift detector (uses wiki / review schemas):** `../scripts/drift_detector.py`.
- **Cross-file status consistency validator:** `../scripts/validate_status_consistency.py` — reports mismatches between `status:` and the cross-file state that should derive it (superseded, promoted, discarded cascade).
