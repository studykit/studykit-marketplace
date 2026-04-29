# a4 Frontmatter Schema

Consolidated frontmatter reference for every file under the `a4/` workspace. This document is the **single source of truth for the frontmatter contract**.

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

Every markdown file declares a `type:` field in frontmatter. The value selects the per-type authoring contract at `plugins/a4/references/<type>-authoring.md`, which lists the body sections required vs optional for that type. The body uses Title Case H2 headings (`## Heading`) per `body-conventions.md`.

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

For wiki pages, `type:` doubles as the file-kind discriminator (e.g., `type: architecture` requires the file to be at `a4/architecture.md`). For issues and spark files, `type:` selects the per-type authoring contract — the file family is already implied by the folder.

Rules:

- Every file must carry `type:`. Missing it is an error.
- For wiki pages, `type:` must match the file basename (e.g., `type: architecture` requires `architecture.md`). Mismatches are errors.

### Body section headings

Body sections are column-0 H2 markdown headings in Title Case with spaces (`## Context`, `## Specification`, `## Change Logs`, …). The recommended set per `type:` lives in the per-type authoring contracts under `plugins/a4/references/<type>-authoring.md` (or, for the wiki pages, `<type>-authoring.md` for each wiki type), each of which lists required / optional sections and tolerates unknown Title Case headings. See `body-conventions.md` for the full heading-form rules.

### Ids

- Ids are **monotonically increasing integers, global to the workspace**. Unique across all issue folders in a given `a4/` (GitHub-issue semantics).
- Next id is computed as `max(existing ids in a4/) + 1` by `../scripts/allocate_id.py`.
- Wiki pages and spark files do **not** carry an `id:` field — they have no issue-tracker identity.

### Path references

Frontmatter fields that reference other files (`depends_on`, `implements`, `target`, `spec`, `supersedes`, `related`, `parent`, `promoted`) accept any of the following forms. All forms resolve to the same file, so they are interchangeable on input — pick whichever reads best in context.

- **`#<id>` short form.** Issue families only. `#3` resolves to whichever file under `usecase/`, `task/<kind>/`, `review/`, `spec/`, or `idea/` carries `id: 3`. Slug-drift-proof. Useful when the artifact's exact slug is irrelevant to the reference. Renders as a GitHub-issue cross-link in synced trackers.
- **`<folder>/<id>` slug-less form.** Issue families only. `usecase/3` resolves to the usecase with id 3 regardless of slug. Adds folder hint without binding to the slug.
- **`<folder>/<id>-<slug>` slug-ful form.** `usecase/3-search-history`. Most self-describing — preferred for human-authored frontmatter that benefits from at-a-glance context. The slug part is a hint: when the file's actual stem differs (slug rename), the id wins and the mismatch is silently ignored.
- **Bare `<id>-<slug>`.** `3-search-history`. Resolves correctly because ids are globally unique. Permitted but folder-prefixed form is preferred for readability.
- **Wiki basename.** `architecture`, `domain`, `nfr`, etc. Wiki pages have no id; reference them by file basename. A review item naming a wiki page writes `target: [architecture, domain]`, not `target: [architecture.md]`. Issue-folder paths and wiki basenames may be mixed in a single `target:` list.
- **Spark stem.** `spark/2026-04-23-2119-caching-strategy.brainstorm`. The `.brainstorm` suffix is part of the filename base, not the extension.

Universal rules:

- **Plain strings.** No brackets — `usecase/3-search-history`, not `[usecase/3-search-history]`. Plain strings keep frontmatter machine-parseable.
- **No `.md` extension.** The validator rejects any reference ending in `.md`.
- **Existence is checked.** Each reference must resolve to a file in the workspace; unresolved refs surface as a `unresolved-ref` violation. Format-only references (e.g., a typo in `#99` where 99 has no file) are treated as authoring errors, not extension metadata.

Body links use a different form — standard markdown `[text](relative/path.md)`, plus plain `#<id>` text where GitHub-issue cross-link rendering is desired. See `body-conventions.md`.

### Dates

- ISO format `YYYY-MM-DD`, unquoted. YAML-native date type.
- All timestamp fields use the same format: `created`, `updated`, session timestamps on spark files.

### Empty collections

Empty lists may be written as `[]` or omitted entirely. Both are semantically equivalent. Prefer omission when the field is not expected to populate; prefer `[]` when the field is part of the type's shape and emptiness is noteworthy (e.g., `promoted: []` on a fresh brainstorm).

### Relationships

The schema fixes **one direction per relationship** — the forward direction is the canonical source. Reverse directions are **derived on demand** (grep, script back-scan) rather than stored. There is currently no stored-reverse field; if a future need arises (a status gate, automated check, or hot query that justifies bypassing derive-on-demand), a script must own writes for the field and the rationale must be documented here before the field is introduced.

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

Unknown fields are **not errors** — they are treated as extension metadata. Skills may carry additional fields (e.g., `tags`, `labels`) per the per-type tables below.

### Status writers

