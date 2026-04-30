# Spike Task Author Flow

## Step 1: Capture intent

Two input modes:

- **No argument.** Read recent conversation. Identify the open question, the hypothesis, and the decision the spike's outcome will inform.
- **Short description / title in the argument.** Use it as a seed; still draw the full content from conversation context.

Draft a scratch summary (do not write to disk yet):

- **Title** — short, human-readable phrase naming the question being explored.
- **Description** — what is being explored, why a spike (vs. going straight to a regular task), the hypothesis, and the decision this informs.
- **Initial status** — `open` (default; backlog), `pending` (enqueue immediately for `/a4:run`), or `complete` (post-hoc; PoC already done). Default to `pending` when the user wants to start exploring now.
- **Artifacts** — frontmatter `artifacts:` lists artifact paths under `artifacts/spike/<id>-<slug>/`. **Never** under the project source tree. Empty list is fine for a freshly authored spike.
- **Dependencies** — `depends_on:` paths (other tasks); spikes typically have none.
- **Labels** — free-form.

`implements:` / `spec:` / `cycle:` are **not** part of the spike schema. If the spike traces to a UC or spec, mention them in `## Description` body prose with markdown links. If the user asks for them, redirect to `/a4:task` or `/a4:bug`.

Present this draft to the user and iterate until the substance is right. One question per turn.

## Step 2: Compose the task body

Required and optional body sections are defined in `${CLAUDE_PLUGIN_ROOT}/references/spike-authoring.md` §Body shape. The required `## Acceptance Criteria` should describe what observable outcome proves or refutes the hypothesis.

Present the composed body to the user. Iterate until confirmed.

## Step 3: Propose the artifact directory

The PoC code lives at `<project-root>/artifacts/spike/<id>-<slug>/`, **outside** the `a4/` workspace.

Ask the user once:

> Spike code will live at `artifacts/spike/<allocated-id>-<slug>/`. Create the directory now?

- **Yes** → create after Step 4 (id is needed for the path). `mkdir -p <project-root>/artifacts/spike/<id>-<slug>`. Optionally drop a `.gitkeep` so the empty directory is committable.
- **No** → leave the path in the task's `## Files` table for the user (or task-implementer) to create later.

Do not auto-create archive paths or scaffolding files. The artifact directory is opt-in scratch space; only the task markdown is mandatory.

## Step 4: Allocate id and write the file

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"
```

Slugify the title (lowercase, hyphenated, drop non-alphanumeric). File path: `a4/spike/<id>-<slug>.md`.

Frontmatter shape, allowed initial statuses (`open | pending | complete`), and the `complete` preflight (path-existence check on `artifacts:` under `artifacts/spike/<id>-<slug>/` or `artifacts/spike/archive/<id>-<slug>/`) are defined in `${CLAUDE_PLUGIN_ROOT}/references/spike-authoring.md` §Frontmatter contract / §`complete` initial-status preflight.

Write the file with `Write`. The initial `status:` is set by the Write itself; no additional flip is needed.

## Step 5: Create the artifact directory (if confirmed in Step 3)

```bash
mkdir -p "$(git rev-parse --show-toplevel)/artifacts/spike/<id>-<slug>"
```

Suggest (do not auto-create) a `README.md` inside it pointing back to the task file as `[spike/<id>-<slug>](../../a4/spike/<id>-<slug>.md)`. Whether to seed scaffolding files is the user's call.

## Step 6: Hand-off

Branch the message by initial status:

- **`open`** — *Spike `spike/<id>-<slug>` written at `status: open` (backlog). Not yet enqueued for `/a4:run`. Transition `open → pending` by editing `status:` directly when ready (the PostToolUse cascade hook refreshes `updated:`).*
- **`pending`** — *Spike `spike/<id>-<slug>` written at `status: pending`. Run `/a4:run` to start exploration.*
- **`complete`** — *Spike `spike/<id>-<slug>` written at `status: complete` (post-hoc documentation; PoC already done).*
