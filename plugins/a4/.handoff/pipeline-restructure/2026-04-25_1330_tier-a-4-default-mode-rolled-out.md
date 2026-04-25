---
timestamp: 2026-04-25_1330
topic: pipeline-restructure
previous: 2026-04-25_1322_tier-a-1-2-3-shipped.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-25_1330. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# pipeline-restructure — checkpoint at 2026-04-25_1330

Tier A is now fully closed. This session shipped Tier A item 4 from `2026-04-25_1322_tier-a-1-2-3-shipped.md` in commit `87294cda6` — `default_mode:` and skill-specific `mode_transitions:` rolled into the nine remaining mode-aware SKILL.md files. Tier B and Tier C remain. Tier B item 5 (formalize the two fields in `references/frontmatter-schema.md`) is now the natural next step because every mode-aware skill declares them and the schema needs to catch up.

## What is committed

- `87294cda6` — `feat(a4): roll default_mode into remaining mode-aware skills`. 10 files changed, 83 insertions / 1 deletion. Nine SKILL.md files updated; marketplace bumped 1.17.0 → 1.18.0.
- `efb25d593` (prior, this session's user commit) — `fix(prompts): clarify Korean reply trigger`. Resolves the dangling `global/prompts/discuss.md` modification flagged as out-of-scope in the previous handoff. The working tree is now clean apart from anything the next session creates.
- `e831de4ff` (prior) — handoff snapshot.
- `defdec4da` (prior) — Tier A items 1–3 shipped.
- `967f9fc03` (prior) — handoff snapshot.

`git log --oneline -6` should show these on top of `78870cad4`.

### Files changed in `87294cda6`

| File | Mode declared | Notes |
|---|---|---|
| `plugins/a4/skills/idea/SKILL.md` | conversational | Capture/discard skill. `disable-model-invocation: true` retained. |
| `plugins/a4/skills/spark-brainstorm/SKILL.md` | conversational | Technique selection / idea convergence are user judgment. |
| `plugins/a4/skills/usecase/SKILL.md` | conversational | One-question-at-a-time Socratic UC discovery. |
| `plugins/a4/skills/auto-usecase/SKILL.md` | autonomous | Name reflects mode. |
| `plugins/a4/skills/arch/SKILL.md` | conversational | Phase-by-phase dialogue with auto-drill into research / decision-drafter / arch-drafter agents. |
| `plugins/a4/skills/auto-bootstrap/SKILL.md` | autonomous | Name reflects mode. |
| `plugins/a4/skills/decision/SKILL.md` | conversational | Records a decision reached by conversation; mechanical writes after handoff token. |
| `plugins/a4/skills/research/SKILL.md` | conversational | User-led research; can hand off to agent-driven investigation. |
| `plugins/a4/skills/research-review/SKILL.md` | autonomous | Review-agent driven; flagged issues require user disposition. |
| `.claude-plugin/marketplace.json` | — | a4 1.17.0 → 1.18.0. |

Each `mode_transitions` block is **skill-specific**, not boilerplate copied from the canonical lists in `references/workflow-mode.md`. The intent: the canonical lists in `workflow-mode.md` are workspace-wide always-on triggers; per-skill blocks enumerate the concrete decision points, ambiguity triggers, ratification gates, and agent-drill points particular to that skill. Adding new triggers to the canonical lists later does not require editing every SKILL.md.

## Mechanical skills remain frontmatter-silent

`handoff`, `compass`, `drift`, `validate`, `index`, `web-design-mock` — none declare `default_mode:` or `mode_transitions:`. This is by design per the table in `references/workflow-mode.md`: they are mode-agnostic. The hook still defaults to `conversational` when the first invoked skill is mode-less.

## What is decided but not implemented

The previous handoff's Tier A is now closed. Carrying forward:

### Tier B (schema/docs alignment)

5. **`references/frontmatter-schema.md` — formalize `default_mode` and `mode_transitions`** under a new "Skill metadata" section. Currently nowhere in the schema; eleven SKILL.md files (`roadmap`, `run`, `task` from `defdec4da`, plus the nine from `87294cda6`) now use both fields without a normative reference. **This is the recommended next item** — it is the natural completion of Tier A item 4.
6. ~~`roadmap/SKILL.md` Task File Schema example missing `kind:`~~ — closed by the prior session's roadmap rewrite.
7. `compass/SKILL.md` Layer 1–4 routing — refine recommendations now that `/a4:run` and `/a4:task` exist as concrete entry points.

### Tier C (open design questions)

8. `/a4:arch` ADR-generation pattern — A (multi-agent debate), B (research-drafter), C (passive detector). Combination B+C is the leading proposal. Not committed.
9. `decision` skill `## Next Steps` guardrail — once authors stop hand-rolling tasks in ADR Next Steps, advise that implementation items become `/a4:task` invocations.
10. "남은 일" single source — `/a4:task` task files plausibly become the canonical tracker; deprecation of ADR `## Next Steps` and handoff `§Open / carried forward` as task-trackers still TBD.
11. `roadmap-reviewer` UC-less audit — review criteria still UC-coverage-shaped; needs reframing for projects whose tasks are ADR-justified.
12. `/a4:run` final-fallback policy — when neither `roadmap.md` nor `bootstrap.md` exists, the skill currently halts and recommends running one of them first. A "best-effort auto-detect" or "read AGENTS.md / package.json scripts" fallback is unresolved. Surfaced explicitly in `run/SKILL.md` § Out of Scope.

## Mode-transition triggers as written (reference for the schema work in Tier B item 5)

The next session may want to use these as input when writing the schema's "Skill metadata" section. Reproduced verbatim so the schema author does not need to grep the nine files separately.

### `idea` — conversational

- **to_conversational**: capture invoked with no idea text; discard target `<id-or-slug>` matches zero or multiple files.
- **to_autonomous**: user emits an explicit handoff token after the idea / discard target is settled and only the mechanical write remains.

### `spark-brainstorm` — conversational

- **to_conversational**: technique selection requires user choice (SCAMPER vs Free vs Mind Mapping vs Reverse vs Random Stimulus, etc.); idea ranking, pruning, or convergence requires user judgment; follow-up topic ambiguity after a brainstorm pass.
- **to_autonomous**: user emits an explicit handoff token to run the selected technique mechanically (e.g., generate N more ideas via the chosen prompt) with no further input expected.

### `usecase` — conversational

- **to_conversational**: every Socratic interview question — one decision per turn; actor / domain-term disambiguation; UC scope or boundary ambiguity (split vs merge); review-item triage requires user disposition.
- **to_autonomous**: user invokes `/a4:auto-usecase` mid-flight to hand the rest of the discovery to the autonomous generator; user emits an explicit handoff token after the UC set is settled and only mechanical wiki + per-UC file writes remain.

### `auto-usecase` — autonomous

- **to_conversational**: input is too thin to generate a UC set without user clarification; generator agent returns `clarification_needed` or low-confidence on a UC set; review items surface a fundamental gap (missing actor, contradictory NFR, scope overlap with existing UCs); destructive operation proposed (overwriting an existing populated `a4/usecase/` set without label).
- **to_autonomous**: skill invoked directly (`/a4:auto-usecase`) — autonomous is the declared default, name reflects mode; resume after the user resolves a clarification request and confirms the next pass.

### `arch` — conversational

- **to_conversational**: phase decision points (tech stack, external dependencies, component boundaries, information flows, interface contracts, test strategy); alternative trade-off requires user choice; ADR-worthy decision surfaces — recommend `/a4:decision` and stop; architecture-reviewer surfaces a usecase-level finding requiring `/a4:usecase iterate`.
- **to_autonomous**: auto-drill into research / decision-drafter / architecture-drafter agents during a phase, returning to conversational on agent completion; user emits an explicit handoff token after a phase is settled and only mechanical wiki-page emission remains.

### `auto-bootstrap` — autonomous

- **to_conversational**: architecture document is missing required fields (tech stack, test strategy) — cannot bootstrap autonomously; build / launch / test command verification fails after retries; destructive operation proposed (overwriting an existing populated `bootstrap.md` without label, deleting prior project files); bootstrap-agent returns `clarification_needed` or ambiguous tooling decision.
- **to_autonomous**: skill invoked directly (`/a4:auto-bootstrap`) — autonomous is the declared default, name reflects mode; resume after the user resolves a clarification or confirms a destructive action.

### `decision` — conversational

- **to_conversational**: decision text or alternatives could not be unambiguously extracted from recent conversation; related research artifact pointer ambiguous (multiple `./research/<slug>.md` candidates, or none when expected); affected wiki pages selection requires user choice (which of architecture / context / domain / actors / nfr to nudge); finalization of an existing draft decision requires user ratification.
- **to_autonomous**: user emits an explicit handoff token after the decision body is settled and only mechanical id allocation, file write, and wiki-page nudges remain.

### `research` — conversational

- **to_conversational**: research scope or option list ambiguous (no comma-separated alternatives, brainstorm/idea file path resolves to multiple candidates); sub-topic prioritization requires user judgment; conflicting sources require user-driven adjudication.
- **to_autonomous**: user emits an explicit handoff token to run agent-driven investigation (web search + draft) with no further input expected; user invokes `/a4:research-review` after the artifact is written (mode flips at the skill boundary).

### `research-review` — autonomous

- **to_conversational**: research-reviewer flags an issue requiring user disposition (apply / dismiss / defer); destructive revision proposed (rewriting whole sections, deleting prior conclusions); target path ambiguous or missing.
- **to_autonomous**: skill invoked directly (`/a4:research-review`) — autonomous is the declared default, name reflects mode; resume after the user resolves a flagged issue and confirms the next disposition.

## Where to start the next session

**Default suggestion: Tier B item 5** — formalize `default_mode` and `mode_transitions` in `references/frontmatter-schema.md`.

Concrete shape:

- New section heading **"Skill metadata"** at the top level of the schema doc, alongside the existing UC / task / decision / etc. sections (which describe **issue** frontmatter — separate concern).
- For `default_mode`: enum of `conversational | autonomous`. Required on mode-aware skills. Omitted on mechanical skills (`handoff`, `compass`, `drift`, `validate`, `index`, `web-design-mock`).
- For `mode_transitions`: object with two optional list-of-string fields, `to_conversational` and `to_autonomous`. List items are short condition phrases (free-form prose, not enums) that document the concrete trigger in human-readable form. The canonical workspace-wide trigger lists live in `references/workflow-mode.md` and apply additively — per-skill lists are skill-specific, not a complete enumeration.
- Cross-reference `references/workflow-mode.md` § Default Mode by Skill (canonical mapping) and § Transition Triggers (canonical workspace-wide list).
- Note that hook code does **not** yet read `default_mode` from frontmatter — `a4_hook.py session-start` seeds `conversational` unconditionally. Wiring that read is a separate later task; this schema-doc change does not depend on it.

Worked examples to point at:

- `plugins/a4/skills/run/SKILL.md` — autonomous example with detailed `mode_transitions`.
- `plugins/a4/skills/task/SKILL.md` — conversational example.
- `plugins/a4/skills/roadmap/SKILL.md` — hand-off-style conversational with `to_autonomous` triggers that fire only at skill boundary.
- `plugins/a4/skills/idea/SKILL.md` — minimal conversational example (capture/discard).
- `plugins/a4/skills/auto-usecase/SKILL.md` and `auto-bootstrap/SKILL.md` — autonomous skills whose name reflects mode.

## How `/a4:run` / `/a4:task` / mode-aware skills behave today

Unchanged from `2026-04-25_1322_tier-a-1-2-3-shipped.md`. That handoff still describes the worked behavior of `/a4:run`, `/a4:task`, and `a4_hook.py` accurately. Re-read its sections "How `/a4:run` behaves today", "How `/a4:task` behaves today", and "How `a4_hook.py` is wired today" if needed.

What's new at this checkpoint is purely **declarative**: nine more SKILL.md files now state their mode contract in frontmatter. No runtime behavior changed. No hooks, scripts, or skill bodies were touched.

## Files to inspect first

- `plugins/a4/references/workflow-mode.md` — the canonical default-mode-by-skill table; § Transition Triggers lists the workspace-wide always-on triggers.
- `plugins/a4/references/frontmatter-schema.md` — target of Tier B item 5. Currently has no "Skill metadata" section.
- `plugins/a4/skills/run/SKILL.md` and `plugins/a4/skills/task/SKILL.md` — canonical worked examples for autonomous and conversational respectively.
- `plugins/a4/skills/roadmap/SKILL.md` — hand-off-style conversational; useful when documenting how `to_autonomous` is intended to fire at skill boundaries.
- The nine SKILL.md files committed in `87294cda6` — collectively the per-skill transitions reference for the schema author.
- `plugins/a4/spec/2026-04-25-workflow-mode-axis.decide.md` — design rationale for the mode axis.

## Don'ts (carried, refreshed)

- No backwards-compat for `kind: plan`. Forward-only.
- No edits in `plugins/a4/.handoff/**` or `plugins/a4/spec/**` (point-in-time, immutable).
- Don't merge `/a4:roadmap` and `/a4:run` back together. The split is decided and shipped.
- Don't consume `default_mode:` from skill frontmatter inside hook code yet. Eleven skills now declare it, but the hook still seeds `conversational` unconditionally — that wiring is a separate later task. Tier B item 5 (this session's recommended next) is documentation only; do not extend its scope into hook code.
- Per-skill `mode_transitions` lists are **additive**, not exhaustive. The canonical workspace-wide triggers in `references/workflow-mode.md` § Transition Triggers always apply on top. When formalizing the schema in Tier B item 5, document this additive relationship explicitly.
- Never `rm -rf a4` from the studykit-plugins root. Match `A4/` case-insensitively on macOS and you wipe tracked content. Use absolute paths under `/tmp` for hook smoke tests, or scoped paths like `plugins/a4/<thing>`.
- The `global/prompts/discuss.md` modification flagged in the previous handoff was committed by the user as `efb25d593 fix(prompts): clarify Korean reply trigger` before this session's changes. The working tree carrying that file forward is no longer a concern; do not re-flag it as out-of-scope leakage.
