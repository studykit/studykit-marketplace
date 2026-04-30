# Step 4: Post-loop Review (user-driven)

Once the loop body settles, **transition to `conversational`** and branch on outcome. There are exactly two branches and they are mutually exclusive on a single run:

- **4a. Failure path** — at least one test-runner review item from Step 3 is open. The user classifies each finding and the run routes accordingly.
- **4b. Ship path** — all tests passed AND all in-scope tasks reached `status: complete`. The user confirms `implementing → shipped` per candidate UC.

Both branches are user-driven. No agent classifies failures or auto-ships UCs. The loop body's autonomy ends at the seam into Step 4.

This skill follows the **stop on strong upstream dependency** policy at `../../../workflows/wiki-authorship.md` §Cross-stage feedback — task implementation is contract-bound to `architecture.md` and AC-bound to `usecase/*.md`, so an upstream finding halts the run rather than retrying against stale assumptions.

## 4a. Failure path — classify findings

For each open test-runner review item, the user picks one of three categories: **task / roadmap**, **architecture**, or **usecase**. Routing per category — including cascade rules, cycle-counter increments, and direct status edits — is in `./failure-classification.md`.

Cycle bound: if 3 cycles complete and failures remain, halt as described in that reference.

## 4b. Ship path — confirm UCs to ship

For each ship-candidate UC, compose a short verdict and ask the user `mark shipped?`. Per-UC candidate rules, verdict template, defer protocol, and the direct-edit ship procedure are in `./uc-ship-review.md`.

The ship unit varies by **pipeline shape** (see `../../../workflows/pipeline-shapes.md`). Per-task vs per-UC ship is `task.implements:`-driven, not invocation-driven:

- **Per-UC ship** — when `task.implements:` is non-empty (Full shape, or Minimal-task-with-UC). Multiple tasks shipping their target UC's full Flow flip the UC `implementing → shipped`.
- **Per-task ship** — when `task.implements:` is empty (Minimal shape's bug / spike / spec-justified task). Each task transitions to `complete` independently and 4b skips UC bookkeeping entirely. That is the normal case for those shapes, not an error.

A run can mix both unit types in one invocation (e.g., a UC-driven task and a spec-justified bug fix shipping in the same cycle); each task's `implements:` field decides which branch its ship verdict takes.

Leftover `implementing` UCs (user deferred on one or more) stay that way; the next `/a4:run iterate` session will re-offer them.

After 4b finishes (or 4a routes the run elsewhere), proceed to wrap-up.
