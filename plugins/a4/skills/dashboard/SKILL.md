---
name: dashboard
description: "Use when the user invokes /dashboard inside a project that uses the a4 plugin's a4/ workflow. Thin wrapper around `scripts/workspace_state.py`: with no arguments renders the full workspace dashboard (wiki pages, stage progress, issue counts, drift alerts, open reviews, active tasks, blocked items, milestones, recent activity, open ideas, open sparks); pass one or more section identifiers (e.g. `drift-alerts active-tasks`) to filter, or `--list-sections` to enumerate. Output is markdown to stdout — no file is written. Triggers: 'dashboard', 'workspace status', 'show a4 state', 'what's the workspace look like'."
argument-hint: "[--list-sections] [<section> ...]"
disable-model-invocation: true
allowed-tools: Bash
---

Run this command and relay stdout verbatim. The script exits nonzero on missing workspace or unknown section name — surface stderr and stop.

!`ROOT=$(git rev-parse --show-toplevel 2>/dev/null) && uv run "${CLAUDE_PLUGIN_ROOT}/scripts/workspace_state.py" "$ROOT/a4" $ARGUMENTS`

