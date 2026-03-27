---
name: commit
description: "This skill should be used when the user explicitly invokes /commit. Commits staged git changes with options for single or split commits, issue prefixing, and language selection."
argument-hint: "[--split] [--issue [ID]] [--lang <en|ko>]"
version: 0.1.0
disable-model-invocation: true
context: fork
model: sonnet
---

# Commit Staged Changes

Commit only the currently staged files. Never run `git add` to stage additional files.

## Argument Parsing

Parse `$ARGUMENTS` for the following options:

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

- Subject line: concise, imperative mood.
- Body: explain what was changed and why.
- If `--issue` resolved a prefix, prepend it to the subject line (e.g., `PROJ-123 feat: add login`).

#### Split mode (`--split`)

1. Analyze the full diff and group changes into meaningful units. A meaningful unit is a set of changes that serve a single purpose and could stand alone as a coherent commit. Grouping criteria:
   - **By intent**: bug fix, feature addition, refactoring, documentation, configuration change, test — each is a separate unit.
   - **By dependency**: if file A's changes only make sense together with file B's changes, they belong in the same unit.
   - **By scope**: changes to unrelated modules or subsystems should be separate units even if they share the same intent (e.g., two independent bug fixes).
   - A single file may be split across units if it contains changes serving different purposes (the patch-based approach in Step 6 preserves this).
2. For each group, compose a separate commit message following the same format as single mode.
3. Present all groups with their file lists and commit messages together.

### Step 4: Preview and confirm

Display the commit plan to the user:

**For single mode:**
```
## Commit Preview

**Files:**
- path/to/file1.ts
- path/to/file2.ts

**Message:**
<commit message>

Proceed? (y/n)
```

**For split mode:**
```
## Commit Preview

### Commit 1 of N
**Files:**
- path/to/file1.ts

**Message:**
<commit message>

### Commit 2 of N
**Files:**
- path/to/file2.ts

**Message:**
<commit message>

Proceed? (y/n)
```

Wait for user approval. If the user requests changes, revise and show the preview again.

### Step 5: Execute commit(s)

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
- **Always preview before committing** — no silent commits.
- **Use HEREDOC** for multi-line commit messages to preserve formatting.
- **Respect project commit conventions** — when composing messages, also apply any commit conventions defined in the project's CLAUDE.md (e.g., trailers, conventional commit format).
