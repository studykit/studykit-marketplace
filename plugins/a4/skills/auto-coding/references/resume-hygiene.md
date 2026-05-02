# Resume Hygiene

At session start, for every task with `status: progress`, edit the frontmatter `status:` from `progress` to `pending` directly (a `progress` status at session-start means the prior session crashed mid-work). The PostToolUse cascade hook refreshes `updated:` automatically.

## Orphaned worktrees

Parallel mode only — serial mode creates no worktrees.

Orphaned worktrees under `<repo>/.claude/worktrees/agent-*/` (created by an agent that crashed or was interrupted before the merge sweep) are **not** swept by `/a4:auto-coding`. Claude Code's startup sweep removes them automatically once they are older than `cleanupPeriodDays` and have no uncommitted changes / untracked files / unpushed commits. Worktrees preserved by the merge-sweep partial-progress rule (failing-task worktrees) are exempt because they hold uncommitted resolution work.
