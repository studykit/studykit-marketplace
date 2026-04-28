# Task Author Mode Flow

## Step 1: Capture intent

Two input modes:

- **No argument beyond `kind`.** Read recent conversation. Identify what the task is about — the title, the work, the affected files, dependencies.
- **Short description / title in the argument.** Use it as a seed; still draw the full content from conversation context.

Draft a scratch summary (do not write to disk yet):

- **Title** — short, human-readable phrase.
- **Description** — one or two paragraphs covering goal, scope, and any non-obvious constraints.
- **Initial status** — one of `open` (default; backlog) / `pending` (enqueue immediately) / `complete` (post-hoc documentation; code already shipped). Decide based on the user's intent. Ask once if unclear, defaulting to `open` for new ideas, `pending` when the user is mid-stream of `/a4:run`-style work, and `complete` when the user describes work that has already landed.
- **Files** — source paths the task writes or modifies. For `feature` / `bug`, point at the project's production tree. For `spike`, paths live under `spike/<id>-<slug>/`.
- **Dependencies** — `depends_on:` paths (other tasks) and any wiki-page context.
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

Empty anchors are not always a problem — small UI tweaks, single-property validations, and roadmap-auto-generated features without a UC group can legitimately stay anchorless. The deeper signal lives in the task body: when the description implies a user-facing scope that no existing UC covers, or an architectural choice that no existing spec records, this is content-aware upward propagation per `../../../docs/spec-triggers.md`. Surface the gap as a review item with `kind: gap`, `target: usecase/` or `target: spec/`, `source: task`, body specifying which upstream artifact appears missing.

## Step 3: Compose the task body

Required and optional body sections, the AC-source convention, and the writer-owned `<log>` rules are defined in the per-kind authoring reference that matches `kind` — `../../../references/task-feature-authoring.md`, `../../../references/task-bug-authoring.md`, or `../../../references/task-spike-authoring.md` §Body shape. Compose the section content per that contract.

Present the composed body to the user. Iterate until confirmed.

## Step 4: For `kind: spike`, propose the sidecar

If `kind: spike`, the PoC code lives at `<project-root>/spike/<id>-<slug>/`, **outside** the `a4/` workspace.

Ask the user once:

> Spike code will live at `spike/<allocated-id>-<slug>/`. Create the directory now?

- **Yes** → create after Step 5 (id is needed for the path). `mkdir -p <project-root>/spike/<id>-<slug>`. Optionally drop a `.gitkeep` so the empty directory is committable.
- **No** → leave the path in the task's `<files>` table for the user (or task-implementer) to create later.

Do not auto-create archive paths or scaffolding files. The spike directory is opt-in scratch space; only the task markdown is mandatory.

## Step 5: Allocate id and write the file

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"
```

Slugify the title (lowercase, hyphenated, drop non-alphanumeric). File path: `a4/task/<kind>/<id>-<slug>.md`.

Frontmatter shape, allowed initial statuses (`open | pending | complete`), and the `complete` preflight (path-existence check on `files:` + the post-hoc `<log>` block — the only case where a skill writes into `<log>` directly) are defined in the per-kind authoring reference that matches `kind` — `../../../references/task-feature-authoring.md`, `../../../references/task-bug-authoring.md`, or `../../../references/task-spike-authoring.md` §Frontmatter contract / §`complete` initial-status preflight.

Write the file with `Write`. Do **not** call `transition_status.py` for the initial status — file creation at `status: open | pending | complete` is the writer's idle state for that initial value.

## Step 6: Refresh `implemented_by:` (if `implements:` non-empty)

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/refresh_implemented_by.py" \
  "$(git rev-parse --show-toplevel)/a4"
```

Idempotent. Skip when `implements:` is empty.

## Step 7: Spike sidecar (if confirmed in Step 4)

```bash
mkdir -p "$(git rev-parse --show-toplevel)/spike/<id>-<slug>"
```

Suggest (do not auto-create) a `README.md` inside it pointing back to the task file as `[task/<id>-<slug>](../a4/task/spike/<id>-<slug>.md)`. Whether to seed scaffolding files is the user's call.

## Step 8: Hand-off

Branch the message by initial status:

- **`open`** — *Task `task/<id>-<slug>` written at `status: open` (backlog). Not yet enqueued for `/a4:run`. Transition `open → pending` via `transition_status.py` when ready to schedule it.*
- **`pending`** — *Task `task/<id>-<slug>` written at `status: pending`. Run `/a4:run` to start the implement + test loop.*
- **`complete`** — *Task `task/<id>-<slug>` written at `status: complete` (post-hoc documentation). No `/a4:run` action needed.*
