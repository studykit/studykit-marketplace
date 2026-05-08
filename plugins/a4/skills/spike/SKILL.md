---
name: spike
description: "Author a time-boxed exploration spike."
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

If the project root resolved to `NOT_A_GIT_REPO` or `a4/` is missing, abort. Ensure `<project-root>/a4/spike/` exists (`mkdir -p` if missing).

## Author

Allocate the next id immediately before writing; use it as `id:` and the filename prefix. Follow `${CLAUDE_PLUGIN_ROOT}/authoring/spike-authoring.md` for frontmatter, body shape, initial-status rules, and the `done` preflight. Write to `a4/spike/<id>-<slug>.md`. `implements:` / `spec:` / `cycle:` are forbidden — cite triggering UCs or specs from `## Description` body prose with markdown links if relevant.

Ask the user once whether to create the artifact directory at `<project-root>/artifacts/spike/<id>-<slug>/`. If yes, `mkdir -p` it after the file is written; a `.gitkeep` is optional. No commit; no implementation agent spawn.
