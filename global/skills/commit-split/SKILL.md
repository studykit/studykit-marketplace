---
name: commit-split
description: "Split staged changes into semantic commits."
argument-hint: "[description] [--issue [ID]] [--lang <en|ko>]"
version: 0.1.0
disable-model-invocation: true
context: fork
model: sonnet
---

# Split-Commit Staged Changes

## Context

- Recent commit style: !`git log --oneline --no-color -5`
- Staged changes: !`git diff --cached --no-color`
- Current branch: !`git branch --show-current`

## Arguments

Parse `$ARGUMENTS` for:

- **Positional `description`**: Any text not part of a flag. Use as the primary source for understanding overall intent. If absent, infer from the diff.
- **`--issue [ID]`**: With value → use as prefix. Without value → auto-detect from branch name or recent commits (`PROJ-123`, `#123`, `GH-123`). If not found, ask user. If absent → no prefix.
- **`--lang <en|ko>`**: Write commit messages in specified language. If absent, decide based on context.

## Task

If nothing is staged, stop: "No staged changes found. Use `git add` to stage files first."

Never stage additional files. Split staged changes into multiple semantically grouped commits.

### Commit message format

```
[<issue-prefix> ]<subject line>

<body>
```

- Subject: concise, imperative mood. Informed by user description if provided.
- Body: `- ` bullet points focusing on **why**.
- Match the project's commit style. Respect any conventions in CLAUDE.md.
- Use HEREDOC for commit messages.

### Execution

Use a temporary branch to safeguard staged content:

1. **Backup**: Create temp branch and commit all staged changes:
   - `git checkout -b _commit-split-backup`
   - `git commit -m "backup"`
2. **Return**: Switch back and unstage:
   - `git checkout -` (back to original branch)
   - `git reset HEAD`
3. **Split**: For each group, selectively stage and commit:
   - `git checkout _commit-split-backup -- <path>` (repeat per file) then `git reset HEAD` + `git add <paths>`
   - `git commit -m "$(cat <<'EOF'` ... `EOF`)"`
4. **Cleanup**: `git branch -D _commit-split-backup`
5. **Verify**: `git log --oneline -<N>`

On failure, restore from backup and report:
```bash
git reset HEAD
git checkout _commit-split-backup -- .
git add .
git branch -D _commit-split-backup
```
