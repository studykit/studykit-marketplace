# research Commit Points

## Author mode

Single commit covers the new research task file. Suggest the commit when the user confirms; do not auto-commit.

```
#<task-id> docs(a4): author research <slug>
```

## Investigation commits

Body fills (sources consulted, findings, options) typically land as separate dated commits with messages naming the research task id. `/a4:research-review` runs against the body before final `→ done`.

Never skip hooks, amend, or force-push without explicit user instruction.
