---
name: idea
description: "This skill should be used when the user explicitly invokes /a4:idea inside a project that uses the a4 plugin's a4/ workflow. Captures a one-line pre-pipeline idea as a new issue file at a4/idea/<id>-<slug>.md, or discards an existing one. The skill allocates the next global id, slugifies the provided text, and writes the frontmatter + body so the user only has to type the idea itself."
argument-hint: "<one-line idea> | discard <id-or-slug> [reason]"
disable-model-invocation: true
allowed-tools: Bash, Write, Read, Edit, Glob
---

# Idea Quick Capture + Discard (a4 plugin)

Two modes:

- **Capture** (default) — `/a4:idea <한 줄 아이디어>`. Writes a new `a4/idea/<id>-<slug>.md` with `status: open`. 30-second capture for pre-pipeline possibilities.
- **Discard** — `/a4:idea discard <id-or-slug> [reason]`. Locates an existing idea file, flips `status: open → discarded`, bumps `updated:`, optionally appends a one-line `## Why discarded` section with the reason.

See `plugins/a4/spec/archive/2026-04-24-idea-slot.decide.md` for the full design rationale, especially the boundary drawn between `idea/` (independent possibilities, captured raw) and `review/` (gaps in current spec, bound to progress).

## Context

- Project root: !`git rev-parse --show-toplevel 2>/dev/null || echo NOT_A_GIT_REPO`
- Today: !`date +%Y-%m-%d`

If the project root resolved to `NOT_A_GIT_REPO`, abort with a clear message. This skill is workspace-scoped and keyed off the git worktree root.

## Task

### 1. Parse argument and dispatch

Read the first whitespace-delimited token of `$ARGUMENTS`.

- If the first token is `discard` (lowercase, exact match), this is the **discard** path — jump to "Discard mode" below.
- Otherwise, this is the **capture** path — continue with steps 2–6.
- If `$ARGUMENTS` is empty or contains only whitespace, abort and tell the user: "Please provide an idea as a one-line argument — e.g., `/a4:idea 콜그래프에 주석 렌더링 넣기` — or discard one via `/a4:idea discard <id>`."

In capture mode, the argument's trimmed text becomes the `title` and the H1 of the new file.

### 2. Verify the workspace

Check that `<project-root>/a4/` exists and is a directory. If not, tell the user no `a4/` workspace was found and stop — ideas are workspace-scoped.

Ensure `<project-root>/a4/idea/` exists; create it with `mkdir -p` if missing (first-time use in this workspace).

### 3. Allocate next id

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "<project-root>/a4"
```

The script prints the next integer. Capture it — this becomes the idea's `id:` and prefixes the filename.

### 4. Generate slug

Produce a URL-friendly slug from the title:

- Lowercase the entire string (ASCII letters only; Korean / CJK characters pass through untouched since they have no case).
- Replace whitespace runs with a single hyphen.
- Remove punctuation that is not a hyphen, alphanumeric, or a non-ASCII word character (keep Korean hangul, kanji, etc.).
- Collapse multiple consecutive hyphens to one.
- Trim leading and trailing hyphens.
- Truncate to 50 characters at a hyphen boundary where possible (never mid-word for ASCII; best-effort for CJK).

If the slug ends up empty after normalization (e.g., argument was pure punctuation), fall back to `untitled`.

Examples:

| Title | Slug |
|-------|------|
| `콜그래프에 주석 렌더링 넣기` | `콜그래프에-주석-렌더링-넣기` |
| `Add caching layer to API` | `add-caching-layer-to-api` |
| `!!!!???` | `untitled` |
| `Rename: the Foo module, v2.0` | `rename-the-foo-module-v20` |

### 5. Compose the file

Write to `<project-root>/a4/idea/<id>-<slug>.md` using the Write tool. Content:

```markdown
---
id: <id>
title: <title>
status: open
promoted: []
related: []
labels: []
created: <today>
updated: <today>
---
# <title>
```

Fields:

- `id:` — the integer from step 3, as a YAML int (no quotes).
- `title:` — the user's trimmed argument. If it contains characters that break bare YAML (colons, `#`, leading/trailing whitespace, quotes), wrap in double quotes and escape as needed.
- `status: open` — literal.
- `promoted: []`, `related: []`, `labels: []` — empty lists as placeholders. `[]` (not omitted) because these fields are part of the idea shape; their emptiness is noteworthy.
- `created:` / `updated:` — today's date in `YYYY-MM-DD` format (from the `date +%Y-%m-%d` context).

