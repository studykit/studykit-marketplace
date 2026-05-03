# /a4:auto-coding Parallel Mode

Procedure for `/a4:auto-coding` Step 2 parallel execution and the merge sweep that integrates the resulting worktree branches. The default serial mode (no extra argument) is documented separately in `./serial-mode.md`.

Commit message form for the merge commits is governed by `${CLAUDE_PLUGIN_ROOT}/authoring/commit-message-convention.md`.

## When to use

Opt-in via `/a4:auto-coding parallel` or `/a4:auto-coding iterate parallel`.

Use parallel mode when the repo has `origin/HEAD` and the user wants worktree-isolated coders to run in parallel for speed. Independent ready tasks dispatch concurrently; mutually-dependent tasks still run sequentially per the dependency graph. Pre-flight requires `HEAD == origin/HEAD` because worktrees branch from `origin/HEAD`; see the body §Agent tool return value for rationale.

Halts immediately when `origin/HEAD` is missing or the pre-flight check fails — no auto-fall-back. Drop the `parallel` arg to use the default serial path instead.

## Decisions

| Aspect | Rule |
|---|---|
| Isolation | `Agent({ isolation: "worktree" })` per `coder`; one worktree per parallel ready task |
| Pre-flight | At Step 1 entry, halt if local `HEAD ≠ origin/HEAD`. User pushes (or runs `git remote set-head origin -a`) before re-invoking. Rationale: see body §Agent tool return value |
| Merge primitive | `git merge --no-ff -m "<conv-msg>"` per task branch — preserves task-commit hash, marks integration boundary, supports `git log --first-parent` traversal |
| Merge order | Ascending `task.id` (deterministic, reproducible across re-runs) |
| Conflict policy | Halt + user resolve. No review item emitted (merge conflicts are immediate-decision items, not artifact-spec gaps) |
| Partial-progress unit | Siblings merged before the conflict stay on main + transition `→ done`; conflicting task's worktree/branch preserved + transition `→ failing`; subsequent siblings not attempted |
| `test-runner` invariant | Step 3 is reachable only when every cycle ready task is integrated. Any merge sweep failure → Step 3 skipped, cycle ends in halt |
| Worktree cleanup (success) | `git worktree unlock <path> && git worktree remove --force <path> && git branch -D <branch>` |
| Worktree cleanup (failure) | Worktree + branch preserved for diagnosis. `/a4:auto-coding iterate parallel` may retry the merge after the user resolves; orphans handled by Claude Code's startup sweep at `cleanupPeriodDays` |
| Branch-to-task mapping | In-memory `{taskId, agentId, worktreePath, worktreeBranch}` per task. Parse format: see body §Agent tool return value. Permanent record via `#<id>` in the merge commit subject |
| `.gitignore` | Projects should add `.claude/worktrees/` to `.gitignore`. Recommendation, not enforced |

## Agent tool return value

Each `Agent({ isolation: "worktree" })` result appends three structured lines after the agent's body output:

```
agentId: <hex>
worktreePath: <absolute path>
worktreeBranch: <branch name>
```

Worktree path: `<repo>/.claude/worktrees/agent-<hex>/`. Branch name: `worktree-agent-<hex>`. Base ref: `origin/HEAD` (not local HEAD — hence the pre-flight check). The `<hex>` portion equals the agentId.

The Agent tool locks the worktree for the duration of the run, so cleanup requires `unlock` before `remove`. `--force` covers any residual untracked content. Agents that make no changes are auto-cleaned by the Agent tool itself; agents that produce changes leave the worktree for the caller to handle.
