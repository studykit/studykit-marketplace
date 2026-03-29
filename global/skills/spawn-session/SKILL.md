---
name: spawn-session
description: This skill should be used when the user says "/spawn-session", "spawn a session", "open a new session", "split this off", "delegate this to another session", or wants to spin off a sub-task into a dedicated child Claude Code session in a new iTerm2 tab.
---

# Spawn Child Session

Spawn a child Claude Code session in a new iTerm2 tab. Walk through each step conversationally — ask one question at a time, then execute via the bundled script.

## Gather Information

### Step 1 — Topic

Ask: **What is the topic or purpose for this child session?**

This becomes the tab title and the `topic` field. Keep it short (a few words).

If `$ARGUMENTS` is provided, use the first argument as the topic and skip asking.

### Step 2 — Skill (optional)

Ask: **Should a skill be injected into the child session?** (e.g., `co-think-architecture`, `co-think-domain`)

Omit the `--skill` flag if the user declines or is unsure.

### Step 3 — Reference Files

Ask: **Are there any files the child session should be aware of?**

Suggest files from the current conversation context that seem relevant. The user can confirm, add, or skip.

### Step 4 — Context Summary

Generate a concise context summary from the conversation so far — what the child session needs to know to pick up the sub-task. Present it to the user for approval or edits.

### Step 5 — Result Patterns (optional)

Ask: **What files do you expect the child session to produce?** (glob patterns, e.g., `docs/*.md`, `src/feature/**/*.ts`)

Omit the `--result-patterns` flag if the user declines or is unsure.

## Execute

Confirm the spawn details with the user, then execute via Bash:

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/spawn-session.sh" \
  --session-id "${CLAUDE_SESSION_ID}" \
  --topic "<TOPIC>" \
  --skill "<SKILL>" \
  --reference-files "<file1.md,file2.md>" \
  --context-summary "<SUMMARY>" \
  --result-patterns "<pattern1,pattern2>"
```

Omit optional flags (`--skill`, `--reference-files`, `--result-patterns`) if not provided. `--session-id` and `--topic` are required. Quote all string values for shell safety.

**Important:** Do not create separate prompt files or run `claude` directly — the script handles session-tree.json registration and context injection via the bootstrap hook.

After execution, report the child session ID and confirm the tab was opened.

## Check Status

To check on existing child sessions:

```bash
export SESSION_TREE=".claude/sessions/${CLAUDE_SESSION_ID}/session-tree.json"
source global/hooks/lib/session-tree.sh
st_read | jq '.children[] | {id, topic, status, resultFiles}'
```