Every status change on `usecase`, `task`, `review`, and `spec` files flows through the single writer at [`../scripts/transition_status.py`](../scripts/transition_status.py), which validates the transition and writes `status:` + `updated:`, then runs any cascade:

- Task reset on UC `revising` (tasks at `progress`/`failing` → `pending`).
- Task / review discard cascade on UC `discarded`.
- Supersedes-chain flip on UC `shipped` (predecessor UC: `shipped → superseded`).
- Supersedes-chain flip on spec `active` (predecessor spec: `active|deprecated → superseded`).

`transition_status.py` does **not** touch the body's optional `## Log` section — that section is hand-maintained when an author wants a body-level audit trail. `status:` is **never hand-edited** after file creation. For cases the writer cannot mechanically reach (`idea` / `brainstorm` `promoted`), drift between `status:` and the supporting cross-references is surfaced as a separate consistency check.

A direct hand edit of `status:` is enforced as an error at stop time only when the resulting jump is **not** in `FAMILY_TRANSITIONS` (e.g. `shipped → ready`). Legal jumps slip past the legality check but still bypass the writer's cascades — the static cross-file consistency checks (`task.pending` revising cascade, `task.discarded` cascade, `review.discarded` cascade, supersedes chain) re-surface any cascade work the writer would have performed. The transition-legality safety net is implemented in [`../scripts/markdown_validator/transitions.py`](../scripts/markdown_validator/transitions.py) and runs on the Stop hook against the working-tree-vs-HEAD git diff.

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

Lifecycle (forward path, escape paths, cascade rules), abstraction discipline, body shape, and authoring guidance live in [`usecase-authoring.md`](./usecase-authoring.md).

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

Kind semantics, lifecycle, initial-status policy, and per-kind authoring guidance live in [`task-feature-authoring.md`](./task-feature-authoring.md), [`task-bug-authoring.md`](./task-bug-authoring.md), [`task-spike-authoring.md`](./task-spike-authoring.md), and [`task-research-authoring.md`](./task-research-authoring.md). The cross-kind artifact directory contract (`artifacts/task/<kind>/<id>-<slug>/`, the `task.files:` artifact-only rule, the spike archive convention, curation policy) lives in [`task-artifacts.md`](./task-artifacts.md).

## Review item (`a4/review/<id>-<slug>.md`)

Unified conduit for findings, gaps, and questions. The `kind:` field distinguishes them; lifecycle is identical.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `review` |
| `id` | yes | int | monotonic global integer |
| `kind` | yes | enum | `finding` \| `gap` \| `question` |
| `status` | yes | enum | `open` \| `in-progress` \| `resolved` \| `discarded` |
| `target` | no | list of paths | issue paths (e.g., `usecase/3-search`) and/or wiki basenames (e.g., `architecture`) this review is about. May mix both. Empty list / omitted is allowed for cross-cutting items. |
| `source` | yes | enum \| string | `self` \| `<reviewer-agent-name>` (e.g., `usecase-reviewer-r2`) |
| `priority` | no | enum | `high` \| `medium` \| `low` |
| `labels` | no | list of strings | free-form |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | yes | date | `YYYY-MM-DD` |

Lifecycle, cascade rules, close guard, and authoring guidance live in [`review-authoring.md`](./review-authoring.md).

## Spec (`a4/spec/<id>-<slug>.md`)

A spec is a **living, prescriptive specification** — the canonical description of a format, protocol, schema, renderer rule, CLI surface, or other artifact whose exact shape the project commits to.

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

Lifecycle (including the `→ superseded` cascade), body structure, `## Decision Log` policy, and authoring guidance live in [`spec-authoring.md`](./spec-authoring.md).

## Idea (`a4/idea/<id>-<slug>.md`)

Pre-pipeline quick-capture slot — Jira-issue-style "Idea / Suggestion" with the minimum fields needed to participate in the issue family. Boundary with `review/`: idea = independent possibility, captured raw; review = gap in current spec, bound to progress.

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

Lifecycle, body shape, deliberately excluded fields, and authoring guidance live in [`idea-authoring.md`](./idea-authoring.md).

## Spark brainstorm (`a4/spark/<YYYY-MM-DD-HHmm>-<slug>.brainstorm.md`)

Pre-pipeline idea-capture session. Lifecycle tracks whether ideas graduated into pipeline artifacts.

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

Lifecycle, body shape, the retired `spark-decide` slot history, and authoring guidance live in [`brainstorm-authoring.md`](./brainstorm-authoring.md).

## Schema enforcement

Body shape is documentation-only; frontmatter rules below are binding.

