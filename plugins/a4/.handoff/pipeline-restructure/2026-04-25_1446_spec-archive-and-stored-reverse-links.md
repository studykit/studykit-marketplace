---
timestamp: 2026-04-25_1446
topic: pipeline-restructure
previous: 2026-04-25_1348_workflow-mode-retired.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-25_1446. To record a later state, create a new handoff file via `/a4:handoff` — never edit this one.

# pipeline-restructure — checkpoint at 2026-04-25_1446

This session opened on Tier C 10 ("남은 일" single source of truth) from the prior handoff but did not close it. While analyzing where ADR-derived design questions belong vs. task-tracker work, a separate but blocking drift surfaced: `plugins/a4/references/frontmatter-schema.md` line 47 declared "Reverse directions are derived by dataview queries, never stored," yet the implementation has had `usecase.implemented_by` as a stored, script-managed reverse field since the `usecase.ready → implementing` gate was wired. The session resolved the drift by writing a successor ADR, restructuring `plugins/a4/spec/` into active vs archived sets, and updating mutable cross-references. Tier C 10 itself remains open and now has two concrete sub-decisions queued (handoff `§Open` redefinition; ADR `## Next Steps` guardrail) that the next session can take up immediately.

## What is committed

- `2b6400197` — `docs(a4): introduce spec/archive layout and ADR for stored reverse links`. 16 files, +139 / −25.
  - Adds `plugins/a4/spec/2026-04-25-stored-reverse-links.decide.md` (the new active ADR — see §New ADR below).
  - Moves 8 prior plugin meta-ADRs from `plugins/a4/spec/` to `plugins/a4/spec/archive/` via `git mv`. After the move, `plugins/a4/spec/` holds exactly one `.decide.md` plus the `archive/` subdirectory.
  - Adds `plugins/a4/CLAUDE.md` (new). Three sections: (1) `<project-root>/a4/` user-project workspace layout (wiki + issue tracker, the directory tree, key conventions); (2) `plugins/a4/spec/` is plugin meta-design, with the new active-vs-archive split rule and a pointer to `decision/SKILL.md` Step 5 as the body-format reference for new ADRs; (3) skill-generated frontmatter is script-managed (status transitions through `transition_status.py`, reverse links through refresh scripts; no hand edits to auto-managed fields).
  - Edits root `CLAUDE.md` — adds an "a4 plugin frontmatter schema" section instructing readers to consult `plugins/a4/references/frontmatter-schema.md` before modifying anything that touches a4 frontmatter, writing a4 skills/scripts, or changing validators.
  - Edits `plugins/a4/references/frontmatter-schema.md` §Relationships (was "Relationships are forward-only"): drops the absolute "never stored" claim, documents the stored-reverse exception with rationale (script ownership + concrete consumer; the consumer for `usecase.implemented_by` is the `transition_status.py` `ready → implementing` gate), and adds a `Storage` column to the forward/reverse table that explicitly marks `implemented_by` as **stored — auto-maintained**.
  - Edits 5 mutable cross-reference sites (`plugins/a4/README.md`, `frontmatter-schema.md`, `obsidian-conventions.md`, `obsidian-dataview.md`, `skills/idea/SKILL.md`) to point at `archive/<filename>` paths.
  - Does **not** bump `.claude-plugin/marketplace.json` — doc-only changes plus a layout reorg, no skill or script behavior change.

`git log --oneline -3` will show `2b6400197` on top, with the handoff commit (this file) above it after step 5.

## New ADR — stored reverse links

`plugins/a4/spec/2026-04-25-stored-reverse-links.decide.md` follows the body structure prescribed by `plugins/a4/skills/decision/SKILL.md` Step 5 (`## Context`, `## Decision`, `## Options Considered`, `## Consequences`). Frontmatter mirrors the decision SKILL Step 5 schema except `id:` is omitted — plugin meta-ADRs use date-prefixed filenames as their identifier (no `allocate_id.py` source exists outside a user-project `a4/`).

**Decision summary.** A reverse-link frontmatter field may be stored when both (a) a script in `plugins/a4/scripts/` owns all writes (validator marks the field auto-managed; hand edits forbidden) and (b) a concrete consumer benefits from frontmatter-direct access (status gate, validator, hot query). Otherwise the default applies: store the forward direction only, derive reverse on demand.

**Partial supersession.** This ADR overturns the 2026-04-23 ADR's blanket "forward-only, never stored" rule but only that specific sentence and the matching `## Rejected Alternatives` row. The rest of the 2026-04-23 ADR (forward-direction canonicality, dataview as default rendering, the relationship field set, the wiki update protocol) remains in force. `supersedes:` frontmatter is left empty because the supersession is partial; the prose `## Decision` section names the scope of the supersession.

**Current scope.** Exactly one stored-reverse field exists: `usecase.implemented_by`. Adding any new one (e.g., the deferred `decision.justifies` mirroring `task.justified_by` — see §Open items below) requires a separate ADR that names the consumer and confirms the maintenance script.

## Why retired blanket "forward-only" needed an ADR

