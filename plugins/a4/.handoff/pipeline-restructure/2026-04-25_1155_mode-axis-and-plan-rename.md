---
timestamp: 2026-04-25_1155
topic: pipeline-restructure
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-25_1155. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# a4 Plugin — Pipeline Restructure: mode axis + plan rename

This session opened a new thread, `pipeline-restructure`, that re-examined the a4 plugin's whole skill pipeline against two failure cases: callgraph-service (UC-less, ADR-heavy) couldn't enter the pipeline, and `/a4:arch` was supposed to delegate ADR creation to `/a4:decision` but the delegation trigger was buried deep enough that ADRs were never actually written from arch. The discussion produced two final ADRs and a series of decisions that landed partially in code and partially still pending. Net of session: pipeline reshape is *committed in code at the rename + workflow-mode-infrastructure level*; the larger structural changes (`/a4:run`, `/a4:task`, `default_mode` rollout, hook integration) are recorded as decisions but not yet implemented.

The single commit covering all in-tree changes is `d536cfe70`.

---

## 1. Headline

- `/a4:plan` renamed to `/a4:roadmap`. Forward-only — no backwards-compat shim. Validators reject `kind: plan` immediately. Same session also adopted `plan` as deprecated for the agent loop and earmarked `/a4:run` as its replacement (not yet implemented).
- Workflow mode formalized as a session-scoped axis (`conversational | autonomous`) with per-session state at `a4/.workflow-state/<session-id>.json`, concurrency-safe across multiple Claude Code sessions in the same workspace. New tool `scripts/workflow_mode.py` is the single entry point for hooks and skills.
- Two final ADRs landed: `spec/2026-04-25-workflow-mode-axis.decide.md` and `spec/2026-04-25-plan-restructure.decide.md`.
- Larger restructure (sketch 2 of 3 considered): `/a4:plan` becomes three skills — `/a4:roadmap` (Phase 1 authoring, conversational), `/a4:task` (single-task authoring, conversational), `/a4:run` (Phase 2 agent loop, autonomous). Only the rename half landed; `/a4:run` and `/a4:task` are *unwritten*.

---

## 2. What changed, where

### Renamed (git mv)

- `plugins/a4/skills/plan/` → `plugins/a4/skills/roadmap/`
- `plugins/a4/agents/plan-reviewer.md` → `plugins/a4/agents/roadmap-reviewer.md`
- `plugins/a4/skills/plan/references/planning-guide.md` → `plugins/a4/skills/roadmap/references/planning-guide.md` (auto-followed)

### New files

- `plugins/a4/references/workflow-mode.md` — full operational spec for the workflow-mode axis. Defines the two modes, session-state schema, lifecycle (init/sweep/cleanup), `default_mode` skill frontmatter contract, default-mode-by-skill table, canonical transition triggers (auto→conv and conv→auto), tool reference, and out-of-scope follow-ups.
- `plugins/a4/scripts/workflow_mode.py` — Python tool. Subcommands `init`, `get`, `set <mode> --trigger <reason>`, `history`, `cleanup`, `sweep`. Atomic writes via `.tmp` + rename. JSON output. `--session` arg with fallback chain `$CLAUDE_SESSION_ID` → SHA256 of `$CLAUDE_TRANSCRIPT_PATH` → pid+epoch. Pyright clean (uses `NoReturn` on `die()`).
- `plugins/a4/spec/2026-04-25-workflow-mode-axis.decide.md` — final ADR. Includes default-mode-by-skill table, canonical triggers, rejected alternatives, out-of-scope followups, discussion log.
- `plugins/a4/spec/2026-04-25-plan-restructure.decide.md` — final ADR. Documents the three-skill split rationale, artifact rename, conditional UC ship-review, AC-source-by-kind table, rejected alternatives, migration recipe.

### Modified — substitutive plan→roadmap rename across non-handoff, non-spec files

