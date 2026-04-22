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

1. Ensure the directory `.handoff/` exists (already created at skill load).
2. Create a new file at `.handoff/<TIMESTAMP>.md` where `<TIMESTAMP>` is the value from Context above (format `YYYY-MM-DD_HHmm`).
3. Write the handoff content **in English**, drawing from the current conversation and any open plans or tasks.
4. **Never overwrite or modify an existing handoff file.** If a file with the same timestamp already exists, append a short suffix (e.g., `_2`) and create a new one.

## Additional Requirements

Treat `$ARGUMENTS` as extra emphasis or constraints from the user (e.g., "focus on the auth refactor", "include the failing test outputs verbatim"). Incorporate these into the relevant sections rather than tacking them on at the end.

$ARGUMENTS

## File Format

Every handoff file must begin with this banner so future sessions know not to edit it:

```markdown
> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at <TIMESTAMP>. To record a later state, create a new handoff file via `/handoff` — never edit this one.
```

Below the banner, write whatever the next session actually needs — structure and sections are up to you. Let the session shape the document, not a template.

Prioritize context that cannot be recovered by looking at the current repo state. In particular, capture:

- **Intent** — what the user is ultimately trying to accomplish, beyond the immediate task.
- **Decisions and their rationale** — what was chosen, and *why* that option beat the alternatives.
- **Reversals** — decisions that were made and later changed, with the reason for the change. A new session that only sees the latest state will otherwise repeat the discarded path.
- **Approaches tried and rejected** — so the next session doesn't redo dead ends.
- **Blockers and open questions** — what is stuck, and what information would unblock it.
- **Next concrete actions** — specific enough to act on without guessing.
- **User statements worth preserving** — preferences, constraints, or context the user gave verbally that would otherwise be lost when the conversation ends.

## Output

After writing the file, tell the user the file path in one short sentence. Do not restate the contents.
