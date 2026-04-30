# a4 Frontmatter Schema

Consolidated frontmatter reference for every file under the `a4/` workspace. This document is the **single source of truth for the frontmatter contract**.

Body-side conventions (heading form, blank-line discipline, change-log and log section format, link form) live in `body-conventions.md`. The two should be read together.

## Scope

Every markdown file under `a4/` carries YAML frontmatter. Files split into three families:

| Family | Examples | Location |
|--------|----------|----------|
| **Wiki page** | `context.md`, `domain.md`, `architecture.md`, `actors.md`, `nfr.md`, `roadmap.md`, `bootstrap.md` | `a4/` root |
| **Issue** | use case, feature task, bug task, spike task, research task, review item, spec, idea | `a4/usecase/`, `a4/feature/`, `a4/bug/`, `a4/spike/`, `a4/research/`, `a4/review/`, `a4/spec/`, `a4/idea/` |
| **Spark** | brainstorm output | `a4/spark/` |

The four task-family folders (`feature`, `bug`, `spike`, `research`) are treated as siblings — they share the same status enum and lifecycle but each carries its own per-type schema and authoring contract. Cross-kind operations (UC cascades, status reset on revising) walk all four; single-kind authoring uses the matching folder only.

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
| Issue — feature task | `feature` |
| Issue — bug task | `bug` |
| Issue — spike task | `spike` |
| Issue — research task | `research` |
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

- **`<id>` integer short form.** Issue families only. A bare YAML integer `3` resolves to whichever file under `usecase/`, `feature/`, `bug/`, `spike/`, `research/`, `review/`, `spec/`, or `idea/` carries `id: 3`. Slug-drift-proof. Useful when the artifact's exact slug is irrelevant to the reference. (Renamed from the legacy `#<id>` string short form in a4 v11.0.0; the validator now rejects any path-ref entry beginning with `#`.)
- **`<folder>/<id>` slug-less form.** Issue families only. `usecase/3` resolves to the usecase with id 3 regardless of slug. Adds folder hint without binding to the slug. The `<folder>` segment is the actual top-level folder name (`feature`, `bug`, `spike`, `research`, etc.) — the legacy `task/<id>` form was retired in a4 v12.0.0.
- **`<folder>/<id>-<slug>` slug-ful form.** `usecase/3-search-history`. Most self-describing — preferred for human-authored frontmatter that benefits from at-a-glance context. The slug part is a hint: when the file's actual stem differs (slug rename), the id wins and the mismatch is silently ignored.
- **Bare `<id>-<slug>`.** `3-search-history`. Resolves correctly because ids are globally unique. Permitted but folder-prefixed form is preferred for readability.
- **Wiki basename.** `architecture`, `domain`, `nfr`, etc. Wiki pages have no id; reference them by file basename. A review item naming a wiki page writes `target: [architecture, domain]`, not `target: [architecture.md]`. Issue-folder paths and wiki basenames may be mixed in a single `target:` list.
- **Spark stem.** `spark/2026-04-23-2119-caching-strategy.brainstorm`. The `.brainstorm` suffix is part of the filename base, not the extension.

Universal rules:

- **Plain strings.** No brackets — `usecase/3-search-history`, not `[usecase/3-search-history]`. Plain strings keep frontmatter machine-parseable.
- **No `.md` extension.** The validator rejects any reference ending in `.md`.
- **Existence is checked.** Each reference must resolve to a file in the workspace; unresolved refs surface as a `unresolved-ref` violation. Format-only references (e.g., a typo in `99` where no file with `id: 99` exists) are treated as authoring errors, not extension metadata.

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

Every status change on `usecase`, the four task families (`feature` / `bug` / `spike` / `research`), `review`, and `spec` files flows through the single writer at [`../scripts/transition_status.py`](../scripts/transition_status.py), which validates the transition and writes `status:` + `updated:`, then runs any cascade:

- Task reset on UC `revising` — across all four task families, tasks at `progress`/`failing` → `pending`.
- Task / review discard cascade on UC `discarded` — across all four task families.
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

## Task family (`a4/<kind>/<id>-<slug>.md`)

Jira "task" semantics — units of executable work — split across four sibling families: `feature`, `bug`, `spike`, `research`. They share the same status enum and lifecycle but each has its own per-type schema and authoring contract. The kind is encoded in `type:` and in the top-level folder; there is **no** `kind:` field. Path references use the actual folder (`feature/<id>-<slug>`, `bug/<id>-<slug>`, etc.) — the legacy `task/<id>-<slug>` shape was retired in a4 v12.0.0.

The four families share the lifecycle defined by `TASK_TRANSITIONS` in `../scripts/status_model.py` and the cross-kind artifact contract documented in [`artifacts.md`](./artifacts.md). Cross-kind operations (UC `revising` / `discarded` cascades, the discard skill) walk all four folders via `TASK_FAMILY_TYPES`.

### Feature task (`a4/feature/<id>-<slug>.md`)

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `feature` |
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | human-readable |
| `status` | yes | enum | `open` \| `pending` \| `progress` \| `complete` \| `failing` \| `discarded` |
| `implements` | no | list of paths | use cases delivered |
| `depends_on` | no | list of paths | other tasks this one needs first |
| `spec` | no | list of paths | specs governing this task |
| `artifacts` | no | list of strings | artifact paths under `artifacts/feature/<id>-<slug>/`. Empty list is the typical default — feature work that ships only production source. Production source paths the task writes or modifies are documented in the body `## Files` section, **not** in this frontmatter field. |
| `cycle` | no | int | implementation cycle number |
| `labels` | no | list of strings | free-form tags |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | yes | date | `YYYY-MM-DD` |

