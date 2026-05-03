---
name: breakdown
description: "This skill should be used when the user needs to derive a batch of task files from existing usecase / spec / architecture inputs. Common triggers include: 'breakdown', 'derive tasks', 'task batch', 'batch tasks from spec', 'plan the implementation tasks'. Writes per-task files at a4/task/<id>-<slug>.md only — no wiki page output. Requires (usecase OR spec) AND ci.md to enter; otherwise redirects to /a4:ci-setup, /a4:spec, /a4:usecase, or /a4:task. The agent-driven implement + test loop is in /a4:auto-coding; single ad-hoc tasks come through /a4:task, /a4:bug, /a4:spike, /a4:research."
argument-hint: <optional: "iterate" to walk task-targeted review items; auto-detects workspace state otherwise>
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Task Breakdown

Decomposes upstream behavioral inputs (`a4/usecase/*.md`, `a4/spec/*.md`) into a batch of implementation tasks, grounded in the actual codebase that `ci.md` already verified runs and tests. Emits one `a4/task/<id>-<slug>.md` per executable unit. The agent-driven implement + test loop lives in `/a4:auto-coding`.

This skill replaces the prior `roadmap` skill. The single-`roadmap.md` wiki narrative was retired with it; phase narrative — when a project benefits from one — is the user's to author directly as a wiki page, not a skill output.

## Workspace Layout

Resolve `a4/` via `git rev-parse --show-toplevel`.

**Required inputs (entry gate):**

- **Behavioral source** — at least one of:
  - `a4/usecase/*.md` — Use Cases (task `implements:` references point here).
  - `a4/spec/*.md` — Specs (task `spec:` references point here).
- **Test-execution anchor** — `a4/ci.md`. Single source of truth for test execution; its presence implies a verified test environment produced by `/a4:ci-setup`. Without it, derived tasks have no executable verification path.

**Optional inputs:**

- `a4/architecture.md` — design intent reference. May drift from the codebase; this skill consults it for component intent and module-responsibility narrative but never as the authority for file paths or module boundaries. The codebase itself is the structural ground truth (Step 2). When arch.md disagrees with code, the code wins; the divergence is recorded as a single review item targeting `architecture` (see Step 4).
- `a4/domain.md`, `a4/actors.md`, `a4/nfr.md`, `a4/context.md` — supporting wiki pages.

**Outputs:**

- `a4/task/<id>-<slug>.md` — one per executable unit of work. `type: task`, `status: open`. The breakdown generator always emits `type: task`; spike / bug / research authoring goes through their dedicated skills.
- `a4/review/<id>-<slug>.md` — findings from `breakdown-reviewer`, plus an optional arch-drift item when the codebase contradicts arch.md.

## Entry Gate

Before any work, verify the input contract:

```bash
behav=$(ls a4/usecase/*.md a4/spec/*.md 2>/dev/null | head -1)
boot=$(ls a4/ci.md 2>/dev/null)
```

| Behavioral source | ci.md | Action |
|-------------------|-------|--------|
| present | present | Continue. Architecture (`a4/architecture.md`) is consulted if present. |
| missing | present | Halt. Tell the user: behavioral source absent. Run `/a4:spec` or `/a4:usecase` for batch grounding, or `/a4:task` for a single ad-hoc task. |
| present | missing | Halt. Tell the user: ci.md absent. Run `/a4:ci-setup` first to set up the test environment and establish the test-execution contract; without it, derived tasks have no verification path. |
| missing | missing | Halt. Tell the user: neither behavioral source nor ci.md is present. Ad-hoc work goes through `/a4:task`. |

