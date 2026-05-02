# Auto-Coding Iteration Entry

Skill-specific addendum on top of `../../../workflows/iterate-mechanics.md`. Read that file first.

## Backlog filter

Open review items where `target: task/*` / `target: bug/*` / `target: spike/*` / `target: research/*`.

`target: roadmap` is no longer a valid target (the type was retired with the prior `roadmap` skill). Stale items still carrying it should be retargeted at `task/<id>-<slug>` or `architecture` and closed.

## Run-specific work between writer calls

- **Cycle counter** — task `cycle:` increments at every revise → re-run pass; the writer's `--reason` cites the cycle number.
- **Cascade reset** — when a task is reset to `pending` for re-implementation, every downstream task whose `depends_on` traces back to it also resets to `pending`.
- **Crash hygiene at session start** — see `./resume-hygiene.md`.
- **Merge-sweep retry** (parallel mode only) — for tasks left at `failing` because the merge sweep hit a conflict, the preserved worktree branch is the user's resolution surface. After the user resolves, `/a4:auto-coding iterate parallel` re-attempts `git merge --no-ff` on that branch from local main; on success it transitions the task to `complete` and runs the standard 3-step worktree cleanup. If the user instead discards the work, the task drops back to `pending` and the next cycle re-spawns a fresh worktree. Default serial iterate has no merge-sweep step; failing tasks resume by re-spawning the coder on the dirty working tree (user resolves residue first per `./serial-mode.md`).
- **Stop on strong upstream** — `target: architecture` and `target: usecase/*` findings halt the run and route to `/a4:arch iterate` or `/a4:usecase iterate` per `../../../workflows/wiki-authorship.md` §Cross-stage feedback. The full classification table is at `./failure-classification.md`.
