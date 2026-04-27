---
name: run
description: "This skill should be used when the user wants to drive the agent-based implement + test loop over the tasks already authored in a4/task/. Common triggers include: 'run', 'implement the tasks', 'run the implementation loop', 'kick off the agents', 'task-implementer', 'agent loop'. Two stages: an autonomous loop body (pick → implement → test, up to 3 cycles), then a user-driven post-loop review that classifies failures or confirms UC ship. Works with or without UCs — UC ship-review is conditional on per-task implements: being non-empty."
argument-hint: <optional: 'iterate' to resume after a halt, 'serial' to opt out of parallel worktree isolation; auto-detects workspace state otherwise>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, TaskCreate, TaskUpdate, TaskList
---

# Implementation Run Loop

Two stages over the tasks already authored in `a4/task/`:

1. **Loop body (Steps 1–3, autonomous)** — pick ready tasks, spawn `task-implementer` agents in isolated worktrees (parallel where independent), merge each successful worktree branch back to local main, run the `test-runner`. Bounded to 3 cycles per invocation.
2. **Post-loop review (Step 4, user-driven)** — depending on the loop's outcome:
   - **Failure path** — user classifies each failing test-runner finding into task / arch / UC and routes accordingly.
   - **Ship path** — user confirms which UCs go `implementing → shipped`.

Reads `a4/bootstrap.md` for build / launch / test / smoke / isolation commands — bootstrap is the single source of truth for Launch & Verify (per [`references/wiki-authorship.md`](${CLAUDE_PLUGIN_ROOT}/references/wiki-authorship.md); `roadmap.md` only links to it for human readers).

Authoring is out of scope: `/a4:roadmap` writes the roadmap + UC-batch tasks; `/a4:task` writes single ad-hoc tasks. This skill assumes both have already produced the task files it consumes.

## Workspace Layout

Resolve `a4/` via `git rev-parse --show-toplevel`. Inputs:

- `a4/task/<id>-<slug>.md` — required. The set of executable units this run consumes.
- `a4/bootstrap.md` — required. Single source of truth for Launch & Verify (build / launch / test / smoke / isolation).
- `a4/roadmap.md` — optional. Provides milestone narrative + dependency-graph snapshot. Links to bootstrap for L&V; this skill does not parse the link.
- `a4/architecture.md` — passed to agents for contract context.
- `a4/usecase/*.md` — read for UC ship-review candidates (Step 4b). Absent in UC-less projects; that's fine.
- `a4/review/*.md` — open review items influence ready-set selection and resume behavior.

Outputs:

- `a4/review/<id>-<slug>.md` — test-runner findings; gap items emitted during ship-review when the user defers.
- Per-task `<log>` entries appended via `scripts/transition_status.py` on every status change.
- Per-task implementation commits authored by `task-implementer` agents.

## Launch & Verify Source

`/a4:run` does not auto-detect commands. Resolution:

1. `a4/bootstrap.md` — single source of truth. Read its `<verify>` section (verified commands, smoke scenario, test isolation flags) plus `<launch>` (build / launch). Both `/a4:auto-bootstrap` and the manual bootstrap flow write these sections; the roadmap (when present) links to them but does **not** own them.
2. **Halt and delegate to `/a4:compass`** when `bootstrap.md` is absent. Invoke compass with the structured diagnosis argument so its Step 3 Gap Diagnosis recommends the correct upstream skill:

   ```
   Skill({ skill: "a4:compass", args: "from=run; missing=bootstrap.md" })
   ```

   `/a4:run` does not pre-judge which upstream skill applies, does not auto-chain into the recommendation, and does not look upstream of `bootstrap.md` itself — compass's pipeline walk owns those decisions. `roadmap.md`'s presence or absence is irrelevant to `/a4:run`'s L&V resolution.

## Mode Detection

Determined by the workspace state, not by frontmatter flags:

