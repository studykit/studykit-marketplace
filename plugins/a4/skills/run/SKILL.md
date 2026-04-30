---
name: run
description: "This skill should be used when the user wants to drive the agent-based implement + test loop over the tasks already authored in a4/{task,bug,spike,research}/. Common triggers include: 'run', 'implement the tasks', 'run the implementation loop', 'kick off the agents', 'task-implementer', 'agent loop'. Two stages: an autonomous loop body (pick → implement → test, up to 3 cycles), then a user-driven post-loop review that classifies failures or confirms UC ship. Works with or without UCs — UC ship-review is conditional on per-task implements: being non-empty."
argument-hint: <optional: 'iterate' to resume after a halt, 'serial' to opt out of parallel worktree isolation; auto-detects workspace state otherwise>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, TaskCreate, TaskUpdate, TaskList
---

# Implementation Run Loop

> **Authoring contracts:** task files this loop reads — `${CLAUDE_PLUGIN_ROOT}/authoring/task-authoring.md`, `${CLAUDE_PLUGIN_ROOT}/authoring/bug-authoring.md`, `${CLAUDE_PLUGIN_ROOT}/authoring/spike-authoring.md`. UC ship gates against `${CLAUDE_PLUGIN_ROOT}/authoring/usecase-authoring.md`. Test-runner findings emit reviews per `${CLAUDE_PLUGIN_ROOT}/authoring/review-authoring.md`. This skill writes status flips by editing `status:` directly; the PostToolUse cascade hook handles `updated:` and any cross-file cascade. The `task-implementer` and `test-runner` agents do their own writes (code + tests, review items).

Two stages over the tasks already authored under the four issue family folders (`a4/task/`, `a4/bug/`, `a4/spike/`, `a4/research/`):

1. **Loop body (Steps 1–3, autonomous)** — pick ready tasks, spawn `task-implementer` agents in isolated worktrees (parallel where independent), merge each successful worktree branch back to local main, run the `test-runner`. Bounded to 3 cycles per invocation.
2. **Post-loop review (Step 4, user-driven)** — failure path: user classifies each failing test-runner finding into task / arch / UC. Ship path: user confirms which UCs go `implementing → shipped`.

Reads `a4/bootstrap.md` for build / launch / test / smoke / isolation commands — bootstrap is the single source of truth for Launch & Verify (per `${CLAUDE_PLUGIN_ROOT}/workflows/wiki-authorship.md`; `roadmap.md` only links to it).

Authoring is out of scope: `/a4:roadmap` writes the roadmap + UC-batch tasks; `/a4:task`, `/a4:bug`, `/a4:spike`, `/a4:research` write single ad-hoc tasks. This skill assumes both have already produced the task files it consumes.

## Workspace Layout

Resolve `a4/` via `git rev-parse --show-toplevel`.

**Inputs:**

- `a4/<type>/<id>-<slug>.md` (under `task/`, `bug/`, `spike/`, or `research/`) — required. The set of executable units this run consumes.
- `a4/bootstrap.md` — required. Single source of truth for Launch & Verify.
- `a4/roadmap.md` — optional. Provides milestone narrative + dependency-graph snapshot.
- `a4/architecture.md` — passed to agents for contract context.
- `a4/usecase/*.md` — read for UC ship-review candidates (Step 4b). Absent in UC-less projects; that's fine.
- `a4/review/*.md` — open review items influence ready-set selection and resume behavior.

**Outputs:**

- `a4/review/<id>-<slug>.md` — test-runner findings; gap items emitted during ship-review when the user defers.
- Per-task `status:` flips via direct frontmatter edit on every status change; `updated:` is refreshed automatically by the PostToolUse cascade hook.
- Per-task implementation commits authored by `task-implementer` agents.

## Launch & Verify Source

Resolution policy: `references/launch-verify-source.md`. When `bootstrap.md` is absent, halt and delegate to `/a4:compass`.

## Mode Detection

- **Implement mode** — any of `a4/task/`, `a4/bug/`, `a4/spike/`, `a4/research/` has `pending` or `failing` tasks, or no test-runner review items yet reference the current cycle. Run Steps 1–4 in order. (`open` tasks are backlog and intentionally **not** picked up here.)
- **Iterate mode** — open review items target a task or `roadmap`. Apply `references/iteration-entry.md` on top of `${CLAUDE_PLUGIN_ROOT}/workflows/iterate-mechanics.md`.
- **Pre-flight** (both modes, run at Step 1 entry) — local `HEAD` must equal `origin/HEAD` per `references/parallel-isolation.md`. Halt with a push instruction on mismatch.
- **Serial fallback** (`/a4:run serial` or `/a4:run iterate serial`) — opt-in mode that skips worktree isolation and the merge sweep entirely. Rules in `references/parallel-isolation.md`.

