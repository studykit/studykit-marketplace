---
name: obsidian-cli
description: >-
  This skill should be used when the user asks to "run an obsidian command",
  "use obsidian cli", "automate obsidian from terminal", "obsidian command line",
  "create note from terminal", "search vault from cli", "manage obsidian plugins via cli",
  "obsidian shell command", or mentions terminal/CLI-based Obsidian vault operations.
argument-hint: <what to do, e.g. "append a task to today's daily note", "search vault for meeting notes", "list all tags with counts">
---

# Obsidian CLI Command Generator

Generate an Obsidian CLI command for: **$ARGUMENTS**

## Overview

The Obsidian CLI enables terminal-based control of the Obsidian application — file operations, search, property management, plugin control, sync, and more. It requires Obsidian 1.12.4+ with CLI registered via Settings > General > "Command line interface". The application must be running for commands to execute.

For platform-specific installation instructions, consult `references/setup.md`.

## Command Structure

All commands follow the pattern:

```bash
obsidian <command> [parameters] [flags]
```

- **Parameters**: `key=value` format. Quote values containing spaces: `content="my text here"`.
- **Flags**: Boolean switches included without values (e.g., `--copy`, `total`, `verbose`).
- **Multiline content**: Use `\n` for newlines, `\t` for tabs within `content=` values.
- **Vault targeting**: Prepend `vault=<name>` (must be the first parameter) when multiple vaults exist.

### File Targeting

Two approaches to identify files:

| Method | Syntax | Behavior |
|--------|--------|----------|
| By name | `file=<name>` | Wikilink-style resolution (no extension needed) |
| By path | `path=<path>` | Exact path from vault root |

When the user provides a note name without extension, use `file=`. When an exact path is given, use `path=`.

## Command Generation Workflow

### Step 1: Classify Intent

Map the user's request to one of these command categories:

| Category | Use When | Key Commands |
|----------|----------|--------------|
| **Daily Notes** | Daily note operations | `daily`, `daily:append`, `daily:prepend`, `daily:read`, `daily:path` |
| **File Operations** | Creating, reading, editing, moving, deleting notes | `create`, `read`, `append`, `prepend`, `open`, `move`, `rename`, `delete` |
| **Search** | Finding content across the vault | `search`, `search:context`, `search:open` |
| **Tasks** | Listing or toggling task checkboxes | `tasks`, `task` |
| **Tags** | Browsing tags and tag usage | `tags`, `tag` |
| **Links** | Analyzing vault link structure | `backlinks`, `links`, `unresolved`, `orphans`, `deadends` |
| **Properties** | Reading, setting, or removing frontmatter properties | `properties`, `property:set`, `property:read`, `property:remove` |
| **Plugins** | Installing, enabling, disabling plugins | `plugins`, `plugin:enable`, `plugin:disable`, `plugin:install`, `plugin:uninstall` |
| **Sync & History** | File history, sync status, restoring versions | `history`, `sync`, `diff` |
| **Vault Info** | Vault metadata, file/folder listing | `vault`, `vaults`, `files`, `folders`, `folder` |
| **Workspace** | Managing workspace layouts | `workspace:save`, `workspace:load`, `workspaces` |
| **Templates** | Listing or inserting templates | `templates`, `template:read`, `template:insert` |
| **Developer** | Debugging, screenshots, eval | `devtools`, `eval`, `dev:screenshot`, `dev:console` |

For the complete command reference with all parameters, consult `references/commands.md`.

### Step 2: Build the Command

Construct the command by combining:

1. **Base command** from the category above
2. **Required parameters** (marked as "required" in the reference)
3. **Optional parameters** only when the user's request specifies them
4. **Output flags** (`total`, `verbose`, `format=json|tsv|csv`) when structured output is needed

#### Common Patterns

**Append content to a note:**
```bash
obsidian append file="Meeting Notes" content="- Action item from standup\n- Follow up with team"
```

**Create a note from template:**
```bash
obsidian create name="Weekly Review" template="Weekly Template" open
```

**Search with context:**
```bash
obsidian search:context query="project deadline" limit=5 format=json
```

**Set a frontmatter property:**
```bash
obsidian property:set file="My Note" name=status value=done type=text
```

**List tasks from daily note:**
```bash
obsidian tasks daily todo
```

**Toggle a specific task:**
```bash
obsidian task ref="Projects/TODO.md:15" toggle
```

**Install and enable a plugin:**
```bash
obsidian plugin:install id=dataview enable
```

**Get vault statistics:**
```bash
obsidian vault info=size
obsidian files total
```

### Step 3: Handle Multi-Step Operations

Some user requests require chaining multiple commands. Present them as a numbered sequence:

**Example — Create a note and set properties:**
```bash
# 1. Create the note
obsidian create name="Sprint Planning" content="# Sprint 42\n\n## Goals\n"

# 2. Set properties
obsidian property:set path="Sprint Planning.md" name=type value=meeting type=text
obsidian property:set path="Sprint Planning.md" name=date value=2025-01-15 type=date
```

**Example — Daily workflow:**
```bash
# 1. Open today's daily note
obsidian daily

# 2. Append morning tasks
obsidian daily:append content="## Morning Tasks\n- [ ] Review PRs\n- [ ] Standup notes"

# 3. Check incomplete tasks
obsidian tasks daily todo
```

### Step 4: Script Integration

When the user needs CLI commands within shell scripts or automation pipelines, apply these patterns:

- **Capture output**: Use `--copy` flag to copy output to clipboard, or pipe stdout.
- **JSON output**: Add `format=json` for machine-parseable results.
- **Conditional logic**: Use `total` flag to get counts for conditionals.
- **Error handling**: Commands exit with non-zero status on failure.

```bash
# Count unresolved links
count=$(obsidian unresolved total)
echo "Unresolved links: $count"

# Export search results as JSON
obsidian search query="TODO" format=json > todos.json

# Batch property update
for file in $(obsidian files folder="Projects" ext=md); do
  obsidian property:set path="$file" name=reviewed value=false type=checkbox
done
```

## Output Template

Present generated commands in this format:

```bash
obsidian <command> [parameters] [flags]
```

**Explanation:**
- State what the command does
- Note any required prerequisites (e.g., plugin must be installed, vault must be specified)
- For multi-step operations, explain the sequence and dependencies

When the command produces output, describe the expected result format (plain text, JSON, TSV, etc.).

## Edge Cases

- **Multiple vaults** — Always include `vault=<name>` as the first parameter when the user has multiple vaults or specifies a vault name.
- **Spaces in names** — Wrap values in quotes: `file="My Note Name"`.
- **Daily notes plugin** — Daily note commands require the Daily Notes or Periodic Notes core plugin to be enabled.
- **Sync commands** — Only available with Obsidian Sync subscription.
- **Publish commands** — Only available with Obsidian Publish subscription.
- **`eval` command** — Executes arbitrary JavaScript in the Obsidian context. Use cautiously and warn the user about potential side effects.

## Additional Resources

### Reference Files

- **`references/commands.md`** — Complete command reference with all parameters, flags, and descriptions organized by category
- **`references/setup.md`** — Platform-specific installation instructions and TUI keyboard shortcuts
