---
name: run
description: "This skill should be used when the user wants to drive the agent-based implement + test loop over the tasks already authored in a4/task/. Common triggers include: 'run', 'implement the tasks', 'run the implementation loop', 'kick off the agents', 'task-implementer', 'agent loop'. Two stages: an autonomous loop body (pick → implement → test, up to 3 cycles), then a user-driven post-loop review that classifies failures or confirms UC ship. Works with or without UCs — UC ship-review is conditional on per-task implements: being non-empty."
argument-hint: <optional: 'iterate' to resume after a halt; auto-detects workspace state otherwise>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, TaskCreate, TaskUpdate, TaskList
---

# Implementation Run Loop

Two stages over the tasks already authored in `a4/task/`:

1. **Loop body (Steps 1–3, autonomous)** — pick ready tasks, spawn `task-implementer` agents (parallel where independent), run the `test-runner`. Bounded to 3 cycles per invocation.
2. **Post-loop review (Step 4, user-driven)** — depending on the loop's outcome:
   - **Failure path** — user classifies each failing test-runner finding into task / arch / UC and routes accordingly.
   - **Ship path** — user confirms which UCs go `implementing → shipped`.

Reads `a4/bootstrap.md` for build / launch / test / smoke / isolation commands — bootstrap is the single source of truth for Launch & Verify (per [`references/wiki-authorship.md`](${CLAUDE_PLUGIN_ROOT}/references/wiki-authorship.md); `roadmap.md` only embeds those bootstrap sections for human readers).

Authoring is out of scope: `/a4:roadmap` writes the roadmap + UC-batch tasks; `/a4:task` writes single ad-hoc tasks. This skill assumes both have already produced the task files it consumes.

## Workspace Layout

Resolve `a4/` via `git rev-parse --show-toplevel`. Inputs:

- `a4/task/<id>-<slug>.md` — required. The set of executable units this run consumes.
- `a4/bootstrap.md` — required. Single source of truth for Launch & Verify (build / launch / test / smoke / isolation).
- `a4/roadmap.md` — optional. Provides milestone narrative + dependency-graph snapshot. Embeds bootstrap's L&V sections; this skill does not parse the embed.
- `a4/architecture.md` — passed to agents for contract context.
- `a4/usecase/*.md` — read for UC ship-review candidates (Step 4b). Absent in UC-less projects; that's fine.
- `a4/review/*.md` — open review items influence ready-set selection and resume behavior.

Outputs:

- `a4/review/<id>-<slug>.md` — test-runner findings; gap items emitted during ship-review when the user defers.
- Per-task `## Log` entries appended via `scripts/transition_status.py` on every status change.
- Per-task implementation commits authored by `task-implementer` agents.

## Launch & Verify Source

`/a4:run` does not auto-detect commands. Resolution:

1. `a4/bootstrap.md` — single source of truth. Read `## Verified Commands` (build / launch / test), `## Smoke Scenario`, `## Test Isolation Flags`. Both `/a4:auto-bootstrap` and the manual bootstrap flow write these sections; the roadmap (when present) embeds them via Obsidian transclusion but does **not** own them.
2. **Halt and delegate to `/a4:compass`** when `bootstrap.md` is absent, per [[plugins/a4/spec/2026-04-25-a4-run-final-fallback-policy]]. Invoke compass with the structured diagnosis argument so its Step 3 Gap Diagnosis recommends the correct upstream skill:

   ```
   Skill({ skill: "a4:compass", args: "from=run; missing=bootstrap.md" })
   ```

   `/a4:run` does not pre-judge which upstream skill applies, does not auto-chain into the recommendation, and does not look upstream of `bootstrap.md` itself — compass's pipeline walk owns those decisions. `roadmap.md`'s presence or absence is irrelevant to `/a4:run`'s L&V resolution.

## Mode Detection

Determined by the workspace state, not by frontmatter flags:

