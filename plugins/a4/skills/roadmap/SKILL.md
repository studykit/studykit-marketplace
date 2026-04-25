---
name: roadmap
description: "This skill should be used when the user needs to author the implementation roadmap and per-task files from an architecture. Common triggers include: 'roadmap', 'plan the implementation', 'build the task set from arch', 'lay out milestones'. Writes a4/roadmap.md (wiki page) plus per-task files in a4/task/. The agent-driven implement + test loop (formerly Phase 2) is being moved to /a4:run; until that split lands this SKILL.md still describes both phases. Single ad-hoc tasks (spike, bug, ADR-justified) live in /a4:task."
argument-hint: <optional: "iterate" to resume; auto-detects workspace state otherwise>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Implementation Roadmap Builder & Executor

Takes the architecture in `a4/architecture.md` (plus the UCs in `a4/usecase/`, the domain model in `a4/domain.md`, and the actor roster in `a4/actors.md`) and authors the implementation roadmap plus per-task files. The legacy Phase 2 (agent loop, integration tests, ship-review) still lives in this file pending the `/a4:run` split.

## Workspace Layout

Resolve `a4/` via `git rev-parse --show-toplevel`. Inputs:

- `a4/architecture.md` — the authoritative architecture wiki page.
- `a4/usecase/*.md` — Use Cases (task `implements:` references point here).
- `a4/domain.md`, `a4/actors.md`, `a4/nfr.md`, `a4/context.md` — supporting wiki pages.
- `a4/bootstrap.md` — bootstrap report (if auto-bootstrap has run). Verified build/launch/test commands live here.

Outputs:

- `a4/roadmap.md` — single wiki page: Overview, Implementation Strategy, Milestones, Launch & Verify, Shared Integration Points.
- `a4/task/<id>-<slug>.md` — one per executable unit of work (Jira-task semantics).
- `a4/review/<id>-<slug>.md` — findings from roadmap-reviewer and failures from test-runner.

Derived views (dependency graph, open-task dashboard, milestone progress, test-failure summary) render via Obsidian dataview; no separate files.

## Roadmap Wiki Schema

```yaml
---
kind: roadmap
updated: 2026-04-24
---
```

No lifecycle, revision, or source SHA fields. Cross-references, footnote markers, and the Wiki Update Protocol follow the shared conventions at `${CLAUDE_PLUGIN_ROOT}/references/obsidian-conventions.md`.

## Task File Schema

```yaml
---
id: 5
title: Render markdown
status: pending | implementing | complete | failing | discarded
implements: [usecase/3-search-history, usecase/4-render-preview]
depends_on: [task/4-parse-config]
justified_by: []
related: []
files: [src/render.ts, src/render.test.ts]
cycle: 1
labels: [renderer]
milestone: v1.0
created: 2026-04-22
updated: 2026-04-24
---
```

Body sections: `## Description`, `## Files` (action/path/change table), `## Unit Test Strategy` (scenarios + isolation + test files), `## Acceptance Criteria` (checklist derived from UCs), `## Interface Contracts` (the contracts this task consumes or provides, with wikilinks to `[[architecture]]` sections), `## Log` (append-only per cycle).

`status` semantics:
- `pending` — not yet assigned.
- `implementing` — an `task-implementer` agent is working or crashed mid-work (reset to `pending` on session resume).
- `complete` — implemented; unit tests pass.
- `failing` — implementation or unit tests failed after an task-implementer attempt.
- `discarded` — UC this task implements was discarded; cascade-flipped by `transition_status.py`.

All task status changes flow through `scripts/transition_status.py`. Cascades: when a UC goes `implementing → revising`, this script flips related `implementing`/`failing` tasks back to `pending` (spec is being rewritten; re-implementation is required). When a UC goes to `discarded`, related tasks cascade to `discarded`.

`cycle:` starts at 1 and increments each retry. `updated:` bumps on every status change (written by the status writer).

## Id Allocation

