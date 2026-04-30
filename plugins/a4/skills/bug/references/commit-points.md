# bug Commit Points

All commit subjects follow `${CLAUDE_PLUGIN_ROOT}/authoring/commit-message-convention.md`.

## Author mode

Single commit covers the new bug task file. Suggest the commit when the user confirms; do not auto-commit.

```
#<task-id> docs(a4): author bug <slug>
```

## Implement-loop commits

Per-task implementation, per-cycle test results, merge-sweep integration — owned by `/a4:run`.

Never skip hooks, amend, or force-push without explicit user instruction.
