# Step 2: Spawn coder

For each ready task, spawn one `Agent` call with `subagent_type: "a4:coder"` and the prompt envelope below. Mode-specific knobs (the `isolation: "worktree"` parameter, parallel-vs-sequential dispatch, branch base) are routed by `./parallel-mode.md` / `./serial-mode.md`.

```
Agent(subagent_type: "a4:coder", isolation: "worktree", prompt: """
Task file: <absolute path to a4/<type>/<id>-<slug>.md, where <type> ∈ {task, bug, spike, research}>
ci file: <absolute path to a4/ci.md>  # single source of truth for test execution
a4 path: <absolute path to a4/>

Read the task file for ## Description, ## References, ## Interface Contracts, ## Change Plan (if present — path-level scope fence), ## Unit Test Strategy, and ## Acceptance Criteria.
Resolve and read the task's implements:, spec:, related:, ## References, and ## Interface Contracts links before coding.
Pull unit-test commands from ci.md's ## How to run tests section.

Implement the task and write its unit tests. All unit tests must pass.
Commit code + unit tests (one commit per task) using subject form
  #<task-id> <type>(a4): <description>
per ${CLAUDE_PLUGIN_ROOT}/authoring/commit-message-convention.md.
Return: result (pass/fail), summary of changes, any issues encountered.
""")
```

## Status flips around the agent call

Before spawning, flip the task `status:` from `queued` to `progress` by editing the task file's frontmatter directly.

Parse each Agent return value's trailing 3 lines (`agentId:`, `worktreePath:`, `worktreeBranch:`) and record `{taskId → agentId, worktreePath, worktreeBranch}` in-memory for Step 2.5. After the agent returns, edit `status:` to `done` or `failing` based on the return value.

The agent commits in its current working tree, which is transparently the worktree (parallel) or the user's branch (serial) — the agent does not need to know which. Mode-specific details (worktree return-value shape, branch naming, cleanup, sequential dispatch, dirty-tree halt) live in `./parallel-mode.md` and `./serial-mode.md`.
