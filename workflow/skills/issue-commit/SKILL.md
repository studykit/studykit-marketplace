---
name: issue-commit
description: "Create a GitHub issue from staged changes (or link to an existing one) and commit with an issue reference. Accepts an optional issue number (e.g., /issue-commit #42) to skip issue creation."
argument-hint: "[#issue-number]"
disable-model-invocation: true
agent: Explore
context: fork
allowed-tools: Bash(git *), Bash(gh *), Agent, mcp__github__issue_write
---

# Issue + Commit Workflow

Create a GitHub issue (or use an existing one) and commit with issue reference. Every commit must have an associated issue — issue-less commits are not supported.

## Step 1: Analyze staged changes
- !`git remote get-url origin` — repository remote URL
- !`git diff --cached --stat --no-color`

Use the context diff provided above together with the stat output to understand the changes. If nothing is staged, stop and tell the user to stage files first (`git add`).

## Step 2: Create or resolve GitHub issue

- !`git diff --cached --no-color`

**Arguments received:** `$ARGUMENTS`

**If an issue number is present above** (e.g., `#42`), skip issue creation and proceed to Step 3 with that issue number.

**If no issue number is present** (arguments are empty), first check recent commits for a related issue:

- !`git log --oneline -3`

Scan commit messages for issue references (`#123`, `GH-123`, `owner/repo#123`, or full GitHub issue URLs). If a recent commit references an issue that covers the same topic as the current staged changes, suggest reusing that issue number and confirm with the user before proceeding.

If no related issue is found, create a new issue. Prefer GitHub MCP `mcp__github__issue_write`; if MCP is unavailable, fall back to `gh issue create`. Write in English.

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

If the intent behind the staged changes is unclear from the diff alone, ask the user: **"What is the intent of these changes?"** and use their answer to write a more accurate commit message.

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

## Key principles

- **Issue** = high-level purpose (Summary only)
- **Commit message** = code-level implementation details
- No duplication between issue body and commit message
- Never commit files that might contain secrets
