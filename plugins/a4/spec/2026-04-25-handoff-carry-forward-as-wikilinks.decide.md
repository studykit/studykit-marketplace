---
title: "Handoff carry-forward items must be on-disk wikilinks"
status: final
decision: "Every carry-forward item in a handoff must be a wikilink to an on-disk tracker (task / draft decision / settled-ADR Open Questions); free-text carry-forward is forbidden."
supersedes: []
related: []
tags: [handoff, carry-forward, trackers, process]
created: 2026-04-25
updated: 2026-04-25
---

# Handoff carry-forward items must be on-disk wikilinks

## Context

Before this decision, the workspace had three concurrent trackers for "still open" work, each with overlapping but distinct semantics:

1. **ADR `## Next Steps`** — a hand-rolled task list embedded in each ADR.
2. **Handoff `§Open` / "still open" / "where to start" sections** — free-form prose listing what the next session should pick up.
3. **`a4/task/<id>-<slug>.md`** — the only proper execution tracker, with frontmatter, status transitions, and a writer.

Two structural problems followed from having three trackers:

- **Manual carry-forward debt.** Each handoff inherited the prior handoff's free-form list and had to re-list it (manual copy) or silently drop it (lost work). There was no on-disk anchor that a fresh session could open and update — only narrative paragraphs in immutable handoff snapshots.
- **Drift across trackers.** A task could appear in an ADR `## Next Steps` list, in three successive handoff `§Open` sections, and never become an `a4/task/` file. There was no mechanism that forced free-text mentions to converge on a tracked artifact.

The fix is not a fourth tracker. The fix is to make the existing trackers canonical and forbid free-text carry-forward in the place where it accumulates fastest — handoffs. Concretely: a carry-forward in a handoff must point to a file the next session can open. If no such file exists yet, the session creates it before listing the item.

This ADR is a process backfill. The rule itself shipped in `9f92bfe7b` directly to `plugins/a4/skills/handoff/SKILL.md` Task §4 without a covering ADR. Per `plugins/a4/CLAUDE.md`, plugin meta-design decisions are recorded as ADRs in `plugins/a4/spec/`. This ADR closes that drift by recording the decision retroactively.

## Decision

Every carry-forward item in a handoff body must be a wikilink to an on-disk tracker. The accepted targets are:

- `[[task/<id>-<slug>]]` — execution-ready or in-progress work (`status: pending | implementing`).
- `[[decision/<id>-<slug>]]` — open design question recorded as a draft ADR (`status: draft`).
- `[[decision/<id>-<slug>#Open Questions]]` — an open question inside a settled ADR.

Free-text carry-forward — an item that lives nowhere on disk — is forbidden. If the appropriate tracker does not exist at carry-forward time, the session creates it before listing the item: `/a4:task` for execution-ready work, `/a4:decision` in draft mode for an open design question, or an `## Open Questions` heading appended to the relevant final ADR. Prose around each wikilink is permitted (one-line context, why it remains open); the wikilink itself is the carry-forward identity.

For projects without a `<project-root>/a4/` workspace — notably handoffs about the a4 plugin itself — the rule applies analogously to the project's on-disk tracker. For plugin meta-design that means `[[plugins/a4/spec/<filename>]]` ADR references and `## Open Questions` headings on relevant ADRs.

The rule is enforced by the `/a4:handoff` skill (`plugins/a4/skills/handoff/SKILL.md` Task §4 "Carry-forward items"). A future companion validator (see `## Open Questions`) may add automated enforcement on the resulting handoff file.

## Options Considered

**A. Add a fourth dedicated "open work" tracker.** A new file (e.g., `a4/open.md` or `a4/backlog.md`) that aggregates everything in flight. Discarded — adds a fourth lifecycle to keep in sync with the existing three. The problem is not lack of a tracker; it is free-text carry-forward in handoffs.