The trigger was an earlier turn in this session noticing that `plugins/a4/references/frontmatter-schema.md` had two contradictory claims:

- Line 47: "Reverse directions are derived by dataview queries, never stored."
- Line 151 (UC schema table): `implemented_by` — "**Auto-maintained** by `scripts/refresh_implemented_by.py` — never hand-write." (i.e., stored.)
- Line 363 (cross-file consistency table): `usecase.implemented_by` row materialized by `refresh_implemented_by.py`.

The schema doc's own self-stated rule (line 6) — "When the ADR and this document disagree, the ADR wins and this document should be updated to match" — meant the line-47 declaration should win and the stored field should be removed from code. But the stored field was load-bearing (`transition_status.py` reads it as a `ready → implementing` gate), so the right fix was to overturn the ADR's absolute rule, not the implementation. That required a new ADR. The successor ADR was written and `spec/` was reorganized so the new active ADR is alone in `spec/` while the partially-superseded predecessor moves to `spec/archive/`.

## Status of the prior handoff's open items

The prior handoff (`2026-04-25_1348_workflow-mode-retired.md`) listed Tier B item 7 plus Tier C items 8–12 as carry-forward. After this session:

- **Tier B 7** — `compass/SKILL.md` Layer 1–4 routing refresh now that `/a4:run` and `/a4:task` exist. **Still open.** Untouched this session.
- **Tier C 8** — `/a4:arch` ADR-generation pattern (A multi-agent debate / B research-drafter / C passive detector; B+C leading). **Still open.**
- **Tier C 9** — `decision` skill `## Next Steps` guardrail ("once authors stop hand-rolling tasks in ADR Next Steps, advise that implementation items become `/a4:task` invocations"). **Still open and now has a sub-task queued** (see §This session's open sub-decisions below).
- **Tier C 10** — "남은 일" single source. **Still open and has two sub-decisions queued** (see below). The session worked through this question conceptually and arrived at the picture below, but did not ship the implementation changes.
- **Tier C 11** — `roadmap-reviewer` UC-less audit reframing. **Still open.** This is the most likely future trigger for adding `decision.justifies` per the new stored-reverse-links ADR.
- **Tier C 12** — `/a4:run` final-fallback policy when neither `roadmap.md` nor `bootstrap.md` exists. **Still open.**

## Tier C 10 — picture this session arrived at

The conceptual conclusion is **not committed as code or doc** but should guide the next session's work on Tier C 10:

The "single source of truth for 남은 일" is not *one file format* but *one canonical place per epistemic stage*. The a4 pipeline already supplies these:

| Stage | What lives here | Canonical location | Status field |
|---|---|---|---|
| Open design question | "Which of A/B/C?" — pending decision | `a4/decision/<id>-<slug>.md` | `status: draft` |
| Open question inside a settled decision | "How does X interact with Y?" beside a final ADR | inside the ADR itself | `## Open Questions` section |
| Execution-ready task | "Implement Z" — known what to do | `a4/task/<id>-<slug>.md` | `status: pending` |
| Active task | currently implementing | `a4/task/<id>-<slug>.md` | `status: implementing` |
| Handoff `§Open` | a snapshot of the above three at session end | the handoff file | (not a tracker — a mirror) |

Implications:

1. **No new file format or directory needed.** All four canonical positions already exist in the schema. The work is making the conventions explicit and removing redundant tracking from ADR `## Next Steps` and handoff `§Open` (which currently both behave as informal trackers).
2. **`a4/decision/*.md` at `status: draft` IS the "draft ADR" mechanism.** `decision/SKILL.md` Step 1 already supports finalize-existing-draft mode; nothing new to build for the design-question stage.
3. **ADR ↔ task link is currently forward-only.** `task.justified_by:` exists; `decision.justifies:` does not. This is *not* a defect today — grep covers it — but if Tier C 11 (`roadmap-reviewer` UC-less audit) needs frontmatter-direct ADR → task lookup, that audit work would be the right time to add `decision.justifies` per the new stored-reverse-links ADR.

## This session's open sub-decisions

These emerged while working through Tier C 10 and were captured as task list items but not shipped. They are subordinate to Tier C 10/9; resolving them ships those Tier C items.

### Sub-decision — Redefine handoff `§Open` section

The current handoff template lets `§Open / carried forward` be a free-form list. That makes carry-forward expensive (every handoff manually re-lists items) and creates a third tracker alongside ADR `## Next Steps` and task files.

**Proposed rule** (not yet shipped): every `§Open` item must be a wikilink to one of:

- `[[task/<id>-<slug>]]` (execution-ready or in-progress work)
- `[[decision/<id>-<slug>]]` at `status: draft` (open design question)
- `[[decision/<id>-<slug>#Open Questions]]` (open question inside a settled ADR)

Free-text carry-forward (= an item that lives nowhere on disk) is forbidden. To put it in `§Open`, first create the task or draft ADR.

**Where this goes.** `plugins/a4/skills/handoff/SKILL.md` would gain a guard in step 4 (drafting the body). Possibly a body validator extension to check `§Open` link types.

**Open** sub-question: should the rule fire as an error or a soft warning? The current handoff body validator (`validate_body.py`) is fairly strict; adding an `§Open`-shape rule could be either a body validator extension or a `validate_handoff.py` companion.

### Sub-decision — Redefine ADR `## Next Steps` section

ADR `## Next Steps` is a "commonly used example" per `decision/SKILL.md` Step 5 (not required) but is currently used as a hand-rolled task list. Once tasks are the canonical execution-ready tracker, `## Next Steps` should hold *implications prose only*: "this decision implies the following pieces of work need to happen — see `[[task/N-...]]`, `[[task/M-...]]`."

**Where this goes.** `plugins/a4/skills/decision/SKILL.md` Step 5 ("Body structure rules") would gain a guideline on what `## Next Steps` is for and what it is not for. No code change needed, just prose guidance. Possibly a `validate_body.py` rule that flags `## Next Steps` items not formatted as wikilinks (warning, not error).

## Hook surface today (unchanged from prior handoff)

`plugins/a4/hooks/hooks.json` declares four events: PostToolUse / Stop / SessionStart (two — bash sweep + Python session-start) / SessionEnd (bash cleanup only — no Python entry per the workflow-mode retirement). The dispatcher's subcommand set is `post-edit | stop | session-start`. This is unchanged this session.

## Where to start the next session

**Default suggestion: ship Sub-decision A (handoff `§Open` redefinition).** It is the cheaper of the two queued sub-decisions and has the largest leverage — every future handoff stops accumulating manual carry-forward debt as soon as the rule is in place. Trigger surface: `plugins/a4/skills/handoff/SKILL.md` Task §4 ("Draft the handoff body").

If the user wants something else, alternative starting points (in rough priority order):

- **Sub-decision B (ADR `## Next Steps` guideline).** Smaller surface but pairs naturally with A. After A and B, Tier C 9 and 10 are both effectively closed.
- **Tier C 8** — `/a4:arch` ADR-generation pattern. The previously leading proposal is B+C (research-drafter + passive detector). Decide and ship.
- **Tier C 11** — `roadmap-reviewer` UC-less audit reframing. This is the natural occasion to propose `decision.justifies` reverse link per the stored-reverse-links ADR — author the proposal in the same ADR or as a sibling.
- **Tier C 12** — `/a4:run` final-fallback policy.
- **Tier B 7** — `compass/SKILL.md` Layer 1–4 routing refresh.

## Files to inspect first

- `plugins/a4/spec/2026-04-25-stored-reverse-links.decide.md` — the new active ADR. Sets the bar for any future stored-reverse field proposal.
- `plugins/a4/spec/archive/2026-04-23-spec-as-wiki-and-issues.decide.md` — the partially-superseded ADR. Still authoritative for forward-direction canonicality, dataview rendering, relationship field set, and wiki update protocol; only its blanket "never stored" claim is overturned.
- `plugins/a4/CLAUDE.md` — the new working notes. Read first when working on the a4 plugin; covers user-project layout, spec/archive convention, and frontmatter-script-management principle.
- `plugins/a4/references/frontmatter-schema.md` §Relationships (lines 45–63) — the updated rule. The `Storage` column on the forward/reverse table is the load-bearing change.
- `plugins/a4/skills/handoff/SKILL.md` Task §4 — where the proposed `§Open` rule would land.
- `plugins/a4/skills/decision/SKILL.md` Step 5 "Body structure rules" — where the proposed `## Next Steps` guideline would land.

## Don'ts (carried, refreshed)

- Don't add a new stored reverse-link field (e.g., `decision.justifies`) without a covering ADR per the stored-reverse-links ADR §Decision. The bar is script ownership + concrete consumer.
- Don't edit any file under `plugins/a4/spec/archive/` or `plugins/a4/.handoff/**` — both are immutable. Supersession of an archived ADR is recorded by writing a new ADR in `spec/`. Handoff revisions are recorded by writing a new handoff.
- Don't move ADRs back from `archive/` to `spec/` without a reason. The split is decided: `spec/` = active, `archive/` = frozen.
- Don't update the prior handoff references in `plugins/a4/.handoff/**` to point at `archive/` — handoffs are point-in-time snapshots; broken paths inside them are the expected aging behavior.
- Don't reintroduce `default_mode:` or `mode_transitions:` frontmatter on any SKILL.md (carried from prior handoff).
- Don't reintroduce `scripts/workflow_mode.py` or any session state file under `a4/.workflow-state/` (carried).
- Don't merge `/a4:roadmap` and `/a4:run` back together (carried).
- Don't `rm -rf a4` from the studykit-plugins root — case-insensitive macOS match wipes tracked content (carried).
- Don't write Tier C 10's "single source" as a new file format or directory. The picture this session arrived at uses only existing schema positions (`a4/decision/*.md` at `status: draft`, ADR `## Open Questions`, `a4/task/*.md`, handoff `§Open` as mirror).
