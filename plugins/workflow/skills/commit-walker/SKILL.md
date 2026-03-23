---
name: commit-walker
description: "This skill should be used when the user wants to walk through git history, study commits, understand codebase evolution, or learn how a project was built. Triggers: 'walk commits', 'walk through history', 'explain commits', 'study the git log', 'how was this built', 'codebase evolution', 'commit-by-commit', 'architectural walkthrough'. Accepts an optional starting ref — omit to start from the first commit."
argument-hint: "[start-ref]"
context: fork
disable-model-invocation: true
allowed-tools: Bash(git *), Read
---

# Commit Walker — Architectural Code Study

Walk through a repository's git history one commit at a time, providing structured architectural analysis of each change. This is a **read-only** skill — it never modifies the repository.

## Step 1: Initialize

Verify the current directory is a git repository:

- `git rev-parse --is-inside-work-tree`

If this fails, stop and tell the user: "This directory is not a git repository. Please navigate to a git repo and try again."

**Determine starting point from arguments:**

`$ARGUMENTS`

- **No arguments:** Start from the very first commit on the current branch.
  - `git rev-list --reverse HEAD | head -1` — this is the starting commit.
  - `git rev-list --oneline --reverse HEAD | head -50` — list the first 50 commits.
- **With a start ref** (commit hash, tag, or branch name): Validate it, then list commits from that point forward.
  - `git rev-parse $ARGUMENTS` — validate the ref exists. If invalid, stop and tell the user.
  - `git log --oneline --reverse $ARGUMENTS..HEAD | head -50` — list up to 50 commits from that point.

Display the total commit count. If there are more than 50 commits, note: "Showing first 50 of N commits. Provide a later start-ref to see further commits."

Ask the user: "How many commits would you like to analyze per round? (default: 1)"

## Step 2: Filter Configuration

By default, trivial commits are **auto-skipped** to focus on meaningful changes.

**Default trivial-commit heuristics:**
- **Merge commits:** Excluded via `--no-merges` in git log
- **Message patterns:** Skip commits whose subject matches:
  - `^(chore|style|ci|build):` (conventional commit prefixes for non-functional changes)
  - `bump version`, `fix typo`, `formatting`, `auto-generated`, `update lock`
  - `^Merge branch`, `^Merge pull request`
- **File patterns:** Skip commits that touch ONLY:
  - Lockfiles: `*lock*`, `*.lock`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
  - Generated files: `*.min.*`, `dist/`, `build/`, `*.generated.*`
  - Config-only: `.gitignore`, `.editorconfig`, `.prettierrc`

Ask the user: "Filter mode? (default: smart filter — skip trivial commits)"
- **smart** (default): Apply the heuristics above
- **all**: Show every commit, including trivial ones
- **path `<pattern>`**: Only show commits touching files matching the pattern (e.g., `src/auth/`)
- **author `<name>`**: Only show commits by a specific author

## Step 3: Walk Loop

For each commit (or batch of N based on pace):

### 3a. Retrieve commit data

- `git show --stat --no-color <sha>` — file-level overview

**Diff strategy based on scope:**
- **5 or fewer files changed:** Show full diff — `git diff <sha>~1..<sha> --no-color`
- **More than 5 files changed:** Show `--stat` summary only. Then selectively read the full diff for files that appear architecturally significant (new modules, API changes, schema changes, config changes).
- **Large diffs (>200 lines for a single file):** Use `Read` to open the actual source file for better context rather than relying on truncated diff output.

### 3b. Apply trivial-commit filter

If the commit matches trivial heuristics and smart filter is active, briefly note:

> Skipping `<short-sha>` — "`<commit subject>`" (reason: merge/formatting/lockfile/generated)

Then continue to the next commit. Always show the skipped commit's subject line so the user can say "go back to that one" if it looks interesting.

### 3c. Analyze — 6-Section Structure

For each non-trivial commit, present a structured analysis:

#### 1. Summary
One-paragraph description of what this commit does and the intent behind it. Focus on the "why", not just the "what".

#### 2. Files Changed
List of modified files with a one-line description of each change's purpose.

#### 3. Architecture Reasoning
Why this change was structured this way. Identify design decisions, tradeoffs, and architectural implications evident in the diff. Consider: separation of concerns, coupling/cohesion, abstraction choices, dependency direction.

#### 4. Patterns & Techniques
Design patterns, coding idioms, conventions, or techniques introduced or followed in this commit. Examples: factory pattern, dependency injection, strategy pattern, middleware chain, observer pattern, etc.

#### 5. Relationship to Previous Commits
How this builds on, extends, or refactors work from previously reviewed commits. Trace the evolutionary thread — what was set up earlier that this commit depends on? What groundwork does this lay for future changes?

#### 6. Key Takeaway
The single most important lesson, insight, or principle a developer should remember from this commit.

### 3d. Navigation

After presenting the analysis, offer navigation options:

- **next** (default) — proceed to the next non-trivial commit
- **skip N** — skip ahead N commits without analysis
- **detail `<file>`** — open a specific source file from the current commit for deeper inspection
- **pace N** — change the number of commits analyzed per round
- **all** — disable filtering, show all remaining commits including trivial ones
- **stop** — end the walkthrough, proceed to session summary

## Step 4: Session End

When the user says "stop" or all commits in the list are exhausted, present a walkthrough summary:

- **Commits reviewed:** N
- **Commits skipped (trivial):** N
- **Major architectural themes:** List the recurring design patterns, architectural decisions, and structural evolution observed across all reviewed commits.
- **Codebase evolution:** Brief narrative of how the codebase grew and changed through the commits reviewed — what was the starting point, what were the major milestones, and where did it end up.

## Important: Read-Only

This skill is strictly read-only. Do NOT use any of the following git commands: `checkout`, `reset`, `commit`, `push`, `rebase`, `merge`, `cherry-pick`, `stash`, `clean`, `rm`. Only use `git log`, `git show`, `git diff`, `git rev-list`, `git rev-parse`, and similar read-only commands.
