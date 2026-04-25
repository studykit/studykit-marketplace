---
name: task
description: "This skill should be used when the user wants to author a single ad-hoc task outside the UC-batch path that /a4:roadmap takes. Common triggers include: 'add a task', 'create a task', 'spike on X', 'log a bug', 'I need a task for', 'one-off task'. Required argument: kind (feature | spike | bug). Optional: implements: (UC paths) and/or justified_by: (ADR paths). Writes a4/task/<id>-<slug>.md; for kind: spike also proposes a project-root spike/<id>-<slug>/ sidecar. Single-task entry. Use /a4:roadmap for batch UC-driven generation; use /a4:run to drive the implement loop."
argument-hint: "kind=<feature|spike|bug> [title or short description]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, TaskCreate, TaskUpdate, TaskList
---

# Single Task Author

Writes one `a4/task/<id>-<slug>.md` outside the UC-batch path. Co-exists with `/a4:roadmap` (which writes the full UC-driven task set in one go). Use this skill when:

- A spike is needed to unblock an architecture or decision question.
- A bug needs a tracked fix.
- An ADR-justified feature needs implementation in a UC-less or partially-UC project.
- A new feature task lands after the initial roadmap was authored.

`/a4:run` is the agent loop that consumes the file this skill produces. This skill never spawns implementation agents itself.

Seed: **$ARGUMENTS**

## Scope

