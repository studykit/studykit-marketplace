---
name: handoff
description: "This skill should be used when the user explicitly invokes /a4:handoff inside a project that uses the a4 plugin's a4/ workflow. Writes a topic-threaded session handoff at <project-root>/.handoff/<topic>/ that references a4/ artifacts via plain Obsidian wikilinks (no transclusion) so the handoff stays a point-in-time snapshot."
argument-hint: "<topic-slug> [additional emphasis]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Session Handoff (a4 plugin)

Writes a session handoff so a fresh Claude Code session can resume the current topic thread without reconstructing prior conversation. Enforces a topic-threaded schema (`topic` / `previous` / `timestamp`) and keeps each handoff Obsidian-native: plain wikilinks for live pointers, verbatim excerpts only when needed.

Invocation: `/a4:handoff <topic-slug> [additional emphasis]`.

## Context

- Timestamp: !`date +"%Y-%m-%d_%H%M"`
- Today: !`date +"%Y-%m-%d"`
- Project root: !`git rev-parse --show-toplevel 2>/dev/null || echo NOT_A_GIT_REPO`

If project root resolved to `NOT_A_GIT_REPO`, abort with a clear message. The handoff directory is project-scoped and keyed off the git worktree root; outside of one, there is no well-defined place to write.

## Task

### 1. Determine topic and filename slug

- **Topic slug** — the first whitespace-separated token in `$ARGUMENTS`. If missing, ask the user. Must match `[a-z0-9-]+` (lowercase, digits, hyphens only — used as the group key for thread resumption).
- **Filename slug** — a short kebab-case description of this session's focus (e.g., `handoff-scripts-and-task-rename`). Derive from session context; ask the user only if genuinely ambiguous.

Final file path: `<project-root>/.handoff/<topic-slug>/<TIMESTAMP>_<filename-slug>.md`. If that exact path already exists, append `_2`, `_3`, … — never overwrite an existing handoff.

Ensure `<project-root>/.handoff/<topic-slug>/` exists (create it if missing).

### 2. Locate the previous handoff on this topic

List files in `<project-root>/.handoff/<topic-slug>/`. Pick the one with the highest `<TIMESTAMP>` filename prefix (the filename is sortable as a string). That file's basename becomes `previous:` in the new frontmatter. If the topic folder does not yet exist or is empty, use `previous: null`.

List available topics with `ls <project-root>/.handoff/` — each subdirectory is a topic.

### 3. Update project documentation in parallel

Before writing the handoff body, identify anything from this session that belongs in long-lived documentation — specs in `a4/spec/`, `CLAUDE.md` rules, README changes, schema references — and update those files first.

The handoff still records the session's narrative and state, but durable decisions live in durable docs. The handoff remains self-contained even if the same knowledge is also in the proper doc.

When updating wiki pages under `<project-root>/a4/`, follow the footnote protocol in `${CLAUDE_PLUGIN_ROOT}/references/obsidian-conventions.md §Wiki Update Protocol` (inline `[^N]` marker + `## Changes` definition). Any `## Changes` entry on `architecture.md` must include a `[[spec/<id>-<slug>]]` wikilink — `drift_detector` raises a `missing-spec-cite` gap otherwise.

When a spec newly cites a research artifact, never hand-edit the `spec`/`research` frontmatter or body. Run the registrar to write all four places atomically:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/register_research_citation.py" \
    "<project-root>/a4" \
    "research/<slug>" \
    "spec/<id>-<slug>"
```

### 4. Draft the handoff body

Write in **English**. Make the handoff self-contained: a fresh session should resume from this file alone without re-reading the broader codebase. Structure and sectioning follow the session's shape.

**Carry-forward items.** Whenever the handoff lists open work, in-progress items, or things the next session should pick up (typical sections: `## Open`, `## Carry-forward`, `## Where to start the next session`, "still open" tier tables), every item must be a wikilink to an on-disk tracker:

- `[[task/<id>-<slug>]]` — execution-ready or in-progress work (`status: pending | implementing`).
- `[[spec/<id>-<slug>]]` — open design question (`status: draft`).
- `[[spec/<id>-<slug>#Open Questions]]` — open question inside an active spec.
- `[[research/<slug>]]` — investigation still in flight (`status: draft`); `final` / `standalone` / `archived` artifacts are not carry-forward.

Before listing carry-forwards, sweep the session against `${CLAUDE_PLUGIN_ROOT}/references/spec-triggers.md` (B1–B6 + content-aware upward propagation) to surface any spec-worthy moment that was discussed but never authored. If a new decision is warranted, run `/a4:spec` to create the draft first, then list its wikilink as carry-forward — never leave the trigger as free-text.

Free-text carry-forward — an item that lives nowhere on disk — is forbidden. If the appropriate tracker doesn't exist yet, create it before listing the item: `/a4:task` for execution-ready work, `/a4:spec` in draft mode for an open design question, `/a4:research` for an open investigation, or add an `## Open Questions` heading to the relevant active spec. Prose around the wikilinks (one-line context, why it's still open) is fine; the wikilink itself is the carry-forward identity.

For projects without a `<project-root>/a4/` workspace, apply the rule analogously: every carry-forward must be a wikilink to an on-disk file the next session can open and update. The file's shape (a draft document, an `## Open Questions` heading on a settled doc, a SKILL/CLAUDE/README path) is the project's call. Free-text without a wikilink target is forbidden in either context.

**References vs. excerpts.** Use `[[relative/path#Heading]]` for pointers the next session should follow live. Do **not** use transclusion (`![[…]]`) — transclusion renders the *current* source, which would let a past handoff silently mutate as the source drifts. When a section genuinely needs a frozen excerpt, paste the text verbatim with a plain attribution to source path and date; the rendering format is the writer's call.

### 5. Write the handoff file

Compose the final file as:

```markdown
---
timestamp: <TIMESTAMP>
topic: <topic-slug>
previous: <prior-handoff-filename-or-null>
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at <TIMESTAMP>. To record a later state, create a new handoff file via `/a4:handoff` — never edit this one.

<draft body from step 4>
```

Write to `<project-root>/.handoff/<topic-slug>/<TIMESTAMP>_<filename-slug>.md`.

### 6. Commit

Stage the handoff together with the doc updates from step 3 and any other working-tree changes that belong to this session's scope. Create a single commit whose message describes the primary work of the session (not merely "add handoff"). Include a short reference to the handoff filename in the commit body if helpful.

Do not skip hooks, do not amend prior commits, do not force-push.

## Additional Requirements

Everything in `$ARGUMENTS` after the topic slug is treated as extra emphasis or constraints (e.g., "focus on the schema decisions", "include the reviewer feedback verbatim", "preserve the rejected-alternatives discussion"). Fold these into the relevant sections of the body rather than appending them.

$ARGUMENTS

## Output

After the commit lands, report the handoff file path and the commit SHA. Do not restate the body — the file is the record.
