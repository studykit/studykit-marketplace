# a4 Common Frontmatter

Cross-cutting frontmatter rules for every markdown file under `a4/`. Family-specific contracts: `./frontmatter-wiki.md` (wiki minimal contract), `./frontmatter-issue.md` (issue-side: `id`, title placeholders, relationships, status changes / cascades, structural relationship fields). Per-type field tables: each `<type>-authoring.md`.

## Scope

Every markdown file under `a4/` carries YAML frontmatter. Two families:

| Family | Examples | Location |
|--------|----------|----------|
| **Wiki page** | `context.md`, `domain.md`, `architecture.md`, `actors.md`, `nfr.md`, `ci.md` | `a4/` root |
| **Issue** | use case, task, bug, spike, research, umbrella, review item, spec, idea, brainstorm | `a4/usecase/`, `a4/task/`, `a4/bug/`, `a4/spike/`, `a4/research/`, `a4/umbrella/`, `a4/review/`, `a4/spec/`, `a4/idea/`, `a4/brainstorm/` |

The four **issue families** (`task`, `bug`, `spike`, `research`) are siblings — one shared status enum and lifecycle (see `./issue-family-lifecycle.md`), each with its own per-type schema. `task` is the default (Jira-style "Task"); `bug` / `spike` / `research` are specialized variants. Cross-family operations (UC cascades, status reset on revising) walk all four; single-family authoring uses the matching folder.

## `type:` field

Every file declares `type:` in frontmatter. The value selects the per-type contract at `./<type>-authoring.md` (body sections, formal field table). Body uses Title Case H2 headings per `./body-conventions.md`.

| Family | `type:` value |
|--------|--------------|
| Wiki — actors | `actors` |
| Wiki — architecture | `architecture` |
| Wiki — ci | `ci` |
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

For wiki pages, `type:` doubles as the file-kind discriminator (`type: architecture` requires `a4/architecture.md`). For issue files, `type:` selects the per-type contract — file family is implied by the folder.

Rules:

- Every file must carry `type:`. Missing is an error.
- Wiki: `type:` must match file basename. Mismatch is an error.

## Path references

Frontmatter fields referencing other files (`depends_on`, `implements`, `target`, `spec`, `supersedes`, `related`, `parent`, `promoted`) accept any of the following. All resolve to the same file — pick whichever reads best.

- **`<id>` integer short form.** Issue folders only. Bare YAML integer `3` resolves to whichever file under `usecase/`, `task/`, `bug/`, `spike/`, `research/`, `umbrella/`, `review/`, `spec/`, `idea/`, `brainstorm/` carries `id: 3`. Slug-drift-proof. Any path-ref beginning with `#` is invalid (legacy `#<id>` removed in a4 v11.0.0).
- **`<folder>/<id>` slug-less form.** Issue folders only. `usecase/3` resolves to the usecase with id 3 regardless of slug. Adds folder hint.
- **`<folder>/<id>-<slug>` slug-ful form.** `usecase/3-search-history`. Most self-describing — preferred for human-authored frontmatter. Slug is a hint; on slug rename, id wins and the mismatch is silently ignored.
- **Bare `<id>-<slug>`.** `3-search-history`. Permitted; folder-prefixed form is preferred for readability.
- **Wiki basename.** `architecture`, `domain`, `nfr`, etc. Wiki pages have no id; reference by file basename. Review item: `target: [architecture, domain]`, not `target: [architecture.md]`. Issue-folder paths and wiki basenames may be mixed in a single `target:` list.

Universal rules:

- **Plain strings.** No brackets — `usecase/3-search-history`, not `[usecase/3-search-history]`.
- **No `.md` extension.** Any reference ending in `.md` is invalid.
- **Existence is checked.** Each reference must resolve to a file; unresolved refs surface as `unresolved-ref`. Format-only refs (typo `99` where no file with `id: 99` exists) are authoring errors, not extension metadata.

Body links use a different form — markdown `[text](relative/path.md)`, plus plain `#<id>` text where GitHub-issue cross-link rendering is desired. See `./body-conventions.md`.

## Empty collections

Empty lists may be `[]` or omitted — semantically equivalent. Prefer omission when the field is not expected to populate; prefer `[]` when emptiness is noteworthy (e.g., `promoted: []` on a fresh idea).

## Unknown fields

Unknown fields are **not errors** — treated as extension metadata. Skills may carry additional fields (`tags`, `labels`) per the per-type tables.

## `created` and `updated`

| Field | Applies to | Type | Format |
|-------|-----------|------|--------|
| `created` | every issue file | timestamp | `YYYY-MM-DD HH:mm` |
| `updated` | every issue file and every wiki page | timestamp | `YYYY-MM-DD HH:mm` |

- Format `YYYY-MM-DD HH:mm` (date + 24-hour time, space-separated). Validator rejects any other shape.
- All timestamps are implicitly Korean Standard Time (KST). No offset is written.
- **`created` is tooling-stamped on first Write.** PostToolUse on `Write` stamps `created: <KST now>` if missing. Once present, immutable — never rewritten by hook or cascade. Authors may pre-populate to backdate; the hook respects any non-empty value. On a fresh Write the hook uses the same KST timestamp for `created:` and `updated:`, so a brand-new file has `created == updated`.
- **`updated` is tooling-managed on every edit.** PostToolUse refreshes `updated:` to current KST on every Write/Edit/MultiEdit of an `a4/*.md` file (wiki + issue). Same auto-bump runs whether the edit changed `status:`, frontmatter, or body. When `status:` flips legally, the cascade handles primary's `updated:` (and every cascaded file's) in the same pass; auto-bump dedupes against that path so each file is rewritten at most once. Authors and skill runtimes do **not** hand-bump `updated:`. Edits bypassing the hook (manual `git checkout`, external editors) leave `updated:` untouched; recover via re-saving through Claude Code or `../scripts/validate.py --fix`.
