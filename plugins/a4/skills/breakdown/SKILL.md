---
name: breakdown
description: "Use when the user needs to derive implementation-ready task files from existing usecase / spec inputs. Common triggers: 'breakdown', 'derive tasks', 'task batch', 'batch tasks from spec', 'plan the implementation tasks'. Reads relevant supporting docs (a4 wiki pages, research/spikes, repo docs) and cites them in each task so implementers know what to read. Writes a4/task/<id>-<slug>.md only — no wiki page output. Requires (usecase OR spec) AND ci.md; otherwise redirects to /a4:ci-setup, /a4:spec, /a4:usecase, or /a4:task."
argument-hint: '<optional: "iterate" to walk task-targeted review items; auto-detects workspace state otherwise>'
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Task Breakdown

Decompose `a4/usecase/*.md` and/or `a4/spec/*.md` into executable `a4/task/<id>-<slug>.md` files. Use the current codebase and `a4/ci.md` to make each task implementable and testable. Read supporting documents when they affect implementation, then cite them in the task (`related:` and/or `## References`) so the implementer can resume without rediscovering context.

## Workspace Layout

Resolve `a4/` via `git rev-parse --show-toplevel`.

**Required inputs (entry gate):**

- **Behavioral source** — at least one of:
  - `a4/usecase/*.md` — Use Cases. Task `implements:` references point here.
  - `a4/spec/*.md` — Specs. Task `spec:` references point here.
- **Test-execution anchor** — `a4/ci.md`. Single source of truth for test execution; its presence implies `/a4:ci-setup` already verified the environment. Without it, derived tasks have no executable verification path.

**Supporting references (optional; read and cite when relevant):**

- a4 wiki pages: `a4/architecture.md`, `a4/domain.md`, `a4/actors.md`, `a4/nfr.md`, `a4/context.md`, plus any other root wiki page that exists.
- a4 issue-side evidence: relevant `a4/research/*.md`, `a4/spike/*.md`, `a4/review/*.md`, or existing tasks that constrain the new batch.
- Repository docs: `README*`, `docs/**/*.md`, `adr/**/*.md`, `adrs/**/*.md`, or similar local documentation discovered by `Glob` / `Grep`.

Supporting references inform task boundaries, file mapping, terminology, interfaces, and tests. They do **not** replace `implements:` / `spec:` as the acceptance-criteria source.

**Outputs:**

- `a4/task/<id>-<slug>.md` — one per executable unit of work. `type: task`, `status: open`. Breakdown always emits `type: task`; spike / bug / research authoring goes through their dedicated skills.
- `a4/review/<id>-<slug>.md` — findings from `breakdown-reviewer`, plus an optional arch-drift item when the codebase contradicts `architecture.md`.

## Entry Gate

Before any work, verify the input contract:

```bash
behav=$(ls a4/usecase/*.md a4/spec/*.md 2>/dev/null | head -1)
boot=$(ls a4/ci.md 2>/dev/null)
```

| Behavioral source | ci.md | Action |
|-------------------|-------|--------|
| present | present | Continue. Discover supporting references after reading the behavioral source. |
| missing | present | Halt. Tell the user: behavioral source absent. Run `/a4:spec` or `/a4:usecase` for batch grounding, or `/a4:task` for a single ad-hoc task. |
| present | missing | Halt. Tell the user: ci.md absent. Run `/a4:ci-setup` first to establish the test-execution contract; without it, derived tasks have no verification path. |
| missing | missing | Halt. Tell the user: neither behavioral source nor ci.md is present. Ad-hoc work goes through `/a4:task`. |

## Modes

- **Derivation mode** — entry gate passes AND there is unmapped behavioral material (UCs/specs without any `implements:` / `spec:` referencing task). Run Steps 1 → 4.
- **Iterate mode** — open review items target a task in one of the four issue family folders (`task/`, `bug/`, `spike/`, `research`). Apply `references/iteration-entry.md`.

Mode detection at session start:

```bash
ls a4/task/*.md a4/bug/*.md a4/spike/*.md a4/research/*.md 2>/dev/null   # any tasks?
ls a4/review/*.md | xargs grep -l 'status: open' 2>/dev/null
```

If every behavioral source is already covered by an existing task and the user's intent is implementation, report that breakdown has no new batch to derive and point to the existing tasks' lifecycle state.

## Workflow

### Step 1: Read behavioral sources and reference inventory

Read every UC in `a4/usecase/*.md` and every spec in `a4/spec/*.md` (skip those already covered by existing `task.implements:` / `task.spec:`). Read `a4/ci.md` for the test-execution contract.

Then inventory supporting references with `Glob` / `Grep`. Read only documents that appear relevant to the candidate behavior, affected code areas, terminology, external interfaces, or test strategy. Keep a per-candidate note of why each supporting doc matters; this becomes each task's `related:` and/or `## References`.

### Step 2: Explore the codebase (authoritative for structure)

The codebase that `ci.md` verified is the **single source of truth** for file paths, module boundaries, naming conventions, and import structure. Inspect:

- Project structure, language conventions, build / test wiring (cross-check against `ci.md` `## How to run tests`).
- File organization patterns relevant to the candidate behavior.
- Existing identifiers (class / function / module names) the new tasks will extend or extend alongside.
- Whether supporting docs match the current code. Code wins for structure; mismatches become review items rather than silent assumptions.

File paths in derived task `## Change Plan` sections must be specific to this codebase (`src/render.ts`, not "a renderer file"). When inferring a path that does not yet exist (`Create` action), follow discovered conventions.

### Step 3: Derive tasks

Procedure: `references/generate.md`. Covers candidate selection, supporting-reference selection, task grouping, file mapping (`## Change Plan`), upstream anchor population (`implements:` / `spec:`), task references (`related:` / `## References`), duplicate detection, and shared integration points.

### Step 4: Verification + drift review

Procedure: `references/verification.md`. Spawn `breakdown-reviewer` for batch coverage / dependency / granularity / file / test / AC / reference verification. When `architecture.md` is present and Step 2 surfaced concrete divergences, also emit a single arch-drift review item.

## Hand-off

After Step 4 closes:

> Tasks ready. Promote new tasks `open → queued` (edit `status:` directly) when they are ready for implementation. Single ad-hoc tasks can be added via `/a4:task`, `/a4:bug`, `/a4:spike`, or `/a4:research`.

Make sure `ci.md` is correct before handing off — re-run `/a4:ci-setup` if test infrastructure changed.

## Commit Points

Per-step subject formats and timing: `references/commit-points.md`.

## Wrap Up

When the user ends the breakdown session:

1. Summarize: tasks created / skipped / total; supporting docs cited; review items written by `breakdown-reviewer`; whether arch drift was emitted; blocked upstream routes, if any (`/a4:arch`, `/a4:spec`, or `/a4:usecase iterate`).
2. Suggest `/a4:handoff` to snapshot the session.

## Agent Usage

- **`breakdown-reviewer`** — `Agent(subagent_type: "a4:breakdown-reviewer")`. Reviews the derived task set against UCs/specs, supporting references, the codebase, and `ci.md`; emits per-finding review items.

This skill invokes no implementation or test-execution agents.

## Non-Goals

- Do not author wiki pages or phase narrative. This skill writes task files and review items only.
- Do not introduce new first-class document types. If a repo has local docs, cite them as supporting references; do not treat them as a4 schema unless an authoring contract exists.
- Do not treat supporting references as AC anchors. AC comes from `implements:` / `spec:` plus the task body.
- Do not infer file paths from supporting docs when those paths contradict the codebase. Code wins.
- Do not drive implementation here. This skill stops after task derivation and review.
- Do not author test-execution commands. `ci.md` is the single source of truth.
- Do not edit supporting docs to resolve drift. Emit review items and route to the owning skill or user edit path.
- Do not skip the entry gate. UC/spec absence ⇒ no batch; ci.md absence ⇒ no batch.
