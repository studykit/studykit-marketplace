---
name: handoff
description: "This skill should be used when the user explicitly invokes /handoff inside a project that uses the a4 plugin's a4/ workflow. Writes a topic-threaded session handoff at <project-root>/.handoff/<topic>/ and snapshots any referenced a4/ sections in place via ![[...]] embed directives resolved at write time."
argument-hint: "<topic-slug> [additional emphasis]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Session Handoff (a4 plugin)

Writes a session handoff so a fresh Claude Code session can resume the current topic thread without reconstructing prior conversation. Complements the global `/handoff` skill — this plugin variant enforces a topic-threaded schema (`topic` / `previous` / `timestamp`) and embeds referenced `a4/` sections at write time so each handoff is a self-contained snapshot.

Invocation: `/a4:handoff <topic-slug> [additional emphasis]`. The plugin namespace prefix (`a4:`) disambiguates from the global `/handoff`; no prefix is needed inside the skill slug itself.

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

You can list available topics with `ls <project-root>/.handoff/` — each subdirectory is a topic.

### 3. Update project documentation in parallel

Before writing the handoff body, identify anything from this session that belongs in long-lived documentation — ADRs in `a4/decision/`, `CLAUDE.md` rules, README changes, schema references — and update those files first.

The handoff still records the session's narrative and state, but durable decisions live in durable docs. The handoff remains self-contained even if the same knowledge is also in the proper doc.

### 4. Draft the handoff body

Write in **English**. Make the handoff self-contained: a fresh session should resume from this file alone without re-reading the broader codebase. Structure and sectioning are your judgment call — let the session shape the document.

**Embed directives.** When the handoff needs to reproduce an `a4/` section at length (ADR excerpt, plan snippet, review report, relevant wiki section), use an Obsidian embed directive rather than copy-pasting:

- `![[relative/path#Heading Text]]` — embed the named heading section.
- `![[relative/path]]` — embed the whole file.

Paths are relative to the project root. The `.md` extension may be omitted (Obsidian convention). Plain wikilinks `[[...]]` (no leading `!`) remain as references and are not expanded.

Embeds are resolved at **write time** — the directive is replaced inline with the referenced content, wrapped in `<!-- injected: path#heading @ YYYY-MM-DD -->` / `<!-- /injected -->` markers for audit trail. This preserves handoff immutability: future changes to the embedded file will not retroactively alter past handoffs.

### 5. Expand embed directives

Write the draft body to a temp file, then run:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/inject_includes.py" <temp-draft> \
    --base-dir "<project-root>" \
    --date "<today>"
```

The command prints the expanded body to stdout — capture it. Non-zero exit means a referenced file or heading was not found. Fix the directive (or the referenced document) and retry; do not write a partially-expanded handoff.

### 6. Write the handoff file

Compose the final file as:

```markdown
---
timestamp: <TIMESTAMP>
topic: <topic-slug>
previous: <prior-handoff-filename-or-null>
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at <TIMESTAMP>. To record a later state, create a new handoff file via `/a4:handoff` — never edit this one.

<expanded body from step 5>
```

Write to `<project-root>/.handoff/<topic-slug>/<TIMESTAMP>_<filename-slug>.md`.

### 7. Commit

Stage the handoff together with the doc updates from step 3 and any other working-tree changes that belong to this session's scope. Create a single commit whose message describes the primary work of the session (not merely "add handoff"). Include a short reference to the handoff filename in the commit body if helpful.

Do not skip hooks, do not amend prior commits, do not force-push.

## Additional Requirements

Everything in `$ARGUMENTS` after the topic slug is treated as extra emphasis or constraints (e.g., "focus on the schema decisions", "include the reviewer feedback verbatim", "preserve the rejected-alternatives discussion"). Fold these into the relevant sections of the body rather than appending them.

$ARGUMENTS

## Output

After the commit lands, report the handoff file path and the commit SHA. Do not restate the body — the file is the record.
