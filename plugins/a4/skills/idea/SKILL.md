---
name: idea
description: "This skill should be used when the user explicitly invokes /a4:idea inside a project that uses the a4 plugin's a4/ workflow. Captures a one-line idea as a new issue file at a4/idea/<id>-<slug>.md, or discards an existing one. The skill allocates the next global id, slugifies the provided text, and writes the frontmatter + body so the user only has to type the idea itself."
argument-hint: "<one-line idea> | discard <id-or-slug> [reason]"
disable-model-invocation: true
allowed-tools: Bash, Write, Read, Edit, Glob
---

# Idea Quick Capture + Discard (a4 plugin)

Two modes:

- **Capture** (default) — `/a4:idea <한 줄 아이디어>`. Writes a new `a4/idea/<id>-<slug>.md` with `status: open`. 30-second capture for raw possibilities.
- **Discard** — `/a4:idea discard <id-or-slug> [reason]`. Locates an existing idea file, flips `status: open → discarded` (the PostToolUse hook refreshes `updated:`), optionally appends a one-line `## Change Logs` bullet.

## Context

- Project root: !`git rev-parse --show-toplevel 2>/dev/null || echo NOT_A_GIT_REPO`
- Today: !`date +%Y-%m-%d`

If the project root resolved to `NOT_A_GIT_REPO`, abort with a clear message. This skill is workspace-scoped and keyed off the git worktree root.

## Workflow

### 1. Parse argument and dispatch

Read the first whitespace-delimited token of `$ARGUMENTS`.

- If the first token is `discard` (lowercase, exact match), this is the **discard** path — apply `references/discard-flow.md`.
- Otherwise, this is the **capture** path — continue with steps 2–6 below.
- If `$ARGUMENTS` is empty or contains only whitespace, abort and tell the user: "Please provide an idea as a one-line argument — e.g., `/a4:idea 콜그래프에 주석 렌더링 넣기` — or discard one via `/a4:idea discard <id>`."

In capture mode, the argument's trimmed text becomes the `title` and the H1 of the new file.

### 2. Verify the workspace

Check that `<project-root>/a4/` exists and is a directory. If not, tell the user no `a4/` workspace was found and stop.

Ensure `<project-root>/a4/idea/` exists; create with `mkdir -p` if missing.

### 3. Allocate next id

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "<project-root>/a4"
```

The script prints the next integer. Capture it — this becomes the idea's `id:` and prefixes the filename.

### 4. Generate slug

Slug derivation rules + examples: `references/slug-rules.md`.

### 5. Compose the file

Frontmatter template + field definitions: `references/capture-template.md`. Use the `Write` tool.

### 6. Report

Tell the user the full file path and the allocated id, e.g.:

```
Captured as idea #12 → /abs/path/to/a4/idea/12-콜그래프에-주석-렌더링-넣기.md
```

If the idea warrants expansion, mention one-line follow-up options:

- Edit the file directly to add rationale inside a `## Why This Matters` or `## Notes` section (both optional per the authoring contract).
- When ready to pursue it, change `status:` to `promoted` and set `promoted: [<target-path>]` pointing at the new artifact (usecase / task / brainstorm).

Do not propose auto-promotion or auto-commit.

## Discard mode

Procedure: `references/discard-flow.md`. Covers target resolution (D1), status check (D2), in-place edit + `## Change Logs` append (D3), report (D4).

## Non-Goals

- Do not commit the new file. Leave it in the working tree.
- Do not propose a target artifact at capture time. Ideas are independent by definition; graduation is a separate, later decision.
- Do not launch a brainstorm or research session off the back of a capture. If the user wants that, they invoke `/a4:brainstorm` or `/a4:research` with the idea path as input themselves.
- Do not surface existing `a4/idea/` open count or nudge the user about prior ideas. Capture is capture; review is separate.
- Do not validate the workspace-wide id uniqueness here. `allocate_id.py` reads current state and returns `max(id) + 1`; the Stop hook catches any collision on next stop.

## Failure modes

- `NOT_A_GIT_REPO` — abort with a short message.
- `a4/` missing — abort; ideas require a workspace.
- Empty `$ARGUMENTS` — abort with a one-line usage hint.
- `allocate_id.py` non-zero exit — relay stderr and abort (capture mode).
- Write fails (disk full, permission) — relay the error; do not retry silently.
- Discard target unresolvable or ambiguous — list candidates or report "no match" per D1.
- Discard target already `promoted` — refuse per D2.
