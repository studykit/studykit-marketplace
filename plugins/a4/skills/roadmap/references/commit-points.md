# roadmap Commit Points

All commit subjects follow `../../../references/commit-message-convention.md`.

## Roadmap generation

Commit `a4/roadmap.md` + all new `a4/task/feature/*.md` files + UCs updated by `refresh_implemented_by.py` together once the user confirms.

```
#<uc-ids> #<task-ids> docs(a4): roadmap for <milestone-or-scope>
```

(List the UC ids first, then task ids; the description names the milestone or feature scope, not the file count.)

## Roadmap revision during verification

Commit revised roadmap / task files + resolved review items as one commit per review round.

```
#<task-ids> #<resolved-review-ids> docs(a4): revise roadmap for review round <N>
```

## Implement-loop commits

Per-task implementation, per-cycle test results, merge-sweep integration, UC ship-transitions are owned by `/a4:run`.

Never skip hooks, amend, or force-push without explicit user instruction.