Lifecycle, initial-status policy, and authoring guidance live in [`feature-authoring.md`](./feature-authoring.md).

### Bug task (`a4/bug/<id>-<slug>.md`)

Schema identical to feature — same field set, same lifecycle. Only the folder, the `type:` literal, and the artifact directory prefix (`artifacts/bug/<id>-<slug>/`) differ.

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

Lifecycle and authoring guidance live in [`bug-authoring.md`](./bug-authoring.md).

### Spike task (`a4/spike/<id>-<slug>.md`)

Time-boxed exploration to unblock a decision. Throwaway PoC code lives in the spike's artifact directory at `<project-root>/artifacts/spike/<id>-<slug>/`, **outside** the `a4/` workspace. `implements` / `spec` / `cycle` are forbidden — spikes are exploratory and never UC deliverables.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `spike` |
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | human-readable |
| `status` | yes | enum | `open` \| `pending` \| `progress` \| `complete` \| `failing` \| `discarded` |
| `depends_on` | no | list of paths | other tasks this one needs first |
| `artifacts` | no | list of strings | artifact paths under `artifacts/spike/<id>-<slug>/` (or `artifacts/spike/archive/<id>-<slug>/...` once archived). **Never** point at the project's production source tree — production paths the spike may also touch are documented in the body `## Files` section. |
| `labels` | no | list of strings | free-form tags |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | yes | date | `YYYY-MM-DD` |

`implements` / `spec` / `cycle` are not part of the spike schema — declaring them is an error. Lifecycle, archive convention, and authoring guidance live in [`spike-authoring.md`](./spike-authoring.md).

### Research task (`a4/research/<id>-<slug>.md`)

Time-boxed written investigation; the body itself is the deliverable. `implements` / `spec` / `cycle` are forbidden — research feeds downstream specs/features via `related:` and inline body links rather than directly delivering a UC.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `research` |
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | human-readable |
| `status` | yes | enum | `open` \| `pending` \| `progress` \| `complete` \| `failing` \| `discarded` |
| `mode` | yes | enum | `comparative` \| `single` |
| `options` | conditional | list of strings | option names — required when `mode: comparative`; forbidden when `mode: single` |
| `depends_on` | no | list of paths | other tasks this one needs first |
| `related` | no | list of paths | soft links — typically the spec(s) or feature(s) this research informs |
| `artifacts` | no | list of strings | artifact paths under `artifacts/research/<id>-<slug>/` (typically empty — research output lives in the body) |
| `labels` | no | list of strings | free-form tags |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | yes | date | `YYYY-MM-DD` |

`implements` / `spec` / `cycle` are not part of the research schema — declaring them is an error. Lifecycle and authoring guidance live in [`research-authoring.md`](./research-authoring.md).

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
| Path-reference format (brackets, `.md` extension, non-positive integer, legacy `#<id>` string) | error |
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
| `<task-family>.status` | `discarded` | UC the task implements flips to `discarded` (applies to `feature` / `bug` / `spike` / `research`) | `transition_status.py` cascade |
| `<task-family>.status` | `pending` (from `progress`/`failing`) | UC the task implements flips to `revising` (applies to `feature` / `bug` / `spike` / `research`) | `transition_status.py` cascade |
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

When these land, update this document **and** the enforcement layer simultaneously — the two must not drift.

## Cross-references

- **Body-level conventions:** `body-conventions.md` — heading form (column-0 H2, Title Case, kebab → Title Case mapping), blank-line discipline, `## Change Logs` and `## Log` entry format, body link form (standard markdown).
- **Id allocator:** `../scripts/allocate_id.py`.
- **Status model (canonical):** `../scripts/status_model.py` — per-family status enums, allowed transitions, terminal / in-progress / active classifications, the `TASK_FAMILY_TYPES` cross-kind grouping, kind enums (review only after a4 v12.0.0), supersedes-trigger and supersedable-target maps (`SUPERSEDES_TRIGGER_STATUS`, `SUPERSEDABLE_FROM_STATUSES`), task / review cascade input sets (`TASK_RESET_ON_REVISING`, `TASK_RESET_TARGET`, `REVIEW_TERMINAL`), and legality predicates (`is_transition_legal`, `legal_targets_from`, `is_terminal`). Imported by the writer (`transition_status.py`), the workspace dashboard (`workspace_state.py`), the consistency checker (`markdown_validator.status_consistency`), the transition-legality safety net (`markdown_validator.transitions`), and search; the prose tables in this document mirror the same data.
- **Status transition writer:** `../scripts/transition_status.py` — single writer for usecase / task / review / spec status changes; runs cascades (revising task reset, discarded cascade, shipped → superseded chain, spec active → superseded chain).
- **Status transition safety net:** `../scripts/markdown_validator/transitions.py` — Stop-hook check that diffs working-tree `status:` against HEAD via git and rejects transitions outside `FAMILY_TRANSITIONS`. Catches direct hand edits that bypass the writer above; the writer is still the recommended path because it also runs cascades.
