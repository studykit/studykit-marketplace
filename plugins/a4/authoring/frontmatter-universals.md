# a4 Frontmatter Universals

> **Audience:** Workspace authors writing `<project-root>/a4/**/*.md` files (or LLMs editing them on the user's behalf). Not for a4 plugin contributors — implementation references live in `../dev/`.

Cross-cutting frontmatter rules that apply to every markdown file under `a4/`. Per-type field tables (required vs optional fields, enum values, types) live in each `<type>-authoring.md`. Schema enforcement and cross-file consistency tables live in `./validator-rules.md`. Body-side conventions live in `./body-conventions.md`.

## Scope

Every markdown file under `a4/` carries YAML frontmatter. Files split into two families:

| Family | Examples | Location |
|--------|----------|----------|
| **Wiki page** | `context.md`, `domain.md`, `architecture.md`, `actors.md`, `nfr.md`, `roadmap.md`, `bootstrap.md` | `a4/` root |
| **Issue** | use case, task, bug, spike, research, review item, spec, idea, brainstorm | `a4/usecase/`, `a4/task/`, `a4/bug/`, `a4/spike/`, `a4/research/`, `a4/review/`, `a4/spec/`, `a4/idea/`, `a4/brainstorm/` |

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
| Issue — brainstorm | `brainstorm` |

For wiki pages, `type:` doubles as the file-kind discriminator (e.g., `type: architecture` requires the file to be at `a4/architecture.md`). For issue files, `type:` selects the per-type authoring contract — the file family is already implied by the folder.

Rules:

- Every file must carry `type:`. Missing it is an error.
- For wiki pages, `type:` must match the file basename (e.g., `type: architecture` requires `architecture.md`). Mismatches are errors.

## Wiki family — shared frontmatter contract

Every wiki page (`actors`, `architecture`, `bootstrap`, `context`, `domain`, `nfr`, `roadmap`) shares the same minimal contract:

```yaml
---
type: <wiki-basename>
updated: YYYY-MM-DD
---
```

- `type:` must equal the file basename (enforced — see `## type:` field above).
- `updated:` is an unquoted ISO date. Bump on every substantive edit (see `./body-conventions.md` § Bumping `updated:`).
- Wiki pages have **no** `id`, **no** `status`, **no** `## Log`, **no** lifecycle. They change continuously; the optional `## Change Logs` body section records why.

Per-wiki authoring files (`<wiki>-authoring.md`) describe only the body sections required for that page; they do not redeclare this contract.

## Ids

- Ids are **monotonically increasing integers, global to the workspace**. Unique across all issue folders in a given `a4/` (GitHub-issue semantics).
- Next id is computed as `max(existing ids in a4/) + 1` by the id allocator (`../scripts/allocate_id.py`). Allocate before writing a new issue file; never invent or reuse.
- Wiki pages do **not** carry an `id:` field — they have no issue-tracker identity.

Allocate the next id:

```bash
uv run ../scripts/allocate_id.py <absolute path to a4/>
```

The script prints the next available id to stdout.

## Path references

Frontmatter fields that reference other files (`depends_on`, `implements`, `target`, `spec`, `supersedes`, `related`, `parent`, `promoted`) accept any of the following forms. All forms resolve to the same file, so they are interchangeable on input — pick whichever reads best in context.

- **`<id>` integer short form.** Issue folders only. A bare YAML integer `3` resolves to whichever file under `usecase/`, `task/`, `bug/`, `spike/`, `research/`, `review/`, `spec/`, `idea/`, or `brainstorm/` carries `id: 3`. Slug-drift-proof. Useful when the artifact's exact slug is irrelevant to the reference. The validator rejects any path-ref entry beginning with `#`.
- **`<folder>/<id>` slug-less form.** Issue folders only. `usecase/3` resolves to the usecase with id 3 regardless of slug. Adds folder hint without binding to the slug. The `<folder>` segment is the actual top-level folder name (`task`, `bug`, `spike`, `research`, etc.); each task family has its own top-level folder.
- **`<folder>/<id>-<slug>` slug-ful form.** `usecase/3-search-history`. Most self-describing — preferred for human-authored frontmatter that benefits from at-a-glance context. The slug part is a hint: when the file's actual stem differs (slug rename), the id wins and the mismatch is silently ignored.
- **Bare `<id>-<slug>`.** `3-search-history`. Resolves correctly because ids are globally unique. Permitted but folder-prefixed form is preferred for readability.
- **Wiki basename.** `architecture`, `domain`, `nfr`, etc. Wiki pages have no id; reference them by file basename. A review item naming a wiki page writes `target: [architecture, domain]`, not `target: [architecture.md]`. Issue-folder paths and wiki basenames may be mixed in a single `target:` list.

Universal rules:

- **Plain strings.** No brackets — `usecase/3-search-history`, not `[usecase/3-search-history]`. Plain strings keep frontmatter machine-parseable.
- **No `.md` extension.** The validator rejects any reference ending in `.md`.
- **Existence is checked.** Each reference must resolve to a file in the workspace; unresolved refs surface as a `unresolved-ref` violation. Format-only references (e.g., a typo in `99` where no file with `id: 99` exists) are treated as authoring errors, not extension metadata.

Body links use a different form — standard markdown `[text](relative/path.md)`, plus plain `#<id>` text where GitHub-issue cross-link rendering is desired. See `./body-conventions.md`.

## Dates

- ISO format `YYYY-MM-DD`, unquoted. YAML-native date type.
- All timestamp fields use the same format: `created`, `updated`.

## Empty collections

Empty lists may be written as `[]` or omitted entirely. Both are semantically equivalent. Prefer omission when the field is not expected to populate; prefer `[]` when the field is part of the type's shape and emptiness is noteworthy (e.g., `promoted: []` on a fresh idea or brainstorm).

## Relationships

The schema fixes **one direction per relationship** — the forward direction is the canonical source. Reverse directions are **derived on demand** (grep, script back-scan) rather than stored. There is currently no stored-reverse field; if a future need arises (a status gate, automated check, or hot query that justifies bypassing derive-on-demand), a script must own writes for the field and the rationale must be documented here before the field is introduced.

| Forward (stored) | Reverse | Storage |
|------------------|---------|---------|
| `depends_on` | `blocks` | derived |
| `implements` | (UC → tasks) | derived |
| `supersedes` | `superseded_by` | derived |
| `parent` | `children` | derived |
| `target` | (review backlinks; wiki-page backlinks) | derived |
| `promoted` | (idea / brainstorm → pipeline backlinks) | derived |
| `related` | (symmetric; no reverse) | — |

## Unknown fields

Unknown fields are **not errors** — they are treated as extension metadata. Skills may carry additional fields (e.g., `tags`, `labels`) per the per-type tables in each `<type>-authoring.md`.

## Status writers

Every status change on `usecase`, the four task issue families (`task` / `bug` / `spike` / `research`), `review`, and `spec` files is **edited directly** on the file. The PostToolUse cascade hook detects the pre→post transition, refreshes `updated:` on the primary file, and runs any cross-file cascade:

- Task reset on UC `revising` — across all four task issue families, tasks at `progress`/`failing` → `pending`.
- Task / review discard cascade on UC `discarded` — across all four task issue families.
- Supersedes-chain flip on UC `shipped` (predecessor UC: `shipped → superseded`).
- Supersedes-chain flip on spec `active` (predecessor spec: `active|deprecated → superseded`).

The hook does **not** touch the body's optional `## Log` section — that section is hand-maintained when an author wants a body-level audit trail. For cases the cascade engine cannot mechanically reach (`idea` / `brainstorm` `promoted`), drift between `status:` and the supporting cross-references is surfaced as a separate consistency check.

Edge cases:

- **Illegal jumps** (e.g. `shipped → ready`, outside `FAMILY_TRANSITIONS`) — the cascade hook silently skips them; the Stop-hook transition-legality safety net (working-tree-vs-HEAD git diff) surfaces them as errors.
- **Legal jumps that bypass the hook** (edits via `git checkout`, external editors, direct script writes) — related files are left unflipped. The cross-file consistency checks (`task.pending` revising cascade, `task.discarded` cascade, `review.discarded` cascade, supersedes chain) re-surface the missing cascade work.
- **Recovery** —
  - Supersedes-chain: `../scripts/validate.py --fix` (workspace-wide, idempotent).
  - Reverse-link (revising / discarded cascades): re-edit the UC's `status:` to retrigger the hook.

## Structural relationship fields

Shared across all issue types. Omit fields that are empty, or use `[]`.

| Field | Applies to | Points at | Meaning |
|-------|-----------|-----------|---------|
| `depends_on` | task | task | Tasks that must complete before this one (lifecycle blocker) |
| `implements` | task | usecase | Use cases delivered by this task |
| `target` | review | any issue path(s) and/or wiki basename(s) | What this review item is about and which wiki pages must record the resolution; mixed lists are allowed |
| `spec` | task (`task` / `bug` only) | spec | Specs that govern this task |
| `supersedes` | spec, usecase | prior spec(s) / usecase(s) | This item replaces the referenced item(s) of the same family |
| `promoted` | idea, brainstorm | spec, usecase, task, brainstorm | Where this item's content graduated to (brainstorm: one-to-many ideas grow into pipeline artifacts; idea: a single captured thought becomes a concrete artifact) |
| `parent` | any issue | same-type issue | Parent in a decomposition hierarchy |
| `related` | any | any | Generic catchall for ties that don't fit other fields but warrant frontmatter-level searchability |

Soft references (see-also, mentions) are expressed as standard markdown links (`[text](relative/path.md)`) in body prose, not frontmatter.

## Cross-references

- **Per-type schemas (formal field tables):** the `## Frontmatter` section of each `./<type>-authoring.md`.
- **Schema enforcement and cross-file status consistency:** `./validator-rules.md`.
- **Body conventions:** `./body-conventions.md` — heading form, blank-line discipline, `## Change Logs` and `## Log` entry format, body link form.
