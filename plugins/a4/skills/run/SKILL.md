---
name: run
description: "This skill should be used when the user wants to drive the agent-based implement + test loop over the tasks already authored in a4/task/. Common triggers include: 'run', 'implement the tasks', 'run the implementation loop', 'kick off the agents', 'task-implementer', 'agent loop'. Picks ready tasks, spawns task-implementer agents (parallel where independent), runs the test-runner, classifies failures, and conditionally performs UC ship-review. Up to 3 cycles. Works with or without UCs — UC ship-review is conditional on per-task implements: being non-empty."
argument-hint: <optional: 'iterate' to resume after a halt; auto-detects workspace state otherwise>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, TaskCreate, TaskUpdate, TaskList
---

# Implementation Run Loop

Drives the agent-based implement + test loop over the tasks already authored in `a4/task/`. Reads `a4/roadmap.md`'s Launch & Verify (or `a4/bootstrap.md` for UC-less projects without a roadmap) for build / launch / test commands. Spawns `task-implementer` per ready task, runs `test-runner` after each cycle, classifies failures, and conditionally ship-reviews UCs. Bounded to 3 cycles per invocation.

Authoring is out of scope: `/a4:roadmap` writes the roadmap + UC-batch tasks; `/a4:task` writes single ad-hoc tasks. This skill assumes both have already produced the task files it consumes.

## Workspace Layout

Resolve `a4/` via `git rev-parse --show-toplevel`. Inputs:

- `a4/task/<id>-<slug>.md` — required. The set of executable units this run consumes.
- `a4/roadmap.md` — preferred. Provides Launch & Verify (build / launch / test commands) and milestone narrative.
- `a4/bootstrap.md` — fallback for UC-less projects with no roadmap. Same Launch & Verify shape.
- `a4/architecture.md` — passed to agents for contract context.
- `a4/usecase/*.md` — read for UC ship-review candidates (Step 5). Absent in UC-less projects; that's fine.
- `a4/review/*.md` — open review items influence ready-set selection and resume behavior.

Outputs:

- `a4/review/<id>-<slug>.md` — test-runner findings; gap items emitted during ship-review when the user defers.
- Per-task `## Log` entries appended via `scripts/transition_status.py` on every status change.
- Per-task implementation commits authored by `task-implementer` agents.

## Launch & Verify Source

`/a4:run` does not auto-detect commands. Resolution order:

1. `a4/roadmap.md` § "Launch & Verify" — the normal path.
2. `a4/bootstrap.md` § "Launch & Verify" — fallback when no `roadmap.md` exists (UC-less single-task or ADR-justified workspaces). Both `/a4:auto-bootstrap` and the manual bootstrap flow write this section.
3. **Halt** if neither exists. Tell the user to run `/a4:auto-bootstrap` (or write `roadmap.md` via `/a4:roadmap`) first. The final fallback policy for projects that decline both is unresolved (see Out of Scope).

## Mode Detection

Determined by the workspace state, not by frontmatter flags:

