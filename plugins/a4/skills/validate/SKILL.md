---
name: validate
description: "Validate a4 workspace frontmatter and status consistency."
argument-hint: "[file ...] [--only <list>] [--skip <list>] [--fix [--dry-run]] [--json]"
disable-model-invocation: true
allowed-tools: Bash, Read
---

# Workspace Validation (a4 plugin)

Runs the registered checks in `markdown_validator.registry.CHECKS` through the unified `validate.py` entrypoint. Two checks ship today:

- **frontmatter** — required fields, enum values, field types, path-reference format (plain string, no brackets, no `.md`), `type:` matches wiki basename, global id uniqueness across issue folders, post-draft authoring invariants (UC `actors:` non-empty at `status >= ready`; `title:` free of placeholders at UC `>= ready` / spec `>= active`). Canonical contract: `${CLAUDE_PLUGIN_ROOT}/authoring/frontmatter-common.md` (universal rules including title placeholders) and per-type field tables in `${CLAUDE_PLUGIN_ROOT}/authoring/<type>-authoring.md`.
- **status** — cross-file status consistency. Flags specs / usecases where `status = superseded` disagrees with which file actually declares `supersedes:`, ideas / brainstorms where `status = promoted` disagrees with the `promoted:` list, and tasks / reviews that did not cascade off a discarded UC. Cascade behavior is documented in `${CLAUDE_PLUGIN_ROOT}/authoring/frontmatter-common.md § Status changes and cascades` and per-type lifecycle sections.

Body shape (heading form, blank-line discipline, link form) lives in `${CLAUDE_PLUGIN_ROOT}/authoring/body-conventions.md`. Issue-only body sections (`## Resume`, `## Log`) live in `${CLAUDE_PLUGIN_ROOT}/authoring/issue-body.md`; wiki-only body sections (`## Change Logs`, Wiki Update Protocol) live in `${CLAUDE_PLUGIN_ROOT}/authoring/wiki-body.md`. Per-type required vs optional section lists live in the per-type authoring contracts under `${CLAUDE_PLUGIN_ROOT}/authoring/`. There is no runtime body validator — body shape is documentation-only.

Invocation: `/a4:validate [file ...] [--only <list>] [--skip <list>] [--fix [--dry-run]] [--json]`.

- No file args — every enabled check runs in workspace mode.
- One or more file paths — file-scope-capable checks restrict to those files (frontmatter validates each file; status walks each file's connected component). Workspace-only checks are skipped silently.
- `--only A,B` runs only the named checks; `--skip A` runs every check except those named. The list of registered checks is `validate.py --list-checks`.
- `--fix` (workspace-only — incompatible with file args) runs the **supersedes-chain recovery sweep** before reporting checks. The sweep walks usecase @ `shipped` and spec @ `active` files carrying `supersedes:` and flips same-family predecessors to `superseded`. Idempotent. Combine with `--dry-run` to preview without writing. Use this when edits bypassed the PostToolUse cascade hook (manual `git checkout`, external editors, scripts that wrote frontmatter directly). Reverse-link cascades (revising / discarded) are not part of `--fix` — preview them with `search.py --references <ref> --references-via implements` and re-edit `status:` to let the hook reapply them.
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
- **One category reports issues** — list them, note the other is clean, and point at the canonical reference doc for the reported class (`frontmatter-common.md` + the relevant `<type>-authoring.md` for frontmatter; `frontmatter-issue.md` § Status changes and cascades + per-type lifecycle sections for status).
- **Multiple categories report issues** — list each labelled set, then: "Fix frontmatter first — consistency checks may resolve in passing once schema issues are fixed (path references and enum values are shared inputs)."

When file arguments are passed, workspace-only checks (none today, but possible in the future) print a `skipped` line; remind the user to re-run the skill workspace-wide before handoff in that case.

### 4. Suggest a follow-up

- For schema and reverse-link issues, do **not** auto-fix. The relevant `/a4:*` iteration skill owns the fix.
- If many violations cluster under a single file, suggest the iteration skill that owns that file (`/a4:usecase iterate`, `/a4:arch iterate`, `/a4:breakdown iterate`) to drive the fix through normal review-item flow.
- For id uniqueness violations, recommend assigning a fresh workspace id when renaming — never hand-pick or reuse an id.
- For status mismatches that look like missed `superseded` flips on a supersedes chain, suggest re-running with `--fix` (or `--fix --dry-run` first) to apply the recovery sweep.

## Non-Goals

- Do not fix anything other than the supersedes-chain recovery sweep enabled by `--fix`. Schema, reverse-link, and transition issues stay the user's / iteration skill's job.
- Do not commit anything. The recovery sweep writes files in place; the user owns the commit.
- Do not invoke this skill autonomously. It is user-triggered; iteration skills and bulk-generation skills do not need to call it.
