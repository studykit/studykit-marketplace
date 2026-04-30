# spike Commit Points

All commit subjects follow `${CLAUDE_PLUGIN_ROOT}/references/commit-message-convention.md`.

## Author mode

Single commit covers the new spike task file + the empty `artifacts/spike/<id>-<slug>/` directory (with `.gitkeep` if added). Suggest the commit when the user confirms; do not auto-commit.

```
#<task-id> docs(a4): author spike <slug>
```

## Implement-loop commits

Per-task implementation, per-cycle test results — owned by `/a4:run`.

Never skip hooks, amend, or force-push without explicit user instruction.
