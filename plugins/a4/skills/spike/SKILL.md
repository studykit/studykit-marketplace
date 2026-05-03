---
name: spike
description: "This skill should be used when the user wants to author a single spike task — a time-boxed exploration to unblock a decision (XP sense). PoC, investigation, benchmark — throwaway code. Common triggers: 'spike on X', 'add a spike', 'create a spike for', 'I need a quick PoC', 'investigate X technically before deciding', 'time-box an exploration'. Writes a4/spike/<id>-<slug>.md and proposes a project-root artifacts/spike/<id>-<slug>/ artifact directory for the throwaway code. `implements:` / `spec:` / `cycle:` are forbidden on spike. For pure written investigation without throwaway code, use /a4:research instead. Single-task entry. To discard a task use /a4:discard."
argument-hint: "[title or short description]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, TaskCreate, TaskUpdate, TaskList, WebSearch, WebFetch
---

# Single Spike Task Author

Writes one `a4/spike/<id>-<slug>.md` per the authoring contract at `${CLAUDE_PLUGIN_ROOT}/authoring/spike-authoring.md`, plus an optional artifact directory at `<project-root>/artifacts/spike/<id>-<slug>/` for throwaway PoC code. No special procedure beyond the contract; this skill is a thin wrapper.

Seed: **$ARGUMENTS**

## Context

- Project root: !`git rev-parse --show-toplevel 2>/dev/null || echo NOT_A_GIT_REPO`
- Today: !`date +%Y-%m-%d`
- Allocated id: !`"${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4" 2>/dev/null || echo ALLOC_FAILED`

If the project root resolved to `NOT_A_GIT_REPO` or `a4/` is missing, abort. Ensure `<project-root>/a4/spike/` exists (`mkdir -p` if missing).

## Author

Use the allocated id above as `id:` and the filename prefix. Follow `${CLAUDE_PLUGIN_ROOT}/authoring/spike-authoring.md` for frontmatter, body shape, initial-status rules, and the `done` preflight. Write to `a4/spike/<id>-<slug>.md`. `implements:` / `spec:` / `cycle:` are forbidden — cite triggering UCs or specs from `## Description` body prose with markdown links if relevant.

Ask the user once whether to create the artifact directory at `<project-root>/artifacts/spike/<id>-<slug>/`. If yes, `mkdir -p` it after the file is written; a `.gitkeep` is optional. No commit; no implementation agent spawn.
