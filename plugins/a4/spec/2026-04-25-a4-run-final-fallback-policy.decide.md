---
title: "/a4:run final-fallback policy when neither roadmap nor bootstrap exists"
status: draft
decision: "TBD — define the final fallback for `/a4:run` when invoked with neither `roadmap.md` nor `bootstrap.md` present in the user-project a4/ workspace."
supersedes: []
related: []
tags: [a4-run, fallback, ux]
created: 2026-04-25
updated: 2026-04-25
---

# /a4:run final-fallback policy

## Context

`/a4:run` selects work to execute when invoked. The current selection ladder consults `<project-root>/a4/roadmap.md` first, then `<project-root>/a4/bootstrap.md`. When neither file exists in the workspace, the current behavior degrades inconsistently — sometimes a no-op, sometimes a confused selection from `task/`, sometimes an error.

The fallback needs an explicit policy. Candidates:

- **No-op.** Print "no roadmap or bootstrap found; nothing to run" and exit.
- **Help message.** Print a one-screen summary of how to populate `roadmap.md` or `bootstrap.md` and exit.
- **Offer to run `/a4:bootstrap`.** Treat the empty workspace as "user is starting fresh" and chain into bootstrap with confirmation.
- **Pick from `task/` directly.** Use `task/*.md` at `status: pending` as the fallback queue, ignoring roadmap/bootstrap entirely. Highest engagement, highest risk of running unintended work.

This is the carry-forward of "Tier C 12" from the pipeline-restructure thread (see [`plugins/a4/.handoff/pipeline-restructure/2026-04-25_1527_carry-forward-link-rule.md`](../.handoff/pipeline-restructure/2026-04-25_1527_carry-forward-link-rule.md) §Tier C 12).

## Open Questions

- **Which fallback.** The leading candidate is "offer to run `/a4:bootstrap`" because it pairs the empty-workspace signal with the most likely user intent. Confirm or reject.
- **Ladder vs. single fallback.** Should the fallback be a single behavior, or a sub-ladder (e.g., bootstrap → help → no-op)?
- **First-run vs. recurring-empty.** Is there a distinction between "fresh workspace, nothing yet" and "workspace existed but roadmap/bootstrap deleted"? If so, the policy may differ — first-run leans toward chaining into bootstrap; recurring-empty leans toward no-op or help.
- **Interaction with `/a4:run` non-empty arguments.** If the user invokes `/a4:run <task-id>` directly, the fallback ladder is bypassed. Confirm this is the desired carve-out, or whether the explicit argument should still be validated against roadmap/bootstrap.
