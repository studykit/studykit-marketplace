---
title: "Permit stored reverse links under script ownership"
status: final
decision: "Reverse-link fields may be stored in frontmatter when (a) a script owns writes and (b) a concrete consumer benefits from frontmatter-direct access; otherwise prefer derive-on-demand."
supersedes: []
related: []
tags: [frontmatter-schema, relationships, reverse-links]
created: 2026-04-25
updated: 2026-04-25
---

# Permit stored reverse links under script ownership

## Context

The `2026-04-23-spec-as-wiki-and-issues` ADR (now at [`archive/2026-04-23-spec-as-wiki-and-issues.decide.md`](archive/2026-04-23-spec-as-wiki-and-issues.decide.md)) decided "Relationship fields store only the forward direction; reverse directions are derived by dataview queries" (§Decision) and reinforced the rule in §Rejected Alternatives:

> "Explicit bidirectional relationship fields (`blocks` stored alongside `depends_on`, `implemented_by` alongside `implements`) — Doubles maintenance and risks drift between forward/reverse. Store only forward direction; dataview computes reverse on demand."

Since then, the implementation introduced one stored reverse field — `usecase.implemented_by`, auto-maintained by `plugins/a4/scripts/refresh_implemented_by.py` — without a covering ADR. The motivation was the `usecase.ready → implementing` status gate enforced by `plugins/a4/scripts/transition_status.py`, which requires `implemented_by:` non-empty. Storing the field in frontmatter avoids re-running the `task.implements:` back-scan inside the writer on every transition. The script is invoked at the end of `/a4:roadmap` Phase 1, from `/a4:task` Step 6, and by the SessionStart hook.

This left the spec ↔ implementation pair in drift: the archived ADR forbids stored reverse, the code stores one, and the schema doc (`plugins/a4/references/frontmatter-schema.md`) was updated to match the code without ADR backing.

The 2026-04-23 reasoning for rejection — "doubles maintenance and risks drift between forward/reverse" — assumed **manual** maintenance. Script-owned reverse-link refresh has near-zero ongoing cost (idempotent; the consumer never sees the back-scan) and drift risk is bounded by the script's correctness, which is testable in one place rather than scattered across every author.

## Decision

A reverse-link frontmatter field may be **stored** when both conditions hold:

1. **Script ownership** — a script in `plugins/a4/scripts/` owns all writes to the field. Hand edits are forbidden; `plugins/a4/scripts/validate_frontmatter.py` marks the field as auto-managed.
2. **Concrete consumer** — at least one named consumer (status gate in `transition_status.py`, validator, or hot query in a skill or hook) benefits from frontmatter-direct access enough to justify bypassing derive-on-demand.

Otherwise the default applies: store the forward direction only; let consumers derive the reverse via Obsidian dataview, grep, or an ad-hoc back-scan.

This decision **partially supersedes** the 2026-04-23 ADR's blanket "forward-only, never store reverse" rule. The rest of that ADR (forward-direction canonicality, dataview as the default rendering layer, the relationship field set, the wiki update protocol) remains in force. Because the supersession is partial, this ADR's `supersedes:` frontmatter is empty; readers should treat the 2026-04-23 §Decision sentence and §Rejected Alternatives row on stored reverse as superseded by this ADR specifically, not the parent ADR as a whole.

**Current scope.** Exactly one stored-reverse field exists today: `usecase.implemented_by`. Future additions (e.g., `decision.justifies` mirroring `task.justified_by`) require a separate ADR that names the consumer and confirms script ownership.

## Options Considered

**A. Restore strict forward-only; remove `usecase.implemented_by` storage.** Aligns code with the archived ADR by changing the code. Cost: rework `transition_status.py` to back-scan `task.implements:` on every UC transition (or carry a runtime cache), rework `validate_status_consistency.py` and any hook code that reads the frontmatter directly, and accept added latency on the hot path. **Rejected** — the existing storage is load-bearing and removing it yields no observable benefit beyond ADR purity.

**B. Permit stored reverse with a bar (this decision).** Codifies the existing exception, gives a clear standard for future additions, and aligns the schema doc with the code. **Selected.**

**C. Permit stored reverse unconditionally.** Removes the bar. **Rejected** — without the script-ownership + concrete-consumer requirement, the original concern (drift between forward/reverse, doubled maintenance) returns. Hand-maintained reverse links were exactly what the 2026-04-23 ADR rightly avoided; this ADR keeps that protection while carving out a narrow, automated exception.

## Consequences

- `plugins/a4/references/frontmatter-schema.md` §Relationships already reflects this decision (updated 2026-04-25 in the same session as this ADR; see the table's `Storage` column and the stored-reverse exception paragraph).
- The 2026-04-23 ADR's "never stored" claim no longer holds in its absolute form. Readers consulting the archived ADR should pair it with this one.
- Adding new stored reverse links is now an ADR-level decision, not a quiet implementation choice. Code review should reject script changes that introduce unannounced auto-managed reverse fields.
- A subsequent ADR can extend the precedent — e.g., to add `decision.justifies` for ADR ↔ task reverse traversal — by naming the consumer (likely the `roadmap-reviewer` agent's UC-less audit per the open Tier C 11 item, or a future drift detector check) and confirming the maintenance script (likely a generalization of `refresh_implemented_by.py`).
