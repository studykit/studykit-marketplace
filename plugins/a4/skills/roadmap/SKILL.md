---
name: roadmap
description: "This skill should be used when the user needs to author the implementation roadmap and per-task files from an architecture. Common triggers include: 'roadmap', 'plan the implementation', 'build the task set from arch', 'lay out milestones'. Writes a4/roadmap.md (wiki page) plus per-task files at a4/task/feature/<id>-<slug>.md. The agent-driven implement + test loop is in /a4:run; single ad-hoc tasks (spike, bug, spec-justified) are in /a4:task."
argument-hint: <optional: "iterate" to resume; auto-detects workspace state otherwise>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Implementation Roadmap Builder

> **Authoring contracts:** the contract for `a4/roadmap.md` — frontmatter, `<plan>` body shape, common mistakes, "Don't" list — lives in [`references/roadmap-authoring.md`](${CLAUDE_PLUGIN_ROOT}/references/roadmap-authoring.md). The contract for the per-task files this skill generates (always `kind: feature`) lives in [`references/task-feature-authoring.md`](${CLAUDE_PLUGIN_ROOT}/references/task-feature-authoring.md). This skill orchestrates the batch.

Takes the architecture in `a4/architecture.md` (plus the UCs in `a4/usecase/`, the domain model in `a4/domain.md`, and the actor roster in `a4/actors.md`) and authors the implementation roadmap plus per-task files. The agent-driven implement + test loop lives in `/a4:run`.

## Workspace Layout

Resolve `a4/` via `git rev-parse --show-toplevel`. Inputs:

- `a4/architecture.md` — the authoritative architecture wiki page.
- `a4/usecase/*.md` — Use Cases (task `implements:` references point here).
- `a4/domain.md`, `a4/actors.md`, `a4/nfr.md`, `a4/context.md` — supporting wiki pages.
- `a4/bootstrap.md` — bootstrap report (if auto-bootstrap has run). Verified build/launch/test commands live here.

Outputs:

- `a4/roadmap.md` — single wiki page covering Overview, Implementation Strategy, Milestones, Dependency Graph snapshot, Launch & Verify pointer, Shared Integration Points (all as H3+ headings inside the `<plan>` section). Launch & Verify is a one-line pointer to `bootstrap.md`, not authored content.
- `a4/task/feature/<id>-<slug>.md` — one per executable unit of work (Jira-task semantics). The roadmap generator always emits `kind: feature` and writes under the `feature/` subfolder; spike / bug tasks come through `/a4:task` instead.
- `a4/review/<id>-<slug>.md` — findings from roadmap-reviewer.

Derived views (dependency graph, open-task dashboard, milestone progress) are produced on demand by `/a4:compass` or by grep over frontmatter; no separate files.

## Schemas

`a4/roadmap.md` frontmatter / body shape: see [`rules/a4-roadmap-authoring.md`](${CLAUDE_PLUGIN_ROOT}/rules/a4-roadmap-authoring.md).

Per-task files (`a4/task/feature/<id>-<slug>.md`) — frontmatter, body sections, status enum + cascades, AC source, `cycle:` semantics: see [`rules/a4-task-feature-authoring.md`](${CLAUDE_PLUGIN_ROOT}/rules/a4-task-feature-authoring.md). The batch generator emits `kind: feature` and `status: pending` for every UC-derived task; single ad-hoc spike / bug entries flow through `/a4:task` (which writes under `a4/task/spike/` or `a4/task/bug/`).

## Id Allocation

