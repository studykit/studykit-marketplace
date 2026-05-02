# a4 Common Frontmatter

Cross-cutting frontmatter rules that apply to every markdown file under `a4/` (both wiki pages and issue files). Family-specific contracts live in `./frontmatter-wiki.md` (wiki minimal contract) and `./frontmatter-issue.md` (issue-side rules — `id`, title placeholders, relationships, status changes and cascades, structural relationship fields). Per-type field tables live in each `<type>-authoring.md`.

## Scope

Every markdown file under `a4/` carries YAML frontmatter. Files split into two families:

| Family | Examples | Location |
|--------|----------|----------|
| **Wiki page** | `context.md`, `domain.md`, `architecture.md`, `actors.md`, `nfr.md`, `bootstrap.md` | `a4/` root |
| **Issue** | use case, task, bug, spike, research, umbrella, review item, spec, idea, brainstorm | `a4/usecase/`, `a4/task/`, `a4/bug/`, `a4/spike/`, `a4/research/`, `a4/umbrella/`, `a4/review/`, `a4/spec/`, `a4/idea/`, `a4/brainstorm/` |

The four **issue families** (`task`, `bug`, `spike`, `research`) are siblings — they share one status enum and lifecycle (see `./issue-family-lifecycle.md`), but each carries its own per-type schema and authoring contract. The `task` family is the default (regular implementation work, equivalent to Jira's "Task" issue type); `bug` / `spike` / `research` are specialized variants. Cross-family operations (UC cascades, status reset on revising) walk all four; single-family authoring uses the matching folder only.

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
| Issue — usecase | `usecase` |
| Issue — task | `task` |
| Issue — bug | `bug` |
| Issue — spike | `spike` |
| Issue — research | `research` |
| Issue — umbrella | `umbrella` |
| Issue — review | `review` |
| Issue — spec | `spec` |
| Issue — idea | `idea` |
| Issue — brainstorm | `brainstorm` |

For wiki pages, `type:` doubles as the file-kind discriminator (e.g., `type: architecture` requires the file to be at `a4/architecture.md`). For issue files, `type:` selects the per-type authoring contract — the file family is already implied by the folder.

Rules:

- Every file must carry `type:`. Missing it is an error.
- For wiki pages, `type:` must match the file basename (e.g., `type: architecture` requires `architecture.md`). Mismatches are errors.

## Path references

Frontmatter fields that reference other files (`depends_on`, `implements`, `target`, `spec`, `supersedes`, `related`, `parent`, `promoted`) accept any of the following forms. All forms resolve to the same file, so they are interchangeable on input — pick whichever reads best in context.

- **`<id>` integer short form.** Issue folders only. A bare YAML integer `3` resolves to whichever file under `usecase/`, `task/`, `bug/`, `spike/`, `research/`, `umbrella/`, `review/`, `spec/`, `idea/`, or `brainstorm/` carries `id: 3`. Slug-drift-proof. Useful when the artifact's exact slug is irrelevant to the reference. Any path-ref entry beginning with `#` is invalid (the legacy `#<id>` short form was removed in a4 v11.0.0; write the bare integer instead).
- **`<folder>/<id>` slug-less form.** Issue folders only. `usecase/3` resolves to the usecase with id 3 regardless of slug. Adds folder hint without binding to the slug. The `<folder>` segment is the actual top-level folder name (`task`, `bug`, `spike`, `research`, etc.); each issue family has its own top-level folder.
- **`<folder>/<id>-<slug>` slug-ful form.** `usecase/3-search-history`. Most self-describing — preferred for human-authored frontmatter that benefits from at-a-glance context. The slug part is a hint: when the file's actual stem differs (slug rename), the id wins and the mismatch is silently ignored.
- **Bare `<id>-<slug>`.** `3-search-history`. Resolves correctly because ids are globally unique. Permitted but folder-prefixed form is preferred for readability.
- **Wiki basename.** `architecture`, `domain`, `nfr`, etc. Wiki pages have no id; reference them by file basename. A review item naming a wiki page writes `target: [architecture, domain]`, not `target: [architecture.md]`. Issue-folder paths and wiki basenames may be mixed in a single `target:` list.

Universal rules:

- **Plain strings.** No brackets — `usecase/3-search-history`, not `[usecase/3-search-history]`.
- **No `.md` extension.** Any reference ending in `.md` is invalid.
- **Existence is checked.** Each reference must resolve to a file in the workspace; unresolved refs surface as a `unresolved-ref` violation. Format-only references (e.g., a typo in `99` where no file with `id: 99` exists) are treated as authoring errors, not extension metadata.

Body links use a different form — standard markdown `[text](relative/path.md)`, plus plain `#<id>` text where GitHub-issue cross-link rendering is desired. See `./body-conventions.md`.

## Empty collections

Empty lists may be written as `[]` or omitted entirely. Both are semantically equivalent. Prefer omission when the field is not expected to populate; prefer `[]` when the field is part of the type's shape and emptiness is noteworthy (e.g., `promoted: []` on a fresh idea or brainstorm).

## Unknown fields

Unknown fields are **not errors** — they are treated as extension metadata. Skills may carry additional fields (e.g., `tags`, `labels`) per the per-type tables in each `<type>-authoring.md`.

## `created` and `updated`

| Field | Applies to | Type | Format |
|-------|-----------|------|--------|
| `created` | every issue file | timestamp | `YYYY-MM-DD HH:mm` |
| `updated` | every issue file and every wiki page | timestamp | `YYYY-MM-DD HH:mm` |

- Format `YYYY-MM-DD HH:mm` (date + 24-hour time, space-separated). The validator rejects any other shape.
- All timestamps are implicitly Korean Standard Time (KST). No timezone offset is written — KST is the project-wide convention, not a per-field declaration.
- **`created` is tooling-stamped on first Write.** When a new issue file is created (PostToolUse on `Write`), the hook stamps `created: <KST now>` if the field is missing. Once present, the value is immutable — neither the hook nor the cascade ever rewrites it. Authors may pre-populate `created:` to backdate; the hook respects any non-empty value.
- **`updated` is tooling-managed on status flips.** When `status:` changes via PostToolUse, the cascade engine refreshes `updated:` to the current KST timestamp on the primary file and on every cascaded related file. For non-status edits (body change, wiki edit) authors hand-bump `updated:` themselves — the hook does not run a global "edit detector".
