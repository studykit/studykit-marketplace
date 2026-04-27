---
name: task
description: "This skill should be used when the user wants to author a single ad-hoc task outside the UC-batch path that /a4:roadmap takes, OR to discard an existing task. Common authoring triggers: 'add a task', 'create a task', 'spike on X', 'log a bug', 'I need a task for', 'one-off task'. Common discard triggers: 'discard task <id>', 'drop task <id>', 'abandon this task', 'task <id> is no longer needed'. Authoring required argument: kind (feature | spike | bug); optional implements: (UC paths) and/or spec: (spec paths); writes a4/task/<id>-<slug>.md; for kind: spike also proposes a project-root spike/<id>-<slug>/ sidecar. Discard form: `discard <id-or-slug> [reason]`; flips status via transition_status.py and appends a `<why-discarded>` note. Single-task entry. Use /a4:roadmap for batch UC-driven generation; use /a4:run to drive the implement loop."
argument-hint: "kind=<feature|spike|bug> [title] | discard <id-or-slug> [reason]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, TaskCreate, TaskUpdate, TaskList
---

# Single Task Author + Discard

Two modes:

- **Author** (default) — writes one `a4/task/<id>-<slug>.md` outside the UC-batch path. Co-exists with `/a4:roadmap` (which writes the full UC-driven task set in one go). Use when a spike is needed to unblock an architecture or decision question; a bug needs a tracked fix; a spec-justified feature needs implementation in a UC-less or partially-UC project; a new feature task lands after the initial roadmap was authored.
- **Discard** — `discard <id-or-slug> [reason]`. Flips an existing task's `status: → discarded` via `transition_status.py` and records the reason. Use when a task is abandoned independent of any UC cascade — e.g., the spike answered its question and no implementation is needed, the bug turned out to be a non-issue, the feature direction was rejected without discarding the parent UC, or `/a4:run` decided the task is no longer worth pursuing.

`/a4:run` is the agent loop that consumes files this skill produces. This skill never spawns implementation agents itself.

Seed: **$ARGUMENTS**

## Scope

