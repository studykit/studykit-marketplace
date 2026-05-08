---
name: auto-coding
description: "Run the a4 implementation and test loop."
argument-hint: "[iterate] [parallel]  # iterate = resume after halt; parallel = worktree-isolated parallel coders; no-arg = fresh serial run"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, TaskCreate, TaskUpdate, TaskList
---

# Auto-Coding Implementation Loop

Two stages over the tasks already authored under the four issue family folders (`a4/task/`, `a4/bug/`, `a4/spike/`, `a4/research/`):

1. **Loop body (Steps 1–3, autonomous)** — pick ready tasks, spawn `coder` agents (one `Agent` call per task; default serial mode runs them sequentially in the user's working tree, opt-in parallel mode wraps each in `isolation: "worktree"` and merges back), then run the `test-runner`. Bounded to 3 cycles per invocation.
2. **Post-loop review (Step 4, user-driven)** — failure path: user classifies each failing test-runner finding into task / arch / UC. Ship path: user confirms which UCs go `implementing → shipped`.

Reads `a4/ci.md` for test / smoke / isolation commands — ci.md is the single source of truth for test execution. See `${CLAUDE_PLUGIN_ROOT}/authoring/ci-authoring.md` for the page contract.

Authoring is out of scope. This skill assumes executable task files already exist and only consumes them.

## Workspace Layout

Resolve `a4/` via `git rev-parse --show-toplevel`.

**Inputs:**

- `a4/<type>/<id>-<slug>.md` (under `task/`, `bug/`, `spike/`, or `research/`) — required. The set of executable units this run consumes.
- `a4/ci.md` — required. Single source of truth for test-execution commands.
- Task-referenced docs — files linked via `implements:`, `spec:`, `related:`, `## References`, and `## Interface Contracts`; the coder resolves and reads them per task.
- `a4/usecase/*.md` — read for UC ship-review candidates (Step 4b). Absent in UC-less projects; that's fine.
- `a4/review/*.md` — open review items influence ready-set selection and resume behavior.

**Outputs:**

- `a4/review/<id>-<slug>.md` — test-runner findings; gap items emitted during ship-review when the user defers.
- Per-task `status:` flips via direct frontmatter edit on every status change.
- Per-task implementation commits authored by `coder` agents.

## Launch & Verify Source

Resolution policy: `references/launch-verify-source.md`. When `ci.md` is absent, halt and tell the user to run `/a4:ci-setup` first.

## Mode Selection

Two orthogonal axes pick the reference set. **Resolve isolation mode first from the invocation argument** — every Step's reference list below depends on it.

### Axis 1 — Isolation mode (argument-driven; resolve first)

| Argument | Mode | Read |
|---|---|---|
| (none) / `iterate` | **Serial** (default) — no worktree, sequential coders, no merge sweep, no pre-flight. Works in any repo, including those without an `origin` remote | `references/serial-mode.md` |
| `parallel` / `iterate parallel` | **Parallel** (opt-in) — worktree-isolated coders, parallel where independent, merge sweep at Step 2.5, pre-flight required (`HEAD == origin/HEAD`). Halts immediately if the repo has no `origin` remote — drop the `parallel` arg to fall back to serial | `references/parallel-mode.md` |

No auto-fall-back on pre-flight failure (halt instead). No in-cycle mode switch.

### Axis 2 — Run vs resume (workspace-state-driven)

- **Implement mode** — any of `a4/task/`, `a4/bug/`, `a4/spike/`, `a4/research/` has `queued` or `failing` tasks, or no test-runner review items yet reference the current cycle. Run Steps 1–4 in order. (`open` tasks are backlog and intentionally **not** picked up here; `holding` tasks are paused under explicit human stewardship and require a manual `holding → progress` flip before they re-enter the loop.)
- **Iterate mode** — open review items target a task. Apply `references/iteration-entry.md`.

Workspace-state probe at session start:

```bash
ls a4/task/*.md a4/bug/*.md a4/spike/*.md a4/research/*.md 2>/dev/null   # any tasks?
grep -lhr '^status: queued' a4/task a4/bug a4/spike a4/research 2>/dev/null
grep -lhr '^status: failing' a4/task a4/bug a4/spike a4/research 2>/dev/null
ls a4/review/*.md | xargs grep -l 'status: open\|target: task/\|target: bug/\|target: spike/\|target: research/'
```

If no tasks exist at all: halt and tell the user to create task files first, then rerun this skill.

## Resume Hygiene

Crash recovery + orphaned worktree handling: `references/resume-hygiene.md`.

## Workflow

References are mode-specific. After resolving Axis 1 above, follow only the column for the active mode.

| Step | Focus | Serial mode (default) | Parallel mode (`parallel` arg) |
|------|-------|-----------------------|--------------------------------|
| 1 | Pick ready tasks | `references/ready-set.md` (pre-flight skipped) + `references/serial-mode.md` | `references/ready-set.md` (pre-flight applies) + `references/parallel-mode.md` |
| 2 | Spawn coder | `references/spawn-coder.md` (drop `isolation: "worktree"`) + `references/serial-mode.md` | `references/spawn-coder.md` + `references/parallel-mode.md` |
| 2.5 | Merge sweep | skipped — see `references/serial-mode.md` | `references/merge-sweep.md` |
| 3 | Integration + smoke tests via test-runner | `references/integration-tests.md` | `references/integration-tests.md` |
| 4 | Post-loop review (failure path / ship path) | `references/post-loop-review.md` | `references/post-loop-review.md` |

## Acceptance Criteria Source by Issue Family

The per-type AC-source convention is defined in the matching authoring rule: tasks draw AC from UC `## Flow` / `## Validation` / `## Error Handling` (or spec `## Specification` body + `architecture.md` for UC-less work) per `${CLAUDE_PLUGIN_ROOT}/authoring/task-authoring.md`; bug tasks draw AC from a reproduction scenario + the regression test pinning the expected behavior per `${CLAUDE_PLUGIN_ROOT}/authoring/bug-authoring.md`; spike tasks draw AC from the hypothesis + expected result in the spike's own body per `${CLAUDE_PLUGIN_ROOT}/authoring/spike-authoring.md`. `/a4:auto-coding` does not enforce these — automated checks do not block on AC source; only the `## Acceptance Criteria` section's presence is required by the authoring contract.

## Commit Points

Per-step subject formats and timing: `references/commit-points.md`.

## Wrap Up

When all tasks are `done` and all tests pass (or when the user ends the session):

1. Summarize: tasks done / revised / still failing, review items opened / resolved / still open, cycles consumed, UCs shipped this run (empty list is fine for UC-less runs).
2. If any tasks remain `queued` / `failing` or any review items are `open`, suggest `/a4:auto-coding iterate` as the resumption path. (`holding` tasks are intentionally paused — surface their count separately so the user knows to resume them manually.)
3. Suggest `/a4:handoff` to snapshot the session.

## Agent Usage

Context is passed via file paths, not agent memory.

- **`coder`** — `Agent(subagent_type: "a4:coder")`. Implements one task + its unit tests; commits code + tests. Reads only the assigned task plus files that task references.
- **`test-runner`** — `Agent(subagent_type: "a4:test-runner")`. Runs integration + smoke tests; emits per-failure review items. Does not classify failures.

## Out of Scope

- **Authoring** — task files, specs, and UCs are written elsewhere. This skill only reads them.
- **"Best-effort auto-detect" of test commands without `ci.md`.** Auto-detection of commands is intentionally out of scope.
- **Per-cycle parallelism beyond independent ready tasks** — coder parallelism is bounded by the dependency graph.
- **Auto-resolution of merge conflicts** — Step 2.5 conflicts halt for the user.

## Non-Goals

- Do not derive or author task files. Consume existing executable tasks only.
- Do not split coder / test-runner into sub-skills.
- Do not split post-loop review (Step 4) into a separate skill, and do not delegate failure classification or UC ship to an agent.
- Do not emit aggregated test reports. All findings are per-review-item files.
