#!/bin/bash
# Block obsidian agents and skills when the current project is not an Obsidian vault.

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

# --- Agent gate: only intercept obsidian-guider ---
if [[ "$TOOL_NAME" == "Agent" ]]; then
  SUBAGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // empty')
  [[ "$SUBAGENT_TYPE" != "obsidian-guider" ]] && exit 0

# --- Skill gate: only intercept obsidian skills ---
elif [[ "$TOOL_NAME" == "Skill" ]]; then
  SKILL_NAME=$(echo "$INPUT" | jq -r '.tool_input.skill // empty')
  case "$SKILL_NAME" in
    dataview|tasks|jira-issue|cli|templater) ;;
    obsidian:dataview|obsidian:tasks|obsidian:jira-issue|obsidian:cli|obsidian:templater) ;;
    *) exit 0 ;;
  esac

else
  exit 0
fi

# Check if .obsidian/ directory exists in the project root
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
if [ ! -d "$PROJECT_DIR/.obsidian" ]; then
  cat >&2 <<EOF
Blocked: This is not an Obsidian vault (no .obsidian/ directory found).
Obsidian agents and skills require an Obsidian vault to operate.
EOF
  exit 2
fi

exit 0
