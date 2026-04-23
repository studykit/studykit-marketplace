---
name: handoff
description: "This skill should be used when the user explicitly invokes /handoff. Write a session handoff file so a fresh Claude Code session can resume the current work."
argument-hint: "[additional requirements]"
disable-model-invocation: true
---

# Session Handoff

Write a handoff file that captures everything a fresh Claude Code session needs to continue the current work. The current session will end after this.

## Context

- Timestamp: !`date +"%Y-%m-%d_%H%M"`

## Task

1. **Update project docs.** Identify anything from this session that belongs in long-lived documentation — architectural decisions, design rationale, new conventions, decision records, CLAUDE.md rules, README changes — and update those docs. This runs in parallel with the handoff, not instead of it: the handoff remains self-contained even if the same knowledge also lives in the proper doc.
2. Create a new file at `.handoff/<TIMESTAMP>.md` using the value from Context. **Never overwrite an existing handoff file** — if one exists at the same timestamp, append a short suffix (e.g., `_2`).
3. Write the handoff **in English**. Make it self-contained: the next session should be able to resume from this file alone, without reconstructing prior conversation or broadly exploring the codebase.
4. Commit the handoff together with the doc updates and any other pending working-tree changes.

## Additional Requirements

Treat `$ARGUMENTS` as extra emphasis or constraints from the user (e.g., "focus on the auth refactor", "include the failing test outputs verbatim"). Incorporate these into the relevant sections rather than tacking them on at the end.

$ARGUMENTS

## File Format

Every handoff file must begin with this banner so future sessions know not to edit it:

```markdown
> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at <TIMESTAMP>. To record a later state, create a new handoff file via `/handoff` — never edit this one.
```

Below the banner, let the session shape the document. Structure and sections are your judgment call.

## Output

After writing the file and creating the commit, tell the user the handoff file path and the commit SHA. Do not restate the contents.