- `plugins/a4/README.md` — Skills row `plan` → `roadmap`, agents row `plan-reviewer` → `roadmap-reviewer`, layout diagram `plan.md` → `roadmap.md`.
- `plugins/a4/agents/roadmap-reviewer.md` — frontmatter `name:`, body sections, `target:` enum, `source:`, target-mapping table all updated.
- `plugins/a4/agents/task-implementer.md` — invoking-skill phrasing now `roadmap` / `run`; "Plan file path" → "Roadmap file path"; classification phrase `roadmap / arch / usecase`.
- `plugins/a4/agents/test-runner.md` — same pattern.
- `plugins/a4/references/frontmatter-schema.md` — wiki-page row, status-writer table (six entries: usecase shipped/discarded, four task rows, review in-progress), `kind` enum row for wiki pages, `usecase.implemented_by` derivation row.
- `plugins/a4/references/obsidian-conventions.md` — wiki-page list.
- `plugins/a4/scripts/common.py` — `WIKI_KINDS` set.
- `plugins/a4/scripts/index_refresh.py` — `WIKI_BASENAMES`, `roadmap_page` / `roadmap_row` (renamed local), Stage table label `Plan` → `Roadmap`.
- `plugins/a4/scripts/refresh_implemented_by.py` — module docstring (`/a4:run` for ship-check; `/a4:roadmap` for Phase 1 invocation site).
- `plugins/a4/scripts/transition_status.py` — error message guidance string.
- `plugins/a4/skills/arch/SKILL.md` — wrap-up step 5 next-skill suggestion.
- `plugins/a4/skills/auto-bootstrap/SKILL.md` — intro paragraph + final pointer.
- `plugins/a4/skills/compass/SKILL.md` — wiki-basename list, Pipeline (interactive) row replaced with `roadmap` / `task` / `run` three rows, route mappings in Layer 2 / Layer 3 / Layer 4.
- `plugins/a4/skills/drift/SKILL.md` — iterate-skill list.
- `plugins/a4/skills/index/SKILL.md` — drift alerts paragraph.
- `plugins/a4/skills/usecase/SKILL.md` — obsidian-conventions reference, wrap-up next-step.
- `plugins/a4/skills/validate/SKILL.md` — iterate-skill list.
- `plugins/a4/skills/roadmap/README.md` — title, primary-file path, current-behavior paragraph, `.plan.md` → `.roadmap.md` (PlantUML diagram still uses the old "plan" actor labels — flagged for future audit).
- `plugins/a4/skills/roadmap/SKILL.md` — frontmatter `name:`, description, intro, all artifact references, mode names (Roadmap mode / Iterate mode), Phase 1 heading, Plan body template `# Plan` → `# Roadmap`, milestones-narrative phrasing, agent prompts, commit-points headings, Non-Goals.
- `.claude-plugin/marketplace.json` — a4 description (`implementation-plan` → `implementation-roadmap`), version `1.15.0` → `1.16.0`.

### Deliberately not modified

- `plugins/a4/.handoff/**` — point-in-time snapshots, immutable per the banner contract. Several mention `plan.md` / `/a4:plan` / `kind: plan`. They are historical and a fresh session reading them must do its own substitution.
- `plugins/a4/spec/**` — finalized ADRs, also historical. Several mention plan; readers should treat them similarly. The two new ADRs from this session document the new shape.
- The PlantUML actor labels inside `skills/roadmap/README.md` — left as `plan (orchestrator)` / "Phase 2 — Implement + Test Loop" because that diagram describes the *legacy* combined skill. Once `/a4:run` is split out, that diagram should be reauthored or moved.

---

## 3. Decisions made, sequenced

In conversation order:

1. **callgraph-service had no `task/`, no `usecase/`** because `/a4:plan` was never invoked. Diagnosis confirmed by reading the workspace; conversation expanded into "should arch generate ADRs autonomously?" then to "what's the right pipeline shape?"
2. **Spike enum already in place but no skill writes single-task spike/bug/feature.** `kind: feature | spike | bug` is required per `frontmatter-schema.md`, but the only writer (`/a4:plan` Phase 1) only emits `kind: feature` from UCs. Decision: add `/a4:task` skill (recorded as #1 in the session task list). Not yet implemented.
3. **Sketch 2 over sketch 1, 3.** Three pipeline-restructure sketches were drawn: minimal (just add `/a4:task`), full split (`/a4:plan` → roadmap + task + run), tracks (UC-track and ADR-track). User chose sketch 2.
4. **plan was always intended for agent automation.** User clarification: Phase 2 (the agent loop) was the *original* core of `/a4:plan`. Phase 1 plan generation was scaffolding for it. So the split decision is not "plan got bloated and we excise the bloat" but "plan covers two tightly-coupled concerns; we name them separately."
5. **Workflow mode axis is orthogonal.** User reframing: the two modes (interactive with user vs LLM-autonomous) cut across all skills, not just specific ones. Session must be able to drift between them freely. Final ADR landed.
6. **Concurrent sessions are real.** User pointed out that `.workflow-state.json` as a single file would race across simultaneous Claude Code sessions. Decision: per-session JSON files with the `session-id` resolution chain.
7. **Plan name → roadmap.** User chose the rename (option C of three name options) over alternatives like `design-plan`, `blueprint`, `plan-author`.
8. **No backwards-compat.** Explicit user direction: "backwards-compat 고려하지 않는 것으로." Validators reject `kind: plan` immediately. Migration is a one-time `git mv` + frontmatter sed.

---

## 4. Open Tasks (from session task tracker)

The session used the harness's task tool to track multi-topic discussion. Final state at session end:

| ID | Subject | Status |
|---:|---------|--------|
| #1 | Task 생성 스킬 부재 | completed (decision: add `/a4:task`) |
| #2 | plan / arch의 UC 전제 완화 여부 | pending — superseded by sketch-2 decision; arch UC-optional is part of the future split, not this session |
| #3 | /a4:arch에서 ADR 기록 유도 강화 | pending — agent-collaboration patterns A/B/C still open |
| #4 | /a4:decision의 ## Next Steps 가드레일 | pending |
| #5 | "남은 일" single source 결정 | pending |
| #6 | plan/SKILL.md task schema kind 누락 (드리프트 보수) | pending — partially absorbed by the rename pass; full closure waits on `/a4:roadmap` SKILL.md task schema cleanup |
| #7 | 기존 프로젝트 retroactive 적용 범위 | pending — direction: forward-only, no retroactive ADR splitting |
| #8 | plan 스킬 재구성 범위 결정 | in_progress — sketch 2 decided; implementation in follow-up |
| #9 | 워크플로우 모드 공식 축 도입 | completed (spec doc + script + ADR landed) |

These are session-scope tasks (harness `TaskCreate`), not workspace-scope tasks (`a4/task/*.md`). They do not migrate to a4/ — they were a discussion structuring tool. The next session should re-read this handoff to understand which decisions are committed and pick up #2–#7 + #8 implementation if continuing the thread.

---

## 5. What's left to implement (in priority order for resumption)

### Tier A — directly blocked by absence

1. **`plugins/a4/skills/run/SKILL.md`** — split out Phase 2 from `roadmap/SKILL.md`. UC-optional: ship-review (Step 2.5) becomes conditional on `implements:` non-empty; Step 2.1 ready conditions vacuously pass for empty `implements:`; task-implementer agent already supports both shapes. Reference paths: `roadmap.md`, `bootstrap.md` (latter as fallback when `roadmap.md` is absent — TBD if `/a4:run` should accept UC-less projects with no roadmap.md). Default mode: `autonomous`.
2. **`plugins/a4/skills/task/SKILL.md`** — single-task authoring. Conversational. Required arg: `kind` (`feature | spike | bug`). Optional `implements:` and `justified_by:`. AC source per kind documented in the plan-restructure ADR. When `kind: spike`, propose creating `spike/<id>-<slug>/` sidecar dir.
3. **`a4_hook.py` integration** — SessionStart should call `workflow_mode.py init --by <first-skill?>`, also run `workflow_mode.py sweep` (mirroring the existing `sweep-old-edited-a4.sh` pattern). SessionEnd should call `workflow_mode.py cleanup`. `hooks/hooks.json` updated accordingly.
4. **`default_mode:` frontmatter** — add to every mode-aware SKILL.md. List in the workflow-mode ADR table is canonical.

### Tier B — schema / docs alignment

5. **`frontmatter-schema.md` extension** — formalize the `default_mode` and `mode_transitions` skill frontmatter fields under a new "Skill metadata" section. Currently the workflow-mode.md spec lives standalone.
6. **Roadmap SKILL.md task schema** — currently still says `kind: plan` is invalid (rename done) but the Task File Schema example block doesn't include `kind:` at all. Add it. Ref task #6.
7. **`compass` Layer 1 mapping update** — `compass/SKILL.md` Layer 1 says `architecture.md exists, roadmap.md missing, tasks expected → recommend /a4:roadmap`. After the `/a4:run` and `/a4:task` split, this routing needs a more nuanced description: roadmap.md missing → `/a4:roadmap`; tasks present + status pending|failing → `/a4:run iterate`; user wants to add a task → `/a4:task`.

### Tier C — design questions still open

8. **`/a4:arch` ADR-generation pattern** — A/B/C from the session. Pattern A is multi-agent option-defenders + synthesizer; B is research-drafter (single agent); C is passive detector at wrap-up. User did not commit to one. Combination (B + C) probably wins.
9. **decision skill `## Next Steps` guardrail** — ADR's `## Next Steps` currently absorbs implementation checklists (D54 in callgraph-service is canonical example). Once `/a4:task` exists, the decision SKILL.md should advise: implementation items become `/a4:task` invocations, not Next Steps prose.
10. **"Open / carried forward" / "Next Steps" / "plan.md checklist" — three places track remaining work.** Decision pending on which is canonical. Sketch-2 plus `/a4:task` essentially solves this — task files become the canonical tracker — but the deprecation of the other forms in handoff and ADR templates is still TBD.
11. **`plan-reviewer` (now `roadmap-reviewer`) UC-less audit** — does the renamed agent's review criteria still make sense for UC-less projects? E.g., "UC Coverage" criterion is meaningless if there are no UCs. Either skip the criterion when no UCs, or reframe as "ADR Coverage" / "task justification coverage."

---

## 6. Files touched (for git diff inspection)

Single commit `d536cfe70` (refactor(a4): rename plan→roadmap, introduce workflow-mode axis), 25 files changed, 922 insertions, 137 deletions. Categorized:

- 2 new ADRs (spec/)
- 1 new reference doc (workflow-mode.md)
- 1 new script (workflow_mode.py)
- 3 git renames (skills/plan→roadmap, agents/plan-reviewer→roadmap-reviewer, skills/plan/references/planning-guide.md→skills/roadmap/references/planning-guide.md)
- 17 in-place edits (README, marketplace.json, all agents, references, scripts, and skill SKILL.mds with cross-references)

The handoff file itself lands in a separate commit per the `/handoff` protocol.

---

## 7. Quick reference for fresh session

### Where to start

If the user says "continue the pipeline restructure": read `spec/2026-04-25-plan-restructure.decide.md` first, then this handoff §5 Tier A.

If the user says "what is the workflow mode axis?": read `references/workflow-mode.md` end-to-end, then `spec/2026-04-25-workflow-mode-axis.decide.md` for rationale.

If the user says "I tried `/a4:plan` and it failed": confirm validators rejected `kind: plan`. The migration is one shell command:
```bash
git mv a4/plan.md a4/roadmap.md
# Edit roadmap.md frontmatter: kind: plan → kind: roadmap
```

### Key invariants set this session

- `workflow_mode.py` is the **only** tool that writes `a4/.workflow-state/<session-id>.json`. Skills and hooks always go through this script.
- `kind: plan` in any wiki-page frontmatter triggers a validator failure. Forward-only.
- `/a4:roadmap` produces only `kind: feature` tasks. `kind: spike` and `kind: bug` will arrive via `/a4:task` once it's written.
- `default_mode` declared in skill frontmatter is consulted only on SessionStart (when that skill is the first invoked); subsequent skill invocations inherit the live session mode.

### Commands likely to come up

```bash
# State of affairs
ls plugins/a4/skills/
# expects: arch auto-bootstrap auto-usecase compass decision drift handoff idea index research research-review roadmap spark-brainstorm usecase validate web-design-mock
# (note: no `plan/`, no `run/` yet, no `task/` yet)

# Validate current shape
uv run plugins/a4/scripts/validate.py "<some/a4/workspace>"

# Confirm marketplace bump
grep -A1 '"name": "a4"' .claude-plugin/marketplace.json
# expects: version "1.16.0"

# Workflow_mode.py smoke
uv run plugins/a4/scripts/workflow_mode.py init --session test-1 --mode conversational --trigger "smoke" --by handoff
uv run plugins/a4/scripts/workflow_mode.py get --session test-1
uv run plugins/a4/scripts/workflow_mode.py set autonomous --trigger "test" --session test-1
uv run plugins/a4/scripts/workflow_mode.py history --session test-1
uv run plugins/a4/scripts/workflow_mode.py cleanup --session test-1
```

### Don't do

- Don't add a `kind: plan` validator backwards-compat path. User-explicit.
- Don't rename inside `.handoff/**` or `spec/**` (point-in-time documents).
- Don't try to merge `/a4:roadmap` and `/a4:run` back together. The split is decided.
- Don't consume `default_mode:` from skill frontmatter without updating SKILL.mds — currently no skill declares it, the field is documented but unrolled.

---

## 8. References landed this session

- `plugins/a4/references/workflow-mode.md` — operational reference for the workflow-mode axis. Read before authoring or modifying mode-aware skills.
- `plugins/a4/spec/2026-04-25-workflow-mode-axis.decide.md` — workflow-mode ADR. Rationale + rejected alternatives.
- `plugins/a4/spec/2026-04-25-plan-restructure.decide.md` — plan-restructure ADR. Three-skill split + rename + AC source by kind + migration.
- `plugins/a4/scripts/workflow_mode.py` — tool reference (run with `--help`).

---

If the user's first directive in the next session specifies concrete work, follow it. If not, the natural starting point is **Tier A item 1**: split Phase 2 out of `roadmap/SKILL.md` into a new `skills/run/SKILL.md`, making the agent loop accessible to UC-less workspaces.