- **Implement mode** — `a4/task/` has `pending` or `failing` tasks, or no test-runner review items yet reference the current cycle. Run Steps 1–4 in order. (`open` tasks are backlog and intentionally **not** picked up here — the user must transition `open → pending` to enqueue them.)
- **Iterate mode** — open review items target a task or `roadmap` (typically from the prior cycle's test-runner). See **Iteration Entry** below before re-running Step 1.

Mode detection at session start:

```bash
ls a4/task/*.md                                   # any tasks?
grep -l '^status: pending'   a4/task/*.md         # pending tasks
grep -l '^status: failing'   a4/task/*.md         # failing tasks
ls a4/review/*.md | xargs grep -l 'status: open\|target: roadmap\|target: task/'
```

If no tasks exist at all: halt and tell the user to run `/a4:roadmap` (UC-driven batch) or `/a4:task` (single ad-hoc) first.

### Iteration Entry

Mechanics (filter, backlog presentation, writer calls, footnote rules, discipline) follow [`references/iterate-mechanics.md`](${CLAUDE_PLUGIN_ROOT}/references/iterate-mechanics.md). This section adds only the run-specific work.

**Backlog filter:** `target: task/*` OR `target: roadmap` (typically `source: test-runner` from the prior cycle).

**Run-specific work** between writer calls:
- **Cycle counter** — task `cycle:` increments at every revise → re-run pass; the `## Log` entry cites the cycle number.
- **Cascade reset** — when a task is reset to `pending` for re-implementation, every downstream task whose `depends_on` traces back to it also resets to `pending` and gets a `## Log` entry.
- **Crash hygiene at session start** — see Resume Hygiene below.
- **Stop on strong upstream** — `target: architecture` and `target: usecase/*` findings halt the run and route to `/a4:arch iterate` or `/a4:usecase iterate` per [`references/wiki-authorship.md`](${CLAUDE_PLUGIN_ROOT}/references/wiki-authorship.md) §Cross-stage feedback. The full classification table is at [`references/failure-classification.md`](${CLAUDE_PLUGIN_ROOT}/skills/run/references/failure-classification.md).

## Resume Hygiene

At session start, for every task with `status: progress`, reset to `pending` via the writer (a `progress` status at session-start means the prior session crashed mid-work):

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/transition_status.py" \
  "$(git rev-parse --show-toplevel)/a4" \
  --file "task/<id>-<slug>.md" --to pending \
  --reason "session-start hygiene: previous session terminated"
```

`scripts/refresh_implemented_by.py` runs automatically via the `scripts/a4_hook.py session-start` SessionStart hook (see `hooks/hooks.json`) to catch task-file changes that happened on other branches.

---

## Step 1: Pick Ready Tasks

A task is **ready** when all of:

- `status ∈ {pending, failing}`
- every `depends_on` entry resolves to a task with `status: complete`
- one of:
  - `implements:` is non-empty AND every UC in `implements:` has `status ∈ {ready, implementing}` (so `revising` / `discarded` / `blocked` / `superseded` / `shipped` UCs' tasks are skipped), OR
  - `implements:` is empty (UC-less task — ADR-justified feature, spike, or bug). Ready conditions vacuously pass; UC status checks do not apply.

Build the ready set by reading task + UC frontmatter.

Independent ready tasks run in parallel. Tasks with mutual dependencies run sequentially.

## Step 2: Spawn task-implementer

For each ready task, spawn one agent:

```
Agent(subagent_type: "a4:task-implementer", prompt: """
Task file: <absolute path to a4/task/<id>-<slug>.md>
Bootstrap file: <absolute path to a4/bootstrap.md>  # single source of truth for L&V
Architecture file: <absolute path to a4/architecture.md>
Relevant UC files: <paths referenced by the task's implements:; empty list when implements: is empty>

Read the task file for Description, Files, Unit Test Strategy, Acceptance Criteria.
Pull build + unit-test commands from bootstrap.md's ## Verified Commands section.

Implement the task and write its unit tests. All unit tests must pass.
Commit code + unit tests (one commit per task).
Return: result (pass/fail), summary of changes, any issues encountered.
""")
```

Before spawning, flip the task via the writer:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/transition_status.py" \
  "$(git rev-parse --show-toplevel)/a4" \
  --file "task/<id>-<slug>.md" --to progress \
  --reason "/a4:run Step 2 spawning task-implementer"
```

After the agent returns, call the writer with `--to complete` or `--to failing` based on the return value (include a `--reason` naming the cycle and outcome). Do not hand-edit `status:` / `updated:` / `## Log` — the writer owns them.

## Step 3: Run Integration + Smoke Tests

After all tasks reach `complete` (or after a cycle ends with failures still outstanding), spawn the test-runner:

```
Agent(subagent_type: "a4:test-runner", prompt: """
Bootstrap file: <absolute path to a4/bootstrap.md>  # single source of truth for L&V
a4/ path: <absolute path>
Cycle: <current integer>

Use bootstrap.md's ## Verified Commands, ## Smoke Scenario, and ## Test Isolation Flags
sections for build / run / test commands. Run integration and smoke tests as defined
there. For each failing test, emit one review item at
a4/review/<id>-<slug>.md via allocate_id.py with:

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

## Step 4: Post-loop Review (user-driven)

Once the loop body settles, **transition to `conversational`** and branch on outcome. There are exactly two branches and they are mutually exclusive on a single run:

- **4a. Failure path** — at least one test-runner review item from Step 3 is open. The user classifies each finding and the run routes accordingly.
- **4b. Ship path** — all tests passed AND all in-scope tasks reached `status: complete`. The user confirms `implementing → shipped` per candidate UC.

Both branches are user-driven. No agent classifies failures or auto-ships UCs. The loop body's autonomy ends at the seam into Step 4.

This skill follows the **stop on strong upstream dependency** policy at [`references/wiki-authorship.md`](${CLAUDE_PLUGIN_ROOT}/references/wiki-authorship.md) §Cross-stage feedback — task implementation is contract-bound to `architecture.md` and AC-bound to `usecase/*.md`, so an upstream finding halts the run rather than retrying against stale assumptions.

### 4a. Failure path — classify findings

For each open test-runner review item, the user picks one of three categories: **task / roadmap**, **architecture**, or **usecase**. Routing per category — including cascade rules, cycle-counter increments, and `transition_status.py` calls — is in [`references/failure-classification.md`](${CLAUDE_PLUGIN_ROOT}/skills/run/references/failure-classification.md).

Cycle bound: if 3 cycles complete and failures remain, halt as described in that reference.

### 4b. Ship path — confirm UCs to ship

For each ship-candidate UC, compose a short verdict and ask the user `mark shipped?`. Per-UC candidate rules, verdict template, defer protocol, and writer call are in [`references/uc-ship-review.md`](${CLAUDE_PLUGIN_ROOT}/skills/run/references/uc-ship-review.md).

The ship unit varies by **pipeline shape** (see [`references/pipeline-shapes.md`](${CLAUDE_PLUGIN_ROOT}/references/pipeline-shapes.md)). Per-task vs per-UC ship is `task.implements:`-driven, not invocation-driven:

- **Per-UC ship** — when `task.implements:` is non-empty (Full shape, or Minimal-feature-with-UC). Multiple tasks shipping their target UC's full Flow flip the UC `implementing → shipped`.
- **Per-task ship** — when `task.implements:` is empty (Minimal shape's bug / spike / ADR-justified feature). Each task transitions to `complete` independently and 4b skips UC bookkeeping entirely. That is the normal case for those shapes, not an error.

A run can mix both unit types in one invocation (e.g., a UC-driven task and an ADR-justified bug fix shipping in the same cycle); each task's `implements:` field decides which branch its ship verdict takes.

Leftover `implementing` UCs (user deferred on one or more) stay that way; the next `/a4:run iterate` session will re-offer them.

After 4b finishes (or 4a routes the run elsewhere), proceed to wrap-up.

---

## Acceptance Criteria Source by Task Kind

When a task-implementer reads a task's `## Acceptance Criteria` section, the source convention (set at authoring time by `/a4:roadmap` or `/a4:task`) is:

| Task kind / shape | AC source |
|---|---|
| `feature` + `implements: [usecase/...]` | UC `## Flow` / `## Validation` / `## Error handling` |
| `feature` + `justified_by: [decision/...]` (UC-less) | ADR `## Decision` + relevant `architecture.md` section |
| `spike` | hypothesis + expected result, the spike's own body |
| `bug` | reproduction scenario + fixed criteria |

`/a4:run` does not enforce this — validators do not block on AC source. The convention is documentation only; the AC section must exist on the task body regardless.

## Commit Points

- **Per-task implementation** — `task-implementer` commits its own code + unit tests per task; `/a4:run` does **not** also commit those files.
- **Per-cycle test results** — commit the emitted test-runner review items + updated task `## Log` entries together as one commit after Step 3.
- **Roadmap revision after test failure** — commit revised task files + status resets + review item linkages as one commit before re-running Step 1.
- **UC ship-transitions (Step 4b)** — commit the UC files confirmed `shipped` together in one commit, separate from task commits. Predecessor UC files auto-flipped to `superseded` by `transition_status.py` are part of the same working-tree change and belong in the same commit. Message prefix: `docs(a4): ship UC <ids>`.
- **Final state** — commit any residual review items / log updates when the user wraps up.

Never skip hooks, amend, or force-push without explicit user instruction.

## Wrap Up

When all tasks are `complete` and all tests pass (or when the user ends the session):

1. Summarize:
   - Tasks completed / revised / still failing.
   - Review items opened / resolved / still open.
   - Cycles consumed.
   - UCs shipped this run (empty list is fine for UC-less runs).
2. If any tasks remain `pending` / `failing` or any review items are `open`, suggest `/a4:run iterate` as the resumption path.
3. Suggest `/a4:handoff` to snapshot the session.

## Agent Usage

Context is passed via file paths, not agent memory.

- **`task-implementer`** — `Agent(subagent_type: "a4:task-implementer")`. Implements one task + its unit tests; commits code + tests. Never reads other tasks' files.
- **`test-runner`** — `Agent(subagent_type: "a4:test-runner")`. Runs integration + smoke tests; emits per-failure review items. Does not classify failures.

`roadmap-reviewer` is **not** invoked from `/a4:run` directly — Step 4a may recommend a scoped re-review of revised tasks, but spawning that agent is `/a4:roadmap iterate`'s responsibility.

## Out of Scope

- **Authoring** — task files, roadmap.md, ADRs, UCs are written elsewhere. `/a4:run` only reads them.
- **"Best-effort auto-detect" of build / test commands without `bootstrap.md`.** When `bootstrap.md` is absent, `/a4:run` delegates to `/a4:compass` per [[plugins/a4/spec/2026-04-25-a4-run-final-fallback-policy]] — the user is routed to the correct upstream skill rather than `/a4:run` guessing commands from `package.json` scripts or `AGENTS.md`. Auto-detection of commands is intentionally out of scope. Note: `roadmap.md`'s presence is irrelevant for L&V resolution — bootstrap is the single source of truth.
- **roadmap-reviewer scoped re-runs** — `/a4:run` Step 4a currently recommends `/a4:roadmap iterate` rather than spawning the reviewer inline. Inline scoped re-review is a possible future addition.
- **Per-cycle parallelism beyond independent ready tasks** — task-implementer parallelism is bounded by the dependency graph; no further parallelization is attempted.

## Non-Goals

- Do not rebuild Phase 1. `/a4:roadmap` owns roadmap authoring; `/a4:task` owns single-task authoring. If `/a4:run` notices a missing task or roadmap gap, it emits a review item targeting `roadmap` and stops — it does not re-author.
- Do not split task-implementer / test-runner into sub-skills. The agent loop is intentionally one skill with cycle semantics and cascade rules.
- Do not split post-loop review (Step 4) into a separate skill, and do not delegate failure classification or UC ship to an agent. The seam is loop body (autonomous) ↔ post-loop review (user-driven); ship is forward-path terminal and stays user-authorized. Verdict / classification details live in `references/failure-classification.md` and `references/uc-ship-review.md` to keep this SKILL.md tight.
- Do not emit aggregated test reports. All findings are per-review-item files.
- Do not flip UC status without going through `transition_status.py`. The script enforces the cascade and log invariants.
