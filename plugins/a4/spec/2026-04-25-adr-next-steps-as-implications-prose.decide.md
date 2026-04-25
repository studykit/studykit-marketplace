---
title: "ADR `## Next Steps` is implications prose with task wikilinks, not a hand-rolled task list"
status: final
decision: "An ADR's `## Next Steps` section holds implications prose that names follow-on work via `[[task/<id>-<slug>]]` wikilinks; it is not a hand-rolled task list and never substitutes for `a4/task/` files."
supersedes: []
related: []
tags: [decision-skill, adr, next-steps, trackers, process]
created: 2026-04-25
updated: 2026-04-25
---

# ADR `## Next Steps` is implications prose with task wikilinks

## Context

The `decision` skill (`plugins/a4/skills/decision/SKILL.md`) lists `## Next Steps` as one of the commonly-used optional sections in an ADR body (Step 5 §Body structure rules). In practice this section has been used as a hand-rolled to-do list — bullet items naming follow-on work, sometimes with assignees or rough dates, but with no link to any `a4/task/` file.

This created the same three-tracker problem documented in [`2026-04-25-handoff-carry-forward-as-wikilinks.decide.md`](2026-04-25-handoff-carry-forward-as-wikilinks.decide.md): ADR `## Next Steps` lists, handoff `§Open` sections, and `a4/task/` files all carried partial views of "still open work", with no mechanism forcing convergence. The handoff side of that problem was closed by the wikilink rule. The ADR side is closed here.

The role of `## Next Steps` in an ADR is to record *implications of the decision* — "this decision implies these pieces of work need to happen" — not to act as a project plan. Implications belong in the ADR because they are part of the decision's footprint; the executable detail (priority, status, owner, sub-steps) belongs in `a4/task/` files. The ADR points at those files; it does not duplicate them.

This is the matching reform on the ADR side of the same principle handoffs now follow: every "still open" item in a long-lived document must point to an on-disk tracker, not stand alone as free text.

## Decision

An ADR's `## Next Steps` section, when present, contains implications prose that names follow-on work via `[[task/<id>-<slug>]]` wikilinks. The section is not a hand-rolled task list. Specifically:

- **Form.** Prose paragraphs naming the implication and citing one or more `[[task/<id>-<slug>]]` wikilinks. Bullet lists are allowed when there are multiple distinct implications, but each bullet must still be implications prose with at least one task wikilink, not a bare to-do item.
- **Substitution rule.** If a line of `## Next Steps` describes executable work without pointing to a task, the session must create the task (`/a4:task`) before merging the ADR. The link is the carry-forward identity, exactly as in handoff carry-forward.
- **Section is optional.** ADRs that have no follow-on work omit the section entirely. Empty or placeholder `## Next Steps` sections are not written.
- **Plugin meta-ADR fallback.** ADRs in `plugins/a4/spec/` (plugin meta-design) have no `<project-root>/a4/task/` workspace. Their `## Next Steps` references plugin-internal artifacts using analogous on-disk anchors: a sibling draft ADR (`[[plugins/a4/spec/<filename>]]`), an `## Open Questions` heading on a settled sibling ADR, or a SKILL.md edit named by file path. The principle — every implication points at a file the next session can open — is unchanged.

The rule is recorded in `plugins/a4/skills/decision/SKILL.md` Step 5 "Body structure rules". A future validator extension to `plugins/a4/scripts/validate_body.py` may flag `## Next Steps` items that are not formatted as wikilinks; severity (warning vs. error) is left as an `## Open Questions` item below.

## Options Considered

**A. Keep `## Next Steps` as a free-form list.** Status quo before this decision. Discarded for the same reason free-form handoff carry-forward was discarded — it accumulates without ever converging on tracked artifacts.

**B. Drop `## Next Steps` entirely; require all follow-on work to live only in `a4/task/`.** Tighter than this decision. Discarded — the implications-prose role is genuinely useful in the ADR itself, because a fresh reader of the ADR benefits from seeing the decision's footprint without having to grep for tasks that link back to it. Removing the section also weakens ADRs as a self-contained record of why the work landed on the backlog.

**C. Implications prose with mandatory task wikilinks (this decision).** Keeps the section's narrative role, removes the "shadow tracker" failure mode, mirrors the handoff carry-forward rule. **Selected.**

**D. Implications prose with optional task wikilinks (soft form).** Allow `## Next Steps` to mention work without linking to a task when no task exists yet, with the expectation that a task will be created later. Discarded — this is functionally identical to the status quo. The strict rule (no listing without a tracker) is what closes the gap.

## Consequences

- **`a4/task/` becomes the single home for executable follow-on work.** ADRs name implications and link; tasks carry status, priority, and execution detail.
- **Session ergonomics.** Writing a substantive ADR may now require creating tasks before finalizing the ADR, especially when the decision has executable consequences. This is acceptable cost — the same coupling already exists for handoff carry-forward.
- **Reading flow.** Readers of an ADR who want execution detail follow the wikilinks. The ADR itself stays compact; tasks evolve over time without rewriting the ADR.
- **Plugin meta-ADRs are constrained but workable.** `plugins/a4/spec/` ADRs have no `a4/task/` workspace; their `## Next Steps` references sibling ADRs, `## Open Questions` sections, or SKILL.md file paths. This is tighter than user-project ADRs but uses the same shape (every implication points at a file).
- **Pairs with the handoff carry-forward rule.** Together, the two rules close the three-tracker problem: handoff `§Open` and ADR `## Next Steps` both flow through `a4/task/`, draft ADRs, or `## Open Questions` anchors. After both rules ship, "still open" exists in exactly one canonical place per item.

## Open Questions

- **Validator severity for `## Next Steps`.** A future check in `plugins/a4/scripts/validate_body.py` could flag `## Next Steps` lines that lack a `[[task/...]]` wikilink. Should this be a warning or a hard error on `draft → final` transition? A hard error couples ADR finalization to task creation; a warning preserves flexibility but risks being ignored.
- **Plugin meta-ADR target shape.** For plugin self-ADRs, `## Next Steps` may want to link to a SKILL.md edit by file path even when no sibling ADR exists. Is `[[plugins/a4/skills/<skill>/SKILL.md]]` an acceptable target form, or should every implication route through a sibling spec ADR or `## Open Questions` heading? Current guidance is permissive; a future ADR may tighten this.
