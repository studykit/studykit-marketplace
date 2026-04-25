---
title: "/a4:run UC ship-review candidate strictness"
status: draft
decision: "TBD — confirm whether `/a4:run` Step 5's UC ship-review requires *every* implementing task on a UC to be `complete` before that UC becomes a candidate, or whether partial-shipping should be supported."
supersedes: []
related: []
tags: [a4-run, ship-review, usecase-lifecycle]
created: 2026-04-25
updated: 2026-04-25
---

# /a4:run UC ship-review candidate strictness

## Context

`plugins/a4/skills/run/SKILL.md` Step 5 ("UC ship-review (conditional, user-confirmed)") collects shipping candidates with this rule:

> A UC X is a candidate when:
> - X.status is `implementing` (flipped by `task-implementer` at work-start per its protocol).
> - Every task with `implements: [usecase/X]` in its frontmatter now has `status: complete`.
> - No review item with `target: usecase/X` is `open` or `in-progress` (all resolved or discarded).

The middle bullet is strict: **every** task implementing a UC must be `complete` for that UC to become a ship-review candidate this cycle. The pipeline-restructure thread's inventory pass (see [[plugins/a4/.handoff/pipeline-restructure/2026-04-25_1804_compass-and-run-fallback-shipped]]) flagged this as ambiguous: is this an intentional all-or-nothing ship gate, or an oversight that prevents partial-shipping when a UC has multiple implementing tasks and only some have completed in the current cycle?

Two scenarios distinguish the cases:

- **All-or-nothing intentional.** Shipping a UC means "the running system reflects this UC end-to-end." If half the tasks are complete and half are still pending/failing, the system reflects a partial UC, which is not a shippable state. Rejecting partial-ship is correct.
- **Partial-ship supported.** A UC whose tasks complete in different cycles should be allowed to ship after the *first* cycle that brings the cumulative task set to `complete`, regardless of which cycle each individual task finished in. The current rule still works for this case if "every task with `implements: [usecase/X]` … has `status: complete`" is interpreted as "every task ever authored against X" rather than "every task completed in this cycle." But the SKILL.md does not say which.

Today's wording can be read either way, and the runtime behavior depends on whether `transition_status.py` resets a `complete` task back to `pending` between cycles (it does not — `complete` is terminal for tasks). So the rule is effectively all-or-nothing across the lifetime of the UC, not just the current cycle.

## Open Questions

- **Intent confirmation.** Is the all-or-nothing reading the intended one? If yes, document it explicitly in `run/SKILL.md` Step 5 to remove the ambiguity. If no, redefine the candidate rule.
- **Multi-cycle path.** If a UC accumulates `complete` tasks across multiple `/a4:run` cycles, when is its ship-review window? The first cycle in which the *last* implementing task completes, or every cycle that has at least one new completion? The current wording suggests the former by accident; confirm.
- **Tasks added mid-implementation.** If a new task with `implements: [usecase/X]` is authored after some original tasks for X already shipped, does X re-enter `implementing` automatically, or does the new task ship independently? `usecase` SKILL.md's status state machine ("`shipped` is forward-path terminal") suggests the former requires a new UC with `supersedes:`. Confirm and document the interaction.
- **Failing tasks blocking ship.** A UC with one `complete` task and one `failing` task blocks ship. This is correct under all-or-nothing, but the failure-classification path in Step 4 already classifies failing tasks. The interaction between "failing task blocks ship" and "Step 4 reclassifies the failure as architecture / UC issue" should be spelled out.
