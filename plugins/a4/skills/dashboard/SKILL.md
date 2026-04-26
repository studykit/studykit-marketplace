---
name: dashboard
description: "This skill should be used when the user explicitly invokes /dashboard inside a project that uses the a4 plugin's a4/ workflow. Renders the workspace dashboard — wiki pages, stage progress, issue counts, drift alerts, open reviews, active tasks, blocked items, milestones, recent activity, open ideas, and open sparks — as a fresh markdown snapshot to stdout. Useful mid-session after a batch of issue edits, or when the user wants a quick overview without running the full /a4:compass flow. Triggers: 'dashboard', 'workspace status', 'show a4 state', 'what's the workspace look like'."
argument-hint: ""
disable-model-invocation: true
allowed-tools: Bash
---

# Workspace Dashboard (a4 plugin)

Surfaces the current state of the `<project-root>/a4/` workspace as a markdown report computed fresh from per-item frontmatter. **No file is written** — the report is printed to stdout for the user to read directly.

Invocation: `/a4:dashboard`.

## Context

- Project root: !`git rev-parse --show-toplevel 2>/dev/null || echo NOT_A_GIT_REPO`

If the project root resolved to `NOT_A_GIT_REPO`, abort with a clear message. The script is workspace-scoped and keyed off the git worktree root.

## Task

### 1. Verify the workspace exists

Check that `<project-root>/a4/` exists and is a directory. If not, tell the user that no `a4/` workspace was found and stop — there is nothing to summarize.

### 2. Render the dashboard

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/workspace_state.py" \
    "<project-root>/a4"
```

Relay the script's stdout verbatim — it is already a complete, user-facing markdown report.

### 3. Suggest a follow-up

- If the report shows open drift alerts, mention that the next applicable `/a4:usecase`, `/a4:arch`, or `/a4:roadmap` iteration resolves them — `/a4:drift` will not help because drift alerts are already emitted as `review/*.md` items.
- If the report shows blocked items with non-empty `depends_on`, point out the nearest unblocked predecessor as a candidate target for `/a4:run` or the relevant iteration skill.
- For a deeper, layered "what should I do next" diagnosis, suggest `/a4:compass` — it consumes the same workspace-state report but routes through gap-diagnosis layers and recommends the next skill to invoke.

## Sections produced

| Section | Source |
|---------|--------|
| Wiki pages | `a4/{context,domain,architecture,actors,nfr,roadmap,bootstrap}.md` frontmatter |
| Stage progress | usecase + task status counts mixed with wiki-page presence |
| Issue counts | per folder × {active, in-progress, terminal, total}; review/task also broken down by `kind` |
| Use cases by source | `usecase/*.md` `source:` distribution |
| Drift alerts (N) | open / in-progress `review/*.md` with `source: drift-detector`, sorted by priority |
| Open reviews (N) | open / in-progress non-drift reviews, sorted by priority then `created` |
| Active tasks (N) | tasks with `status` in `{pending, implementing, failing}` |
| Blocked items (N) | any issue with `status: blocked`, includes `depends_on` chain |
| Milestones | tasks complete / total + open reviews per active milestone |
| Recent activity | top 10 issues by `updated:` desc |
| Open ideas (N) | non-terminal `idea/*.md` |
| Open sparks (N) | non-terminal `spark/*.md` |

The full output schema and section-builder code lives in `plugins/a4/scripts/workspace_state.py`'s module docstring — it is the single source of truth for what this skill (and `/a4:compass` Step 3.2) renders.

## Non-Goals

- Do not write any file. The dashboard is stdout-only — it is regenerated each invocation.
- Do not edit `a4/` content. The script reads frontmatter only.
- Do not commit anything. The skill is read-only.
