---
type: decide
pipeline: spark
topic: "Plan Skill Restructure: rename to roadmap, split out task and run"
date: 2026-04-25
updated: 2026-04-25
status: final
framework: "analysis-driven"
decision: "Rename `/a4:plan` to `/a4:roadmap` (Phase 1 — authoring), split the agent loop into a future `/a4:run` (Phase 2 — implement + test + ship), and add `/a4:task` for single-task authoring outside the batch. plan.md → roadmap.md, kind:plan → kind:roadmap. Forward-only rename — no backwards-compatibility shim."
tags: [a4-pipeline, plan, roadmap, task, run, skill-rename, skill-split]
---
# Decision Record: Plan Skill Restructure

> Source: pipeline-restructuring conversation triggered by review of why callgraph-service (UC-less, ADR-driven) couldn't enter the existing pipeline. The user observed that `/a4:plan` was originally built around agent-driven implementation automation, not just planning, and that "plan" as a name was overloaded with the EnterPlanMode primitive and conflated multiple roles.

## Context

`/a4:plan` had accumulated four roles in two phases:

- **Phase 1** — `plan.md` authoring + per-task batch generation + plan-reviewer verification (conversational planning).
- **Phase 2 Step 2.1-2.2** — implementation orchestration via task-implementer agents.
- **Phase 2 Step 2.3-2.4** — test orchestration via test-runner agent + 3-cycle loop.
- **Phase 2 Step 2.5** — UC ship-review and `shipped` transition.

Three problems compounded:

1. **Name vs role mismatch.** `description: autonomously planning, implementing, testing, and iterating` — the skill name `plan` covered only the first verb.

2. **No entry point for ad-hoc tasks.** `/a4:plan` only generated tasks from UCs in batch mode. Single tasks needed for spike, bug, or ADR-justified work had no skill — but `frontmatter-schema.md:67` mandates "always written by an LLM via a skill or agent — never hand-edited."

