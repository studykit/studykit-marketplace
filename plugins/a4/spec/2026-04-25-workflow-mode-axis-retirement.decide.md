---
type: decide
pipeline: spark
topic: "Workflow Mode Axis Retirement"
date: 2026-04-25
updated: 2026-04-25
status: final
framework: "analysis-driven"
decision: "Retire the workflow-mode axis end-to-end. Delete scripts/workflow_mode.py, references/workflow-mode.md, the SessionEnd Python hook, and the SessionStart workflow-mode init/sweep. Strip default_mode and mode_transitions frontmatter from all SKILL.md files. Mode-as-prompting-guidance moves to skill body prose where the LLM actually attends to it."
supersedes: ["2026-04-25-workflow-mode-axis"]
tags: [a4-pipeline, workflow, retirement, hooks, skill-frontmatter]
---

# Decision Record: Workflow Mode Axis Retirement

> Supersedes `2026-04-25-workflow-mode-axis.decide.md`. The earlier ADR shipped a session-scoped state-machine for a `conversational | autonomous` mode axis with per-skill `default_mode:` + `mode_transitions:` frontmatter. Subsequent investigation in the same calendar day found the design end-to-end inert at runtime and architecturally unimplementable on Claude Code's hook surface. This ADR records the retirement.

## Context

The retired ADR (`2026-04-25-workflow-mode-axis`) declared three components:

1. **State machine** at `<project-root>/a4/.workflow-state/<session-id>.json`, managed by `scripts/workflow_mode.py` (subcommands `init` / `get` / `set` / `history` / `cleanup` / `sweep`).
2. **Lifecycle hooks** wired through `scripts/a4_hook.py`: `_workflow_mode_init/_sweep` at SessionStart, `_workflow_mode_cleanup` at SessionEnd.
3. **Skill frontmatter contract**: `default_mode: conversational | autonomous` declares the entry mode; `mode_transitions:` documents skill-specific triggers as free-form prose lists.

After Tier A item 4 of the pipeline-restructure thread rolled `default_mode` and `mode_transitions` into the remaining nine mode-aware SKILL.md files (commit `87294cda6`), totaling twelve declarations across the plugin's skills, a follow-up review surfaced three distinct failure modes:

### Failure mode 1 — `current_mode` has no readers or transition writers

Auditing the live tree:

- `grep -rn "workflow_mode\|workflow-mode" plugins/a4 --include="*.py" --include="*.sh" --include="*.json"` returned only the hook lifecycle wiring in `a4_hook.py` and the script itself.
- No skill body, no agent, no script outside the lifecycle ever invoked `workflow_mode.py get` or `workflow_mode.py set`.
- The `_workflow_mode_init` helper hardcoded `current_mode="conversational"` (`a4_hook.py:467`); the `--mode` CLI flag on `workflow_mode.py init` was never exercised.

Net runtime behavior: the state file was born `conversational`, lived `conversational`, died `conversational`. The state machine had no readers and no transition writers besides creation. It was a database row no query ever read.

### Failure mode 2 — SessionStart-reads-first-skill is architecturally impossible

`references/workflow-mode.md:78` (in the retired form) stated:

> "When a skill is the **first** invocation of a session, the SessionStart hook reads its `default_mode` and seeds the session file."

SessionStart fires before any user prompt or skill invocation. There is no "first invoked skill" at that point — the user has not typed anything, and Claude has not yet selected a skill via description match. The hook surface cannot know which skill will be invoked first.

### Failure mode 3 — no Claude Code hook surface covers all skill-invocation paths

To make `default_mode` runtime-meaningful would require a hook event that fires on every skill invocation regardless of how the skill was triggered. The available events do not provide this:

| Surface | Coverage | Limitation |
|---|---|---|
| PreToolUse on `Skill` tool | Claude-initiated `Skill(...)` calls | Misses user-typed `/a4:run` (harness routes the slash command directly without a tool call) and misses harness-level auto-triggered description matches |
| UserPromptSubmit, parse `/a4:<name>` | User-typed slash commands | Misses Claude-initiated and auto-triggered cases; brittle string parsing of free-form prompts |
| SessionStart with `additionalContext` | All sessions | Cannot be skill-derived because no skill is yet in scope |

No single available hook covers all three skill-invocation paths uniformly. The retired design assumed a hook surface Claude Code does not provide.

### Failure mode 4 — `mode_transitions` was prose-in-YAML smuggling

