---
name: validate
description: "This skill should be used when the user explicitly invokes /validate inside a project that uses the a4 plugin's a4/ workflow. Runs the shared frontmatter and body-convention validators against the project's a4/ workspace and reports any schema or Obsidian-convention violations. Useful before handoff or after manual edits to surface issues the drift detector does not cover."
argument-hint: "[file] [--json]"
disable-model-invocation: true
allowed-tools: Bash, Read
---

# Workspace Validation (a4 plugin)

Runs three category validators against `<project-root>/a4/` through a single aggregator `validate.py`:

- **frontmatter** — required fields, enum values, field types, path-reference format (plain string, no brackets, no `.md`), wiki-kind basename match, `wiki_impact` names a known wiki kind, global id uniqueness across issue folders. Canonical schema: `plugins/a4/references/frontmatter-schema.md`.
- **body** — footnote definition shape (`[^N]: YYYY-MM-DD — [[target]]`, U+2014 em dash), footnote label monotonicity starting at 1, footnote payload is never a `review/*` item, every body wikilink resolves. Canonical rules: `plugins/a4/references/obsidian-conventions.md`.
- **status consistency** — cross-file status consistency. Flags decisions where `status = superseded` disagrees with which file actually declares `supersedes:`, and ideas / spark brainstorms where `status = promoted` disagrees with the `promoted:` list. Workspace-only — skipped in single-file mode. Rules: `plugins/a4/references/frontmatter-schema.md §Cross-file status consistency`.

The three categories cover **different** inconsistencies than `/a4:drift`:

| Check | Owner |
|-------|-------|
| close-guard / missing-wiki-page / stale-footnote / orphan-marker / orphan-definition | `/a4:drift` (cross-session wiki↔issue drift) |
| Frontmatter schema, id uniqueness, path format | `/a4:validate` (this skill) |
| Footnote shape, wikilink resolution, monotonicity | `/a4:validate` (this skill) |
| Cross-file status consistency (`superseded`, `promoted`) | `/a4:validate` (this skill) |

Invocation: `/a4:validate [file] [--json]`. With a file path, the per-file categories check only that file; cross-file status consistency is skipped because it is a global property of the workspace. With `--json`, the aggregator emits a single combined structured report to stdout.

Per-category CLI entrypoints (`validate_frontmatter.py`, `validate_body.py`, `validate_status_consistency.py`) remain available and unchanged — use them directly when you want a single class of check.

## Context

- Project root: !`git rev-parse --show-toplevel 2>/dev/null || echo NOT_A_GIT_REPO`

If the project root resolved to `NOT_A_GIT_REPO`, abort with a clear message. The validators are workspace-scoped and keyed off the git worktree root.

## Task

### 1. Verify the workspace exists

Check that `<project-root>/a4/` exists and is a directory. If not, tell the user that no `a4/` workspace was found and stop — there is nothing to validate.

### 2. Run the aggregator

Pass `$ARGUMENTS` straight through so callers can use `[file]` and `--json` without the skill needing to parse each flag:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/validate.py" \
    "<project-root>/a4" $ARGUMENTS
```

Exit code 0 when no violations across all categories, 2 when any category reports violations, 1 for usage errors (missing workspace, file not inside workspace). Capture both stdout and stderr — human-readable violation bodies are on stderr; category section headers (`=== frontmatter ===` / `=== body ===` / `=== status consistency ===`) and `OK` lines are on stdout; `--json` output goes entirely to stdout.

### 3. Surface the result

Relay the aggregator's output verbatim — the section labels are already present. Do **not** suppress one category because another succeeded; users need the full picture in one pass.

Report the aggregate status as one of:

- **All clean** — "OK — frontmatter, body, and status-consistency validators report no violations."
- **Only one reports violations** — list them, note the others are clean, and point at the canonical reference doc for the reported class (frontmatter-schema, obsidian-conventions, or frontmatter-schema §Cross-file status consistency).
- **Multiple report violations** — list each labelled set, then: "Fix frontmatter first — body and consistency checks may resolve in passing once schema issues are fixed (path references and enum values are shared inputs)."

Single-file mode adds one nuance: the consistency check was skipped (the aggregator emits this explicitly); remind the user to re-run the skill workspace-wide before handoff.

### 4. Suggest a follow-up

- Do **not** auto-fix. Validators are read-only; the user or the relevant `/a4:*` iteration skill owns the fix.
- If many violations cluster under a single file, suggest the iteration skill that owns that file (`/a4:usecase iterate`, `/a4:arch iterate`, `/a4:roadmap iterate`) to drive the fix through normal review-item flow.
- For id uniqueness violations, recommend using `plugins/a4/scripts/allocate_id.py` when renaming — never hand-pick an id.

## Non-Goals

- Do not fix violations here. The skill only reports; the user or an iteration skill fixes.
- Do not run the drift detector. `/a4:drift` covers a different class of inconsistency (cross-session wiki↔issue drift); running both is the user's choice.
- Do not commit anything. Validators are read-only.
- Do not invoke this skill autonomously. It is user-triggered; iteration skills and bulk-generation skills do not need to call it.
