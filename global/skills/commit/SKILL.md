---
name: commit
description: "Use on explicit /commit. Commit staged git changes; supports issue prefixes and language selection."
argument-hint: "[description] [--issue [ID]] [--lang <en|ko>]"
version: 0.1.0
disable-model-invocation: true
context: fork
model: sonnet
---

# Commit Staged Changes

## Context

- Recent commit style: !`git log --oneline --no-color -5`
- Staged changes: !`git diff --cached --no-color`
- Current branch: !`git branch --show-current`

## Arguments

Parse `$ARGUMENTS` for:

- **Positional `description`**: Any text not part of a flag. Use as the primary source for the commit message. If absent, infer from the diff.
- **`--issue [ID]`**: With value → use as prefix. Without value → auto-detect from branch name or recent commits (`PROJ-123`, `#123`, `GH-123`). If not found, ask user. If absent → no prefix.
- **`--lang <en|ko>`**: Write commit message in specified language. If absent, decide based on context.

## Task

If nothing is staged, stop: "No staged changes found. Use `git add` to stage files first."

Based on the staged changes, create a single git commit. Never stage additional files. Never split into multiple commits — use `/commit-split` for that.

Call multiple tools in a single response. Stage and create the commit using a single message. Do not use any other tools or do anything else. Do not send any other text or messages besides the tool calls.

### Commit message format

```
[<issue-prefix> ]<subject line>

<body>
```

- Subject: concise, imperative mood. Shaped by user description if provided.
- Body: `- ` bullet points focusing on **why**. If no description and intent is unclear, ask first.
- Match the project's commit style from recent commits.
- Respect any commit conventions in the project's CLAUDE.md.
- Use HEREDOC for the commit message.