| Rule | Behavior |
|------|----------|
| Unknown frontmatter fields | **ignored** (the one point of leniency) |
| Missing required frontmatter field | error |
| Wrong type for a known field | error |
| Value outside enum for a known field | error |
| Path-reference format (brackets, `.md` extension, malformed `#<id>`) | error |
| Path reference does not resolve to any workspace file | error (`unresolved-ref`) |
| `type` on wiki page disagrees with filename | error |
| Filename leading id disagrees with `id:` field | error (`id-filename-mismatch`) |
| Id collision across issue folders | error |
| UC `status >= ready` with empty `actors:` | error (`missing-actors-post-draft`) |
| `title:` contains placeholder (`TBD`, `???`, `<placeholder>`, `<todo>`, `TODO:`) when UC is `>= ready` or spec is `>= active` | error (`placeholder-in-title`) |
| File in an issue / spark folder has no frontmatter | error |
| `status:` jump (HEAD → working tree) outside `FAMILY_TRANSITIONS` for `usecase` / `task` / `review` / `spec` | error (`illegal-transition`) — Stop hook safety net for direct edits that bypass `transition_status.py` |

How violations are surfaced (block, notify, ignore) is the surfacing layer's concern, not the schema's.

### Cross-file status consistency

Several enum values are semantically derived from cross-file state rather than being chosen in isolation:

| Field | Derived value | Condition | Materialized by |
|-------|--------------|-----------|-----------------|
| `usecase.status` | `superseded` | A newer `usecase/*.md` with `supersedes: [<this>]` has `status: shipped` | `transition_status.py` cascade (fires during successor's `→ shipped` transition) |
| `task.status` | `discarded` | UC the task implements flips to `discarded` | `transition_status.py` cascade |
| `task.status` | `pending` (from `implementing`/`failing`) | UC the task implements flips to `revising` | `transition_status.py` cascade |
| `review.status` | `discarded` | UC named by `target:` flips to `discarded` | `transition_status.py` cascade |
| `spec.status` | `superseded` | Another `spec/*.md` declares `supersedes: [<this>]` and has `status: active` | `transition_status.py` cascade (fires during successor's `→ active` transition) |
| `idea.status` | `promoted` | Own `promoted:` list is non-empty | user-driven; surfaced as a consistency check |
| `spark/*.brainstorm.md` `status` | `promoted` | Own `promoted:` list is non-empty | user-driven; surfaced as a consistency check |

Both directions of mismatch (stale terminal status with no supporting cross-reference, or unflipped status despite supporting cross-reference) are reported. Reporting is non-mutating — no file is changed automatically.

## Known deferred items

These are schema items deliberately left softened until a follow-up round.

1. **Issue `## Log` entry format.** Body-level `## Log` is hand-maintained when authors choose to populate it; the exact entry format (prefix, timestamp granularity, author attribution) is not yet locked.
2. **Exact YAML grammar for path references.** Plain string is the current rule; whether to allow alternative forms (list-of-maps for typed references, etc.) is not yet decided.
3. **Stricter enums.** Several fields are currently open strings (`source` on review items) because the full value set has not been enumerated.
4. **`task.files:` artifact-path enforcement.** The artifact-only contract on `task.files:` is documented but not yet enforced. Pending enforcement work: per-kind prefix check (`artifacts/task/<kind>/<id>-<slug>/...` for `spike` is required, optional for the other kinds; `spike` paths may also start with `artifacts/task/spike/archive/<id>-<slug>/`), plus a task-id-vs-path consistency check (the `<id>-<slug>` segment must match the file's own id and slug). Until then, frontmatter `files:` paths that still point at production source or a foreign id are tolerated.
5. **`research` `complete` initial-status preflight.** The path-existence check on `files:` (already enforced for `spike` and `feature`/`bug`) needs extension to `research` — when `research` is authored at `status: complete` with non-empty `files:`, every artifact path must exist under `artifacts/task/research/<id>-<slug>/` before the writer accepts the file.

When these land, update this document **and** the enforcement layer simultaneously — the two must not drift.

## Cross-references

- **Body-level conventions:** `body-conventions.md` — heading form (column-0 H2, Title Case, kebab → Title Case mapping), blank-line discipline, `## Change Logs` and `## Log` entry format, body link form (standard markdown).
- **Id allocator:** `../scripts/allocate_id.py`.
- **Status model (canonical):** `../scripts/status_model.py` — per-family status enums, allowed transitions, terminal / in-progress / active classifications, kind enums, supersedes-trigger and supersedable-target maps (`SUPERSEDES_TRIGGER_STATUS`, `SUPERSEDABLE_FROM_STATUSES`), task / review cascade input sets (`TASK_RESET_ON_REVISING`, `TASK_RESET_TARGET`, `REVIEW_TERMINAL`), and legality predicates (`is_transition_legal`, `legal_targets_from`, `is_terminal`). Imported by the writer (`transition_status.py`), the workspace dashboard (`workspace_state.py`), the consistency checker (`markdown_validator.status_consistency`), the transition-legality safety net (`markdown_validator.transitions`), and search; the prose tables in this document mirror the same data.
- **Status transition writer:** `../scripts/transition_status.py` — single writer for usecase / task / review / spec status changes; runs cascades (revising task reset, discarded cascade, shipped → superseded chain, spec active → superseded chain).
- **Status transition safety net:** `../scripts/markdown_validator/transitions.py` — Stop-hook check that diffs working-tree `status:` against HEAD via git and rejects transitions outside `FAMILY_TRANSITIONS`. Catches direct hand edits that bypass the writer above; the writer is still the recommended path because it also runs cascades.
