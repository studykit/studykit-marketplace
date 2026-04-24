---
name: validate
description: "This skill should be used when the user explicitly invokes /validate inside a project that uses the a4 plugin's a4/ workflow. Runs the shared frontmatter and body-convention validators against the project's a4/ workspace and reports any schema or Obsidian-convention violations. Useful before handoff or after manual edits to surface issues the drift detector does not cover."
argument-hint: "[file] [--json]"
disable-model-invocation: true
allowed-tools: Bash, Read
---

# Workspace Validation (a4 plugin)

Runs two validators against `<project-root>/a4/`:

- `validate_frontmatter.py` — required fields, enum values, field types, path-reference format (plain string, no brackets, no `.md`), wiki-kind basename match, `wiki_impact` names a known wiki kind, global id uniqueness across issue folders. Canonical schema: `plugins/a4/references/frontmatter-schema.md`.
- `validate_body.py` — footnote definition shape (`[^N]: YYYY-MM-DD — [[target]]`, U+2014 em dash), footnote label monotonicity starting at 1, footnote payload is never a `review/*` item, every body wikilink resolves. Canonical rules: `plugins/a4/references/obsidian-conventions.md`.

The two validators cover **different** inconsistencies than `/a4:drift`:

| Check | Owner |
|-------|-------|
| close-guard / missing-wiki-page / stale-footnote / orphan-marker / orphan-definition | `/a4:drift` (cross-session wiki↔issue drift) |
| Frontmatter schema, id uniqueness, path format | `/a4:validate` (this skill) |
| Footnote shape, wikilink resolution, monotonicity | `/a4:validate` (this skill) |

Invocation: `/a4:validate [file] [--json]`. With a file path, only that single file is validated. With `--json`, each validator emits structured JSON to stdout instead of the default human-readable output.

## Context

- Project root: !`git rev-parse --show-toplevel 2>/dev/null || echo NOT_A_GIT_REPO`

If the project root resolved to `NOT_A_GIT_REPO`, abort with a clear message. The validators are workspace-scoped and keyed off the git worktree root.

## Task

### 1. Verify the workspace exists

Check that `<project-root>/a4/` exists and is a directory. If not, tell the user that no `a4/` workspace was found and stop — there is nothing to validate.

### 2. Run the frontmatter validator

Pass `$ARGUMENTS` straight through so callers can use `[file]` and `--json` without the skill needing to parse each flag:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/validate_frontmatter.py" \
    "<project-root>/a4" $ARGUMENTS
```

Exit code 0 when no violations, 2 when violations found, 1 for usage errors. Capture both stdout and stderr — human-readable output is on stderr when violations exist, stdout for `OK`; `--json` output goes to stdout regardless.

### 3. Run the body validator

Same argument passthrough:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/validate_body.py" \
    "<project-root>/a4" $ARGUMENTS
```

Same exit-code and stream conventions as step 2.

### 4. Surface the combined result

Relay each validator's output verbatim, clearly labelled (e.g., `=== frontmatter ===` / `=== body ===`). Do **not** suppress one set because the other succeeded — users need the full picture in one pass.

Report the aggregate status as one of:

- **Both clean** — "OK — frontmatter and body validators report no violations."
- **Frontmatter violations only** — list them, then: "Body validator is clean. Fix the frontmatter issues above; they block schema-dependent tooling (dataview queries, id allocator, drift detector)."
- **Body violations only** — list them, then: "Frontmatter is clean. Fix the body issues above; most block Obsidian rendering or wikilink navigation."
- **Both have violations** — list each set, then: "Fix frontmatter first — body checks that depend on frontmatter paths may be cleaner after schema issues are resolved."

### 5. Suggest a follow-up

- Do **not** auto-fix. Validators are read-only; the user or the relevant `/a4:*` iteration skill owns the fix.
- If many violations cluster under a single file, suggest the iteration skill that owns that file (`/a4:usecase iterate`, `/a4:arch iterate`, `/a4:plan iterate`) to drive the fix through normal review-item flow.
- For id uniqueness violations, recommend using `plugins/a4/scripts/allocate_id.py` when renaming — never hand-pick an id.

## Non-Goals

- Do not fix violations here. The skill only reports; the user or an iteration skill fixes.
- Do not run the drift detector. `/a4:drift` covers a different class of inconsistency (cross-session wiki↔issue drift); running both is the user's choice.
- Do not regenerate `a4/INDEX.md`. `/a4:index` and `/a4:compass` own that.
- Do not commit anything. Validators are read-only.
- Do not invoke this skill autonomously. It is user-triggered; iteration skills and bulk-generation skills do not need to call it.
