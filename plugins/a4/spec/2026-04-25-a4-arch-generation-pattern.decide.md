---
title: "/a4:arch ADR-generation pattern selection"
status: draft
decision: "TBD — leading combination is B+C (research-drafter + passive detector)."
supersedes: []
related: []
tags: [a4-arch, adr-generation, multi-agent]
created: 2026-04-25
updated: 2026-04-25
---

# /a4:arch ADR-generation pattern selection

## Context

`/a4:arch` should generate architectural decision records (ADRs) from project context. Three candidate patterns surfaced in earlier sessions:

- **A. Multi-agent debate.** A council of role-typed agents argues options; the chair synthesizes the chosen ADR. High cost, high quality on contested decisions.
- **B. Research-drafter.** A research pass enumerates options and tradeoffs; a drafter writes the ADR from research output. Mid cost, well-suited to decisions where the option space is the bottleneck.
- **C. Passive detector.** Watches the working tree for signals that an architectural decision is being made implicitly (new dependency, new directory layout, new external API surface) and prompts the user to record it. Low cost, catches drift.

B+C is the leading combination — explicit decisions go through B, implicit ones get caught by C. A is held in reserve for high-stakes contested cases.

This is the carry-forward of "Tier C 8" from the pipeline-restructure thread (see [`plugins/a4/.handoff/pipeline-restructure/2026-04-25_1527_carry-forward-link-rule.md`](../.handoff/pipeline-restructure/2026-04-25_1527_carry-forward-link-rule.md) §Tier C 8).

## Open Questions

- **Confirm B+C as the selection.** Or is one of B / C alone sufficient for the first cut, with the other added later?
- **Detector signal set for C.** What are the concrete signals — `package.json` / `pyproject.toml` diffs, new top-level directories, `mcp.json` changes, new third-party SDK imports? Pinning the signal set determines C's complexity.
- **Drafter prompt shape for B.** Is B a single-shot drafter that calls `/a4:research` first, or is it composed inside `/a4:arch` itself? Composition affects where the research artifacts land (`research/` vs. inline).
- **Output landing.** B+C both write to `<project-root>/a4/decision/`. Should the detector (C) ever write directly, or always nudge the user to invoke `/a4:decision` (which already has the writer)? Direct writes risk bypassing the wiki-nudge step.
