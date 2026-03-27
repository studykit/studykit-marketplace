---
name: commit
description: "This skill should be used when the user explicitly invokes /commit. Commits staged git changes with options for single or split commits, issue prefixing, and language selection."
argument-hint: "[description] [--split] [--issue [ID]] [--lang <en|ko>]"
version: 0.1.0
disable-model-invocation: true
context: fork
model: sonnet
---

# Commit Staged Changes

Commit only the currently staged files. Never run `git add` to stage additional files.

## Argument Parsing

Parse `$ARGUMENTS` for the following options:

### Positional `description`

Any text in `$ARGUMENTS` that is not part of a flag or its value is treated as the user's description of the changes. This description provides intent context for composing the commit message.

- **Present**: Use it as the primary source for the commit message subject and body. The diff is still analyzed, but the user's description takes priority for explaining **why** the changes were made.
- **Absent**: Infer the commit message entirely from the diff (current behavior).

Examples:
- `/commit fix login redirect bug` → description is `fix login redirect bug`
- `/commit --issue PROJ-123 add retry logic for flaky API` → description is `add retry logic for flaky API`
- `/commit --split refactor auth module` → description is `refactor auth module`

### `--split`

- **Present**: Split staged changes into multiple commits grouped by semantic meaning.
- **Absent** (default): Create a single commit for all staged changes.

### `--issue [ID]`

- **`--issue PROJ-123`** (with value): Use the given ID as the issue prefix.
- **`--issue`** (no value): Auto-detect the issue number from:
  1. Current branch name (e.g., `feature/PROJ-123-add-login` → `PROJ-123`)
  2. Most recent commit message (e.g., `PROJ-123 fix: ...` → `PROJ-123`)
  - Common patterns: `PROJ-123`, `#123`, `GH-123`
  - If no issue number is found, ask the user whether to proceed without one.
- **Option absent**: No issue prefix. Do not attempt to detect one.

### `--lang <en|ko>`

- **With value**: Write commit messages in the specified language.
- **Absent**: Let the LLM decide based on context (e.g., project conventions, CLAUDE.md instructions).

## Execution Steps

### Step 0: Check recent commit style

Run:
- !`git log --oneline --no-color -5`

Use the recent commit messages as a reference for the commit message style in this project.

### Step 1: Analyze staged changes

Run:
- !`git diff --cached --no-color`

If nothing is staged, stop and tell the user: "No staged changes found. Use `git add` to stage files first."

Read the full diff to understand the nature of the changes.

### Step 2: Resolve issue prefix

Only if `--issue` is present:

- **With explicit ID**: Use it directly.
- **Without ID**: Extract an issue number from:
  - `git branch --show-current`
  - The recent commit messages from Step 0
  - If not found, ask the user whether to proceed without an issue prefix.

### Step 3: Compose commit message(s)

#### Single mode (default)

Write one commit message for all staged changes. Format:

```
[<issue-prefix> ]<subject line>

<body>
```

- Subject line: concise, imperative mood. If the user provided a description, use it to shape the subject line.
- Body: use `- ` bullet points focusing on **why** the changes were made. If the user provided a description, use it as the primary explanation of intent. If no description was given and the intent is unclear from the diff, ask the user before composing the message.
- If `--issue` resolved a prefix, prepend it to the subject line (e.g., `PROJ-123 feat: add login`).

#### Split mode (`--split`)

1. Analyze the full diff and group changes into meaningful units. A meaningful unit is a set of changes that serve a single purpose and could stand alone as a coherent commit. Grouping criteria:
   - **By intent**: bug fix, feature addition, refactoring, documentation, configuration change, test — each is a separate unit.
   - **By dependency**: if file A's changes only make sense together with file B's changes, they belong in the same unit.
   - A single file may be split across units if it contains changes serving different purposes (the patch-based approach in Step 6 preserves this).
2. For each group, compose a separate commit message following the same format as single mode.
3. Present all groups with their file lists and commit messages together.

### Step 4: Execute commit(s)

#### Single mode

Commit the already-staged files using a HEREDOC:

```bash
git commit -m "$(cat <<'EOF'
<commit message>
EOF
)"
```

#### Split mode

Use a patch-based approach to preserve hunk-level staging precision:

1. Save the staged diff as a patch:
   `git diff --cached > /tmp/commit-skill-staged.patch`
2. Unstage everything:
   `git reset HEAD`
3. For each group, in order:
   a. Apply only that group's files from the patch:
      `git apply --cached --include='<file path>' /tmp/commit-skill-staged.patch`
      (repeat `--include='<path>'` for each file in the group)
   b. Commit:
      `git commit -m "$(cat <<'EOF'
      <commit message>
      EOF
      )"`
4. After all commits, clean up:
   `rm /tmp/commit-skill-staged.patch`
5. Show the result:
   `git log --oneline -<N>` (where N = number of commits created)

If any step fails, restore the original staging from the patch and report the error:
```bash
git apply --cached /tmp/commit-skill-staged.patch
rm /tmp/commit-skill-staged.patch
```

## Key Principles

- **Never stage additional files** — only commit what the user has already staged.
- **Use HEREDOC** for multi-line commit messages to preserve formatting.
- **Respect project commit conventions** — when composing messages, also apply any commit conventions defined in the project's CLAUDE.md (e.g., trailers, conventional commit format).
