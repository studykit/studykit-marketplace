---
name: roadmap
description: "This skill should be used when the user needs to author the implementation roadmap and per-task files from an architecture. Common triggers include: 'roadmap', 'plan the implementation', 'build the task set from arch', 'lay out milestones'. Writes a4/roadmap.md (wiki page) plus per-task files at a4/task/<id>-<slug>.md. The agent-driven implement + test loop is in /a4:run; single ad-hoc tasks come through /a4:task, /a4:bug, /a4:spike, /a4:research."
argument-hint: <optional: "iterate" to resume; auto-detects workspace state otherwise>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Implementation Roadmap Builder

> **Authoring contracts:** `a4/roadmap.md` — `${CLAUDE_PLUGIN_ROOT}/authoring/roadmap-authoring.md`. Per-task files (always `type: task` for the batch path): `${CLAUDE_PLUGIN_ROOT}/authoring/task-authoring.md`. This skill orchestrates the batch.

Takes the architecture in `a4/architecture.md` (plus the UCs in `a4/usecase/`, the domain model in `a4/domain.md`, and the actor roster in `a4/actors.md`) and authors the implementation roadmap plus per-task files. The agent-driven implement + test loop lives in `/a4:run`.

## Workspace Layout

Resolve `a4/` via `git rev-parse --show-toplevel`.

**Inputs:**

- `a4/architecture.md` — the authoritative architecture wiki page.
- `a4/usecase/*.md` — Use Cases (task `implements:` references point here).
- `a4/domain.md`, `a4/actors.md`, `a4/nfr.md`, `a4/context.md` — supporting wiki pages.
- `a4/bootstrap.md` — bootstrap report (if auto-bootstrap has run). Verified build/launch/test commands live here.

**Outputs:**

- `a4/roadmap.md` — single wiki page covering Overview, Implementation Strategy, Milestones, Dependency Graph snapshot, Launch & Verify pointer, Shared Integration Points (all H3+ headings inside `## Plan`). Launch & Verify is a one-line pointer to `bootstrap.md`, not authored content.
- `a4/task/<id>-<slug>.md` — one per executable unit of work. The roadmap generator always emits `type: task`; spike / bug / research tasks come through their dedicated authoring skills.
- `a4/review/<id>-<slug>.md` — findings from roadmap-reviewer.

Derived views (dependency graph, open-task dashboard, milestone progress) are produced on demand by `/a4:compass` or by grep over frontmatter — no separate files.

## Id Allocation

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"
```

## Modes

- **Roadmap mode** — `a4/roadmap.md` absent OR all four issue family folders (`a4/task/`, `a4/bug/`, `a4/spike/`, `a4/research/`) are empty. Run Steps 1 → 4.
- **Iterate mode** — open review items target `roadmap` or a task. Apply `references/iteration-entry.md` on top of `${CLAUDE_PLUGIN_ROOT}/dev/iterate-mechanics.md`.

Mode detection at session start:

```bash
ls a4/task/*.md a4/bug/*.md a4/spike/*.md a4/research/*.md 2>/dev/null   # any tasks?
ls a4/review/*.md | xargs grep -l 'status: open\|target: roadmap\|target: task/\|target: bug/\|target: spike/\|target: research/'
```

If `a4/task/` already has the full set and the user's intent is to run the implement loop, redirect them to `/a4:run`.

## Workflow

### Step 1: Read sources

Read `a4/architecture.md`, every UC in `a4/usecase/*.md`, supporting wiki pages, and `a4/bootstrap.md` (**required** — single source of truth for Launch & Verify; do not duplicate verified commands into roadmap.md). If `bootstrap.md` is absent, suggest `/a4:auto-bootstrap` first. Continue only if the user opts to proceed without it.

### Step 2: Explore the codebase

Check project structure, conventions, test setup, build configuration. File paths in task frontmatter must be specific to this codebase (`src/render.ts`, not "a renderer file").

### Step 3: Generate roadmap + tasks

Procedure: `references/generate.md`. Covers implementation strategy selection, milestones, per-task derivation, shared integration points, and file writing.

### Step 4: Roadmap verification

Procedure: `references/verification.md`. Spawn `roadmap-reviewer`, walk findings under the stop-on-strong-upstream policy, loop up to 3 review rounds.

## Hand-off to /a4:run

After Step 4 closes:

> Roadmap ready. Run `/a4:run` to start the implement + test loop. Single ad-hoc tasks can be added at any time via `/a4:task`, `/a4:bug`, `/a4:spike`, or `/a4:research`.

`/a4:run` reads `a4/bootstrap.md` directly. Make sure `bootstrap.md` exists and its `## Verify` content is correct before handing off — re-run `/a4:auto-bootstrap` if architecture changed.

## Commit Points

Per-step subject formats and timing: `references/commit-points.md`.

## Wrap Up

When the user ends the roadmap-authoring session:

1. Summarize: tasks authored / revised, review items opened / resolved / still open, whether `/a4:run` is the next step or `/a4:arch` / `/a4:usecase iterate` (if upstream issues).
2. Suggest `/a4:handoff` to snapshot the session.

## Agent Usage

- **`roadmap-reviewer`** — `Agent(subagent_type: "a4:roadmap-reviewer")`. Reviews the roadmap + tasks against architecture / UCs; emits per-finding review items.

`task-implementer` and `test-runner` are `/a4:run`'s agents — not invoked from this skill.

## Non-Goals

- Do not split the roadmap into per-milestone files. `roadmap.md` holds all milestone narrative in one file.
- Do not add a `phase:` or `milestone:` frontmatter field to tasks (a4 v6.0.0 retired `milestone:` from issue frontmatter). Milestone grouping lives in `roadmap.md`'s `## Plan` narrative.
- Do not maintain a separate `roadmap.history.md`.
- Do not emit aggregated roadmap-review reports. All findings are per-review-item files.
- Do not track per-source SHAs on `roadmap.md`.
- Do not run the implement loop here. That is `/a4:run`'s exclusive role.
- Do not author Launch & Verify content in `roadmap.md`. `bootstrap.md` is the single source of truth.
