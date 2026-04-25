---
timestamp: 2026-04-25_1241
topic: pipeline-restructure
previous: 2026-04-25_1155_mode-axis-and-plan-rename.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-25_1241. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# pipeline-restructure — checkpoint at 2026-04-25_1241

No code changes since the previous handoff (`78870cad4` at 2026-04-25_1155). Working tree is clean. This handoff exists to refresh the resumption pointer; the substantive state and decisions are still those captured in [`2026-04-25_1155_mode-axis-and-plan-rename.md`](./2026-04-25_1155_mode-axis-and-plan-rename.md). Read that file for the full picture.

## What is committed

- `d536cfe70` — `refactor(a4): rename plan→roadmap, introduce workflow-mode axis`. 25 files. Adds `references/workflow-mode.md`, `scripts/workflow_mode.py`, the two ADRs (`spec/2026-04-25-workflow-mode-axis.decide.md`, `spec/2026-04-25-plan-restructure.decide.md`), renames `skills/plan/` → `skills/roadmap/` and `agents/plan-reviewer.md` → `agents/roadmap-reviewer.md`, and substitutes `plan` → `roadmap` across non-handoff non-spec files. Marketplace bumped to 1.16.0.
- `78870cad4` — `docs(handoff): snapshot pipeline-restructure session state`. The previous handoff.

`git log --oneline -3` should show these two on top of the prior baseline `e8628f80c`.

## What is decided but not implemented

The previous handoff §5 lists three tiers in priority order. Repeating the resume order here so this file stands alone:

### Tier A (blocked-by-absence)

1. **`plugins/a4/skills/run/SKILL.md`** — split Phase 2 out of `roadmap/SKILL.md`. UC-optional: ship-review (Step 2.5) only when `implements:` non-empty; ready conditions vacuously pass for empty `implements:`. `default_mode: autonomous`. Reads `roadmap.md`'s Launch & Verify; falls back to `bootstrap.md` for UC-less projects with no roadmap (final fallback policy not yet decided).
2. **`plugins/a4/skills/task/SKILL.md`** — single-task authoring. `default_mode: conversational`. Required `kind` arg (`feature | spike | bug`). Optional `implements:` (UC) and `justified_by:` (ADR). For `kind: spike`, propose creating `spike/<id>-<slug>/` sidecar. Acceptance-criteria source by kind documented in the plan-restructure ADR.
3. **`a4_hook.py` integration** — `SessionStart` calls `workflow_mode.py init` + `sweep`; `SessionEnd` calls `workflow_mode.py cleanup`. Update `hooks/hooks.json`.
4. **`default_mode:` frontmatter rolled into every mode-aware skill SKILL.md** — table from the workflow-mode ADR is the canonical mapping.

### Tier B (schema/docs alignment)

5. `frontmatter-schema.md` — formalize `default_mode` and `mode_transitions` skill-frontmatter fields under a new "Skill metadata" section.
6. `roadmap/SKILL.md` Task File Schema example — currently does not include the `kind:` field; add it (closes the original drift task #6).
7. `compass/SKILL.md` Layer 1–4 routing — refine recommendations after `/a4:run` and `/a4:task` exist.

### Tier C (open design questions)

8. `/a4:arch` ADR-generation pattern — A (multi-agent debate), B (research-drafter), C (passive detector) discussed in the previous session; combination B+C is the leading proposal. Not committed.
9. `decision` skill `## Next Steps` guardrail — once `/a4:task` exists, advise that implementation items become `/a4:task` invocations.
10. "남은 일" single source — `/a4:task` task files plausibly become the canonical tracker; deprecation of ADR `## Next Steps` and handoff `§Open / carried forward` as task-trackers still TBD.
11. `roadmap-reviewer` UC-less audit — review criteria still UC-coverage-shaped; needs reframing for projects whose tasks are ADR-justified.

## Where to start the next session

Default suggestion (if the user gives no specific directive on resume): begin Tier A item 1 — write `plugins/a4/skills/run/SKILL.md`. The bulk of the content is excised from the current `roadmap/SKILL.md` Phase 2 section (lines 238–380 in the renamed file). Make Step 2.5 (UC ship-review) conditional on `implements:` non-empty and add a brief note on the AC source convention (`justified_by:` ADR for UC-less features, etc.). The legacy combined Phase 1 + Phase 2 prose currently sits inside `roadmap/SKILL.md`; after the split, `roadmap/SKILL.md` keeps only Phase 1 plus a pointer to `/a4:run`.

If the user asks "what's the state of the workflow-mode tooling?" — `scripts/workflow_mode.py` is functional and Pyright-clean. Smoke commands documented in the previous handoff §7. Hook integration (Tier A item 3) is the next logical step.

## Files to inspect first

- `plugins/a4/skills/roadmap/SKILL.md` — has both Phase 1 and Phase 2 inline; this is the source for the `/a4:run` extraction.
- `plugins/a4/spec/2026-04-25-plan-restructure.decide.md` — three-skill split rationale, AC source by kind, conditional ship-review, migration recipe.
- `plugins/a4/spec/2026-04-25-workflow-mode-axis.decide.md` — mode axis rationale, default-mode-by-skill table, canonical transition triggers, out-of-scope follow-ups.
- `plugins/a4/references/workflow-mode.md` — operational reference; consult before authoring or modifying mode-aware skills.
- `plugins/a4/scripts/workflow_mode.py` — single tool; see `--help` for subcommands.

## Don'ts (carried from the previous handoff)

- No backwards-compat for `kind: plan`. Forward-only.
- No edits in `plugins/a4/.handoff/**` or `plugins/a4/spec/**` (point-in-time, immutable).
- Don't try to merge `/a4:roadmap` and `/a4:run` back together. The split is decided.
- Don't consume `default_mode:` from skill frontmatter without first rolling the field into the relevant SKILL.mds — currently no skill declares it.