Always allocate via the shared utility before creating a task or review item:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"
```

## Modes

Determined by the workspace state, not by frontmatter flags:

- **Roadmap mode** — `a4/roadmap.md` absent OR `a4/task/` (any kind subfolder) is empty. Run Step 1 onward.
- **Iterate mode** — open review items target `roadmap` or a task. See **Iteration Entry** below.

Mode detection at session start:

```bash
ls a4/task/*/*.md                                           # any tasks? (recursive: feature/, bug/, spike/)
ls a4/review/*.md | xargs grep -l 'status: open\|target: roadmap\|target: task/'
```

If `a4/task/feature/` already has the full set and the user's intent is to run the implement loop, redirect them to `/a4:run`.

### Iteration Entry

Mechanics (filter, backlog presentation, writer calls, footnote rules, discipline) follow [`references/iterate-mechanics.md`](${CLAUDE_PLUGIN_ROOT}/references/iterate-mechanics.md). This section adds only the roadmap-specific work.

**Backlog filter:** `target: roadmap` OR `target: task/*` OR same in `wiki_impact`.

**Roadmap-specific work** between writer calls:
- **Re-emit revised roadmap / task files** in place of hand-edits when the resolution restructures milestones, dependency graph, or task split.
- **Scoped roadmap-reviewer rerun** — after revising tasks for a finding, run `roadmap-reviewer` once over the revised subset (not the full roadmap) and only proceed if the scoped review passes. This is the inline review loop unique to roadmap.
- **Cascade awareness** — if a task's `depends_on` changes, downstream tasks may also need adjustments; surface those to the user before resolving.

---

## Step 1: Read Sources

Read these files up front:

- `a4/architecture.md` — technology stack, components, information flows, interface contracts, test strategy.
- `a4/usecase/*.md` — every UC (ids, actors, flows, acceptance criteria). Use `grep -l` to enumerate.
- `a4/domain.md`, `a4/actors.md`, `a4/nfr.md`, `a4/context.md` — supporting wiki pages.
- `a4/bootstrap.md` — **required**. Single source of truth for Launch & Verify (build / launch / test / smoke / isolation). The roadmap embeds this content rather than copying it; do not duplicate the verified commands into roadmap.md.

If `bootstrap.md` is absent, suggest `/a4:auto-bootstrap` first. Continue only if the user opts to proceed without it.

## Step 2: Explore the Codebase

Check project structure, conventions, test setup, build configuration. File paths in task frontmatter must be specific to this codebase (`src/render.ts`, not "a renderer file").

## Step 3: Generate Roadmap + Tasks

Enter plan mode (the `EnterPlanMode` Claude Code primitive). Design:

1. **Implementation strategy** (component-first / feature-first / hybrid) — read `${CLAUDE_SKILL_DIR}/references/planning-guide.md` for guidance.
2. **Milestones** — group tasks into named deliverable sets (`v1.0`, `beta`, `phase-1`). Milestones drive roadmap narrative sequencing.
3. **Tasks** (one per executable unit):
   - Derive from architecture components + UC flows.
   - Size: covers 1–5 related UCs, touches 1–3 components, independently testable, ≤ ~500 lines.
   - File mapping (source files + unit test files following the bootstrap/codebase convention).
   - Dependencies (`depends_on:` using plain `task/<id>-<slug>` strings).
   - Unit test scenarios + isolation strategy.
   - Acceptance criteria derived from UC flows, validation, error handling (per the AC source table above).
   - Milestone assignment (`milestone:` field).
   - `kind: feature` (the batch generator emits feature for UC-derived work).
4. **Shared Integration Points** — identify any file appearing in 3+ tasks' file lists. Define the integration pattern.
5. **Launch & Verify** — *do not author content here*. `bootstrap.md` is the single source of truth (per [`references/wiki-authorship.md`](${CLAUDE_PLUGIN_ROOT}/references/wiki-authorship.md)); roadmap.md links to it. `/a4:run` reads `bootstrap.md` directly.

Exit plan mode. Write artifacts.

**`a4/roadmap.md` body** — write `<plan>` with H3 subsections (Overview, Implementation Strategy, Milestones, Dependency Graph snapshot, Launch & Verify pointer, Shared Integration Points) per [`rules/a4-roadmap-authoring.md`](${CLAUDE_PLUGIN_ROOT}/rules/a4-roadmap-authoring.md) §Body shape. Launch & Verify is a one-line link to `[bootstrap](bootstrap.md)` — never inline content. Shared Integration Points is emitted only when a file appears in 3+ tasks. Append a `<change-logs>` bullet citing the driving wiki/issue.

**Per-task files** — allocate ids via `allocate_id.py`, write `a4/task/feature/<id>-<slug>.md` per [`rules/a4-task-feature-authoring.md`](${CLAUDE_PLUGIN_ROOT}/rules/a4-task-feature-authoring.md) (`kind: feature`, `status: pending`). The roadmap's Milestones subsection references them via standard markdown links pointing into `feature/<id>-<slug>.md`.

After all task files are written, refresh the reverse link on each UC so `ready → implementing` will pass mechanical validation:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/refresh_implemented_by.py" \
  "$(git rev-parse --show-toplevel)/a4"
```

This back-scans every task's `implements:` list and writes `implemented_by: [...]` onto each referenced UC. The script is idempotent; run it again after any task file is created, renamed, or has its `implements:` list edited.

Commit roadmap generation together when the user confirms (see Commit Points).

## Step 4: Roadmap Verification

Spawn `Agent(subagent_type: "a4:roadmap-reviewer")`. Pass:
- `a4/` absolute path
- Prior open roadmap-targeted review item ids (to deduplicate)

The reviewer emits per-finding review items to `a4/review/<id>-<slug>.md` and returns a summary.

Walk each new review item per the **stop on strong upstream dependency** policy at [`references/wiki-authorship.md`](${CLAUDE_PLUGIN_ROOT}/references/wiki-authorship.md) §Cross-stage feedback — roadmap depends directly on architecture (component → task split) and UCs (UC → AC source), so upstream findings halt this skill rather than continuing with stale assumptions.

- **Roadmap-level fix** — edit `roadmap.md` or the affected task file; flip the review item via `transition_status.py --to resolved` (which appends the `<log>` entry); add a `<change-logs>` bullet on `roadmap.md` if it changed.
- **Arch / usecase finding** — **stop**. Leave the review item `status: open` with its existing `target:` pointing at `architecture` or `usecase/...`. Tell the user to run `/a4:arch` or `/a4:usecase iterate` and resume `/a4:roadmap iterate` afterwards.
- **Defer** — leave `status: open`. Capture the deferral reason in conversation notes / handoff.

Loop up to 3 review rounds if roadmap-level revisions are substantial. Once the reviewer returns `ACTIONABLE` (or the user explicitly approves moving on with deferred findings), the roadmap is ready. Suggest `/a4:run` to drive the implement loop.

---

## Hand-off to /a4:run

After Step 4 closes, this skill's job is done. The implement + test loop, status transitions, failure classification, and UC ship-review live in `/a4:run`. Tell the user:

> Roadmap ready. Run `/a4:run` to start the implement + test loop. Single ad-hoc tasks (spike / bug / spec-justified feature) can be added at any time via `/a4:task`.

`/a4:run` reads `a4/bootstrap.md` (single source of truth for Launch & Verify). Make sure `bootstrap.md` exists and its `<verify>` content (verified commands, smoke scenario, test isolation flags) is correct before handing off — re-run `/a4:auto-bootstrap` if architecture changed.

## Commit Points

All commit subjects follow [`commit-message-convention.md`](${CLAUDE_PLUGIN_ROOT}/references/commit-message-convention.md).

- **Roadmap generation** — commit `a4/roadmap.md` + all new `a4/task/feature/*.md` files + UCs updated by `refresh_implemented_by.py` together once the user confirms. Subject:
  ```
  #<uc-ids> #<task-ids> docs(a4): roadmap for <milestone-or-scope>
  ```
  (List the UC ids first, then task ids; the description names the milestone or feature scope, not the file count.)
- **Roadmap revision during verification** — commit revised roadmap / task files + resolved review items as one commit per review round. Subject:
  ```
  #<task-ids> #<resolved-review-ids> docs(a4): revise roadmap for review round <N>
  ```

Implement-loop commit points (per-task implementation, per-cycle test results, merge-sweep integration, UC ship-transitions) are owned by `/a4:run`.

Never skip hooks, amend, or force-push without explicit user instruction.

## Wrap Up

When the user ends the roadmap-authoring session:

1. Summarize:
   - Tasks authored / revised.
   - Review items opened / resolved / still open.
   - Whether `/a4:run` is the next step (most cases) or `/a4:arch` / `/a4:usecase iterate` (when the reviewer surfaced upstream issues).
2. Suggest `/a4:handoff` to snapshot the session.

## Agent Usage

Context is passed via file paths, not agent memory.

- **`roadmap-reviewer`** — `Agent(subagent_type: "a4:roadmap-reviewer")`. Reviews the roadmap + tasks against architecture / UCs; emits per-finding review items.

`task-implementer` and `test-runner` are `/a4:run`'s agents — not invoked from this skill.

## Non-Goals

- Do not split the roadmap into per-milestone files. `roadmap.md` holds all milestone narrative in one file per the spec.
- Do not add a `phase:` frontmatter field to tasks. `milestone:` covers phase semantics.
- Do not maintain a separate `roadmap.history.md`. Each task's `<log>` section records per-task history; the workspace's git history covers the rest.
- Do not emit aggregated roadmap-review reports. All findings are per-review-item files.
- Do not track per-source SHAs on `roadmap.md`. The wiki update protocol's `<change-logs>` + drift-detector flow handles cross-reference consistency.
- Do not run the implement loop here. That is `/a4:run`'s exclusive role; merging the two back together is explicitly out of scope per the plan-restructure spec.
- Do not author Launch & Verify content in `roadmap.md`. `bootstrap.md` is the single source of truth; the roadmap links to it. If the verified commands need updating, re-run `/a4:auto-bootstrap`.
