# Agent Reuse Guide

When the same agent type needs to be invoked multiple times within a session, offer the user a choice between reusing the existing agent (preserving prior context) or spawning a fresh one.

## When This Applies

- A subagent of the same type was already spawned earlier in the current session
- The new task is related to the previous one (e.g., re-reviewing after revisions, follow-up exploration)

## Pattern

### First Invocation

Always assign a `name` when spawning:

```
Agent(subagent_type: "usecase-reviewer", name: "reviewer")
```

Record the returned agent ID internally for potential reuse.

### Subsequent Invocations

Before launching a new agent of the same type, ask the user:

> The previous **usecase-reviewer** agent still has context from the last review.
> - **Reuse** — send the new task to the existing agent (it remembers prior findings)
> - **Fresh** — spawn a new agent (clean slate, no prior context)
>
> Which do you prefer?

- **Reuse** — use `SendMessage(to: <agent-id>)` with the new task prompt. The agent retains its full prior transcript.
- **Fresh** — spawn a new `Agent(subagent_type: "...", name: "...")`.

### Prompt for Reused Agent

When sending a follow-up task via SendMessage, always include the full file paths (working file, source files, report output path) — the same paths a fresh agent would receive. The agent's context window retains prior findings, but file paths may change between invocations (e.g., report label increments per revision). Also state what changed since the last invocation:

> **Follow-up review request.**
> Working file: `<path>`
> Source files: `<paths>`
> Report path: `<report-path>`
>
> The working file has been updated since your last review. Changes:
> - UC-3 situation revised (was vague, now concrete)
> - UC-5 added (new use case from exploration)
>
> Focus on whether your prior findings have been addressed, plus evaluate the new content.

## Trade-offs

| | Reuse (SendMessage) | Fresh (new Agent) |
|---|---|---|
| **Prior context** | Retained — agent remembers its own findings | None — must pass previous report paths for continuity |
| **Judgment quality** | Better continuity on "was this fixed?" checks | Unbiased fresh evaluation |
| **Context window** | Grows with each reuse — may degrade on long sessions | Clean context each time |
| **Best for** | Iterative review-revise cycles within one session | First review, or when a clean perspective is needed |

## Default Recommendation

For most iterative workflows (review → revise → re-review), **reuse** is the better default — suggest it first but let the user decide.