- **Implement mode** — `a4/task/` has `pending` or `failing` tasks, or no test-runner review items yet reference the current cycle. Run Step 1 → 5 in order.
- **Iterate mode** — open review items target a task or `roadmap` (typically from the prior cycle's test-runner). Walk them before re-running Step 1.

Mode detection at session start:

```bash
ls a4/task/*.md                                   # any tasks?
grep -l '^status: pending'   a4/task/*.md         # pending tasks
grep -l '^status: failing'   a4/task/*.md         # failing tasks
ls a4/review/*.md | xargs grep -l 'status: open\|target: roadmap\|target: task/'
```

If no tasks exist at all: halt and tell the user to run `/a4:roadmap` (UC-driven batch) or `/a4:task` (single ad-hoc) first.

## Resume Hygiene

At session start, for every task with `status: implementing`, reset to `pending` via the writer (an `implementing` status at session-start means the prior session crashed mid-work):

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
Roadmap file: <absolute path to a4/roadmap.md, or a4/bootstrap.md when no roadmap.md exists>
Architecture file: <absolute path to a4/architecture.md>
Relevant UC files: <paths referenced by the task's implements:; empty list when implements: is empty>

Read the task file for Description, Files, Unit Test Strategy, Acceptance Criteria.
Pull build + unit-test commands from the Launch & Verify section of the roadmap (or bootstrap).

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
  --reason "/a4:run Step 2 spawning task-implementer"
```

After the agent returns, call the writer with `--to complete` or `--to failing` based on the return value (include a `--reason` naming the cycle and outcome). Do not hand-edit `status:` / `updated:` / `## Log` — the writer owns them.

## Step 3: Run Integration + Smoke Tests

After all tasks reach `complete` (or after a cycle ends with failures still outstanding), spawn the test-runner:

```
Agent(subagent_type: "a4:test-runner", prompt: """
Roadmap file: <absolute path to a4/roadmap.md, or a4/bootstrap.md when no roadmap.md exists>
a4/ path: <absolute path>
Cycle: <current integer>

Use the Launch & Verify config for build / run / test commands. Run integration and
smoke tests as defined there. For each failing test, emit one review item at
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

## Step 4: Analyze Results

Read the returned summary. If all passed AND all tasks `complete`: proceed to Step 5 (UC ship-review). Do **not** declare the run complete until Step 5 finishes (or its candidate set is empty).

If failures exist, classify each test-runner review item. **Transition to `conversational`** before classifying — failure classification is a decision point that belongs to the user.

- **Task / roadmap issue** — coding error, missing logic, or roadmap-level oversight. Revise the affected task file(s): update Description, Files, Acceptance Criteria, or `depends_on` as needed; reset the task's `status: pending`; increment `cycle:`; append a `## Log` entry citing the review item that triggered the revision. Any transitively affected downstream tasks also reset to `pending`. Re-run roadmap-reviewer on the revised tasks (single scoped round). If it passes, return to Step 1.
- **Architecture issue** — wrong contract, missing component, or test-strategy gap. Update the test-runner review item `target: architecture` if not already so (create a new arch-targeted review item if needed). **Stop the run.** Recommend `/a4:arch iterate`. On resume, the new review items from `arch iterate` drive the fix.
- **Use-case issue** — ambiguous flow / validation / error handling. Retarget to `usecase/<id>-<slug>`. **Stop the run.** Recommend `/a4:usecase iterate`. (Only meaningful for UC-driven tasks; UC-less tasks cannot produce a UC-targeted finding.)

If 3 cycles complete and failures remain: halt. Mark affected tasks `status: failing`, append `## Log` per failure, leave all test-runner review items `open`. Report the state to the user. Transition to `conversational`.

## Step 5: UC ship-review (conditional, user-confirmed)

Runs only when Step 4 reached the happy-path branch (all tests passed, all tasks `complete`). The goal: for each UC whose implementation is now complete, let the user confirm that the running system reflects it, then flip `status: implementing → shipped` via the writer.

**Conditional on UC presence.** If no task in this run has a non-empty `implements:` (the project is UC-less, or every task in scope is a spike / bug / ADR-justified feature), the candidate set is empty by construction — skip directly to wrap-up. This is not an error; it's the UC-less normal case.

When `implements:` is populated on at least one task:

1. **Collect candidates.** A UC X is a candidate when:
   - X.status is `implementing` (flipped by `task-implementer` at work-start per its protocol).
   - Every task with `implements: [usecase/X]` in its frontmatter now has `status: complete`.
   - No review item with `target: usecase/X` is `open` or `in-progress` (all resolved or discarded).

   If the candidate set is empty, skip to wrap-up.

2. **Review each candidate.** For every candidate X, read:
   - The UC file (Flow, Validation, Error handling, Expected Outcome).
   - The `## Log` entries of its implementing tasks.
   - The test-runner return summary from Step 3 (passed-test names relevant to X).

   Compose a short per-UC verdict — **two to four sentences** — covering: (a) which task(s) implemented it, (b) which tests exercise its flow / validation / error handling, (c) any Expected Outcome point not yet visibly covered by the tests. No new files, no review items emitted here.

3. **Present to the user.** Transition to `conversational`. For each candidate X, show the verdict and ask:
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
     --reason "/a4:run cycle <N>; tests <list>; user confirmed"
   ```

   The script validates that every task in `implemented_by:` is `complete` (refuses otherwise), writes `status: shipped`, bumps `updated:`, and appends the `## Log` entry. If the UC has a non-empty `supersedes:` list, the same invocation cascades each supersedes target from `shipped` to `superseded` with a back-pointer log entry. Do **not** hand-edit the UC frontmatter or the supersedes targets.

5. **Commit** all UC ship-transitions together as one commit (see Commit Points). The cascade-flipped predecessor UCs land in the same working-tree change as the ship edit and belong in the same commit.

After Step 5, declare the run complete and proceed to wrap-up. Leftover `implementing` UCs (user deferred on one or more) stay that way; the next `/a4:run iterate` session will re-offer them.

**`shipped` is forward-path terminal.** If a UC needs revision later, either (a) create a new UC via `/a4:usecase` with `supersedes: [usecase/<old-id>-<slug>]`; when that new UC eventually ships, the writer flips the old one to `superseded`. Or (b) flip `shipped → discarded` via the writer when the code is being removed. Never try to move a UC back from `shipped` to `implementing` or `draft`.

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
- **UC ship-transitions (Step 5)** — commit the UC files confirmed `shipped` together in one commit, separate from task commits. Predecessor UC files auto-flipped to `superseded` by `transition_status.py` are part of the same working-tree change and belong in the same commit. Message prefix: `docs(a4): ship UC <ids>`.
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

`roadmap-reviewer` is **not** invoked from `/a4:run` directly — Step 4 may recommend a scoped re-review of revised tasks, but spawning that agent is `/a4:roadmap iterate`'s responsibility.

## Out of Scope

- **Authoring** — task files, roadmap.md, ADRs, UCs are written elsewhere. `/a4:run` only reads them.
- **Final fallback when neither roadmap.md nor bootstrap.md exists** — currently halts with a recommendation. A "best-effort auto-detect" or "read AGENTS.md / package.json scripts" fallback is unresolved and not implemented.
- **roadmap-reviewer scoped re-runs** — `/a4:run` Step 4 currently recommends `/a4:roadmap iterate` rather than spawning the reviewer inline. Inline scoped re-review is a possible future addition.
- **Per-cycle parallelism beyond independent ready tasks** — task-implementer parallelism is bounded by the dependency graph; no further parallelization is attempted.

## Non-Goals

- Do not rebuild Phase 1. `/a4:roadmap` owns roadmap authoring; `/a4:task` owns single-task authoring. If `/a4:run` notices a missing task or roadmap gap, it emits a review item targeting `roadmap` and stops — it does not re-author.
- Do not split task-implementer / test-runner into sub-skills. The agent loop is intentionally one skill with cycle semantics and cascade rules.
- Do not emit aggregated test reports. All findings are per-review-item files.
- Do not flip UC status without going through `transition_status.py`. The script enforces the cascade and log invariants.
