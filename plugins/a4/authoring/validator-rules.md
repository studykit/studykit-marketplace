# a4 Validator Rules

Frontmatter validation contract — what the validator rejects, what it ignores, and how cross-file status consistency is checked. Per-type field shapes (required vs optional, enum values, types) live in each `./<type>-authoring.md`. Universal frontmatter rules (path-reference format, status writers, ids) live in `./frontmatter-universals.md`.

This document is the canonical reference for `../scripts/markdown_validator/*.py` and the `/a4:validate` skill.

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
| `status:` jump (HEAD → working tree) outside `FAMILY_TRANSITIONS` for `usecase` / `task` / `review` / `spec` | error (`illegal-transition`) — Stop hook safety net; the PostToolUse cascade hook silently skips illegal jumps, so this surfaces them |

How violations are surfaced (block, notify, ignore) is the surfacing layer's concern, not the schema's.

## Cross-file status consistency

Several enum values are semantically derived from cross-file state rather than being chosen in isolation:

| Field | Derived value | Condition | Materialized by |
|-------|--------------|-----------|-----------------|
| `usecase.status` | `superseded` | A newer `usecase/*.md` with `supersedes: [<this>]` has `status: shipped` | PostToolUse cascade hook (fires during successor's `→ shipped` transition); `validate.py --fix` for recovery |
| `<task-family>.status` | `discarded` | UC the task implements flips to `discarded` (applies to `task` / `bug` / `spike` / `research`) | PostToolUse cascade hook |
| `<task-family>.status` | `pending` (from `progress`/`failing`) | UC the task implements flips to `revising` (applies to `task` / `bug` / `spike` / `research`) | PostToolUse cascade hook |
| `review.status` | `discarded` | UC named by `target:` flips to `discarded` | PostToolUse cascade hook |
| `spec.status` | `superseded` | Another `spec/*.md` declares `supersedes: [<this>]` and has `status: active` | PostToolUse cascade hook (fires during successor's `→ active` transition); `validate.py --fix` for recovery |
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

- **Universal frontmatter rules:** `./frontmatter-universals.md` — `type:` field, ids, path-reference format, dates, empty collections, relationships, unknown fields, status writers, structural relationship fields table.
- **Per-type field tables:** the `## Frontmatter` section of each `./<type>-authoring.md`.
- **Validator entrypoint:** `../scripts/validate.py` — unified CLI; runs every check registered in `markdown_validator.registry.CHECKS`.
- **Frontmatter validator:** `../scripts/markdown_validator/frontmatter.py` — required fields, enums, types, path-reference format, id uniqueness, post-draft authoring invariants.
- **Status consistency checker:** `../scripts/markdown_validator/status_consistency.py` — the cross-file table above.
- **Transition legality safety net:** `../scripts/markdown_validator/transitions.py` — Stop-hook git-diff check.
