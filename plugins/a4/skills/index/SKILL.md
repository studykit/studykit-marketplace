---
name: index
description: "This skill should be used when the user explicitly invokes /index inside a project that uses the a4 plugin's a4/ workflow. Regenerates a4/INDEX.md — the workspace dashboard of wiki pages, stage progress, open issues, drift alerts, milestones, recent activity, and open sparks. Useful mid-session after a batch of issue edits, or when the user wants a fresh snapshot without running the full /a4:compass flow."
argument-hint: "[--dry-run]"
disable-model-invocation: true
allowed-tools: Bash, Read
---

# Workspace Index Refresh (a4 plugin)

Regenerates `<project-root>/a4/INDEX.md` from current workspace state. The INDEX is a **view** — per-item frontmatter in `a4/` remains the source of truth. Each section contains an Obsidian dataview block for live rendering plus a static markdown fallback wrapped in `<!-- static-fallback-start: X -->` / `<!-- static-fallback-end: X -->` markers; the static portion is a snapshot as of the moment this skill ran.

Invocation: `/a4:index [--dry-run]`. With `--dry-run`, the rendered content is printed to stdout and `a4/INDEX.md` is not touched — useful for previewing changes before committing.

## Context

- Project root: !`git rev-parse --show-toplevel 2>/dev/null || echo NOT_A_GIT_REPO`

If the project root resolved to `NOT_A_GIT_REPO`, abort with a clear message. The script is workspace-scoped and keyed off the git worktree root.

## Task

### 1. Verify the workspace exists

Check that `<project-root>/a4/` exists and is a directory. If not, tell the user that no `a4/` workspace was found and stop — there is nothing to index.

### 2. Run the refresher

Pass `$ARGUMENTS` straight through to the script so callers can use `--dry-run` or `--stdout` without the skill needing to know each flag:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/index_refresh.py" \
    "<project-root>/a4" $ARGUMENTS
```

The script always fully regenerates `a4/INDEX.md` — both dataview query blocks (fixed literal text) and static fallback tables (computed fresh). Exit code 0 on success.

### 3. Surface the result

- **Default run** — relay the script's stdout verbatim (`Wrote <path>`). Do not read INDEX.md back to summarize unless the user asks; the file is a dashboard meant to be viewed directly.
- **`--dry-run`** — the script's stdout is the full rendered content. If it is long, offer to write it when the user confirms.

### 4. Suggest a follow-up

- The skill does **not** commit. INDEX.md lands in the working tree; the user (or the next session-closing of a a4 skill) sweeps it up.
- If the dashboard shows open drift alerts, mention that `/a4:drift` will not help (drift alerts are already emitted review items) — the next applicable `/a4:usecase`, `/a4:arch`, or `/a4:plan` iteration resolves them.

## Sections produced

| Section | Dataview | Static fallback |
|---------|----------|-----------------|
| Wiki pages | query over `a4/*.md` where `kind:` is set | table of the 7 wiki kinds, presence + last-updated |
| Stage progress | *(none — cross-folder aggregate)* | table of Usecase / Arch / Bootstrap / Plan / Impl state |
| Open issues | grouped query over issue folders | per-type open / in-progress / terminal / total |
| Drift alerts (N) | query over `review/*.md` where `source: drift-detector` and status open/in-progress | table listing each alert's wiki target, priority, status |
| Milestones | group tasks by `milestone:` field | tasks complete / total, open reviews per milestone |
| Recent activity | top 10 by `updated` descending across all issue folders | same list as static table |
| Spark (open N) | `a4/spark/*.md` where status is missing or `open` | bullet list with flavor (brainstorm/decide) |

Stage progress is static-only because it mixes wiki-page presence (single-file checks) with cross-folder issue aggregates; a single dataview block cannot express both cleanly.

## Non-Goals

- Do not commit INDEX.md. Leave it in the working tree.
- Do not edit `a4/` content other than `INDEX.md`. The refresher reads frontmatter only.
- Do not merge into surgical sections. The script overwrites the whole file every run; manual edits to INDEX.md will be lost on the next `/a4:compass` or `/a4:index` invocation.
