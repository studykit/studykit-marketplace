# breakdown Commit Points

All commit subjects follow `../../../authoring/commit-message-convention.md`.

## Task batch derivation

Commit all new `a4/task/*.md` files together once the user confirms.

```
#<task-ids> docs(a4): derive tasks from <upstream-summary>
```

(The description names the upstream sources or feature scope, not the file count.)

## Drift review (optional)

When Step 4 emits an arch-drift review item, commit it together with the task batch (drift was discovered during the same derivation step):

```
#<task-ids> #<drift-review-id> docs(a4): derive tasks from <upstream-summary> + arch drift review
```

## Task revision during verification

Commit revised task files + resolved review items as one commit per review round:

```
#<task-ids> #<resolved-review-ids> docs(a4): revise tasks for review round <N>
```

## Implement-loop commits

Per-task implementation, per-cycle test results, merge-sweep integration, UC ship-transitions are owned by `/a4:auto-coding`.

Never skip hooks, amend, or force-push without explicit user instruction.
