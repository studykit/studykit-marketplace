---
timestamp: 2026-04-25_1348
topic: pipeline-restructure
previous: 2026-04-25_1330_tier-a-4-default-mode-rolled-out.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-25_1348. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# pipeline-restructure — checkpoint at 2026-04-25_1348

This session reversed Tier A item 4 of the prior handoff and the broader workflow-mode infrastructure that surrounded it. Tier B item 5 (formalize `default_mode` / `mode_transitions` in `references/frontmatter-schema.md`) is now obsolete and has been retired alongside the implementation it would have documented. The shipped workflow-mode axis was found to be end-to-end inert at runtime and architecturally unimplementable on Claude Code's hook surface; the design has been retired in full and a successor ADR records the rationale.

## What is committed

- `6dcf4c6c8` — `refactor(a4): retire workflow-mode axis end-to-end`. 18 files changed, 139 insertions / 641 deletions.
  - Deletes `plugins/a4/scripts/workflow_mode.py` (state-machine CLI).
  - Deletes `plugins/a4/references/workflow-mode.md` (operational spec).
  - Edits `plugins/a4/scripts/a4_hook.py` — removes `_session_end`, the `session-end` dispatch in `main()`, the `_workflow_mode_init/_sweep/_cleanup` helpers, the `_session_start` calls into them, and the workflow-mode language in the module docstring.
  - Edits `plugins/a4/hooks/hooks.json` — drops the SessionEnd Python hook entry (the bash `cleanup-edited-a4.sh` SessionEnd hook stays); strips workflow-mode language from the top-level description and from the SessionStart description.
  - Edits twelve `SKILL.md` files — removes both `default_mode:` and `mode_transitions:` frontmatter blocks from `idea`, `spark-brainstorm`, `usecase`, `auto-usecase`, `arch`, `auto-bootstrap`, `decision`, `research`, `research-review`, `roadmap`, `run`, `task`. (Mechanical skills `handoff`, `compass`, `drift`, `validate`, `index`, `web-design-mock` never declared the fields.)
  - Edits `plugins/a4/skills/roadmap/SKILL.md:130` — removes the "distinct from the workflow-mode axis" disambiguation comment beside `EnterPlanMode`.
  - Bumps `.claude-plugin/marketplace.json` a4 1.18.0 → 1.19.0.
  - Adds `plugins/a4/spec/2026-04-25-workflow-mode-axis-retirement.decide.md` — successor ADR with full rationale and options-considered analysis.
- `422e1002a` (prior, last session) — handoff snapshot for the now-retired Tier A item 4.
- `87294cda6` (prior) — `feat(a4): roll default_mode into remaining mode-aware skills`. The frontmatter blocks added in this commit were removed in `6dcf4c6c8`.
- `efb25d593` (prior) — `fix(prompts): clarify Korean reply trigger`.

`git log --oneline -5` should show `6dcf4c6c8` on top, with `422e1002a`, `87294cda6`, `efb25d593`, `e831de4ff` underneath.

## Why retired (compressed)

The full rationale lives in `plugins/a4/spec/2026-04-25-workflow-mode-axis-retirement.decide.md`. Four failure modes drove the decision:

1. **`current_mode` had no readers or transition writers.** `grep -rn "workflow_mode" plugins/a4 --include="*.py" --include="*.sh" --include="*.json"` returned only the lifecycle hook wiring and the script itself. No skill, agent, or script ever called `workflow_mode.py get` or `set`. The `_workflow_mode_init` helper hardcoded `current_mode="conversational"`. The state machine had no live consumer.

2. **SessionStart-reads-first-skill is architecturally impossible.** The retired `references/workflow-mode.md:78` claimed the SessionStart hook reads the first invoked skill's `default_mode`. SessionStart fires before any user prompt or skill invocation; there is no "first invoked skill" at that point.

3. **No Claude Code hook surface covers all skill-invocation paths uniformly.** PreToolUse on `Skill` catches Claude-initiated `Skill(...)` calls but misses user-typed `/a4:run` (harness-routed without a tool call) and harness-level auto-triggered description matches. UserPromptSubmit catches user-typed slash commands but misses the other two. SessionStart cannot be skill-derived. The required hook event does not exist on Claude Code today.

