---
name: issue-commit
description: "This skill should be used when the user invokes /issue-commit. Create a GitHub issue from staged changes (or link to an existing issue), commit with issue reference, push, and add an issue comment with changes and commit SHA. Accepts an optional issue number argument (e.g., /issue-commit #42)."
disable-model-invocation: true
allowed-tools: Bash(git *), Bash(gh *)
---

# Issue + Commit Workflow

Create a GitHub issue (or use an existing one), commit with issue reference, push, then add a comment to the issue with changes and commit SHA. Every commit must have an associated issue — issue-less commits are not supported.

When an issue number is provided as an argument (e.g., `/issue-commit #42` or `/issue-commit 42`), skip issue creation and use the given issue number for the commit and comment steps.


## Step 1: Analyze staged changes
- !`git remote get-url origin` — repository remote URL
- !`git diff --cached --stat --no-color`

Use the context diff provided above together with the stat output to understand the changes. If nothing is staged, stop and tell the user to stage files first (`git add`).

## Step 2: Create or resolve GitHub issue

- !`git diff --cached --no-color`

**If an issue number was provided as an argument**, skip issue creation and proceed to Step 3 with that issue number.

**If no issue number was provided**, create a new issue. Prefer GitHub MCP `issue_write`; if MCP is unavailable, fall back to `gh issue create`. Write in English.

**Title**: Short, action-oriented (under 70 chars).

**Body**: Summary section only — high-level description of what this work enables. No code details.

```
## Summary
<1-3 sentences: what the work enables or solves, from a user/system perspective>
```

**Example**:
```
Title: Add Codex CLI as LLM provider

## Summary
Add OpenAI Codex CLI as a third LLM provider option, enabling codex exec subprocess-based queries for translation and vocabulary generation alongside the existing Claude and Copilot providers.
```

## Step 3: Commit with issue reference

Commit the already-staged files as-is. Do NOT stage additional files or run `git add`. Use a HEREDOC to pass the multi-line commit message.

**Format**:
```
#<issue-number> <short title>

- <code-level change: what was modified/added and technical rationale>
- <code-level change>
```

The body lines describe concrete code changes with enough technical detail that an LLM can understand the implementation without reading the diff.

**Example**:
```
#10 Add Codex CLI as LLM provider with codex exec subprocess integration

- Add CodexProvider class using asyncio subprocess to call codex exec with --output-schema for structured queries and --json for streaming
- Register codex in LLMProviderType literal and provider factory
- Add codex_default_model and codex_timeout settings to server config
- Add CODEX_MODEL_PRESETS and codex option to AI settings provider selector
- Install Node.js 22 and @openai/codex in Dockerfile, mount ~/.codex/auth.json
```

## Step 4: Push and capture commit SHA

```bash
git push
git rev-parse HEAD
```

Capture the full commit SHA from `git rev-parse HEAD` for use in the issue comment.

## Step 5: Add issue comment

After push, add a comment to the issue with the Changes details and commit SHA. Prefer GitHub MCP `add_issue_comment`; if MCP is unavailable, fall back to `gh issue comment`.

```
## Changes
- <Module/area>: <code-level change description>
- <Module/area>: <code-level change description>

Commit: <full-commit-sha>
```

**Example**:
```
## Changes
- Server: Add CodexProvider class with codex exec subprocess for structured and streaming queries
- Server config: Register codex in LLMProviderType, add codex_default_model and codex_timeout
- Chrome Extension: Add CODEX_MODEL_PRESETS and codex option to AI settings UI
- Docker: Install Node.js 22 and @openai/codex, mount auth.json

Commit: 165afe3abc123def456...
```

## Key principles

- **Issue** = high-level purpose (Summary only)
- **Commit message** = code-level implementation details
- **Issue comment** = changes by module + commit SHA link
- No duplication between issue body and commit message
- Never commit files that might contain secrets
