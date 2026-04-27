---
name: dashboard
description: "This skill should be used when the user wants a snapshot of the a4/ workspace state — full dashboard or one or more pre-defined sections. Triggers: 'dashboard', 'workspace status', 'show a4 state', 'what's the workspace look like', 'show drift', 'show active tasks', 'what's blocked', 'milestone progress', 'recent activity', 'open reviews', 'open ideas', 'open sparks', 'wiki pages', 'issue counts', 'stage progress', 'usecase sources'. Translates the user's natural-language request into a single `scripts/workspace_state.py` invocation and surfaces the markdown report. Output is markdown to stdout — no file is written. ROUTING: if the user wants per-item filtering by status / kind / milestone / references / labels / custom field, use `/a4:find` instead. If the user wants to know what to do next, is stuck mid-pipeline, or needs a recommendation rather than just a snapshot, use `/a4:compass` instead."
argument-hint: "[<natural-language section request, or raw section identifiers, or --list-sections>]"
context: fork
model: haiku
allowed-tools: Bash
---

# a4 Workspace Dashboard

Translate the user's request into a single `scripts/workspace_state.py` call and relay its markdown output. With no argument, render the full dashboard.

Argument: **$ARGUMENTS**

## Step 1: Resolve workspace root

```bash
ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
```

If the command fails or `$ROOT/a4/` is not a directory, abort with a clear message — there is no workspace to snapshot.

## Step 2: Build the workspace_state.py invocation

`scripts/workspace_state.py` is the single entry point. Its full surface is documented in its module docstring and via `--list-sections`. Available section identifiers (each renders one markdown section; pass none for the full dashboard):

| Identifier | What it shows |
|------------|---------------|
| `wiki-pages` | presence + last-updated for the 7 canonical wiki kinds |
| `stage-progress` | mixed-axis view of usecase / arch / bootstrap / roadmap / impl |
| `issue-counts` | per folder × {active, in_progress, terminal, total}, plus by-kind for review/task |
| `usecases-by-source` | UC `source:` distribution (Reverse-only detection) |
| `drift-alerts` | open / in-progress reviews with `source: drift-detector`, sorted by priority then id desc |
| `open-reviews` | open / in-progress non-drift reviews, sorted by priority then created then id |
| `active-tasks` | tasks with status in {pending, progress, failing} |
| `blocked-items` | any issue with status: blocked, with depends_on chain |
| `milestones` | per active milestone — tasks complete/total + open reviews |
| `recent-activity` | top 10 issue items by `updated:` desc |
| `open-ideas` | non-terminal `idea/*.md` |
| `open-sparks` | non-terminal `spark/*.md` |

Special flag: `--list-sections` prints the identifiers and exits.

**Translation guide for natural-language requests:**

- empty argument → no flags (full dashboard)
- "show drift" / "any drift" / "drift findings" → `drift-alerts`
- "active tasks" / "what's running" / "what's in progress" → `active-tasks`
- "what's blocked" / "blocked items" → `blocked-items`
- "open reviews" / "review queue" → `open-reviews`
- "milestone progress" / "how is v1.0 going" → `milestones`
- "recent activity" / "what changed lately" / "latest" → `recent-activity`
- "wiki pages" / "wiki status" → `wiki-pages`
- "issue counts" / "how many tasks/reviews/..." → `issue-counts`
- "stage progress" / "where are we in the pipeline" → `stage-progress`
- "open ideas" / "idea backlog" → `open-ideas`
- "open sparks" / "brainstorm backlog" → `open-sparks`
- "usecase sources" / "which UCs came from where" → `usecases-by-source`
- combined requests ("drift and blocked") → multiple identifiers in the requested order: `drift-alerts blocked-items`
- "list sections" / "what sections are there" / "what can dashboard show" → `--list-sections`
- raw identifiers passed directly (e.g. `/a4:dashboard drift-alerts active-tasks`) → pass `$ARGUMENTS` through verbatim

If the request is genuinely ambiguous (e.g. "show me everything important"), default to the full dashboard rather than guessing a subset. If the request asks for per-item search ("find tasks for v1.0", "what implements usecase/3"), do not run dashboard — tell the user to use `/a4:find` instead.

## Step 3: Run the script

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/workspace_state.py" "$ROOT/a4" <translated-args>
```

Surface stdout verbatim. The script exits non-zero on a missing workspace or an unknown section identifier — surface stderr and stop without retrying.

## Step 4: Format the response

The script already returns markdown. Relay it as-is — do not editorialize, summarize, or reorder sections. The dashboard is a snapshot tool; deeper diagnosis lives in `/a4:compass`, per-item search lives in `/a4:find`.

## Notes

- This skill is read-only. It never writes a file or mutates frontmatter.
- For filtering individual items by status / kind / milestone / references / custom frontmatter field, use `/a4:find`.
- For pipeline-state diagnosis and "what should I do next" routing, use `/a4:compass`.