- **In:** writing one task file at `status: pending`, allocating its id, resolving `implements:` / `justified_by:` references, proposing the `spike/<id>-<slug>/` sidecar for `kind: spike`, refreshing `implemented_by:` on referenced UCs.
- **Out:** UC-batch generation (`/a4:roadmap`), implement / test loop (`/a4:run`), automated reviewer (single-task author is the user's own thinking; no machine critique is auto-spawned). No commit.

## Pre-flight

1. Resolve project root: `git rev-parse --show-toplevel`. If not a git repo, abort.
2. Verify `<project-root>/a4/` exists. If not, abort — this skill is workspace-scoped.
3. Ensure `<project-root>/a4/task/` exists; create with `mkdir -p` if missing.
4. Parse `kind` from the argument or the recent conversation. **`kind` is required**; if absent or not one of `feature | spike | bug`, ask the user once which kind this task is.

## Step 1: Capture intent

Two input modes:

- **No argument beyond `kind`.** Read recent conversation. Identify what the task is about — the title, the work, the affected files, dependencies.
- **Short description / title in the argument.** Use it as a seed; still draw the full content from conversation context.

Draft a scratch summary (do not write to disk yet):

- **Title** — short, human-readable phrase. Example: "Render markdown preview".
- **Description** — one or two paragraphs covering goal, scope, and any non-obvious constraints.
- **Files** — source paths the task writes or modifies. For `feature` / `bug`, point at the project's production tree. For `spike`, paths live under `spike/<id>-<slug>/` (see Step 4).
- **Dependencies** — `depends_on:` paths (other tasks) and any wiki-page context (architecture sections, etc.).
- **Cycle / labels / milestone** — start `cycle: 1`; labels are free-form.

Present this draft to the user and iterate until the substance is right. One question per turn.

## Step 2: Resolve `implements:` (UC) and `justified_by:` (ADR)

These are optional and orthogonal — a task may declare zero, one, or both.

**`implements:`** — list of `usecase/<id>-<slug>` paths (no `.md`, no brackets) the task delivers.

- **`feature`** typically declares this when the project is UC-driven.
- **`spike`** is typically empty; spikes are exploratory rather than deliverables. A spike *may* reference a UC if the exploration is scoped to that UC's questions.
- **`bug`** declares this when the bug is traceable to a specific UC's flow.

Discovery: `Glob a4/usecase/*.md`. Show the user candidates by title; confirm the final list. The candidate UC must be at `status ∈ {ready, implementing}` for the task to be picked up by `/a4:run` later.

**`justified_by:`** — list of `decision/<id>-<slug>` paths backing the task.

- **`feature`** in a UC-less project (no relevant UC exists) declares this; the ADR's `## Decision` + relevant `architecture.md` section becomes the AC source.
- **`spike`** declares this when the exploration was triggered by an ADR's `## Open Questions` or `## Discussion Log`.
- **`bug`** declares this when an ADR sets the expected behavior the bug violates.

Discovery: `Glob a4/decision/*.md`. Confirm matches with the user.

If the kind is `feature` and **both** `implements:` and `justified_by:` end up empty, ask the user where the AC will be drawn from. A `feature` task with no AC source is a smell — either point it at a UC, point it at an ADR, or downgrade to `spike` if the work is genuinely exploratory.

Empty anchors are not always a problem — small UI tweaks, single-property validations, and roadmap-auto-generated features without a UC group can legitimately stay anchorless. The deeper signal lives in the task body: when the description implies a user-facing scope that no existing UC covers, or an architectural choice that no existing ADR records, this is content-aware upward propagation per [`references/adr-triggers.md`](${CLAUDE_PLUGIN_ROOT}/references/adr-triggers.md). Surface the gap as a review item with `kind: gap`, `target: usecase/` or `target: decision/` (omit `target:` for cross-cutting), `source: task`, body specifying which upstream artifact appears missing. The user can author the upstream artifact and re-link the task, or close the review with `discarded` + rationale ("genuinely small, no upstream needed").

## Step 3: Compose the task body

Required body sections (mirrors `/a4:roadmap`'s task schema):

- `## Description` — what and why.
- `## Files` — action / path / change table. For `spike`, every path is under `spike/<id>-<slug>/`.
- `## Unit Test Strategy` — scenarios + isolation strategy + test file paths. For `spike`, this may be a one-line "validate hypothesis via <method>".
- `## Acceptance Criteria` — checklist. Source by kind:

  | Task kind / shape | AC source |
  |---|---|
  | `feature` + `implements: [usecase/...]` | UC `## Flow` / `## Validation` / `## Error handling` |
  | `feature` + `justified_by: [decision/...]` (UC-less) | ADR `## Decision` + relevant `architecture.md` section |
  | `spike` | hypothesis + expected result, the spike's own body |
  | `bug` | reproduction scenario + fixed criteria |

  Validators do not enforce source-by-kind — this is a documentation convention. The `## Acceptance Criteria` section must exist regardless.

- `## Interface Contracts` — contracts this task consumes or provides, with wikilinks to `[[architecture]]` sections. For UC-less work, link to the ADR (`[[decision/<id>-<slug>]]`) or the relevant `architecture.md` section. May be empty for self-contained spikes.
- `## Log` — append-only; starts empty (`status: pending` is the implicit creation entry, written by the writer on first transition).

Present the composed body to the user. Iterate until confirmed.

## Step 4: For `kind: spike`, propose the sidecar

If `kind: spike`, the PoC code lives at `<project-root>/spike/<id>-<slug>/`, **outside** the `a4/` workspace (per the experiments-slot ADR).

Ask the user once:

> Spike code will live at `spike/<allocated-id>-<slug>/`. Create the directory now?

- **Yes** → create after Step 5 (id is needed for the path). `mkdir -p <project-root>/spike/<id>-<slug>`. Optionally drop a `.gitkeep` so the empty directory is committable.
- **No** → leave the path in the task's `## Files` table for the user (or task-implementer) to create later.

Do not auto-create archive paths or scaffolding files. The spike directory is opt-in scratch space; only the task markdown is mandatory.

## Step 5: Allocate id and write the file

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"
```

Slugify the title (lowercase, hyphenated, drop non-alphanumeric). File path: `a4/task/<id>-<slug>.md`.

Frontmatter:

```yaml
---
id: <allocated>
title: <human-readable title>
kind: feature | spike | bug
status: pending
implements: [<paths or empty>]
depends_on: [<paths or empty>]
justified_by: [<paths or empty>]
related: []
files: [<paths>]
cycle: 1
labels: []
milestone: <optional>
created: <today>
updated: <today>
---
```

Write the file with `Write`. Do **not** call `transition_status.py` for the initial `pending` — file creation at `status: pending` is the writer's idle state and the create is itself the log-implicit "first appearance" event. Subsequent transitions go through the writer.

## Step 6: Refresh `implemented_by:` (if `implements:` non-empty)

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/refresh_implemented_by.py" \
  "$(git rev-parse --show-toplevel)/a4"
```

Idempotent. Back-scans every task's `implements:` list and writes `implemented_by: [...]` onto each referenced UC. Skip when `implements:` is empty.

## Step 7: Spike sidecar (if confirmed in Step 4)

```bash
mkdir -p "$(git rev-parse --show-toplevel)/spike/<id>-<slug>"
```

Suggest (do not auto-create) a `README.md` inside it pointing back to the task file as `[[task/<id>-<slug>]]`. Whether to seed scaffolding files is the user's call — single spikes vary widely.

## Step 8: Hand-off

Tell the user:

> Task `task/<id>-<slug>` written at `status: pending`. Run `/a4:run` to start the implement + test loop (it will pick up this task plus any other ready ones). For more single tasks, re-invoke `/a4:task`.

If the user wants the task implemented immediately and no other ready tasks are pending, they may invoke `/a4:run` directly — mode flips to `autonomous` at the skill boundary.

## Commit Points

- **Single commit covers** the new task file + any UC files updated by `refresh_implemented_by.py` (when `implements:` is non-empty) + the empty `spike/<id>-<slug>/` directory (with `.gitkeep` if added). Suggest the commit when the user confirms; do not auto-commit.
- Implement-loop commits (per-task implementation, per-cycle test results) are owned by `/a4:run`.

Never skip hooks, amend, or force-push without explicit user instruction.

## Wrap Up

When the task file is written:

1. Summarize:
   - Task id, title, kind.
   - `implements:` / `justified_by:` references (or "none — AC sourced from <X>").
   - Whether the spike sidecar was created.
   - Files updated by `refresh_implemented_by.py`, if any.
2. Suggest `/a4:run` as the next step.
3. Suggest `/a4:handoff` only if the broader session warrants a snapshot — single-task authoring usually doesn't.

## Non-Goals

- Do not run a reviewer agent. Single-task authorship is conversational; the user's own confirmation is the gate.
- Do not author multiple tasks in one invocation. Re-invoke `/a4:task` per task. Use `/a4:roadmap` for the batch path.
- Do not write `roadmap.md`. If the project has no roadmap and the user wants one, redirect to `/a4:roadmap`. Single tasks are valid without a roadmap (they read `bootstrap.md`'s Launch & Verify in `/a4:run`).
- Do not flip task status beyond the initial `pending` write. `/a4:run` and `transition_status.py` own all subsequent transitions.
- Do not create `spike/archive/`. Archiving a finished spike is a manual `git mv` per the experiments-slot ADR.
