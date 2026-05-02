# Step 2.5: Merge Sweep

**Skipped in `serial` mode** (serial agents commit directly to local main; nothing to integrate).

## Procedure

For each task that returned `pass`, in **ascending `task.id` order**, integrate its worktree branch into local main with a no-fast-forward merge:

```bash
git merge --no-ff -m "#<task-id> merge(a4): integrate <task-slug>" <worktreeBranch>
```

On success, clean up immediately:

```bash
git worktree unlock  <worktreePath>
git worktree remove --force <worktreePath>
git branch -D <worktreeBranch>
```

## On conflict — halt + partial-progress

Per `./parallel-isolation.md`:

- Sibling tasks already merged in this sweep stay on main; they retain `status: complete`.
- The conflicting task's worktree and branch are **preserved** for user diagnosis. Transition the task to `failing` via the writer with `--reason "/a4:run merge conflict in <files>; resolve and re-run /a4:run iterate"`.
- Subsequent siblings in the sweep are **not attempted**; they remain at `progress` until `/a4:run iterate` retries the sweep.
- Do not emit a review item for the conflict — the halt message names the conflicting task and files directly.
- Skip Step 3 entirely; the cycle ends in halt.

Tasks that returned `fail` from Step 2 do not enter the sweep — their worktrees are preserved at the `failing` status from Step 2's writer call, and `/a4:run iterate` re-attempts after the user resolves.
