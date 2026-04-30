# Task Author Flow

## Step 1: Capture intent

Two input modes:

- **No argument.** Read recent conversation. Identify what the task is about — the title, the work, the affected files, dependencies.
- **Short description / title in the argument.** Use it as a seed; still draw the full content from conversation context.

Draft a scratch summary (do not write to disk yet):

- **Title** — short, human-readable phrase.
- **Description** — one or two paragraphs covering goal, scope, and any non-obvious constraints.
- **Initial status** — one of `open` (default; backlog) / `pending` (enqueue immediately) / `complete` (post-hoc documentation; code already shipped). Decide based on the user's intent. Ask once if unclear, defaulting to `open` for new ideas, `pending` when the user is mid-stream of `/a4:run`-style work, and `complete` when the user describes work that has already landed.
- **Artifacts** — frontmatter `artifacts:` lists artifact paths under `artifacts/task/<id>-<slug>/`. Typically empty (production source paths go in the body `## Files` table); populate only when the task uses an artifact directory.
- **Dependencies** — `depends_on:` paths (other tasks) and any wiki-page context.
- **Cycle / labels** — start `cycle: 1`; labels are free-form.

Present this draft to the user and iterate until the substance is right. One question per turn.

## Step 2: Resolve `implements:` (UC) and `spec:` (spec)

These are optional and orthogonal — a task may declare zero, one, or both.

**`implements:`** — list of `usecase/<id>-<slug>` paths (no `.md`, no brackets) the task delivers.

- Typically declared when the project is UC-driven.
- Discovery: `Glob a4/usecase/*.md`. Show the user candidates by title; confirm the final list. The candidate UC must be at `status ∈ {ready, implementing}` for the task to be picked up by `/a4:run` later.

**`spec:`** — list of `spec/<id>-<slug>` paths backing the task.

- Declared in UC-less projects (no relevant UC exists); the spec's `## Specification` body + relevant `architecture.md` section becomes the AC source.
- Discovery: `Glob a4/spec/*.md`. Confirm matches with the user.

If **both** `implements:` and `spec:` end up empty, ask the user where the AC will be drawn from. A task with no AC source is a smell — either point it at a UC, point it at a spec, or downgrade to `spike` (use `/a4:spike` instead) if the work is genuinely exploratory.

Empty anchors are not always a problem — small UI tweaks, single-property validations, and roadmap-auto-generated tasks without a UC group can legitimately stay anchorless. The deeper signal lives in the task body: when the description implies a user-facing scope that no existing UC covers, or an architectural choice that no existing spec records, surface the gap as a review item with `kind: gap`, `target: usecase/` or `target: spec/`, `source: task`, body specifying which upstream artifact appears missing.

## Step 3: Compose the task body

Required and optional body sections and the AC-source convention are defined in `${CLAUDE_PLUGIN_ROOT}/references/task-authoring.md` §Body shape. Compose the section content per that contract.

Present the composed body to the user. Iterate until confirmed.

## Step 4: Allocate id and write the file

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"
```

Slugify the title (lowercase, hyphenated, drop non-alphanumeric). File path: `a4/task/<id>-<slug>.md`.

Frontmatter shape, allowed initial statuses (`open | pending | complete`), and the `complete` preflight (path-existence check on `artifacts:`) are defined in `${CLAUDE_PLUGIN_ROOT}/references/task-authoring.md` §Frontmatter contract / §`complete` initial-status preflight.

Write the file with `Write`. Do **not** call `transition_status.py` for the initial status — file creation at `status: open | pending | complete` is the writer's idle state for that initial value.

## Step 5: Hand-off

Branch the message by initial status:

- **`open`** — *Task `task/<id>-<slug>` written at `status: open` (backlog). Not yet enqueued for `/a4:run`. Transition `open → pending` via `transition_status.py` when ready to schedule it.*
- **`pending`** — *Task `task/<id>-<slug>` written at `status: pending`. Run `/a4:run` to start the implement + test loop.*
- **`complete`** — *Task `task/<id>-<slug>` written at `status: complete` (post-hoc documentation). No `/a4:run` action needed.*