## Id Allocation

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"
```

## Modes

- **Derivation mode** — entry gate passes AND there is unmapped behavioral material (UCs/specs without any `implements:` / `spec:` referencing task). Run Steps 1 → 4.
- **Iterate mode** — open review items target a task in one of the four issue family folders (`task/`, `bug/`, `spike/`, `research/`). Apply `references/iteration-entry.md`

Mode detection at session start:

```bash
ls a4/task/*.md a4/bug/*.md a4/spike/*.md a4/research/*.md 2>/dev/null   # any tasks?
ls a4/review/*.md | xargs grep -l 'status: open' 2>/dev/null
```

If every behavioral source is already covered by an existing task and the user's intent is to start implementing, point them at the next implement step — direct `queued → progress` walk per `${CLAUDE_PLUGIN_ROOT}/authoring/issue-family-lifecycle.md`, or `/a4:auto-coding` for the agent-driven loop.

## Workflow

### Step 1: Read behavioral sources

Read every UC in `a4/usecase/*.md` and every spec in `a4/spec/*.md` (skip those already covered by an existing `task.implements:` / `task.spec:`). Read `a4/ci.md` for the test-execution contract — task acceptance criteria reference its `## How to run tests` commands. Read `a4/architecture.md` if present, treating it as design intent reference only.

### Step 2: Explore the codebase (authoritative for structure)

The codebase that `ci.md` verified is the **single source of truth** for file paths, module boundaries, naming conventions, and import structure. Inspect:

- Project structure, language conventions, build / test wiring (cross-check against `ci.md` `## How to run tests`).
- File organization patterns relevant to the upstream behavioral material.
- Existing identifiers (class / function / module names) the new tasks will extend or extend alongside.

When `architecture.md` is present, compare arch claims against codebase observations during this step. Record divergences for the optional drift review item (Step 4).

File paths in derived task frontmatter must be specific to this codebase (`src/render.ts`, not "a renderer file"). When inferring a path that does not yet exist (`Create` action), follow the conventions discovered above.

### Step 3: Derive tasks

Procedure: `references/generate.md`. Covers task derivation from each behavioral source, file mapping (auto-populated `## Change Plan`), upstream anchor population (`implements:` / `spec:` auto-fill), duplicate detection (skip + summary), and shared integration points.

### Step 4: Verification + drift review

Procedure: `references/verification.md`. Spawn `breakdown-reviewer` for batch coverage / dependency / AC verification. When arch.md is present and Step 2 surfaced concrete divergences, also emit a single arch-drift review item.

## Hand-off

After Step 4 closes:

> Tasks ready. Begin the implement step — drive each task directly (`queued → progress → complete` per `${CLAUDE_PLUGIN_ROOT}/authoring/issue-family-lifecycle.md`) or run `/a4:auto-coding` for the agent-driven loop. Single ad-hoc tasks can be added at any time via `/a4:task`, `/a4:bug`, `/a4:spike`, or `/a4:research`. Promote new tasks `open → queued` (edit `status:` directly) when you are ready for them to be picked up.

Both implement forms read `a4/ci.md`'s `## How to run tests` as the single source of truth. Make sure `ci.md` exists and its content is correct before handing off — re-run `/a4:ci-setup` if architecture or test infrastructure changed.

## Commit Points

Per-step subject formats and timing: `references/commit-points.md`.

## Wrap Up

When the user ends the breakdown session:

1. Summarize: tasks created / skipped (existing) / total. Review items written by `breakdown-reviewer`. Whether an arch-drift review was emitted. Recommended next step (begin the implement step — directly or via `/a4:auto-coding` — for the new tasks; `/a4:arch` if drift was significant; `/a4:spec` or `/a4:usecase iterate` if upstream review items came back).
2. Suggest `/a4:handoff` to snapshot the session.

## Agent Usage

- **`breakdown-reviewer`** — `Agent(subagent_type: "a4:breakdown-reviewer")`. Reviews the derived task set against upstream usecases / specs and the architecture intent (when present); emits per-finding review items.

`coder` and `test-runner` are `/a4:auto-coding`'s agents — not invoked from this skill.

## Non-Goals

- Do not author any wiki page. `roadmap.md` is no longer a skill output (and the type was retired with it). Phase narrative belongs to whatever wiki page the user chooses to maintain manually, or to `architecture.md`.
- Do not infer file paths from `architecture.md` when those paths do not exist in the codebase. Code wins.
- Do not drive the implement step here. The implement step (whether direct or via `/a4:auto-coding`) follows breakdown, not within it.
- Do not author test-execution commands. `ci.md` is the single source of truth.
- Do not edit `architecture.md` to resolve drift. Emit a review item; resolution flows through `/a4:arch iterate`.
- Do not skip the entry gate. UC/spec absence ⇒ no batch; ci.md absence ⇒ no batch.
