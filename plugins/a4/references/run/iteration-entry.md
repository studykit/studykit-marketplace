# Run Iteration Entry

Skill-specific addendum on top of `../iterate-mechanics.md`. Read that file first.

## Backlog filter

Open review items where:

- `target: task/*`, OR
- `target: roadmap` (typically `source: test-runner` from the prior cycle).

## Run-specific work between writer calls

- **Cycle counter** — task `cycle:` increments at every revise → re-run pass; the `<log>` entry cites the cycle number.
- **Cascade reset** — when a task is reset to `pending` for re-implementation, every downstream task whose `depends_on` traces back to it also resets to `pending` and gets a `<log>` entry.
- **Crash hygiene at session start** — see `./resume-hygiene.md`.
- **Merge-sweep retry** — for tasks left at `failing` because the merge sweep hit a conflict, the preserved worktree branch is the user's resolution surface. After the user resolves, `/a4:run iterate` re-attempts `git merge --no-ff` on that branch from local main; on success it transitions the task to `complete` and runs the standard 3-step worktree cleanup. If the user instead discards the work, the task drops back to `pending` and the next cycle re-spawns a fresh worktree.
- **Stop on strong upstream** — `target: architecture` and `target: usecase/*` findings halt the run and route to `/a4:arch iterate` or `/a4:usecase iterate` per `../wiki-authorship.md` §Cross-stage feedback. The full classification table is at `../../skills/run/references/failure-classification.md`.
