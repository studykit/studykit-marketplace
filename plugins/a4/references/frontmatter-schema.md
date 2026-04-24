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

## Structural relationship fields

Shared across all issue types. Omit fields that are empty, or use `[]`.

| Field | Applies to | Points at | Meaning |
|-------|-----------|-----------|---------|
| `depends_on` | issue | issue | Items that must complete before this one (lifecycle blocker) |
| `implements` | task | usecase | Use cases delivered by this task |
| `target` | review | any issue or wiki | What this review item is about |
| `wiki_impact` | review, issue | wiki basename(s) | Wiki pages requiring update when this item resolves |
| `justified_by` | any issue | decision | Decisions that justify this item |
| `supersedes` | decision | prior decision(s) | This decision replaces the referenced decision(s) |
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
| `status` | yes | enum | `draft` \| `implementing` \| `done` \| `blocked` |
| `actors` | no | list of strings | actor names as defined in `actors.md` |
| `depends_on` | no | list of paths | other use cases this UC needs first |
| `justified_by` | no | list of paths | decisions justifying this UC |
| `related` | no | list of paths | catchall |
| `labels` | no | list of strings | free-form tags |
| `milestone` | no | string | milestone name (e.g., `v1.0`) |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | yes | date | `YYYY-MM-DD` |

## Task (`a4/task/<id>-<slug>.md`)

Jira "task" semantics — a unit of executable work. The `kind:` field distinguishes regular implementation, time-boxed exploration, and defect work; lifecycle is identical across kinds.

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | human-readable |
| `kind` | yes | enum | `feature` \| `spike` \| `bug` |
| `status` | yes | enum | `pending` \| `implementing` \| `complete` \| `failing` |
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
| `status` | yes | enum | `open` \| `in-progress` \| `resolved` \| `dismissed` |
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

ADR stored as an issue — the canonical decision slot from the wiki+issues duality. Decisions arrive here via two paths: (a) direct authoring for straightforward rules, and (b) `/a4:spark-decide` finalization for option-comparison / research-driven decisions. Both paths produce the same frontmatter shape; the body may carry optional `## Options Considered`, `## Research Findings`, `## Evaluation`, and `<details><summary>Discussion Log</summary>` sections when spark-decide wrote it.

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

Decisions enter at `draft` while the rationale is still being written, move to `final` once committed, and later to `superseded` only when a newer decision declares `supersedes: [decision/<this-id>-<slug>]`.

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

**Note on spark-decide.** Historically `a4/spark/<YYYY-MM-DD-HHmm>-<slug>.decide.md` was a separate "pre-pipeline decision" slot. It has been retired: the `/a4:spark-decide` skill now writes directly into `a4/decision/<id>-<slug>.md` as a first-class decision issue. The decision-issue schema above covers all spark-decide output.

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
- **Drift detector (uses wiki / review schemas):** `plugins/a4/scripts/drift_detector.py`.
- **Read-only parser:** `plugins/a4/scripts/read_frontmatter.py`.
- **Spark schemas (origin):** `plugins/a4/skills/spark-brainstorm/SKILL.md` (spark-decide writes into the `decision` issue schema — no separate spark-decide frontmatter).