- **Implement mode** — `a4/task/` has `pending` or `failing` tasks, or no test-runner review items yet reference the current cycle. Run Steps 1–4 in order. (`open` tasks are backlog and intentionally **not** picked up here — the user must transition `open → pending` to enqueue them.)
- **Iterate mode** — open review items target a task or `roadmap` (typically from the prior cycle's test-runner). See **Iteration Entry** below before re-running Step 1.
- **Pre-flight** (applies to both modes, run at Step 1 entry) — local `HEAD` must equal `origin/HEAD` per [`references/parallel-isolation.md`](${CLAUDE_PLUGIN_ROOT}/skills/run/references/parallel-isolation.md). Halt with a push instruction on mismatch.
- **Serial fallback** (`/a4:run serial` or `/a4:run iterate serial`) — opt-in mode that skips worktree isolation and the merge sweep entirely. Use only when worktree isolation is unavailable; rules in [`references/parallel-isolation.md`](${CLAUDE_PLUGIN_ROOT}/skills/run/references/parallel-isolation.md).

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
- **Cycle counter** — task `cycle:` increments at every revise → re-run pass; the `<log>` entry cites the cycle number.
- **Cascade reset** — when a task is reset to `pending` for re-implementation, every downstream task whose `depends_on` traces back to it also resets to `pending` and gets a `<log>` entry.
- **Crash hygiene at session start** — see Resume Hygiene below.
- **Merge-sweep retry** — for tasks left at `failing` because Step 2.5 hit a conflict, the preserved worktree branch is the user's resolution surface. After the user resolves, `/a4:run iterate` re-attempts `git merge --no-ff` on that branch from local main; on success it transitions the task to `complete` and runs the standard 3-step worktree cleanup. If the user instead discards the work, the task drops back to `pending` and the next cycle re-spawns a fresh worktree.
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

Orphaned worktrees under `<repo>/.claude/worktrees/agent-*/` (created by an agent that crashed or was interrupted before the merge sweep) are **not** swept by `/a4:run`. Claude Code's startup sweep removes them automatically once they are older than `cleanupPeriodDays` and have no uncommitted changes / untracked files / unpushed commits. Worktrees preserved by the merge-sweep partial-progress rule (failing-task worktrees) are exempt because they hold uncommitted resolution work.

---

## Step 1: Pick Ready Tasks

**Pre-flight (parallel mode only; skipped in `serial` mode).** Before scanning the ready set:

```bash
local=$(git rev-parse HEAD)
origin=$(git rev-parse origin/HEAD)
test "$local" = "$origin" \
  || halt "push local commits to origin (or run 'git remote set-head origin -a' if origin's default branch changed) before running /a4:run"
```

Rationale and recovery in [`references/parallel-isolation.md`](${CLAUDE_PLUGIN_ROOT}/skills/run/references/parallel-isolation.md).

A task is **ready** when all of:

- `status ∈ {pending, failing}`
- every `depends_on` entry resolves to a task with `status: complete`
- one of:
  - `implements:` is non-empty AND every UC in `implements:` has `status ∈ {ready, implementing}` (so `revising` / `discarded` / `blocked` / `superseded` / `shipped` UCs' tasks are skipped), OR
  - `implements:` is empty (UC-less task — spec-justified feature, spike, or bug). Ready conditions vacuously pass; UC status checks do not apply.

Build the ready set by reading task + UC frontmatter.

Independent ready tasks run in parallel. Tasks with mutual dependencies run sequentially.

## Step 2: Spawn task-implementer

For each ready task, spawn one agent **with worktree isolation** (omit `isolation: "worktree"` only in `serial` mode):

```
Agent(subagent_type: "a4:task-implementer", isolation: "worktree", prompt: """
Task file: <absolute path to a4/task/<id>-<slug>.md>
Bootstrap file: <absolute path to a4/bootstrap.md>  # single source of truth for L&V
Architecture file: <absolute path to a4/architecture.md>
Relevant UC files: <paths referenced by the task's implements:; empty list when implements: is empty>

Read the task file for <description>, <files>, <unit-test-strategy>, <acceptance-criteria>.
Pull build + unit-test commands from bootstrap.md's <verify> section.

Implement the task and write its unit tests. All unit tests must pass.
Commit code + unit tests (one commit per task) using subject form
  #<task-id> <type>(a4): <description>
per ${CLAUDE_PLUGIN_ROOT}/references/commit-message-convention.md.
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

Parse each Agent return value's trailing 3 lines (`agentId:`, `worktreePath:`, `worktreeBranch:`) and record `{taskId → agentId, worktreePath, worktreeBranch}` in-memory for Step 2.5. After the agent returns, call the writer with `--to complete` or `--to failing` based on the return value (include a `--reason` naming the cycle and outcome). Do not hand-edit `status:` / `updated:` / `<log>` — the writer owns them.

The agent commits in its current working tree, which is transparently the worktree — the agent does not need to know it is isolated. Worktree return-value shape, branch naming, and cleanup commands live in [`references/parallel-isolation.md`](${CLAUDE_PLUGIN_ROOT}/skills/run/references/parallel-isolation.md).

## Step 2.5: Merge Sweep

**Skipped in `serial` mode** (serial agents commit directly to local main; nothing to integrate).

For each task that returned `pass`, in **ascending `task.id` order**, integrate its worktree branch into local main with a no-fast-forward merge:

```bash
git merge --no-ff -m "#<task-id> merge(a4): integrate <task-slug>" <worktreeBranch>
```

On success, clean up immediately:

```bash
git worktree unlock  <worktreePath>
git worktree remove --force <worktreePath>
git branch -D <worktreeBranch>
```

**On conflict — halt + partial-progress.** Per [`references/parallel-isolation.md`](${CLAUDE_PLUGIN_ROOT}/skills/run/references/parallel-isolation.md):

- Sibling tasks already merged in this sweep stay on main; they retain `status: complete`.
- The conflicting task's worktree and branch are **preserved** for user diagnosis. Transition the task to `failing` via the writer with `--reason "/a4:run merge conflict in <files>; resolve and re-run /a4:run iterate"`.
- Subsequent siblings in the sweep are **not attempted**; they remain at `progress` until `/a4:run iterate` retries the sweep.
- Do not emit a review item for the conflict — the halt message names the conflicting task and files directly.
- Skip Step 3 entirely; the cycle ends in halt.

Tasks that returned `fail` from Step 2 do not enter the sweep — their worktrees are preserved at the `failing` status from Step 2's writer call, and `/a4:run iterate` re-attempts after the user resolves.

## Step 3: Run Integration + Smoke Tests

**Invariant:** Step 3 runs only when every cycle ready task is integrated into local main (parallel mode: every Step 2.5 merge succeeded; serial mode: every task committed without halt). Any merge sweep failure → skip Step 3 and end the cycle in halt. The test-runner runs against a fully-integrated tree so its `target:` mapping (failure → task) stays honest.

Otherwise, spawn the test-runner:

```
Agent(subagent_type: "a4:test-runner", prompt: """
Bootstrap file: <absolute path to a4/bootstrap.md>  # single source of truth for L&V
a4/ path: <absolute path>
Cycle: <current integer>

Use bootstrap.md's <verify> section (verified commands, smoke scenario, test isolation
flags) for build / run / test commands. Run integration and smoke tests as defined
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
- **Per-task ship** — when `task.implements:` is empty (Minimal shape's bug / spike / spec-justified feature). Each task transitions to `complete` independently and 4b skips UC bookkeeping entirely. That is the normal case for those shapes, not an error.

A run can mix both unit types in one invocation (e.g., a UC-driven task and a spec-justified bug fix shipping in the same cycle); each task's `implements:` field decides which branch its ship verdict takes.

Leftover `implementing` UCs (user deferred on one or more) stay that way; the next `/a4:run iterate` session will re-offer them.

After 4b finishes (or 4a routes the run elsewhere), proceed to wrap-up.

---

## Acceptance Criteria Source by Task Kind

When a task-implementer reads a task's `<acceptance-criteria>` section, the source convention (set at authoring time by `/a4:roadmap` or `/a4:task`) is:

| Task kind / shape | AC source |
|---|---|
| `feature` + `implements: [usecase/...]` | UC `<flow>` / `<validation>` / `<error-handling>` |
| `feature` + `spec: [spec/...]` (UC-less) | spec `decision:` frontmatter + relevant `architecture.md` section |
| `spike` | hypothesis + expected result, the spike's own body |
| `bug` | reproduction scenario + fixed criteria |

`/a4:run` does not enforce this — validators do not block on AC source. The convention is documentation only; the AC section must exist on the task body regardless.

## Commit Points

All commit subjects follow [`references/commit-message-convention.md`](${CLAUDE_PLUGIN_ROOT}/references/commit-message-convention.md).

- **Per-task implementation** — `task-implementer` commits its own code + unit tests per task as `#<task-id> <type>(a4): <description>` (`feat` / `fix` per task kind). `/a4:run` does not also commit those files.
- **Per-task integration (Step 2.5, parallel mode only)** — `git merge --no-ff -m "#<task-id> merge(a4): integrate <task-slug>" <worktreeBranch>` per successfully-implemented task. Serial mode skips this step (task-implementer commits land directly on local main).
- **Per-cycle test results** — after Step 3, commit the emitted test-runner review items + updated task `<log>` entries as one commit:
  ```
  #<r1> #<r2> ... chore(a4): cycle <N> test-runner findings
  ```
  (Drop the id list when zero findings were emitted; commit the log updates alone as `chore(a4): cycle <N> test-runner clean`.)
- **Roadmap revision after test failure** — commit revised task files + status resets + review item linkages as one commit before re-running Step 1:
  ```
  #<task-ids> #<resolved-review-ids> docs(a4): revise tasks for cycle <N> findings
  ```
- **UC ship-transitions (Step 4b)** — commit the UC files confirmed `shipped` together in one commit, separate from task commits. Predecessor UC files auto-flipped to `superseded` by `transition_status.py` are part of the same working-tree change and belong in the same commit:
  ```
  #<uc-id1> [#<uc-id2> ...] docs(a4): ship UC <slug1> [<slug2> ...]
  ```
- **Final state** — commit any residual review items / log updates when the user wraps up:
  ```
  #<id> [#<id> ...] chore(a4): wrap up cycle <N>
  ```
  (ID-less when only ambient log lines changed.)

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

- **Authoring** — task files, roadmap.md, specs, UCs are written elsewhere. `/a4:run` only reads them.
- **"Best-effort auto-detect" of build / test commands without `bootstrap.md`.** When `bootstrap.md` is absent, `/a4:run` delegates to `/a4:compass` — the user is routed to the correct upstream skill rather than `/a4:run` guessing commands from `package.json` scripts or `AGENTS.md`. Auto-detection of commands is intentionally out of scope. Note: `roadmap.md`'s presence is irrelevant for L&V resolution — bootstrap is the single source of truth.
- **roadmap-reviewer scoped re-runs** — `/a4:run` Step 4a currently recommends `/a4:roadmap iterate` rather than spawning the reviewer inline. Inline scoped re-review is a possible future addition.
- **Per-cycle parallelism beyond independent ready tasks** — task-implementer parallelism is bounded by the dependency graph; no further parallelization is attempted.
- **Auto-fall-back to `serial` mode** — `/a4:run` does not detect worktree-isolation availability and does not silently degrade. Serial mode is opt-in via the `serial` arg; the parallel model with worktree isolation is the default.
- **Auto-resolution of merge conflicts** — Step 2.5 conflicts halt for the user. Trivial-conflict heuristics (`git rerere`, import-merge) and LLM-driven semantic resolution are deferred.

## Non-Goals

- Do not rebuild Phase 1. `/a4:roadmap` owns roadmap authoring; `/a4:task` owns single-task authoring. If `/a4:run` notices a missing task or roadmap gap, it emits a review item targeting `roadmap` and stops — it does not re-author.
- Do not split task-implementer / test-runner into sub-skills. The agent loop is intentionally one skill with cycle semantics and cascade rules.
- Do not split post-loop review (Step 4) into a separate skill, and do not delegate failure classification or UC ship to an agent. The seam is loop body (autonomous) ↔ post-loop review (user-driven); ship is forward-path terminal and stays user-authorized. Verdict / classification details live in `references/failure-classification.md` and `references/uc-ship-review.md` to keep this SKILL.md tight.
- Do not emit aggregated test reports. All findings are per-review-item files.
- Do not flip UC status without going through `transition_status.py`. The script enforces the cascade and log invariants.