Always allocate via the shared utility before creating a task or review item:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"
```

## Modes

Determined by the workspace state, not by frontmatter flags:

- **Roadmap mode** — `a4/roadmap.md` absent OR `a4/task/` is empty. Run Phase 1.
- **Implement mode** — `a4/task/` has `pending` or `failing` tasks, or no test-runner review items yet reference the current cycle. Run Phase 2.
- **Iterate mode** — open review items target `roadmap` or a task (typically from the prior cycle's test-runner). Walk them before re-running Phase 2.

Mode detection runs at session start via:

```bash
ls a4/task/*.md                                  # any tasks?
grep -l '^status: pending'   a4/task/*.md       # pending tasks
grep -l '^status: failing'   a4/task/*.md       # failing tasks
ls a4/review/*.md | xargs grep -l 'status: open\|target: roadmap\|target: task/' # open review items
```

## Resume Hygiene

At session start, for every task with `status: implementing`, reset to `pending` via `scripts/transition_status.py` (an `implementing` status at session-start means the prior session crashed mid-work). The writer records the `## Log` entry. See "Session-start resume hygiene" below Step 2.5 for the exact invocation.

---

## Phase 1 — Roadmap Generation + Verification

### Step 1.1: Read Sources

Read these files up front:

- `a4/architecture.md` — technology stack, components, information flows, interface contracts, test strategy.
- `a4/usecase/*.md` — every UC (ids, actors, flows, acceptance criteria). Use `grep -l` to enumerate.
- `a4/domain.md`, `a4/actors.md`, `a4/nfr.md`, `a4/context.md` — supporting wiki pages.
- `a4/bootstrap.md` — if present. Extract verified build/launch/test commands; use them directly instead of auto-detection.

If `bootstrap.md` is absent, suggest `/a4:auto-bootstrap` first. Continue only if the user opts to proceed without it.

### Step 1.2: Explore the Codebase

Check project structure, conventions, test setup, build configuration. File paths in task frontmatter must be specific to this codebase (`src/render.ts`, not "a renderer file").

### Step 1.3: Generate Roadmap + Tasks

Enter plan mode (the `EnterPlanMode` Claude Code primitive — distinct from the workflow-mode axis). Design:

1. **Implementation strategy** (component-first / feature-first / hybrid) — read `${CLAUDE_SKILL_DIR}/references/planning-guide.md` for guidance.
2. **Milestones** — group tasks into named deliverable sets (`v1.0`, `beta`, `phase-1`). Milestones drive roadmap narrative sequencing.
3. **Tasks** (one per executable unit):
   - Derive from architecture components + UC flows.
   - Size: covers 1–5 related UCs, touches 1–3 components, independently testable, ≤ ~500 lines.
   - File mapping (source files + unit test files following the bootstrap/codebase convention).
   - Dependencies (`depends_on:` using task wikilink paths).
   - Unit test scenarios + isolation strategy.
   - Acceptance criteria derived from UC flows, validation, error handling.
   - Milestone assignment (`milestone:` field).
4. **Shared Integration Points** — identify any file appearing in 3+ tasks' file lists. Define the integration pattern.
5. **Launch & Verify** — build command, launch command, smoke scenario, test isolation flags. Pull directly from `bootstrap.md` when available.

Exit plan mode. Write artifacts:

**`a4/roadmap.md` body** (with the wiki frontmatter above):

```markdown
# Roadmap

> Implements the architecture in [[architecture]] to deliver the use cases in [[context]].

## Overview

<One paragraph: what is being implemented, how it serves the UCs, key sequencing intuition.>

## Implementation Strategy

- **Approach:** <component-first | feature-first | hybrid>
- **Incremental delivery:** <how the system stays testable at each step>
- **Key constraints:** <architectural or operational constraints shaping order>

## Milestones

### v1.0 — Foundation

**Goal:** <what "done" means for this milestone>
**Scope:** [[task/1-setup-schema]], [[task/2-auth-service]], [[task/3-render-engine]]
**Success criteria:** <observable outcome — e.g., "user can send a message and see a response">
**Risks:** <anything with mitigation>

### v1.1 — Enrichment

…

## Dependency Graph (snapshot)

```plantuml
@startuml
[task/1-setup-schema] as T1
[task/2-auth-service] as T2
[task/3-render-engine] as T3
T2 --> T1
T3 --> T1
@enduml
```

> Authoritative source: per-task `depends_on:` frontmatter. This diagram is a point-in-time snapshot; regenerate via compass / dataview when tasks change.

## Launch & Verify

| Item | Value |
|------|-------|
| App type | <web app / VS Code extension / CLI / API / …> |
| Build command | <e.g., `npm run build`> |
| Launch command | <e.g., `npm run dev`> |
| Launch URL / view | <e.g., `http://localhost:3000`> |
| Smoke scenario | <minimal end-to-end interaction> |
| Test isolation | <flags — e.g., `--disable-extensions`, `--user-data-dir=<tmpdir>`> |

## Shared Integration Points

<Only when a file appears in 3+ tasks.>

| File | Integration Pattern | Contributing Tasks |
|------|--------------------|-------------------|
| `src/app.ts` | Handler registration; tasks register their handlers via `app.register(...)` | [[task/2-auth-service]], [[task/3-render-engine]], [[task/5-history-service]] |

## Changes

[^1]: 2026-04-24 — [[architecture]]
```

**Per-task files** — allocate ids via `allocate_id.py`, write `a4/task/<id>-<slug>.md` using the schema above. The roadmap.md's Milestones section references them via wikilinks. Tasks must include `kind: feature | spike | bug` (required); the batch generator emits `kind: feature` for every UC-derived task — single ad-hoc spike / bug entries are authored via `/a4:task`.

After all task files are written, refresh the reverse link on each UC so `ready → implementing` will pass mechanical validation:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/refresh_implemented_by.py" \
  "$(git rev-parse --show-toplevel)/a4"
```

This back-scans every task's `implements:` list and writes `implemented_by: [...]` onto each referenced UC. The script is idempotent; run it again after any task file is created, renamed, or has its `implements:` list edited.

Commit roadmap generation together when the user confirms (see Commit Points).

### Step 1.4: Roadmap Verification

Spawn `Agent(subagent_type: "a4:roadmap-reviewer")`. Pass:
- `a4/` absolute path
- Prior open roadmap-targeted review item ids (to deduplicate)

The reviewer emits per-finding review items to `a4/review/<id>-<slug>.md` and returns a summary.

Walk each new review item:
- **Roadmap-level fix** — edit `roadmap.md` or the affected task file; resolve the review item (`status: resolved`, append `## Log`, add wiki footnote if roadmap.md changed).
- **Arch / usecase finding** — **stop Phase 1**. Leave the review item `status: open` with its existing `target:` pointing at `architecture` or `usecase/...`. Tell the user to run `/a4:arch` or `/a4:usecase iterate` and resume `/a4:roadmap iterate` afterwards.
- **Defer** — leave `status: open` with a `## Log` reason.

Loop up to 3 review rounds if roadmap-level revisions are substantial. Once the reviewer returns `ACTIONABLE` (or the user explicitly approves moving on with deferred findings), proceed to Phase 2.

---

## Phase 2 — Implement + Test Loop (max 3 cycles)

Implementation is delegated to subagents on a per-task basis. Each agent runs in a fresh context and receives only one task file plus the contracts it needs.

### Step 2.1: Pick Ready Tasks

A task is **ready** when all of:
- `status ∈ {pending, failing}`
- every `depends_on` entry resolves to a task with `status: complete`
- every UC in `implements:` has `status ∈ {ready, implementing}` (so `revising`/`discarded`/`blocked`/`superseded`/`shipped` UCs' tasks are skipped)

Build the ready set by reading task + UC frontmatter.

Independent ready tasks run in parallel. Tasks with mutual dependencies run sequentially.

### Step 2.2: Spawn task-implementer

For each ready task, spawn one agent:

```
Agent(subagent_type: "a4:task-implementer", prompt: """
Task file: <absolute path to a4/task/<id>-<slug>.md>
Roadmap file: <absolute path to a4/roadmap.md>
Architecture file: <absolute path to a4/architecture.md>
Relevant UC files: <paths referenced by the task's implements:>

Read the task file for Description, Files, Unit Test Strategy, Acceptance Criteria.
Pull build + unit-test commands from the roadmap's Launch & Verify section.

Implement the task and write its unit tests. All unit tests must pass.
Commit code + unit tests (one commit per task).
Return: result (pass/fail), summary of changes, any issues encountered.
""")
```

Before spawning, flip the task via the writer:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/transition_status.py" \
  "$(git rev-parse --show-toplevel)/a4" \
  --file "task/<id>-<slug>.md" --to implementing \
  --reason "/a4:roadmap Step 2.2 spawning task-implementer"
```

After the agent returns, call the writer with `--to complete` or `--to failing` based on the return value (include a `--reason` naming the cycle and outcome). Do not hand-edit `status:` / `updated:` / `## Log` — the writer owns them.

### Step 2.3: Run Integration + Smoke Tests

After all tasks reach `complete` (or after a cycle ends with failures still outstanding), spawn the test-runner:

```
Agent(subagent_type: "a4:test-runner", prompt: """
Roadmap file: <absolute path to a4/roadmap.md>
a4/ path: <absolute path>
Cycle: <current integer>

Use the Launch & Verify config for build/run/test commands. Run integration and
smoke tests as defined in the roadmap. For each failing test, emit one review item
at a4/review/<id>-<slug>.md via allocate_id.py with:

  kind: finding
  status: open
  target: <task/<id>-<slug> if the failure is traceable to a task; otherwise roadmap>
  source: test-runner
  wiki_impact: []
  priority: high | medium
  labels: [test-failure, cycle-<N>]

Body includes: test name, expected vs actual, full stack/log snippet, and best-guess
root cause pointer (without classifying as roadmap/arch/usecase — the calling skill does
that classification).

Return: counts (passed, failed), list of review item ids written.
""")
```

### Step 2.4: Analyze Results

Read the returned summary. If all passed AND all tasks `complete`: proceed to Step 2.5 (UC done-review). Do **not** declare the roadmap complete until Step 2.5 finishes.

If failures exist, classify each test-runner review item:

- **Task / roadmap issue** — the failure is a coding error, missing logic, or roadmap-level oversight. Revise the affected task file(s): update Description, Files, Acceptance Criteria, or `depends_on` as needed; reset the task's `status: pending`; increment `cycle:`; append a `## Log` entry citing the review item that triggered the revision. Any transitively affected downstream tasks also reset to `pending`. Re-run roadmap-reviewer on the revised tasks (single scoped round). If it passes, return to Step 2.1.
- **Architecture issue** — the failure exposes a wrong contract, missing component, or test-strategy gap. Update the test-runner review item `target: architecture` if not already so (create a new arch-targeted review item if needed). **Stop Phase 2.** Recommend `/a4:arch iterate`. On resume, the new review items from `arch iterate` drive the fix.
- **Use-case issue** — the failure exposes ambiguous flow / validation / error handling. Retarget to `usecase/<id>-<slug>`. **Stop Phase 2.** Recommend `/a4:usecase iterate`.

If 3 cycles complete and failures remain: halt. Mark affected tasks `status: failing`, append `## Log` per failure, leave all test-runner review items `open`. Report the state to the user.

### Step 2.5: UC ship-review (user-confirmed)

Runs only when Step 2.4 reached the happy-path branch (all tests passed, all tasks `complete`). The goal: for each UC whose implementation is now complete, let the user confirm that the running system reflects it, then flip `status: implementing → shipped` via the writer.

1. **Collect candidates.** A UC X is a candidate when:
   - X.status is `implementing` (flipped by `task-implementer` at work-start per its protocol).
   - Every task with `implements: [usecase/X]` in its frontmatter now has `status: complete`.
   - No review item with `target: usecase/X` is `open` or `in-progress` (all resolved or discarded).

   If the candidate set is empty, skip to wrap-up.

2. **Review each candidate.** For every candidate X, read:
   - The UC file (Flow, Validation, Error handling, Expected Outcome).
   - The `## Log` entries of its implementing tasks.
   - The test-runner return summary from Step 2.3 (passed-test names relevant to X).

   Compose a short per-UC verdict — **two to four sentences** — covering: (a) which task(s) implemented it, (b) which tests exercise its flow / validation / error handling, (c) any Expected Outcome point not yet visibly covered by the tests. No new files, no review items emitted here.

3. **Present to the user.** For each candidate X, show the verdict and ask:
   > UC X is ready to mark shipped based on completed tasks and passing tests. [verdict]. Mark shipped?

   Accept natural-language answers:
   - `"yes"`, `"ok"`, `"맞아요"`, `"확정"`, `"mark shipped"`, `"ship it"` → confirm.
   - `"not yet"`, `"아직"`, `"let me verify"`, `"hold"` → defer (leave `implementing`).
   - `"no — X is incomplete because..."` → defer with reason; fold the reason into a fresh review item `target: usecase/X`, `kind: gap`, `source: self`.

4. **Apply confirmations via the writer.** For every UC the user confirmed:

   ```bash
   uv run "${CLAUDE_PLUGIN_ROOT}/scripts/transition_status.py" \
     "$(git rev-parse --show-toplevel)/a4" \
     --file "usecase/<id>-<slug>.md" --to shipped \
     --reason "Phase 2 cycle <N>; tests <list>; user confirmed"
   ```

   The script validates that every task in `implemented_by:` is `complete` (refuses otherwise), writes `status: shipped`, bumps `updated:`, and appends the `## Log` entry. If the UC has a non-empty `supersedes:` list, the same invocation cascades each supersedes target from `shipped` to `superseded` with a back-pointer log entry. Do **not** hand-edit the UC frontmatter or the supersedes targets.

5. **Commit** all UC ship-transitions together as one commit (see Commit Points). The cascade-flipped predecessor UCs land in the same working-tree change as the ship edit and belong in the same commit.

After Step 2.5, declare the roadmap complete and proceed to wrap-up. Leftover `implementing` UCs (user deferred on one or more) stay that way; the next `/a4:roadmap iterate` session will re-offer them.

**`shipped` is forward-path terminal.** If a UC needs revision later, either (a) create a new UC via `/a4:usecase` with `supersedes: [usecase/<old-id>-<slug>]`; when that new UC eventually ships, the writer flips the old one to `superseded`. Or (b) flip `shipped → discarded` via the writer when the code is being removed. Never try to move a UC back from `shipped` to `implementing` or `draft`.

### Session-start resume hygiene revisited

The "reset `implementing` tasks to `pending`" rule at session start is still correct, but route it through the writer:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/transition_status.py" \
  "$(git rev-parse --show-toplevel)/a4" \
  --file "task/<id>-<slug>.md" --to pending \
  --reason "session-start hygiene: previous session terminated"
```

`scripts/refresh_implemented_by.py` also runs automatically via the `scripts/a4_hook.py session-start` SessionStart hook (see `hooks/hooks.json`) to catch any task-file changes that happened on other branches.

---

## Commit Points

- **Roadmap generation** — commit `a4/roadmap.md` + all new `a4/task/*.md` files together once the user confirms the initial roadmap.
- **Roadmap revision during verification** — commit revised roadmap / task files + resolved review items as one commit per review round.
- **Per-task implementation** — task-implementer commits its own code + unit tests per task; the orchestrating skill does **not** also commit those files.
- **Per-cycle test results** — commit the emitted test-runner review items + updated task `## Log` entries together as one commit after Step 2.3.
- **Roadmap revision after test failure** — commit revised task files + status resets + review item linkages as one commit before re-running Step 2.1.
- **UC ship-transitions (Step 2.5)** — commit the UC files confirmed `shipped` together in one commit, separate from task commits. Predecessor UC files auto-flipped to `superseded` by `transition_status.py` are part of the same working-tree change and belong in the same commit. Message prefix: `docs(a4): ship UC <ids>`.
- **Final state** — commit the final roadmap / tasks / review items when the user wraps up.

Never skip hooks, amend, or force-push without explicit user instruction.

## Wrap Up

When the user ends the session, or when all tasks are `complete` and all tests pass:

1. Summarize:
   - Tasks completed / revised / still failing.
   - Review items opened / resolved / still open.
   - Cycles consumed.
2. If any tasks remain `pending` / `failing` or any review items are `open`, suggest `/a4:roadmap iterate` as the resumption path.
3. Suggest `/a4:handoff` to snapshot the session.

## Agent Usage

Context is passed via file paths, not agent memory.

- **`roadmap-reviewer`** — `Agent(subagent_type: "a4:roadmap-reviewer")`. Reviews the roadmap + tasks against architecture / UCs; emits per-finding review items.
- **`task-implementer`** — `Agent(subagent_type: "a4:task-implementer")`. Implements one task + its unit tests; commits code + tests. Never reads other tasks' files.
- **`test-runner`** — `Agent(subagent_type: "a4:test-runner")`. Runs integration + smoke tests; emits per-failure review items. Does not classify failures.

## Non-Goals

- Do not split the roadmap into per-milestone files. `roadmap.md` holds all milestone narrative in one file per the ADR.
- Do not add a `phase:` frontmatter field to tasks. `milestone:` covers phase semantics.
- Do not maintain a separate `roadmap.history.md`. Each task's `## Log` section records per-task history; the workspace's git history covers the rest.
- Do not emit aggregated test reports or aggregated roadmap-review reports. All findings are per-review-item files.
- Do not track per-source SHAs on `roadmap.md`. The wiki update protocol's footnote + drift-detector flow handles cross-reference consistency.

