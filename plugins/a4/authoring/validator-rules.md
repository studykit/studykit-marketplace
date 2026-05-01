# a4 Validator Rules

> **Audience:** Workspace authors writing `<project-root>/a4/**/*.md` files (or LLMs editing them on the user's behalf). Not for a4 plugin contributors — implementation references live in `../dev/`.

Frontmatter validation contract — what the validator rejects, what it ignores, and how cross-file status consistency is checked. Per-type field shapes (required vs optional, enum values, types) live in each `./<type>-authoring.md`. Universal frontmatter rules (path-reference format, status writers, ids) live in `./frontmatter-universals.md`.

This document is the canonical reference for the validator — what it rejects, ignores, and reports.

## Schema enforcement

Body shape is documentation-only; frontmatter rules below are binding.

| Rule | Behavior |
|------|----------|
| Unknown frontmatter fields | **ignored** (the one point of leniency) |
| Missing required frontmatter field | error |
| Wrong type for a known field | error |
| Value outside enum for a known field | error |
| Path-reference format (brackets, `.md` extension, non-positive integer, leading `#` on a path-ref entry) | error |
| Path reference does not resolve to any workspace file | error (`unresolved-ref`) |
| `type` on wiki page disagrees with filename | error |
| Filename leading id disagrees with `id:` field | error (`id-filename-mismatch`) |
| Id collision across issue folders | error |
| UC `status >= ready` with empty `actors:` | error (`missing-actors-post-draft`) |
| `title:` contains placeholder (`TBD`, `???`, `<placeholder>`, `<todo>`, `TODO:`) when UC is `>= ready` or spec is `>= active` | error (`placeholder-in-title`) |
| File in an issue folder has no frontmatter | error |
| `status:` jump (HEAD → working tree) outside `FAMILY_TRANSITIONS` for `usecase` / `task` / `review` / `spec` | error (`illegal-transition`) — Stop hook safety net; the PostToolUse cascade hook silently skips illegal jumps, so this surfaces them |

How violations are surfaced (block, notify, ignore) is the surfacing layer's concern, not the schema's.

## Cross-file status consistency

Several enum values are semantically derived from cross-file state rather than being chosen in isolation:

| Field | Derived value | Condition | Materialized by |
|-------|--------------|-----------|-----------------|
| `usecase.status` | `superseded` | A newer `usecase/*.md` with `supersedes: [<this>]` has `status: shipped` | PostToolUse cascade hook (fires during successor's `→ shipped` transition); `../scripts/validate.py --fix` for recovery |
| `<task-family>.status` | `discarded` | UC the task implements flips to `discarded` (applies to `task` / `bug` / `spike` / `research`) | PostToolUse cascade hook |
| `<task-family>.status` | `pending` (from `progress`/`failing`) | UC the task implements flips to `revising` (applies to `task` / `bug` / `spike` / `research`) | PostToolUse cascade hook |
| `review.status` | `discarded` | UC named by `target:` flips to `discarded` | PostToolUse cascade hook |
| `spec.status` | `superseded` | Another `spec/*.md` declares `supersedes: [<this>]` and has `status: active` | PostToolUse cascade hook (fires during successor's `→ active` transition); `../scripts/validate.py --fix` for recovery |
| `idea.status` | `promoted` | Own `promoted:` list is non-empty | user-driven; surfaced as a consistency check |
| `brainstorm.status` | `promoted` | Own `promoted:` list is non-empty | user-driven; surfaced as a consistency check |

Both directions of mismatch (stale terminal status with no supporting cross-reference, or unflipped status despite supporting cross-reference) are reported. Reporting is non-mutating — no file is changed automatically.

## Cross-references

- **Universal frontmatter rules:** `./frontmatter-universals.md` — `type:` field, ids, path-reference format, dates, empty collections, relationships, unknown fields, status writers, structural relationship fields table.
- **Per-type field tables:** the `## Frontmatter` section of each `./<type>-authoring.md`.