Mode detection at session start:

```bash
ls a4/task/*.md a4/bug/*.md a4/spike/*.md a4/research/*.md 2>/dev/null   # any tasks?
grep -lhr '^status: pending' a4/task a4/bug a4/spike a4/research 2>/dev/null
grep -lhr '^status: failing' a4/task a4/bug a4/spike a4/research 2>/dev/null
ls a4/review/*.md | xargs grep -l 'status: open\|target: roadmap\|target: task/\|target: bug/\|target: spike/\|target: research/'
```

If no tasks exist at all: halt and tell the user to run `/a4:roadmap` (UC-driven batch) or one of `/a4:task`, `/a4:bug`, `/a4:spike`, `/a4:research` (single ad-hoc) first.

## Resume Hygiene

Crash recovery + orphaned worktree handling: `references/resume-hygiene.md`.

## Workflow

| Step | Focus | Procedure |
|------|-------|-----------|
| 1 | Pick ready tasks (+ pre-flight) | `references/ready-set.md` |
| 2 | Spawn task-implementer (worktree isolation) | `references/spawn-implementer.md` |
| 2.5 | Merge sweep (parallel mode) | `references/merge-sweep.md` |
| 3 | Integration + smoke tests via test-runner | `references/integration-tests.md` |
| 4 | Post-loop review (failure path / ship path) | `references/post-loop-review.md` |

## Acceptance Criteria Source by Issue Family

The per-type AC-source convention is defined in the matching authoring rule: tasks draw AC from UC `## Flow` / `## Validation` / `## Error Handling` (or spec `## Specification` body + `architecture.md` for UC-less work) per `${CLAUDE_PLUGIN_ROOT}/authoring/task-authoring.md`; bug tasks draw AC from a reproduction scenario + the regression test pinning the expected behavior per `${CLAUDE_PLUGIN_ROOT}/authoring/bug-authoring.md`; spike tasks draw AC from the hypothesis + expected result in the spike's own body per `${CLAUDE_PLUGIN_ROOT}/authoring/spike-authoring.md`. `/a4:run` does not enforce these — automated checks do not block on AC source; only the `## Acceptance Criteria` section's presence is required by the authoring contract.

## Commit Points

Per-step subject formats and timing: `references/commit-points.md`.

## Wrap Up

When all tasks are `complete` and all tests pass (or when the user ends the session):

1. Summarize: tasks completed / revised / still failing, review items opened / resolved / still open, cycles consumed, UCs shipped this run (empty list is fine for UC-less runs).
2. If any tasks remain `pending` / `failing` or any review items are `open`, suggest `/a4:run iterate` as the resumption path.
3. Suggest `/a4:handoff` to snapshot the session.

## Agent Usage

Context is passed via file paths, not agent memory.

- **`task-implementer`** — `Agent(subagent_type: "a4:task-implementer")`. Implements one task + its unit tests; commits code + tests. Never reads other tasks' files.
- **`test-runner`** — `Agent(subagent_type: "a4:test-runner")`. Runs integration + smoke tests; emits per-failure review items. Does not classify failures.

`roadmap-reviewer` is **not** invoked from `/a4:run` directly.

## Out of Scope

- **Authoring** — task files, roadmap.md, specs, UCs are written elsewhere. `/a4:run` only reads them.
- **"Best-effort auto-detect" of build / test commands without `bootstrap.md`.** Auto-detection of commands is intentionally out of scope.
- **roadmap-reviewer scoped re-runs** — `/a4:run` Step 4a currently recommends `/a4:roadmap iterate` rather than spawning the reviewer inline.
- **Per-cycle parallelism beyond independent ready tasks** — task-implementer parallelism is bounded by the dependency graph.
- **Auto-fall-back to `serial` mode** — opt-in via the `serial` arg only.
- **Auto-resolution of merge conflicts** — Step 2.5 conflicts halt for the user.

## Non-Goals

- Do not rebuild Phase 1. `/a4:roadmap` owns roadmap authoring; `/a4:task`, `/a4:bug`, `/a4:spike`, `/a4:research` own single-task authoring.
- Do not split task-implementer / test-runner into sub-skills.
- Do not split post-loop review (Step 4) into a separate skill, and do not delegate failure classification or UC ship to an agent.
- Do not emit aggregated test reports. All findings are per-review-item files.
- Do not hand-edit `updated:` — only edit `status:` and let the PostToolUse cascade hook refresh `updated:`.
