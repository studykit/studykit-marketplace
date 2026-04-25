---
title: "Compass Step 2 catalog consistency audit"
status: draft
decision: "TBD — audit `compass/SKILL.md` Step 2.1 catalog against the actual a4 skill set and decide whether and how to fix any drift."
supersedes: []
related: []
tags: [compass, catalog, audit]
created: 2026-04-25
updated: 2026-04-25
---

# Compass Step 2 catalog consistency audit

## Context

`compass/SKILL.md` Step 2.1 ("Catalog") presents three skill tables — Ideation, Pipeline (interactive), Pipeline (autonomous), Standalone — when the workspace is empty (or, post Tier B 7 refresh, when the empty workspace also has no implementation code).

The pipeline-restructure thread's inventory pass (see [[plugins/a4/.handoff/pipeline-restructure/2026-04-25_1804_compass-and-run-fallback-shipped]]) noticed that the catalog tables may be partially out of date relative to the full skill set under `plugins/a4/skills/`. Specifically, it is unclear whether every current skill is represented, whether each table's category is still the right home for each entry, and whether descriptions reflect each skill's current SKILL.md description field. Skills added or substantially refreshed after the catalog was first authored — `auto-usecase`, `auto-bootstrap`, `task`, `run`, `web-design-mock`, `idea`, `spark-brainstorm`, `drift`, `validate`, `index`, `handoff` — are the most likely drift candidates.

The catalog is the user's first impression of a4's surface area when they have no workspace yet, so drift here is high-visibility and easy to notice once spotted.

## Open Questions

- **Inventory.** Is every skill under `plugins/a4/skills/` represented in some Step 2.1 table? Use `ls plugins/a4/skills/` and walk through the catalog.
- **Categorization.** Are the four categories (Ideation / Pipeline interactive / Pipeline autonomous / Standalone) still the right partition? Where do `idea`, `spark-brainstorm`, `validate`, `drift`, `index`, `handoff`, and `compass` itself belong?
- **Description drift.** Is each catalog row's "What it does" column consistent with the linked skill's SKILL.md description field? When a skill description has been refreshed, the catalog often lags.
- **Brownfield interaction.** Step 2.0 brownfield branch may pre-empt the catalog for code-bearing projects. Does the catalog still need to mention `auto-usecase` and `auto-bootstrap` prominently when Step 2.0 already routes to them, or does the catalog become the "no code, greenfield" entry path only?
