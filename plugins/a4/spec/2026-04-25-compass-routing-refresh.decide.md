---
title: "Compass routing refresh for /a4:run and /a4:task era"
status: draft
decision: "TBD — refresh `compass/SKILL.md` Layer 1–4 routing to account for `/a4:run` and `/a4:task` skills that postdate the original routing."
supersedes: []
related: []
tags: [compass, routing, skill-selection]
created: 2026-04-25
updated: 2026-04-25
---

# Compass routing refresh for /a4:run and /a4:task era

## Context

`plugins/a4/skills/compass/SKILL.md` routes user intent across a4 skills in four layers:

- **Layer 1** — triage of the user's request shape.
- **Layer 2** — capture vs. design vs. execute partition.
- **Layer 3** — skill selection within the chosen partition.
- **Layer 4** — invocation form (which skill, with what arguments).

The routing predates the introduction of `/a4:run` (autonomous execution) and `/a4:task` (executable work-unit creation). The current routing either silently never reaches these skills or routes through stale predecessors. A refresh is needed.

This is the carry-forward of "Tier B 7" from the pipeline-restructure thread (see [`plugins/a4/.handoff/pipeline-restructure/2026-04-25_1527_carry-forward-link-rule.md`](../.handoff/pipeline-restructure/2026-04-25_1527_carry-forward-link-rule.md) §Tier B 7).

## Open Questions

- **SKILL.md edit vs. ADR scope.** The deliverable is an edit to `compass/SKILL.md`. Does this need a full ADR, or is a working-note section directly in `compass/SKILL.md` (with a `<!-- TODO -->` marker) the cheaper anchor? The current handoff uses this draft ADR as the anchor; if the refresh raises broader design questions during implementation, this ADR is where they land. If not, the ADR may close as a pure pointer with no `## Decision` content of its own.
- **Layer-by-layer or full rewrite.** Does the routing need a full Layer 1–4 rewrite, or surgical inserts at the points where `/a4:run` and `/a4:task` should appear?
- **Test surface.** How is routing correctness validated? Unit tests are unlikely; the current evidence is "the skill triggers correctly when invoked." Is there a canonical set of intents to walk through manually after the edit?