4. **`mode_transitions` was prose-in-YAML smuggling.** Each block was 6-12 lines of free-form English prose nested in YAML lists. The retired schema spec itself acknowledged the items were "free-form prose, not enums" — i.e., explicitly unmachine-readable. Putting prose in a structured-data slot owned by an external system (Claude Code's SKILL.md frontmatter) bought nothing: cannot be validated, will never be parsed by code, harder to read than plain markdown, inflated the YAML header.

The conjunction of failure modes 1-3 is decisive: the shipped infrastructure had no observable effect, the documented integration path could not work, and no alternative hook surface exists. Failure mode 4 separately motivated removing `mode_transitions` from frontmatter on its own merits.

## Status of the prior handoff's open items

The prior handoff (`2026-04-25_1330_tier-a-4-default-mode-rolled-out.md`) listed Tier B and Tier C carry-forward items. After this session:

### Tier B (schema/docs alignment) — resolved by retirement

5. ~~`references/frontmatter-schema.md` — formalize `default_mode` and `mode_transitions`~~ — **obsolete**. The fields no longer exist; the schema doc remains correctly scoped to a4 workspace (issue/wiki) frontmatter and needs no change.
6. ~~`roadmap/SKILL.md` Task File Schema example missing `kind:`~~ — closed by prior session.
7. **`compass/SKILL.md` Layer 1–4 routing — refine recommendations now that `/a4:run` and `/a4:task` exist as concrete entry points.** Still open. Independent of the workflow-mode retirement.

### Tier C (open design questions) — partially resolved

8. **`/a4:arch` ADR-generation pattern** — A (multi-agent debate), B (research-drafter), C (passive detector). Combination B+C is the leading proposal. Still open.
9. **`decision` skill `## Next Steps` guardrail** — once authors stop hand-rolling tasks in ADR Next Steps, advise that implementation items become `/a4:task` invocations. Still open.
10. **"남은 일" single source** — `/a4:task` task files plausibly become the canonical tracker; deprecation of ADR `## Next Steps` and handoff `§Open / carried forward` as task-trackers still TBD. Still open.
11. **`roadmap-reviewer` UC-less audit** — review criteria still UC-coverage-shaped; needs reframing for projects whose tasks are ADR-justified. Still open.
12. **`/a4:run` final-fallback policy** — when neither `roadmap.md` nor `bootstrap.md` exists, the skill currently halts and recommends running one of them first. A "best-effort auto-detect" or "read AGENTS.md / package.json scripts" fallback is unresolved. Surfaced in `run/SKILL.md` § Out of Scope.

## What was deliberately not changed

- **`plugins/a4/spec/2026-04-25-workflow-mode-axis.decide.md`** — the retired ADR remains immutable per the spec/ convention. Supersession is recorded by the new ADR (`2026-04-25-workflow-mode-axis-retirement.decide.md`), not by editing the original.
- **`plugins/a4/spec/2026-04-25-plan-restructure.decide.md`** — also immutable. Its core contribution (the `roadmap` / `task` / `run` skill split) is unaffected by this retirement; only the `default_mode:` rollout claim within it is implicitly retracted. The retirement ADR §Consequences notes this without editing the plan-restructure ADR.
- **Prior handoffs in `plugins/a4/.handoff/pipeline-restructure/`** — all four prior handoffs remain immutable point-in-time snapshots. Their open-items lists describe the world as it was at that timestamp; this handoff records the current state.
- **`plugins/a4/references/frontmatter-schema.md`** — never modified. It was correctly scoped to a4-workspace issue/wiki frontmatter all along; the proposed "Skill metadata" section was never added because it would have been a category error (skill frontmatter is owned by Claude Code, not by a4; a4 only ever had custom-field extensions).
- **`plugins/a4/references/hook-conventions.md`** — never modified. Its rules are not workflow-mode-specific. The §2 "edit-record family" SessionEnd cleanup pattern still has a live instance (`cleanup-edited-a4.sh`); the table on line 185 listing SessionEnd as "Always exit 0" remains accurate for the bash hook that survives.
- **`plugins/a4/hooks/README.md`** — never modified. It already only mentioned the `session-start` subcommand, not `session-end`.

## Hook surface today (post-retirement)

`plugins/a4/hooks/hooks.json` declares four events:

- **PostToolUse** (`Write|Edit|MultiEdit`) — `a4_hook.py post-edit`. Records edited `a4/*.md` to `.claude/tmp/a4-edited/a4-edited-<sid>.txt` and reports per-component status-consistency mismatches as `additionalContext`.
- **Stop** — `a4_hook.py stop`. Validates all `a4/*.md` edited this session via `validate_frontmatter.py` + `validate_body.py` (in-process imports). Returns `2` on violations to force Claude retry.
- **SessionStart** — two hooks in declared order: (1) `sweep-old-edited-a4.sh` (bash) deletes orphan `a4-edited-*.txt` files older than 1 day, (2) `a4_hook.py session-start` refreshes UC `implemented_by:` reverse-links via `refresh_implemented_by.py` and reports workspace-wide status-consistency mismatches via `validate_status_consistency.py`.
- **SessionEnd** — single hook: `cleanup-edited-a4.sh` (bash) deletes this session's `a4-edited-<sid>.txt` record file. The Python `session-end` dispatcher subcommand is gone.

The dispatcher's subcommand set is now `post-edit | stop | session-start`. `session-end` was deleted.

## Where to start the next session

The pipeline-restructure thread's mode-axis sub-thread is closed. Open items above (Tier B item 7, Tier C items 8-12) are independent of mode and can be tackled in any order.

**Default suggestion: Tier C item 12** — `/a4:run` final-fallback policy when neither `roadmap.md` nor `bootstrap.md` exists. Currently the skill halts and recommends running one of them first; the question is whether a best-effort auto-detect (read `AGENTS.md`, `package.json` scripts, `Makefile`, etc.) is preferable for UC-less / bootstrap-less projects. Concrete trigger surface: `run/SKILL.md` § Out of Scope explicitly flags this as unresolved.

If the user wants something else, alternative starting points:

- **Tier C item 8** — `/a4:arch` ADR-generation pattern. The previously leading proposal is B+C (research-drafter + passive detector). Decide and ship.
- **Tier C item 9** — `decision` skill `## Next Steps` guardrail.
- **Tier C item 11** — `roadmap-reviewer` UC-less audit reframing.
- **Tier B item 7** — `compass/SKILL.md` Layer 1–4 routing refresh now that `/a4:run` and `/a4:task` exist.

## Files to inspect first

- `plugins/a4/spec/2026-04-25-workflow-mode-axis-retirement.decide.md` — the rationale for what was removed, including the four failure modes and three options considered. Read this first if any question about the retirement comes up.
- `plugins/a4/scripts/a4_hook.py` — the post-retirement dispatcher. Subcommands `post-edit`, `stop`, `session-start` only. Reads cleaner now (the workflow-mode helpers section is gone).
- `plugins/a4/hooks/hooks.json` — current hook wiring after the SessionEnd Python entry was removed.
- `plugins/a4/skills/run/SKILL.md` — the canonical autonomous-skill body example. Note that the frontmatter no longer carries `default_mode:` or `mode_transitions:`. Mode-as-prompting-guidance is implicit in the body's step structure and decision points.
- `plugins/a4/skills/task/SKILL.md` — the canonical conversational-skill body example, similarly cleaned.
- `plugins/a4/references/hook-conventions.md` — unchanged but worth re-reading; the rules apply uniformly to all four remaining hooks.

## Don'ts (carried, refreshed)

- Don't reintroduce `default_mode:` or `mode_transitions:` frontmatter on any SKILL.md without first defining a runtime consumer that can read them. The retirement ADR enumerates the failure modes; any reintroduction proposal must address all four.
- Don't reintroduce `scripts/workflow_mode.py` or any `current_mode` state file under `a4/.workflow-state/` without a hook event that can drive it (Claude Code does not currently provide one).
- Don't add a "Skill metadata" section to `references/frontmatter-schema.md`. That doc is correctly scoped to a4-workspace issue/wiki frontmatter; SKILL.md frontmatter is Claude Code's schema, not a4's.
- No backwards-compat for `kind: plan`. Forward-only.
- No edits in `plugins/a4/.handoff/**` or `plugins/a4/spec/**` (point-in-time / immutable). Supersession is recorded by writing a successor file, not by amending originals.
- Don't merge `/a4:roadmap` and `/a4:run` back together. The split is decided and shipped.
- Never `rm -rf a4` from the studykit-plugins root. Match `A4/` case-insensitively on macOS and you wipe tracked content. Use absolute paths under `/tmp` for hook smoke tests, or scoped paths like `plugins/a4/<thing>`.
- Per-skill mode-transition prose belongs in skill body markdown (e.g., a `## Mode transitions` section) if it's added at all — never in YAML frontmatter. The retirement ADR §Failure mode 4 documents why.
