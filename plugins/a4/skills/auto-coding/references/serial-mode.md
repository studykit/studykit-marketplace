# /a4:auto-coding Serial Mode

Sequential, no-isolation execution path for `/a4:auto-coding`. Covers Steps 1–3 specialization that differs from parallel mode (`./parallel-mode.md`).

The coder agent contract (call shape, prompt envelope, status flips around the call) is shared with parallel mode — see `./spawn-coder.md`. Mode-specific deltas are tabulated below.

## When to use

Default — invoked by `/a4:auto-coding` or `/a4:auto-coding iterate` (no extra argument).

Works in any repo regardless of remote configuration. Parallel mode (opt-in via the `parallel` arg) is the alternative for users with `origin/HEAD` who want worktree-isolated parallel coders for speed; see `./parallel-mode.md`.

A single `/a4:auto-coding` invocation runs in one mode end-to-end — no in-cycle mode switch.

## Decisions

| Aspect | Rule |
|---|---|
| Pre-flight | **Skipped.** No `HEAD == origin/HEAD` check — no remote dependency |
| Step 1 ready-set | Same definition as parallel mode. Independent-task parallelism is moot (see Step 2) |
| Step 2 spawn | Drop `isolation: "worktree"` from the call in `./spawn-coder.md`. Tasks spawn **sequentially** in ascending `task.id` order — no parallel coders, even when the dependency graph would allow it |
| Working tree | Each coder runs in the repo's main working tree on the user's current branch. Commits land directly on that branch — no separate base ref, no branch-to-task mapping |
| Step 2.5 merge sweep | Skipped — see `./merge-sweep.md` (parallel-only) |
| Coder failure | If the agent halted before committing or resetting, the working tree may be left dirty. Transition the task to `failing` and surface dirty paths in the halt message. User resolves (`git stash` / `git reset` / commit-as-wip) before re-invoking `/a4:auto-coding iterate`. Subsequent ready tasks in the cycle are **not attempted** after the first halt |
| Step 3 invariant | Reachable only when every cycle ready task committed without halt. No merge-sweep failure path exists |
| Resume hygiene | Only the standard `progress → queued` session-start reset applies. `holding` tasks are not touched by resume hygiene. No orphan-worktree handling (none are created) |
| Worktree cleanup | N/A |

## Mode mixing

`/a4:auto-coding iterate` (default serial) may follow a prior `/a4:auto-coding parallel` session **only when** no failing-task worktrees were preserved by the parallel-mode partial-progress rule. If any are present:

- resolve them in parallel mode (`/a4:auto-coding iterate parallel`) first, OR
- remove them manually (`git worktree remove --force <path> && git branch -D <branch>`) before switching.
