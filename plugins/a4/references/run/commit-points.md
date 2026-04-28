# run Commit Points

All commit subjects follow `../commit-message-convention.md`.

## Per-task implementation

`task-implementer` commits its own code + unit tests per task as `#<task-id> <type>(a4): <description>` (`feat` / `fix` per task kind). `/a4:run` does not also commit those files.

## Per-task integration (Step 2.5, parallel mode only)

```
git merge --no-ff -m "#<task-id> merge(a4): integrate <task-slug>" <worktreeBranch>
```

Per successfully-implemented task. Serial mode skips this step (task-implementer commits land directly on local main).

## Per-cycle test results

After Step 3, commit the emitted test-runner review items + updated task `<log>` entries as one commit:

```
#<r1> #<r2> ... chore(a4): cycle <N> test-runner findings
```

(Drop the id list when zero findings were emitted; commit the log updates alone as `chore(a4): cycle <N> test-runner clean`.)

## Roadmap revision after test failure

Commit revised task files + status resets + review item linkages as one commit before re-running Step 1:

```
#<task-ids> #<resolved-review-ids> docs(a4): revise tasks for cycle <N> findings
```

## UC ship-transitions (Step 4b)

Commit the UC files confirmed `shipped` together in one commit, separate from task commits. Predecessor UC files auto-flipped to `superseded` by `transition_status.py` are part of the same working-tree change and belong in the same commit:

```
#<uc-id1> [#<uc-id2> ...] docs(a4): ship UC <slug1> [<slug2> ...]
```

## Final state

Commit any residual review items / log updates when the user wraps up:

```
#<id> [#<id> ...] chore(a4): wrap up cycle <N>
```

(ID-less when only ambient log lines changed.)

Never skip hooks, amend, or force-push without explicit user instruction.
