---
name: validate
description: "This skill should be used when the user explicitly invokes /validate inside a project that uses the a4 plugin's a4/ workflow. Runs the registered markdown_validator checks (frontmatter + cross-file status consistency by default) against the project's a4/ workspace and reports any violations. Useful before handoff or after manual edits to surface issues the drift detector does not cover."
argument-hint: "[file ...] [--only <list>] [--skip <list>] [--json]"
disable-model-invocation: true
allowed-tools: Bash, Read
---

# Workspace Validation (a4 plugin)

Runs the registered checks in `markdown_validator.registry.CHECKS` through the unified `validate.py` entrypoint. Two checks ship today:

- **frontmatter** — required fields, enum values, field types, path-reference format (plain string, no brackets, no `.md`), `type:` matches wiki basename, global id uniqueness across issue folders. Canonical schema: `${CLAUDE_PLUGIN_ROOT}/references/frontmatter-schema.md`.
- **status** — cross-file status consistency. Flags specs / usecases where `status = superseded` disagrees with which file actually declares `supersedes:`, ideas / spark brainstorms where `status = promoted` disagrees with the `promoted:` list, and tasks / reviews that did not cascade off a discarded UC. Rules: `${CLAUDE_PLUGIN_ROOT}/references/frontmatter-schema.md §Cross-file status consistency`.

Body shape (section tags, required vs optional sections, blank-line discipline) is documented in `${CLAUDE_PLUGIN_ROOT}/references/body-conventions.md` and the per-type authoring contracts under `${CLAUDE_PLUGIN_ROOT}/references/`. There is no runtime body validator — body shape is documentation-only.

Invocation: `/a4:validate [file ...] [--only <list>] [--skip <list>] [--json]`.

- No file args — every enabled check runs in workspace mode.
- One or more file paths — file-scope-capable checks restrict to those files (frontmatter validates each file; status walks each file's connected component). Workspace-only checks are skipped silently.
- `--only A,B` runs only the named checks; `--skip A` runs every check except those named. The list of registered checks is `validate.py --list-checks`.
- `--json` emits a single combined structured report to stdout for CI / pre-commit consumers.

## Context

- Project root: !`git rev-parse --show-toplevel 2>/dev/null || echo NOT_A_GIT_REPO`

If the project root resolved to `NOT_A_GIT_REPO`, abort with a clear message. The validators are workspace-scoped and keyed off the git worktree root.

## Task

### 1. Verify the workspace exists

Check that `<project-root>/a4/` exists and is a directory. If not, tell the user that no `a4/` workspace was found and stop — there is nothing to validate.

### 2. Run the validator

Pass `$ARGUMENTS` straight through so callers can use file paths and selector flags (`--only`, `--skip`, `--json`) without the skill needing to parse each flag:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/validate.py" \
    "<project-root>/a4" $ARGUMENTS
```

Exit code 0 when every enabled check is clean, 2 when any check reports issues, 1 for usage errors (missing workspace, file not inside workspace, unknown check name in `--only` / `--skip`). Capture both stdout and stderr — human-readable issue bodies are on stderr; category section headers (`=== frontmatter ===` / `=== status ===`) and `OK` lines are on stdout; `--json` output goes entirely to stdout.

### 3. Surface the result

Relay the validator output verbatim — the section labels are already present. Do **not** suppress one category because another succeeded; users need the full picture in one pass.

Report the aggregate status as one of:

- **All clean** — "OK — every enabled check reports no issues."
- **One category reports issues** — list them, note the other is clean, and point at the canonical reference doc for the reported class (frontmatter-schema or frontmatter-schema §Cross-file status consistency).
- **Multiple categories report issues** — list each labelled set, then: "Fix frontmatter first — consistency checks may resolve in passing once schema issues are fixed (path references and enum values are shared inputs)."

When file arguments are passed, workspace-only checks (none today, but possible in the future) print a `skipped` line; remind the user to re-run the skill workspace-wide before handoff in that case.

### 4. Suggest a follow-up

- Do **not** auto-fix. Validators are read-only; the user or the relevant `/a4:*` iteration skill owns the fix.
- If many violations cluster under a single file, suggest the iteration skill that owns that file (`/a4:usecase iterate`, `/a4:arch iterate`, `/a4:roadmap iterate`) to drive the fix through normal review-item flow.
- For id uniqueness violations, recommend using `${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py` when renaming — never hand-pick an id.

## Non-Goals

- Do not fix violations here. The skill only reports; the user or an iteration skill fixes.
- Do not commit anything. Validators are read-only.
- Do not invoke this skill autonomously. It is user-triggered; iteration skills and bulk-generation skills do not need to call it.
