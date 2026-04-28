# Resume Hygiene

At session start, for every task with `status: progress`, reset to `pending` via the writer (a `progress` status at session-start means the prior session crashed mid-work):

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/transition_status.py" \
  "$(git rev-parse --show-toplevel)/a4" \
  --file "task/<kind>/<id>-<slug>.md" --to pending \
  --reason "session-start hygiene: previous session terminated"
```

`scripts/refresh_implemented_by.py` runs automatically via the `scripts/a4_hook.py session-start` SessionStart hook (see `hooks/hooks.json`) to catch task-file changes that happened on other branches.

## Orphaned worktrees

Orphaned worktrees under `<repo>/.claude/worktrees/agent-*/` (created by an agent that crashed or was interrupted before the merge sweep) are **not** swept by `/a4:run`. Claude Code's startup sweep removes them automatically once they are older than `cleanupPeriodDays` and have no uncommitted changes / untracked files / unpushed commits. Worktrees preserved by the merge-sweep partial-progress rule (failing-task worktrees) are exempt because they hold uncommitted resolution work.