**B. Merge the three trackers into one.** Collapse ADR `## Next Steps`, handoff `§Open`, and `a4/task/` into a single artifact type. Discarded — each plays a distinct epistemic role: ADR `## Next Steps` records implications of a settled decision; handoff `§Open` records what the next session should resume; `a4/task/` records executable work. Merging loses the staging from "open question" to "draft decision" to "executable task".

**C. Forbid free-text carry-forward; require wikilinks to existing tracker types (this decision).** Keeps the existing three trackers, removes the fourth implicit tracker (free-form handoff prose), and forces carry-forward to flow through the canonical artifacts. **Selected.**

**D. Keep free-text carry-forward but add a soft warning.** A validator flags non-wikilinked carry-forward without blocking writes. Discarded as the primary mechanism — soft warnings on a hot path tend to be ignored. The hard rule lives in the SKILL.md instructions to the model; a validator may later add a soft warning on top, but the rule itself is not advisory.

## Consequences

- **Bootstrap requirement.** The rule applies to handoffs written *after* `9f92bfe7b`. Every open carry-forward from handoffs written before the rule needs an on-disk anchor created before the next handoff lists it. The 2026-04-25_1527 handoff is the last transitional snapshot allowed to use free-text carry-forward, with explicit notes on where each item's anchor should live.
- **Handoffs become referential.** A handoff body is a snapshot of session narrative plus pointers; the live state lives in the trackers it references. Reading a handoff therefore typically requires opening the linked files for current state — handoffs no longer attempt to be self-sufficient state records.
- **`/a4:handoff` may need to invoke `/a4:task` or `/a4:decision`.** When a session ends with carry-forward that has no anchor, the handoff skill must create the anchor first. This couples the handoff skill to the task and decision skills more tightly than before.
- **Plugin self-handoff fallback.** Handoffs written about the a4 plugin itself (in `plugins/a4/.handoff/`) cannot use `[[task/...]]` or `[[decision/...]]` because there is no `<project-root>/a4/` workspace. They use the analogous form: `[[plugins/a4/spec/<filename>]]` for draft ADRs and `## Open Questions` headings on settled ADRs.
- **`a4/task/`, `a4/decision/`, and ADR `## Open Questions` are now load-bearing.** Stale or missing trackers no longer fail silently — they fail at the next handoff write, when the session is forced to materialize the anchor.
- **Marketplace version bump policy.** Per root `CLAUDE.md`, behavior changes to a plugin bump the marketplace version. The shipping rule was `1.19.0 → 1.20.0` in `9f92bfe7b`; subsequent rules consistent with this ADR continue to bump per change.

## Open Questions

- **Validator enforcement scope and severity.** Should a companion validator scan handoff bodies for carry-forward sections and flag items that are not wikilinks? If so:
  - **Where does it live?** `plugins/a4/scripts/validate_body.py` currently scans the user-project `<project-root>/a4/` workspace, not the project's `.handoff/`. Two candidates: (1) extend `validate_body.py` with a handoff-aware mode, (2) add a new `plugins/a4/scripts/validate_handoff.py` companion. The companion option keeps `validate_body.py`'s scope clean but duplicates frontmatter-loading and section-walking utilities.
  - **Hard error or soft warning?** A hard error blocks the handoff write; the session must materialize the anchor before retrying. A soft warning allows the write but surfaces the issue. Hard error matches the SKILL.md rule's spirit ("free-text is forbidden") but increases friction at session end. Soft warning is more forgiving but at risk of being ignored.
  - **Heuristic for detecting a "carry-forward section".** Section-name match (`§Open`, `## Carry-forward`, `## Where to start`) is brittle; a more robust signal might be "any unordered list inside a section whose H2 name matches a configurable regex". Needs a concrete proposal.
- **Retroactive bootstrap order.** When the next session bootstraps the open carry-forwards from the 2026-04-25_1527 handoff, in what order should anchors be created? The handoff lists them by tier; creating draft ADRs in tier order is one option, but some carry-forwards (e.g., the validator follow-up) are sub-questions of other anchors and should attach as `## Open Questions` rather than as standalone draft ADRs. A short ordering pass at the start of the next session is likely the cheapest path.