3. **UC-less projects locked out of agent automation.** Phase 2 ran only after Phase 1, which required UC files. Investigation showed agent-level UC dependencies were soft (task-implementer's UC transition step is conditional on non-empty `implements:`; test-runner is already UC-agnostic; ship-review can no-op when no UC tasks), so the lockout was structural, not technical.

The earlier ADRs (`2026-04-23-spec-as-wiki-and-issues`, `2026-04-24-experiments-slot`, `2026-04-24-skill-naming-convention`) had landed `task/` as a folder hosting `kind: feature | spike | bug` enum but never added a skill that could write into it outside `/a4:plan`'s batch path.

## Success Criteria

Ranked:

1. **Names match roles** — `roadmap` authors a roadmap; `run` runs the implementation loop; `task` writes one task.
2. **UC-less projects can use agent automation** — the same task-implementer + test-runner agents apply with or without UCs, controlled by per-task frontmatter (`implements:` empty for ADR-justified or spike tasks).
3. **Single-task entry coexists with batch entry** — `/a4:plan`'s Phase 1 (now `/a4:roadmap`) and `/a4:task` both write into `a4/task/`, distinguished by entry shape (batch UC-driven vs single ad-hoc).
4. **Validators reject the old shape immediately** — `kind: plan` no longer valid; no backwards-compat shim. Forward-only.
5. **Existing agents and scripts touch unchanged** — task-implementer, test-runner, plan-reviewer (renamed to roadmap-reviewer), allocate_id, transition_status all work with the renamed artifacts via path/identifier substitution.

## Decision

### Three skills replace the previous `/a4:plan`

| Skill | Role | Default mode |
|-------|------|--------------|
| `/a4:roadmap` | Phase 1 — author `a4/roadmap.md` + batch task generation from UCs + arch + bootstrap. plan-reviewer (renamed `roadmap-reviewer`) verifies. | conversational |
| `/a4:task` (new) | Single-task authoring. `kind: feature \| spike \| bug` argument; `implements:` (UC) and/or `justified_by:` (ADR) optional. spike sidecar `spike/<id>-<slug>/` proposed when `kind: spike`. | conversational |
| `/a4:run` (new) | Phase 2 — agent loop. Pick ready tasks → task-implementer (parallel/sequential) → test-runner → analyze → optional UC ship-review when UC-attached tasks exist. Up to 3 cycles. | autonomous |

`/a4:roadmap` and `/a4:run` are not chained automatically — the user invokes them in sequence (or `/a4:run` can be invoked directly when tasks already exist from earlier `/a4:roadmap` or `/a4:task` work).

### Artifact renames

| Before | After |
|--------|-------|
| `a4/plan.md` | `a4/roadmap.md` |
| `kind: plan` (wiki page enum) | `kind: roadmap` |
| `/a4:plan` invocation | `/a4:roadmap` invocation |
| `agents/plan-reviewer.md` | `agents/roadmap-reviewer.md` |
| `Agent(subagent_type: "a4:plan-reviewer")` | `Agent(subagent_type: "a4:roadmap-reviewer")` |
| `skills/plan/` directory | `skills/roadmap/` directory |

The `EnterPlanMode` / `ExitPlanMode` Claude Code primitives keep their existing names (they are tool names from the host, not artifacts of this plugin) — the skill body uses them but no longer overloads "plan" as the skill's name.

### UC ship-review (Step 2.5) becomes conditional

`/a4:run` Step 2.5 runs only for tasks whose `implements:` resolves to UC files. Tasks with empty `implements:` (single spike, bug, ADR-justified feature) skip ship-review naturally — the candidate UC set is empty.

This formalizes what was previously a vacuous-truth implicit branch: UC-less projects now explicitly reach `/a4:run` completion without ship-review, with no special-case code.

### Acceptance Criteria source per task kind

`task` body must declare AC, sourced as follows:

| Task kind / shape | AC source |
|---|---|
| `feature` + `implements: [usecase/...]` | UC `## Flow` / `## Validation` / `## Error handling` (existing convention) |
| `feature` + `justified_by: [decision/...]` (UC-less project) | ADR `## Decision` + relevant `architecture.md` section |
| `spike` | hypothesis + expected result, the spike's own body |
| `bug` | reproduction scenario + fixed criteria |

Validators do not enforce source-by-kind; this is a documentation convention. The task body must contain a `## Acceptance Criteria` section regardless.

### Forward-only rename

Validators reject `kind: plan` immediately. No backwards-compat shim, no deprecation period. Existing workspaces (callgraph-service, plugin's own `plugins/a4/`) require a one-time manual migration:

```
git mv a4/plan.md a4/roadmap.md
# replace kind: plan → kind: roadmap in frontmatter
```

This decision was explicit: "backwards-compat 고려하지 않는 것으로."

### Workflow-mode integration

Each new and renamed skill declares `default_mode:` per the workflow-mode-axis ADR:

- `roadmap` → `conversational`
- `task` → `conversational`
- `run` → `autonomous`

Mid-flight transitions follow the canonical triggers in that ADR. `/a4:run` specifically transitions to `conversational` on task-implementer ambiguity, test-runner failure classification, UC ship-review, and 3-cycle cap.

## Out of Scope (this revision)

Landed in this session: artifact rename and the supporting documentation. Pending in follow-up sessions:

- **`/a4:run` SKILL.md** — split out the Phase 2 content from the current `roadmap/SKILL.md` (which still bundles both phases pending split).
- **`/a4:task` SKILL.md** — neither the file nor the content exists yet; needs first-write.
- **`default_mode:` frontmatter rolled into every mode-aware skill SKILL.md** — currently declared only in this ADR's table.
- **Hook integration** — `a4_hook.py` still needs the `workflow_mode.py init` / `cleanup` / `sweep` calls.
- **`roadmap-reviewer` audit** — the renamed agent still has its body adapted from `plan-reviewer`; rationale is unchanged but section labels could be tightened.
- **Existing-workspace migration** — manual `git mv` + frontmatter sed is the user's responsibility; tooling for this is not built.

## Rejected Alternatives

| Option | Reason |
|--------|--------|
| **Keep `/a4:plan` as-is** (option D in pipeline restructuring sketch) | Name↔role mismatch persists. UC-less projects remain locked out of agent automation. Single-task entry stays absent. |
| **Add `/a4:task` only, leave `/a4:plan` untouched** | Solves single-task entry but does nothing for the name overload or UC-less automation. Half measure. |
| **Split `/a4:plan` Phase 2 into 4 skills (implement / test / ship)** | Sub-step skills (`/a4:implement`, `/a4:test`, `/a4:ship`) fragment what is genuinely a tightly-coupled agent loop with cycle semantics and cascade rules. The 3-skill split (`roadmap` / `task` / `run`) preserves the loop while extracting the orthogonal authoring concerns. |
| **Workspace mode flag (`a4/.workspace.yaml: mode: arch-driven \| uc-driven`)** | Forces every skill to branch on a static workspace property. Real workflows are mixed (UC-driven projects also accumulate ADRs and run spikes). The orthogonal-axis approach (UC-shape ⊥ workflow-mode) handles this without a switch. |
| **Make `/a4:plan` UC-optional rather than splitting** | plan has 17 deep UC integration points (Phase 2 ready conditions, cascade rules, ship-review, plan body templates referencing `[[context]]`). Loosening all of them is essentially a rewrite, with the result being "/a4:plan but slightly different." Splitting is simpler and preserves UC-driven full-stack semantics in `/a4:roadmap`. |
| **Rename to `/a4:design-plan` / `/a4:blueprint` / `/a4:plan-author`** | Considered. `roadmap` won because it (a) is shorter, (b) clearly conveys the milestone-and-sequence narrative the wiki page contains, (c) has no overload with the EnterPlanMode primitive, (d) makes the artifact-name `roadmap.md` natural. |
| **Backwards-compat shim** (validators temporarily accept `kind: plan`) | User direction: forward-only. Adding a shim invites confusion when the next session sees both kinds in the wild. Migration is one-time and mechanical. |
| **Auto-archive the old `/a4:plan` SKILL.md to `archive/`** | The git history contains the rename; an archive directory adds noise without affording recovery the user can't get from `git show`. |

## Migration

For the plugin itself:

- `git mv plugins/a4/skills/plan plugins/a4/skills/roadmap`
- `git mv plugins/a4/agents/plan-reviewer.md plugins/a4/agents/roadmap-reviewer.md`
- Substitute `plan` → `roadmap` in non-handoff, non-spec files (artifact references, kind enum, agent name, skill-invocation strings)
- `marketplace.json` minor bump (1.15.0 → 1.16.0)

For consuming workspaces (callgraph-service or any other a4 user):

```bash
git mv a4/plan.md a4/roadmap.md
# In the new roadmap.md frontmatter, replace `kind: plan` with `kind: roadmap`.
# Validators will reject the old form on the next /a4:validate run.
```

No script is provided — the migration is one shell command + one find/replace.

## Discussion Log

<details>
<summary>Conversation summary</summary>

**Trigger.** While reviewing why callgraph-service's 44 ADRs accumulated `## Next Steps` blocks that read like task content, the user diagnosed that the missing `/a4:task` skill had pushed task-shaped content into ADRs. The fix surfaced a deeper question: was `/a4:plan` doing too much under one name?

**Pipeline restructuring sketches.** Three sketches presented (1: minimal — add `/a4:task` only; 2: split — `roadmap` + `task` + `run`; 3: tracks — separate UC-track and ADR-track pipelines). User selected sketch 2.

**Plan's original intent.** User clarified that `/a4:plan`'s focus was always "agent-based feature implementation automation." So Phase 2 was core, not drift. The split therefore separates concerns within plan rather than excising a bolted-on Phase 2.

**Workflow-mode axis.** Surfaced as orthogonal to this restructure. The two ADRs are recorded separately (this one + `2026-04-25-workflow-mode-axis.decide.md`) because each has independent rationale and lifecycle, but they landed in the same session.

**Name choice — `roadmap`.** Considered alternatives (`design-plan`, `blueprint`, `plan-author`). `roadmap` chosen for milestone+sequence connotation, lack of overload with EnterPlanMode, and clean artifact filename `roadmap.md`.

**Forward-only.** Confirmed explicitly: no validator backwards-compat, no shim. Migration is mechanical and one-time per workspace.

</details>
