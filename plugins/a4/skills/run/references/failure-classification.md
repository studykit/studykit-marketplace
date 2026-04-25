# Failure Classification (post-loop review, failure branch)

After the loop body (Steps 1–3) completes with at least one failing test, classify each test-runner review item into one of three categories. Classification is **user-driven** — the SKILL.md transitions to `conversational` and the user picks the category for each finding. The agent loop does not auto-classify.

This document is the routing table the SKILL.md references. Cross-stage stop/continue policy lives in [`plugins/a4/references/wiki-authorship.md`](../../../references/wiki-authorship.md) §Cross-stage feedback — task implementation is contract-bound to `architecture.md` and AC-bound to `usecase/*.md`, so an upstream finding **stops** the run.

## Routing table

| Category | What it means | Action | Routing |
|---|---|---|---|
| **task / roadmap** | Coding error, missing logic, or roadmap-level oversight (task scope wrong, depends_on missing, AC ambiguous within the task body) | Revise the affected task file(s): update Description / Files / Acceptance Criteria / `depends_on`. Reset the task `status: pending`. Increment `cycle:`. Append `## Log` entry citing the review item. Reset transitively-affected downstream tasks to `pending`. Re-run roadmap-reviewer on the revised tasks (single scoped round). If it passes, return to Step 1. | continue (next cycle) |
| **architecture** | Wrong contract, missing component, or test-strategy gap | Update or create the test-runner review item with `target: architecture`. **Stop** the run. Recommend `/a4:arch iterate`. On resume, the new arch-targeted review items drive the fix. | stop, route to `/a4:arch iterate` |
| **usecase** | Ambiguous flow / validation / error handling (only for UC-driven tasks; UC-less tasks cannot produce this) | Retarget the review item to `usecase/<id>-<slug>`. **Stop** the run. Recommend `/a4:usecase iterate`. | stop, route to `/a4:usecase iterate` |

## Cycle bound

If 3 cycles complete and failures remain after each `task / roadmap` revision attempt: halt the run. Mark affected tasks `status: failing`, append `## Log` per failure, leave all test-runner review items `open`. Report the state to the user and transition to `conversational`. The user can resume via `/a4:run iterate` after addressing the underlying issue.

## Status writer reminder

All `status:` and `## Log` mutations on `task/<id>-<slug>.md` go through `scripts/transition_status.py`. Never hand-edit `status:` / `updated:` / `## Log` — the writer owns them.