The body is just the H1. Longer ideas can be edited in later — this skill writes the minimum.

### 6. Report

Tell the user the full file path and the allocated id, e.g.:

```
Captured as idea #12 → /abs/path/to/a4/idea/12-콜그래프에-주석-렌더링-넣기.md
```

If the idea warrants expansion, mention one-line follow-up options:

- Edit the file directly to add rationale under a `## Why this matters` or `## Notes` section.
- When ready to pursue it, change `status:` to `promoted` and set `promoted: [<target-path>]` pointing at the new artifact (usecase / task / spark session).

Do not propose auto-promotion or auto-commit.

## Discard mode

Triggered when `$ARGUMENTS` starts with the token `discard`. The remainder after the first whitespace is parsed as: `<id-or-slug> [reason]`.

### D1. Resolve the idea file

The second token is the **target**. Accept three forms and resolve in this order:

1. **Numeric id** (e.g., `12`) — glob `<project-root>/a4/idea/<id>-*.md`. Exactly one match expected; error if zero or multiple.
2. **Folder-prefixed path** (e.g., `idea/12-foo`) — glob `<project-root>/a4/<path>.md`. Exactly one match expected.
3. **Slug fragment** (any other non-empty token) — glob `<project-root>/a4/idea/*-<fragment>*.md`. If exactly one matches, use it; if multiple match, list them to the user and ask which.

If no file resolves, abort with: "No idea file found for `<target>`. List candidates with `ls a4/idea/`."

### D2. Check current status

Read the resolved file's frontmatter. If `status` is:

- `open` → proceed to D3.
- `promoted` → abort: "Idea `<path>` is already `promoted`. Discarding a promoted idea is ambiguous; edit by hand if you truly want to reverse that."
- `discarded` → report "`<path>` is already `discarded`. No change." and exit.

### D3. Apply the discard

Edit the file in-place via the `Edit` tool:

1. Change the frontmatter `status:` value from `open` to `discarded`.
2. Update the frontmatter `updated:` to today's date.
3. If a reason was provided (any tokens after `<id-or-slug>`), append a body section (or add one if not already present):

   ```markdown
   ## Why discarded

   <reason text>
   ```

   Use the reason verbatim — no re-wording. If the section already exists, append a new line under it prefixed with today's date.

### D4. Report

Tell the user:

```
Discarded idea #<id> → /abs/path/to/a4/idea/<id>-<slug>.md
Reason recorded: <reason or "none">
```

Do not commit. Leave in the working tree.

## Non-Goals

- Do not commit the new file. Leave it in the working tree.
- Do not propose a target artifact at capture time. Ideas are independent by definition; graduation is a separate, later decision.
- Do not launch a brainstorm or research session off the back of a capture. If the user wants that, they invoke `/a4:spark-brainstorm` or `/a4:research` with the idea path as input themselves.
- Do not surface existing `a4/idea/` open count or nudge the user about prior ideas. Capture is capture; review is separate (`/a4:compass` or `/a4:index` shows the open-idea count).
- Do not validate the workspace-wide id uniqueness here. `allocate_id.py` reads current state and returns `max(id) + 1`; a race with a concurrent session is extremely unlikely in single-user workflows, and the Stop-hook validator catches any collision on next stop.

## Failure modes

- `NOT_A_GIT_REPO` — abort with a short message.
- `a4/` missing — abort; ideas require a workspace.
- Empty `$ARGUMENTS` — abort with a one-line usage hint.
- `allocate_id.py` non-zero exit — relay stderr and abort (capture mode).
- Write fails (disk full, permission) — relay the error; do not retry silently.
- Discard target unresolvable or ambiguous — list candidates or report "no match" per D1.
- Discard target already `promoted` — refuse per D2.
