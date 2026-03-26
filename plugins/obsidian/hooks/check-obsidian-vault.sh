#!/bin/bash
# Block obsidian plugin skills when the current project is not an Obsidian vault.
# Checks for .obsidian/ directory in the project root.

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Only intercept Skill tool invocations
[[ "$TOOL_NAME" != "Skill" ]] && exit 0

# Check if .obsidian/ directory exists in the project root
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
if [ ! -d "$PROJECT_DIR/.obsidian" ]; then
  cat >&2 <<EOF
Blocked: This is not an Obsidian vault (no .obsidian/ directory found in project root).
The obsidian plugin skills (dataview, tasks, jira-issue) require an Obsidian vault to be useful.
EOF
  exit 2
fi

exit 0
