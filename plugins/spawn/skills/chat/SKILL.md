---
name: chat
description: This skill should be used when the user says "/chat", "spawn a session", "open a new session", "split this off", "delegate this to another session", "resume a session", or wants to spin off a sub-task into a dedicated child Claude Code session in a new iTerm2 tab.
---

# Spawn or Resume Child Session

Spawn a child Claude Code session in a new iTerm2 tab, or resume an existing one. Walk through each step conversationally — ask one question at a time, then execute via the bundled script.

**Important:** This skill can only be used from the main session. If `$SESSION_TREE` is set and the current session is a child session, inform the user that child sessions cannot spawn further children.

## Resume Flow

If the user wants to resume an existing session (e.g., "resume design-review", "reopen api-spec"), skip the gather steps and execute directly:

```bash
uv run "${CLAUDE_SKILL_DIR}/scripts/spawn_session.py" \
  --session-id "${CLAUDE_SESSION_ID}" \
  --resume "<TOPIC>"
```

## Spawn Flow — Gather Information

### Step 1 — Topic

Ask: **What is the topic or purpose for this child session?**

This becomes the tab title and the `topic` field. Keep it short (a few words).

If `$ARGUMENTS` is provided, use the first argument as the topic and skip asking.

### Step 2 — Persona

Use AskUserQuestion to let the user pick a persona for the child session.

- header: `Persona`
- question: "Which persona should the child session use?"
- options: `discuss` (Focused discussion partner — thinks through problems conversationally). Include other personas available in `prompts/` if any.
- multiSelect: false

Default to `discuss` if the user doesn't have a strong preference.

### Step 3 — Reference Files

Use AskUserQuestion to let the user select reference files.

- header: `Files`
- question: "Which files should the child session be aware of?"
- options: Pick up to 4 relevant file paths mentioned in the conversation. Use short relative paths as labels. Do NOT read the files — just pass paths.
- multiSelect: true

If the user selects nothing, omit the `--reference-files` flag.

### Step 4 — Context Summary

Generate concise context from the conversation so far — what the child session needs to know to pick up the sub-task. This becomes the `--bootstrap-prompt-snippet` value.

## Execute

Confirm the spawn details with the user, then execute via Bash:

```bash
uv run "${CLAUDE_SKILL_DIR}/scripts/spawn_session.py" \
  --session-id "${CLAUDE_SESSION_ID}" \
  --topic "<TOPIC>" \
  --persona "<PERSONA>" \
  --reference-files "<file1.md,file2.md>" \
  --bootstrap-prompt-snippet "<SUMMARY>"
```

Omit optional flags (`--persona`, `--reference-files`, `--bootstrap-prompt-snippet`) if not provided. `--session-id` and `--topic` are required. Quote all string values for shell safety.

**Important:** Do not create separate prompt files or run `claude` directly — the script handles session-tree.json registration, prompt generation, and iTerm2 launch.

After execution, report the child session ID and confirm the tab was opened.
