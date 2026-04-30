# Research Task Author Flow

## Step 1: Capture intent

Two input modes:

- **No argument.** Read recent conversation. Identify the question being researched.
- **Short description / title in the argument.** Use it as a seed; still draw the full content from conversation context.

Draft a scratch summary (do not write to disk yet):

- **Title** — short, human-readable phrase naming the question or comparison.
- **Description / context** — why the research is needed; what specific question or comparison purpose.
- **Mode** — `comparative` (option-comparison) or `single` (flat topic / question). Required.
- **Options** — list of option names, required when `mode: comparative`. Each option becomes an H3 subsection under `## Options` in the body.
- **Initial status** — `open` (default; backlog), `pending` (enqueue), `progress` (start investigating now), or `complete` (post-hoc; investigation captured in this conversation). Default to `pending` when user wants to schedule, `progress` when starting now, `complete` for one-shot conversational capture.
- **Artifacts** — frontmatter `artifacts:` lists artifact paths under `artifacts/research/<id>-<slug>/`. Typically empty (the body is the deliverable); populate only when ancillary artifacts (raw data, charts, evaluation scripts) need to live alongside.
- **Dependencies** — `depends_on:` paths (other tasks); typically none.
- **Related** — `related:` paths to other artifacts the investigation informs (e.g., a spec being drafted) or that informed it.
- **Labels** — free-form.

`implements:` / `spec:` / `cycle:` are **not** part of the research schema. If the research is scoped to a UC or triggered by a spec, mention them in `## Context` body prose with markdown links.

Present this draft to the user and iterate until the substance is right. One question per turn.

## Step 2: Compose the task body

Required and optional body sections are defined in `${CLAUDE_PLUGIN_ROOT}/references/research-authoring.md` §Body shape:

- `## Context` (required) — 1–3 sentences naming the question.
- `## Options` (required for `mode: comparative`) — one H3 per option name. Each subsection: Sources consulted / Key findings / Raw excerpts (optionally folded in `<details>`).
- `## Findings` (required for `mode: single`) — same structure, flat.

Authors may seed an empty body and fill it later under `status: progress`, or capture the full investigation in this conversation and write at `status: complete` (post-hoc).

Present the composed body to the user. Iterate until confirmed.

## Step 3: Allocate id and write the file

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"
```

Slugify the title (lowercase, hyphenated, drop non-alphanumeric). File path: `a4/research/<id>-<slug>.md`.

Frontmatter shape, allowed initial statuses, and the `complete` preflight (body-section presence) are defined in `${CLAUDE_PLUGIN_ROOT}/references/research-authoring.md` §Frontmatter contract / §`complete` initial-status preflight.

Write the file with `Write`. The initial `status:` is set by the Write itself; no additional flip is needed.

## Step 4: Hand-off

Branch the message by initial status:

- **`open`** — *Research `research/<id>-<slug>` written at `status: open` (backlog). Not yet enqueued. Transition `open → pending` when ready to schedule.*
- **`pending`** — *Research `research/<id>-<slug>` written at `status: pending`. Start the investigation when ready (the user or an investigator agent fills `## Context` + `## Options`/`## Findings`).*
- **`progress`** — *Research `research/<id>-<slug>` written at `status: progress`. Investigation underway — fill the body sections as evidence accumulates. When finalized, optionally run `/a4:research-review` before flipping to `complete`.*
- **`complete`** — *Research `research/<id>-<slug>` written at `status: complete` (post-hoc; investigation captured in this conversation). Optionally run `/a4:research-review` for a quality pass.*
