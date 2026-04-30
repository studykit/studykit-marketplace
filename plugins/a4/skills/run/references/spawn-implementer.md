# Step 2: Spawn task-implementer

For each ready task, spawn one agent **with worktree isolation** (omit `isolation: "worktree"` only in `serial` mode):

```
Agent(subagent_type: "a4:task-implementer", isolation: "worktree", prompt: """
Task file: <absolute path to a4/<type>/<id>-<slug>.md, where <type> ∈ {task, bug, spike, research}>
Bootstrap file: <absolute path to a4/bootstrap.md>  # single source of truth for L&V
Architecture file: <absolute path to a4/architecture.md>
Relevant UC files: <paths referenced by the task's implements:; empty list when implements: is empty>

Read the task file for ## Description, ## Files, ## Unit Test Strategy, ## Acceptance Criteria.
Pull build + unit-test commands from bootstrap.md's ## Verify section.

Implement the task and write its unit tests. All unit tests must pass.
Commit code + unit tests (one commit per task) using subject form
  #<task-id> <type>(a4): <description>
per ${CLAUDE_PLUGIN_ROOT}/references/commit-message-convention.md.
Return: result (pass/fail), summary of changes, any issues encountered.
""")
```

## Status flips around the agent call

Before spawning, flip the task via the writer:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/transition_status.py" \
  "$(git rev-parse --show-toplevel)/a4" \
  --file "<type>/<id>-<slug>.md" --to progress \
  --reason "/a4:run Step 2 spawning task-implementer"
```

Parse each Agent return value's trailing 3 lines (`agentId:`, `worktreePath:`, `worktreeBranch:`) and record `{taskId → agentId, worktreePath, worktreeBranch}` in-memory for Step 2.5. After the agent returns, call the writer with `--to complete` or `--to failing` based on the return value (include a `--reason` naming the cycle and outcome). Do not hand-edit `status:` / `updated:` — the writer owns them.

The agent commits in its current working tree, which is transparently the worktree — the agent does not need to know it is isolated. Worktree return-value shape, branch naming, and cleanup commands live in `./parallel-isolation.md`.