Reviewing `arch/SKILL.md:7-15`, `run/SKILL.md:7-17`, and the seven other mode-aware SKILL.md files: each `mode_transitions:` block was 6-12 lines of free-form English prose stuffed into nested YAML lists. The retired schema spec itself acknowledged the items were "free-form prose, not enums" — i.e., explicitly unmachine-readable. Stuffing prose into a structured-data slot owned by an external system (Claude Code's SKILL.md frontmatter) buys nothing:

- Cannot be validated (no enum)
- Will never be parsed by code (the schema author explicitly disclaimed it)
- Harder to read and edit than a plain `## Mode transitions` body section
- Inflates the YAML header so the actual SKILL.md body sits below the screen fold

If the intended consumer is the LLM reading SKILL.md when the skill triggers, body markdown serves better than nested YAML lists.

## Decision

Retire the workflow-mode axis in full. Specifically:

1. **Delete `plugins/a4/scripts/workflow_mode.py`** — the state-machine CLI.
2. **Delete `plugins/a4/references/workflow-mode.md`** — the operational spec for retired infrastructure.
3. **Edit `plugins/a4/scripts/a4_hook.py`** — remove `_session_end`, the `session-end` dispatch, the `_workflow_mode_init/_sweep/_cleanup` helpers, and their calls inside `_session_start`. Update the module docstring to reflect the reduced subcommand set (`post-edit` / `stop` / `session-start` only).
4. **Edit `plugins/a4/hooks/hooks.json`** — remove the SessionEnd Python hook entry (the bash `cleanup-edited-a4.sh` SessionEnd hook stays). Strip workflow-mode language from the top-level description and from the SessionStart description.
5. **Edit twelve SKILL.md files** — remove both `default_mode:` and `mode_transitions:` frontmatter blocks from `idea`, `spark-brainstorm`, `usecase`, `auto-usecase`, `arch`, `auto-bootstrap`, `decision`, `research`, `research-review`, `roadmap`, `run`, `task`. The mechanical skills (`handoff`, `compass`, `drift`, `validate`, `index`, `web-design-mock`) never declared the fields and are unaffected.
6. **Edit `plugins/a4/skills/roadmap/SKILL.md:130`** — remove the "distinct from the workflow-mode axis" disambiguation comment beside `EnterPlanMode` (no remaining axis to disambiguate against).
7. **Bump `.claude-plugin/marketplace.json` a4 version 1.18.0 → 1.19.0**.

## Rationale

The case for retirement is the conjunction of failure modes 1-3:

- Failure mode 1 alone establishes that the shipped infrastructure has zero observable effect. Removing it cannot regress behavior because there was no behavior.
- Failure mode 2 establishes that the documented integration path was never going to work. Wiring `default_mode` reads at SessionStart cannot be made to function as described.
- Failure mode 3 establishes that no alternative hook event provides the uniform coverage the design needs. The hook surface required does not exist on Claude Code today.

Together, the retired design depends on (a) a runtime that consumes mode (none built), (b) a hook event that reads skill frontmatter at the right moment (none available), and (c) skill authors maintaining frontmatter for both. Two of three preconditions are unrecoverable without changes external to the plugin.

Failure mode 4 separately argues that `mode_transitions` was misplaced even on its own merits. Retiring the field clears the way for the same content to live in body markdown if a future redesign wants it there.

The mode-as-prompting-guidance value — the LLM noticing decision points, ratification gates, agent-drill points within a skill — is preserved by leaving that content in the skill body where it has always been the dominant signal, and is not lost by removing the frontmatter declarations that no consumer ever read.

## Options Considered

### A. Retire end-to-end (chosen)

Delete the infrastructure, the docs, the script, the frontmatter. Mode becomes a documentation concept inside skill bodies, not a runtime state machine.

- **Pros**: Removes inert code. Eliminates the architecturally impossible SessionStart-reads-first-skill claim. Frees skill authors from maintaining frontmatter no consumer reads.
- **Cons**: Loses the ability to ever flip mode programmatically without a future redesign. (Acceptable: the current design could not flip it either.)

### B. Skill-body-driven via `Bash(workflow_mode.py set ...)` plus UserPromptSubmit hook

Each autonomous skill begins with a Bash invocation to set the state file; a new UserPromptSubmit hook injects the current mode as `additionalContext` so Claude can attend to it across prompts.

- **Pros**: Keeps the state-machine infrastructure. Provides a real path to surface mode to the LLM.
- **Cons**: Requires designing and shipping the UserPromptSubmit hook (not built). Requires modifying every skill body to write transitions (not built). Mode visible only on the *next* prompt after a flip — within-prompt transitions remain invisible. `default_mode` frontmatter remains unused since the body controls the flip. End result is mostly the same prompting-guidance pattern as Option A but with a stateful coupling that can drift.

### C. Defer pending Claude Code hook surface changes

Wait for Claude Code to add a `SkillStart` (or equivalent) hook event, then revisit.

- **Pros**: Preserves the existing infrastructure and frontmatter declarations against a possible future where they become useful.
- **Cons**: The infrastructure remains inert in the meantime. The frontmatter declarations remain prose-in-YAML antipatterns. Twelve SKILL.md files carry maintenance burden for hypothetical future use. No concrete signal that the hook event is forthcoming.

Option A wins because the existing implementation has no live consumer and the documented integration path is impossible. Options B and C both require external preconditions (a built hook, or an unreleased Claude Code event) before any value materializes.

## Consequences

- The infrastructure is gone. Future sessions reading these spec ADRs alone (without checking the live tree) may believe the workflow-mode axis still exists; they need to consult this retirement ADR or the live tree.
- `references/frontmatter-schema.md` was never modified to formalize `default_mode` / `mode_transitions` — that work (Tier B item 5 of the pipeline-restructure thread) is now obsolete. The frontmatter-schema doc remains correctly scoped to the a4 workspace (issue/wiki frontmatter), unrelated to SKILL.md frontmatter.
- The plan-restructure ADR (`2026-04-25-plan-restructure.decide.md`) mentions `default_mode:` rollout as a follow-up step. Its core contribution — the `roadmap` / `task` / `run` skill split — is unaffected by this retirement; only the frontmatter rollout claim within it is retracted. The ADR is not superseded.
- No SKILL.md content was lost beyond the frontmatter blocks. The body sections of each skill already describe their decision points and handoff conditions; the frontmatter blocks were duplicating content the body always carried.
- `references/hook-conventions.md` continues to apply unchanged — its examples and rules are not workflow-mode-specific. The §2 "edit-record family" SessionEnd cleanup pattern still has a live instance (`cleanup-edited-a4.sh`).

## Out of Scope

- Designing a successor mode-tracking mechanism. If a future need arises, that becomes its own ADR.
- Editing the retired ADR (`2026-04-25-workflow-mode-axis`) or the plan-restructure ADR. Both remain immutable per the spec/ convention. Supersession is recorded here, not by amending the originals.
- Editing prior handoffs. They remain immutable point-in-time snapshots; this retirement is recorded by the next handoff in the `pipeline-restructure` thread (alongside this ADR commit).