- **In (author mode):** writing one task file at `status: pending`, allocating its id, resolving `implements:` / `spec:` references, proposing the `spike/<id>-<slug>/` sidecar for `kind: spike`, refreshing `implemented_by:` on referenced UCs.
- **In (discard mode):** flipping an existing task's `status: → discarded` via `transition_status.py`, appending an optional `<why-discarded>` note, advising on the spike sidecar (no auto-delete).
- **Out:** UC-batch generation (`/a4:roadmap`), implement / test loop (`/a4:run`), automated reviewer (single-task author is the user's own thinking; no machine critique is auto-spawned). No commit.

## Pre-flight

1. Resolve project root: `git rev-parse --show-toplevel`. If not a git repo, abort.
2. Verify `<project-root>/a4/` exists. If not, abort — this skill is workspace-scoped.
3. Ensure `<project-root>/a4/task/` exists; create with `mkdir -p` if missing.
4. **Mode dispatch.** Read the first whitespace-delimited token of `$ARGUMENTS`:
   - If the token is exactly `discard` (lowercase), this is **discard mode** — jump to the "## Discard mode" pointer below and load `references/discard.md`; skip Steps 1–8 entirely.
   - Otherwise this is **author mode** — continue with Step 5.
5. Parse `kind` from the argument or the recent conversation. **`kind` is required for author mode**; if absent or not one of `feature | spike | bug`, ask the user once which kind this task is.

## Step 1: Capture intent

Two input modes:

- **No argument beyond `kind`.** Read recent conversation. Identify what the task is about — the title, the work, the affected files, dependencies.
- **Short description / title in the argument.** Use it as a seed; still draw the full content from conversation context.

Draft a scratch summary (do not write to disk yet):

- **Title** — short, human-readable phrase. Example: "Render markdown preview".
- **Description** — one or two paragraphs covering goal, scope, and any non-obvious constraints.
- **Initial status** — one of `open` (default; backlog) / `pending` (enqueue immediately) / `complete` (post-hoc documentation; code already shipped). Decide based on the user's intent. Ask once if unclear, defaulting to `open` for new ideas, `pending` when the user is mid-stream of `/a4:run`-style work, and `complete` when the user describes work that has already landed.
- **Files** — source paths the task writes or modifies. For `feature` / `bug`, point at the project's production tree. For `spike`, paths live under `spike/<id>-<slug>/` (see Step 4).
- **Dependencies** — `depends_on:` paths (other tasks) and any wiki-page context (architecture sections, etc.).
- **Cycle / labels / milestone** — start `cycle: 1`; labels are free-form.

Present this draft to the user and iterate until the substance is right. One question per turn.

## Step 2: Resolve `implements:` (UC) and `spec:` (spec)

These are optional and orthogonal — a task may declare zero, one, or both.

**`implements:`** — list of `usecase/<id>-<slug>` paths (no `.md`, no brackets) the task delivers.

- **`feature`** typically declares this when the project is UC-driven.
- **`spike`** is typically empty; spikes are exploratory rather than deliverables. A spike *may* reference a UC if the exploration is scoped to that UC's questions.
- **`bug`** declares this when the bug is traceable to a specific UC's flow.

Discovery: `Glob a4/usecase/*.md`. Show the user candidates by title; confirm the final list. The candidate UC must be at `status ∈ {ready, implementing}` for the task to be picked up by `/a4:run` later.

**`spec:`** — list of `spec/<id>-<slug>` paths backing the task.

- **`feature`** in a UC-less project (no relevant UC exists) declares this; the spec's `## Decision` + relevant `architecture.md` section becomes the AC source.
- **`spike`** declares this when the exploration was triggered by a spec's `## Open Questions` or `## Discussion Log`.
- **`bug`** declares this when a spec sets the expected behavior the bug violates.

Discovery: `Glob a4/spec/*.md`. Confirm matches with the user.

If the kind is `feature` and **both** `implements:` and `spec:` end up empty, ask the user where the AC will be drawn from. A `feature` task with no AC source is a smell — either point it at a UC, point it at a spec, or downgrade to `spike` if the work is genuinely exploratory.

Empty anchors are not always a problem — small UI tweaks, single-property validations, and roadmap-auto-generated features without a UC group can legitimately stay anchorless. The deeper signal lives in the task body: when the description implies a user-facing scope that no existing UC covers, or an architectural choice that no existing spec records, this is content-aware upward propagation per [`references/spec-triggers.md`](${CLAUDE_PLUGIN_ROOT}/references/spec-triggers.md). Surface the gap as a review item with `kind: gap`, `target: usecase/` or `target: spec/` (omit `target:` for cross-cutting), `source: task`, body specifying which upstream artifact appears missing. The user can author the upstream artifact and re-link the task, or close the review with `discarded` + rationale ("genuinely small, no upstream needed").

## Step 3: Compose the task body

Required body sections (per `body_schemas/task.xsd`):

- `<description>` — what and why.
- `<files>` — action / path / change table. For `spike`, every path is under `spike/<id>-<slug>/`.
- `<unit-test-strategy>` — scenarios + isolation strategy + test file paths. For `spike`, this may be a one-line "validate hypothesis via <method>".
- `<acceptance-criteria>` — checklist. Source by kind:

  | Task kind / shape | AC source |
  |---|---|
  | `feature` + `implements: [usecase/...]` | UC `<flow>` / `<validation>` / `<error-handling>` |
  | `feature` + `spec: [spec/...]` (UC-less) | spec `decision:` frontmatter + relevant `architecture.md` section |
  | `spike` | hypothesis + expected result, the spike's own body |
  | `bug` | reproduction scenario + fixed criteria |

  Validators do not enforce source-by-kind — this is a documentation convention. The `<acceptance-criteria>` section must exist regardless.

Optional body sections (per the XSD): `<interface-contracts>` (contracts this task consumes or provides, with markdown links to `architecture.md` sections — e.g., `[architecture#SessionService](../architecture.md#sessionservice)`. For UC-less work, link to the spec or the relevant `architecture.md` section. May be omitted for self-contained spikes); `<log>` (append-only writer-owned trail; starts absent — `status: pending` is the implicit creation entry, written by the writer on first transition); `<change-logs>` (audit trail when the task body is materially edited post-create); `<why-discarded>` (populated by discard mode).

Present the composed body to the user. Iterate until confirmed.

## Step 4: For `kind: spike`, propose the sidecar

If `kind: spike`, the PoC code lives at `<project-root>/spike/<id>-<slug>/`, **outside** the `a4/` workspace (per the experiments-slot spec).

Ask the user once:

> Spike code will live at `spike/<allocated-id>-<slug>/`. Create the directory now?

- **Yes** → create after Step 5 (id is needed for the path). `mkdir -p <project-root>/spike/<id>-<slug>`. Optionally drop a `.gitkeep` so the empty directory is committable.
- **No** → leave the path in the task's `<files>` table for the user (or task-implementer) to create later.

Do not auto-create archive paths or scaffolding files. The spike directory is opt-in scratch space; only the task markdown is mandatory.

## Step 5: Allocate id and write the file

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"
```

Slugify the title (lowercase, hyphenated, drop non-alphanumeric). File path: `a4/task/<id>-<slug>.md`.

Frontmatter (substitute the initial status decided in Step 1):

```yaml
---
type: task
id: <allocated>
title: <human-readable title>
kind: feature | spike | bug
status: open | pending | complete
implements: [<paths or empty>]
depends_on: [<paths or empty>]
spec: [<paths or empty>]
related: []
files: [<paths>]
cycle: 1
labels: []
milestone: <optional>
created: <today>
updated: <today>
---
```

Allowed initial statuses are `open` (default — backlog), `pending` (enqueue for `/a4:run`), and `complete` (post-hoc documentation). `progress` and `failing` are writer-only; never use them as initial states.

**`complete` initial-status preflight.** When the chosen initial status is `complete`, the work is asserted to already be shipped — verify before writing:

1. For each path in `files:`, confirm it exists in the working tree (`test -e` on the absolute path). If any path is missing, halt and ask the user: (a) fix the path, or (b) downgrade the initial status to `pending` so the task enters the implement loop.
2. Required body sections (`<description>`, `<files>`, `<unit-test-strategy>`, `<acceptance-criteria>`) must still be present per `body_schemas/task.xsd` — `complete` does not exempt the task from documentation. `<interface-contracts>` is optional; include it when relevant.
3. After writing the file, append an explicit `<log>` block recording the post-hoc origin (the writer never logged a `progress → complete` transition for this task):

   ```markdown
   <log>

   - <YYYY-MM-DD> created at status: complete (post-hoc documentation; code shipped prior to task authorship)

   </log>
   ```

   This is the only case where a skill writes into `<log>` directly — every subsequent entry must come from `transition_status.py`.

Write the file with `Write`. Do **not** call `transition_status.py` for the initial status — file creation at `status: open | pending | complete` is the writer's idle state for that initial value and the create is itself the log-implicit "first appearance" event (the post-hoc `<log>` block above is the documented exception for the `complete` case). Subsequent transitions go through the writer.

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

Suggest (do not auto-create) a `README.md` inside it pointing back to the task file as `[task/<id>-<slug>](../a4/task/<id>-<slug>.md)`. Whether to seed scaffolding files is the user's call — single spikes vary widely.

## Step 8: Hand-off

Branch the message by initial status:

- **`open`** — *Task `task/<id>-<slug>` written at `status: open` (backlog). Not yet enqueued for `/a4:run`. Transition `open → pending` via `transition_status.py` when ready to schedule it.*
- **`pending`** — *Task `task/<id>-<slug>` written at `status: pending`. Run `/a4:run` to start the implement + test loop (it will pick up this task plus any other ready ones).*
- **`complete`** — *Task `task/<id>-<slug>` written at `status: complete` (post-hoc documentation). No `/a4:run` action needed. UC ship-gate will treat this task as done if it `implements:` a UC.*

For more single tasks, re-invoke `/a4:task`. If the user wants the task implemented immediately and no other ready tasks are pending, they may invoke `/a4:run` directly — mode flips to `autonomous` at the skill boundary.

## Discard mode

Triggered when `$ARGUMENTS` starts with the token `discard`. Apply the procedure in [`references/discard.md`](references/discard.md): resolve the target task by id / `task/<id>-<slug>` / slug fragment (D1), confirm current status is `open | pending | progress | complete | failing` (D2), flip via `transition_status.py --to discarded` and append an optional `<why-discarded>` block (D3), advise on the spike sidecar without auto-deleting (D4), skip `refresh_implemented_by.py` since `implements:` did not change (D5), and report (D6). UC-cascade discards (when a UC flips to `discarded`) are handled automatically by `transition_status.py` — discard mode is for **explicit one-off task discards**.

## Commit Points

All commit subjects follow [`commit-message-convention.md`](${CLAUDE_PLUGIN_ROOT}/references/commit-message-convention.md).

- **Author mode** — single commit covers the new task file + any UC files updated by `refresh_implemented_by.py` (when `implements:` is non-empty) + the empty `spike/<id>-<slug>/` directory (with `.gitkeep` if added). Suggest the commit when the user confirms; do not auto-commit. Subject:
  ```
  #<task-id> [#<uc-id> ...] docs(a4): author task <slug>
  ```
  (Include each UC id touched by the reverse-link refresh; the slug is the new task's slug.)
- **Discard mode** — see `references/discard.md` D6 for commit scope. Subject:
  ```
  #<task-id> docs(a4): discard task <slug>
  ```
- Implement-loop commits (per-task implementation, per-cycle test results, merge-sweep integration, UC ship) are owned by `/a4:run`.

Never skip hooks, amend, or force-push without explicit user instruction.

## Wrap Up

**Author mode** — when the task file is written:

1. Summarize: task id / title / kind, `implements:` / `spec:` references (or "none — AC sourced from <X>"), whether the spike sidecar was created, files updated by `refresh_implemented_by.py`.
2. Suggest `/a4:run` as the next step.
3. Suggest `/a4:handoff` only if the broader session warrants a snapshot — single-task authoring usually doesn't.

**Discard mode** — D6 in `references/discard.md` already produces the summary. Do not suggest `/a4:run` (no new work). Suggest `/a4:handoff` only if the broader session warrants a snapshot.

## Non-Goals

- Do not run a reviewer agent. Single-task authorship is conversational; the user's own confirmation is the gate.
- Do not author multiple tasks in one invocation. Re-invoke `/a4:task` per task. Use `/a4:roadmap` for the batch path.
- Do not discard multiple tasks in one invocation. Re-invoke `/a4:task discard <id>` per task. UC-cascade discards happen automatically when the parent UC is discarded — do not duplicate that path here.
- Do not write `roadmap.md`. If the project has no roadmap and the user wants one, redirect to `/a4:roadmap`. Single tasks are valid without a roadmap (they read `bootstrap.md`'s Launch & Verify in `/a4:run`).
- Do not flip task status beyond the initial `open` / `pending` / `complete` write (author mode) or the explicit `→ discarded` flip (discard mode). `/a4:run` and `transition_status.py` own all other transitions, including `open → pending` (the user requests it; the writer applies it).
- Do not auto-delete or auto-archive `spike/<id>-<slug>/` on discard. Archiving a finished spike is a manual `git mv` per the experiments-slot spec.
- Do not delete the task file on discard. The file stays at `status: discarded` so its `<log>` and `<why-discarded>` remain part of the workspace history; `git rm` is a separate user choice.
