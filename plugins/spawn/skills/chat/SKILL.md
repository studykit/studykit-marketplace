---
name: chat
description: This skill should be used when the user says "/chat", "spawn a session", "open a new session", "split this off", "delegate this to another session", or wants to spin off a sub-task into a dedicated child Claude Code session in a new iTerm2 tab.
---

# Spawn Child Session

Spawn a child Claude Code session in a new iTerm2 tab. Walk through each step conversationally — ask one question at a time, then execute via the bundled script.

## Gather Information

### Step 1 — Topic

Ask: **What is the topic or purpose for this child session?**

This becomes the tab title and the `topic` field. Keep it short (a few words).

If `$ARGUMENTS` is provided, use the first argument as the topic and skip asking.

### Step 2 — Skill (optional)

Use AskUserQuestion to let the user pick a skill to inject into the child session.

- header: `Skill`
- question: "Should a skill be injected into the child session?"
- options: Pick up to 4 relevant skills from the available skill list. Always include a "None" option (description: "No skill — plain session").
- multiSelect: false

If the user selects "None" or "Other" with no input, omit the `--skill` flag.

### Step 3 — Reference Files

Use AskUserQuestion to let the user select reference files.

- header: `Files`
- question: "Which files should the child session be aware of?"
- options: Pick up to 4 relevant file paths mentioned in the conversation. Use short relative paths as labels. Do NOT read the files — just pass paths.
- multiSelect: true

If the user selects "Other", they can add additional file paths as free text. If the user selects nothing, omit the `--reference-files` flag.

### Step 4 — Additional Context

Generate concise additional context from the conversation so far — what the child session needs to know to pick up the sub-task.

### Step 5 — Result Patterns (optional)

Use AskUserQuestion to let the user specify expected output files.

- header: `Output`
- question: "What files do you expect the child session to produce?"
- options: Infer up to 3 likely patterns from the topic/context (e.g., `docs/*.md`, `src/**/*.ts`). Always include a "None" option (description: "No expected output — discussion only").
- multiSelect: true
- Tell the user: "The child session may also produce result files depending on your conversation."

If the user selects "None", omit the `--result-patterns` flag.

## Execute

Confirm the spawn details with the user, then execute via Bash:

```bash
uv run "${CLAUDE_SKILL_DIR}/scripts/spawn_session.py" \
  --session-id "${CLAUDE_SESSION_ID}" \
  --topic "<TOPIC>" \
  --skill "<SKILL>" \
  --reference-files "<file1.md,file2.md>" \
  --additional-context "<SUMMARY>" \
  --result-patterns "<pattern1,pattern2>"
```

Omit optional flags (`--skill`, `--reference-files`, `--additional-context`, `--result-patterns`) if not provided. `--session-id` and `--topic` are required. Quote all string values for shell safety.

**Important:** Do not create separate prompt files or run `claude` directly — the script handles session-tree.json registration and context injection via the bootstrap hook.

After execution, report the child session ID and confirm the tab was opened.