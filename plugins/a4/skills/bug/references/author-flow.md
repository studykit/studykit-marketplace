# Bug Task Author Flow

## Step 1: Capture intent

Two input modes:

- **No argument.** Read recent conversation. Identify what is broken — observed behavior, expected behavior, reproduction.
- **Short description / title in the argument.** Use it as a seed; still draw the full content from conversation context.

Draft a scratch summary (do not write to disk yet):

- **Title** — short, human-readable phrase naming the defect.
- **Description** — observed behavior, expected behavior, reproduction steps. State the regression test that will pin the expected behavior.
- **Initial status** — one of `open` (default; backlog) / `pending` (enqueue immediately) / `complete` (post-hoc documentation; fix already shipped). Default to `open` for a freshly logged defect, `pending` when the user wants the implement loop to pick it up immediately.
- **Artifacts** — frontmatter `artifacts:` lists artifact paths under `artifacts/bug/<id>-<slug>/`. Typically empty (production fix lives in the project source tree, documented in body `## Files`); populate only when reproduction artifacts (repro repo, crash log, screenshot) have lasting value.
- **Dependencies** — `depends_on:` paths (other tasks) and any wiki-page context.
- **Cycle / labels** — start `cycle: 1`; labels are free-form.

Present this draft to the user and iterate until the substance is right. One question per turn.

## Step 2: Resolve `implements:` (UC) and `spec:` (spec)

These are optional and orthogonal — a bug task may declare zero, one, or both. Empty anchors are common for cross-cutting fixes.

**`implements:`** — declare when the bug traces to a specific UC's flow.

- Discovery: `Glob a4/usecase/*.md`. Show the user candidates by title; confirm the final list.

**`spec:`** — declare when the bug is a regression against a spec's expected behavior.

- Discovery: `Glob a4/spec/*.md`. Confirm matches with the user.

If neither anchor is appropriate, leave both empty — the AC source is the regression test the body specifies.

## Step 3: Compose the task body

Required and optional body sections are defined in `${CLAUDE_PLUGIN_ROOT}/authoring/bug-authoring.md` §Body shape. The required `## Unit Test Strategy` must include a regression scenario that fails before the fix and passes after — closing a bug without that test is the most common reason the same bug returns.

Present the composed body to the user. Iterate until confirmed.

## Step 4: Allocate id and write the file

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"
```

Slugify the title (lowercase, hyphenated, drop non-alphanumeric). File path: `a4/bug/<id>-<slug>.md`.

Frontmatter shape, allowed initial statuses (`open | pending | complete`), and the `complete` preflight (path-existence check on `artifacts:`) are defined in `${CLAUDE_PLUGIN_ROOT}/authoring/bug-authoring.md` §Frontmatter contract / §`complete` initial-status preflight.

Write the file with `Write`. The initial `status:` is set by the Write itself; no additional flip is needed.

## Step 5: Hand-off

Branch the message by initial status:

- **`open`** — *Bug `bug/<id>-<slug>` written at `status: open` (backlog). Not yet enqueued for `/a4:run`. Transition `open → pending` by editing `status:` directly when ready to schedule it (the PostToolUse cascade hook refreshes `updated:`).*
- **`pending`** — *Bug `bug/<id>-<slug>` written at `status: pending`. Run `/a4:run` to start the regression-test + fix loop.*
- **`complete`** — *Bug `bug/<id>-<slug>` written at `status: complete` (post-hoc documentation; fix already shipped). No `/a4:run` action needed.*
