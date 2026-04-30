# a4 Frontmatter Universals

Cross-cutting frontmatter rules that apply to every markdown file under `a4/`. Per-type field tables (required vs optional fields, enum values, types) live in each `<type>-authoring.md`. Schema enforcement and cross-file consistency tables live in `./validator-rules.md`. Body-side conventions live in `./body-conventions.md`.

## Scope

Every markdown file under `a4/` carries YAML frontmatter. Files split into three families:

| Family | Examples | Location |
|--------|----------|----------|
| **Wiki page** | `context.md`, `domain.md`, `architecture.md`, `actors.md`, `nfr.md`, `roadmap.md`, `bootstrap.md` | `a4/` root |
| **Issue** | use case, task, bug, spike, research, review item, spec, idea | `a4/usecase/`, `a4/task/`, `a4/bug/`, `a4/spike/`, `a4/research/`, `a4/review/`, `a4/spec/`, `a4/idea/` |
| **Spark** | brainstorm output | `a4/spark/` |

The four issue families that share the task lifecycle (`task`, `bug`, `spike`, `research`) are siblings — they share the same status enum and lifecycle but each carries its own per-type schema and authoring contract. The `task` family is the default (regular implementation work, equivalent to Jira's "Task" issue type); `bug` / `spike` / `research` are specialized variants. Cross-family operations (UC cascades, status reset on revising) walk all four; single-family authoring uses the matching folder only.

## `type:` field

Every markdown file declares a `type:` field in frontmatter. The value selects the per-type authoring contract at `./<type>-authoring.md`, which lists the body sections required vs optional for that type and the formal field table. The body uses Title Case H2 headings (`## Heading`) per `./body-conventions.md`.

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
| Issue — bug | `bug` |
| Issue — spike | `spike` |
| Issue — research | `research` |
| Issue — review | `review` |
| Issue — spec | `spec` |
| Issue — idea | `idea` |
| Spark — brainstorm | `brainstorm` |

For wiki pages, `type:` doubles as the file-kind discriminator (e.g., `type: architecture` requires the file to be at `a4/architecture.md`). For issues and spark files, `type:` selects the per-type authoring contract — the file family is already implied by the folder.

Rules:

- Every file must carry `type:`. Missing it is an error.
- For wiki pages, `type:` must match the file basename (e.g., `type: architecture` requires `architecture.md`). Mismatches are errors.

## Body section headings

Body sections are column-0 H2 markdown headings in Title Case with spaces (`## Context`, `## Specification`, `## Change Logs`, …). The recommended set per `type:` lives in the per-type authoring contracts under `./<type>-authoring.md`, each of which lists required / optional sections and tolerates unknown Title Case headings. See `./body-conventions.md` for the full heading-form rules.

## Ids

- Ids are **monotonically increasing integers, global to the workspace**. Unique across all issue folders in a given `a4/` (GitHub-issue semantics).
- Next id is computed as `max(existing ids in a4/) + 1` by `../scripts/allocate_id.py`.
- Wiki pages and spark files do **not** carry an `id:` field — they have no issue-tracker identity.

## Path references

Frontmatter fields that reference other files (`depends_on`, `implements`, `target`, `spec`, `supersedes`, `related`, `parent`, `promoted`) accept any of the following forms. All forms resolve to the same file, so they are interchangeable on input — pick whichever reads best in context.

- **`<id>` integer short form.** Issue folders only. A bare YAML integer `3` resolves to whichever file under `usecase/`, `task/`, `bug/`, `spike/`, `research/`, `review/`, `spec/`, or `idea/` carries `id: 3`. Slug-drift-proof. Useful when the artifact's exact slug is irrelevant to the reference. (Renamed from the legacy `#<id>` string short form in a4 v11.0.0; the validator now rejects any path-ref entry beginning with `#`.)
- **`<folder>/<id>` slug-less form.** Issue folders only. `usecase/3` resolves to the usecase with id 3 regardless of slug. Adds folder hint without binding to the slug. The `<folder>` segment is the actual top-level folder name (`task`, `bug`, `spike`, `research`, etc.) — in a4 v12.0.0+ each task family has its own folder; the legacy `task/<kind>/<id>` shape (with a kind subfolder) was retired.
- **`<folder>/<id>-<slug>` slug-ful form.** `usecase/3-search-history`. Most self-describing — preferred for human-authored frontmatter that benefits from at-a-glance context. The slug part is a hint: when the file's actual stem differs (slug rename), the id wins and the mismatch is silently ignored.
- **Bare `<id>-<slug>`.** `3-search-history`. Resolves correctly because ids are globally unique. Permitted but folder-prefixed form is preferred for readability.
- **Wiki basename.** `architecture`, `domain`, `nfr`, etc. Wiki pages have no id; reference them by file basename. A review item naming a wiki page writes `target: [architecture, domain]`, not `target: [architecture.md]`. Issue-folder paths and wiki basenames may be mixed in a single `target:` list.
- **Spark stem.** `spark/2026-04-23-2119-caching-strategy.brainstorm`. The `.brainstorm` suffix is part of the filename base, not the extension.

Universal rules:

- **Plain strings.** No brackets — `usecase/3-search-history`, not `[usecase/3-search-history]`. Plain strings keep frontmatter machine-parseable.
- **No `.md` extension.** The validator rejects any reference ending in `.md`.
- **Existence is checked.** Each reference must resolve to a file in the workspace; unresolved refs surface as a `unresolved-ref` violation. Format-only references (e.g., a typo in `99` where no file with `id: 99` exists) are treated as authoring errors, not extension metadata.

Body links use a different form — standard markdown `[text](relative/path.md)`, plus plain `#<id>` text where GitHub-issue cross-link rendering is desired. See `./body-conventions.md`.

## Dates

- ISO format `YYYY-MM-DD`, unquoted. YAML-native date type.
- All timestamp fields use the same format: `created`, `updated`, session timestamps on spark files.

## Empty collections

Empty lists may be written as `[]` or omitted entirely. Both are semantically equivalent. Prefer omission when the field is not expected to populate; prefer `[]` when the field is part of the type's shape and emptiness is noteworthy (e.g., `promoted: []` on a fresh brainstorm).

## Relationships

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

## Unknown fields

Unknown fields are **not errors** — they are treated as extension metadata. Skills may carry additional fields (e.g., `tags`, `labels`) per the per-type tables in each `<type>-authoring.md`.

## Status writers

Every status change on `usecase`, the four task issue families (`task` / `bug` / `spike` / `research`), `review`, and `spec` files is **edited directly** on the file. The PostToolUse cascade hook (`../scripts/a4_hook.py`) detects the pre→post transition, refreshes `updated:` on the primary file, and runs any cross-file cascade:

- Task reset on UC `revising` — across all four task issue families, tasks at `progress`/`failing` → `pending`.
- Task / review discard cascade on UC `discarded` — across all four task issue families.
- Supersedes-chain flip on UC `shipped` (predecessor UC: `shipped → superseded`).
- Supersedes-chain flip on spec `active` (predecessor spec: `active|deprecated → superseded`).

The hook does **not** touch the body's optional `## Log` section — that section is hand-maintained when an author wants a body-level audit trail. For cases the cascade engine cannot mechanically reach (`idea` / `brainstorm` `promoted`), drift between `status:` and the supporting cross-references is surfaced as a separate consistency check.

A direct hand edit of `status:` is enforced as an error at stop time only when the resulting jump is **not** in `FAMILY_TRANSITIONS` (e.g. `shipped → ready`); the cascade hook silently ignores illegal jumps and the static safety net surfaces them. Legal jumps that bypass the hook entirely (e.g. edits made via `git checkout`, an external editor, or scripts that wrote frontmatter directly) leave related files unflipped — the static cross-file consistency checks (`task.pending` revising cascade, `task.discarded` cascade, `review.discarded` cascade, supersedes chain) re-surface the missing cascade work. For supersedes-chain recovery specifically, run `../scripts/validate.py --fix` (workspace-wide, idempotent). For reverse-link recovery (revising / discarded), re-edit the UC's `status:` to retrigger the hook. The transition-legality safety net is implemented in `../scripts/markdown_validator/transitions.py` and runs on the Stop hook against the working-tree-vs-HEAD git diff.

## Structural relationship fields

Shared across all issue types. Omit fields that are empty, or use `[]`.

| Field | Applies to | Points at | Meaning |
|-------|-----------|-----------|---------|
| `depends_on` | task | task | Tasks that must complete before this one (lifecycle blocker) |
| `implements` | task | usecase | Use cases delivered by this task |
| `target` | review | any issue path(s) and/or wiki basename(s) | What this review item is about and which wiki pages must record the resolution; mixed lists are allowed |
| `spec` | task (`task` / `bug` only) | spec | Specs that govern this task |
| `supersedes` | spec, usecase | prior spec(s) / usecase(s) | This item replaces the referenced item(s) of the same family |
| `promoted` | spark/brainstorm, idea | spec, usecase, task, spark/brainstorm | Where this item's content graduated to (brainstorm: one-to-many ideas grow into pipeline artifacts; idea: a single captured thought becomes a concrete artifact) |
| `parent` | any issue | same-type issue | Parent in a decomposition hierarchy |
| `related` | any | any | Generic catchall for ties that don't fit other fields but warrant frontmatter-level searchability |

Soft references (see-also, mentions) are expressed as standard markdown links (`[text](relative/path.md)`) in body prose, not frontmatter.

## Cross-references

- **Per-type schemas (formal field tables):** the `## Frontmatter` section of each `./<type>-authoring.md`.
- **Schema enforcement and cross-file status consistency:** `./validator-rules.md`.
- **Body conventions:** `./body-conventions.md` — heading form, blank-line discipline, `## Change Logs` and `## Log` entry format, body link form.
- **Id allocator:** `../scripts/allocate_id.py`.
- **Status model (canonical):** `../scripts/status_model.py` — per-family status enums, allowed transitions, terminal / in-progress / active classifications, the `ISSUE_FAMILY_TYPES` cross-family grouping for the four task issue families, kind enums (review only after a4 v12.0.0), supersedes-trigger and supersedable-target maps, task / review cascade input sets, and legality predicates. Imported by the cascade engine (`status_cascade.py`), the cascade hook (`a4_hook.py`), the workspace dashboard (`workspace_state.py`), the consistency checker (`markdown_validator.status_consistency`), the transition-legality safety net (`markdown_validator.transitions`), and search.
- **Cascade engine:** `../scripts/status_cascade.py` — supersedes / discarded / revising cascade primitives shared by the PostToolUse cascade hook and the `validate.py --fix` recovery sweep.
- **Cascade hook:** `../scripts/a4_hook.py` — PostToolUse hook that detects pre→post `status:` transitions and runs cascades on related files.
- **Recovery sweep:** `../scripts/validate.py` `--fix` — supersedes-chain idempotent sweep for edits that bypassed the hook.
- **Status transition safety net:** `../scripts/markdown_validator/transitions.py` — Stop-hook check that diffs working-tree `status:` against HEAD via git and rejects transitions outside `FAMILY_TRANSITIONS`. Catches illegal direct edits the cascade hook silently ignored.
