---
title: "roadmap-reviewer UC-less audit reframing"
status: draft
decision: "TBD — reframe `roadmap-reviewer` to audit the roadmap as a graph of tasks/decisions/architecture rather than as a use-case tree."
supersedes: []
related: []
tags: [roadmap-reviewer, audit, reverse-links]
created: 2026-04-25
updated: 2026-04-25
---

# roadmap-reviewer UC-less audit reframing

## Context

The `roadmap-reviewer` agent currently audits the workspace along use-case (UC) lines — walking each `usecase/*.md`, checking its implementing tasks, surfacing gaps. This shape predates the wiki-and-issues model where UCs are one issue type among several (`usecase`, `task`, `decision`, `review`, `idea`, `spark`) and the wiki pages (`context.md`, `domain.md`, `architecture.md`, etc.) carry cross-cutting concerns.

A UC-less audit reframes the reviewer to walk the workspace as a graph: tasks and their `implements` / `depends_on` / `justified_by` edges, decisions and their `supersedes` / `related` edges, wiki pages and their footnote markers pointing back to decisions. The audit checks reachability, dangling references, status consistency, and orphan artifacts — without privileging UCs as the entry point.

This reframing is the natural occasion to introduce `decision.justifies` as a stored reverse-link (mirror of `task.justified_by`). Per [`2026-04-25-stored-reverse-links.decide.md`](2026-04-25-stored-reverse-links.decide.md), adding a new stored reverse-link field requires its own ADR naming the consumer; this reviewer reframing is that consumer.

This is the carry-forward of "Tier C 11" from the pipeline-restructure thread (see [`plugins/a4/.handoff/pipeline-restructure/2026-04-25_1527_carry-forward-link-rule.md`](../.handoff/pipeline-restructure/2026-04-25_1527_carry-forward-link-rule.md) §Tier C 11). It is the largest-scope carry-forward.

## Open Questions

- **Audit checks.** What are the concrete checks the reframed reviewer runs? Candidates: dangling forward-links, status-consistency gates (e.g., a `final` decision whose `justifies` tasks are all closed → archive candidate?), orphan tasks (no `justified_by`, no `implements`), wiki-impact gaps that never resolved.
- **`decision.justifies` ADR scope.** Should the field be added in a sibling ADR (separate from the reviewer reframing), or as part of the reviewer ADR itself? The stored-reverse-links ADR's "concrete consumer" bar suggests the consumer (reviewer) and the field can co-decide, but ADR purity argues for separation.
- **Refresh script ownership.** If `decision.justifies` ships, who owns its writes? Likely a generalization of `refresh_implemented_by.py` (e.g., `refresh_reverse_links.py` parameterized by forward/reverse field pairs).
- **UC-less but UC-aware.** Does the reframed reviewer ignore UCs entirely, or does it still surface UC-related findings as one report among many? The former is conceptually cleaner; the latter may be more practical.
- **Output shape.** Does the reviewer write `review/<id>-<slug>.md` items (current shape), or does it produce a single dashboard-style report? The two are not mutually exclusive.
