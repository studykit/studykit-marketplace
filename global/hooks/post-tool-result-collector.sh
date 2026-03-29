#!/usr/bin/env bash
# post-tool-result-collector.sh — PostToolUse hook
# When a child session writes a file, check if it matches resultPatterns
# and register it in resultFiles in session-tree.json.

# Guard: not a child session if SESSION_TREE is unset
[[ -z "$SESSION_TREE" ]] && exit 0

# Read stdin (PostToolUse hook JSON)
input=$(cat)

# Filter: only act on Write or Edit tools
tool_name=$(printf '%s' "$input" | jq -r '.tool_name // empty')
[[ "$tool_name" != "Write" && "$tool_name" != "Edit" ]] && exit 0

# Extract file_path from tool_input
file_path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
[[ -z "$file_path" ]] && exit 0

# Source the session-tree library
source "$(dirname "$0")/lib/session-tree.sh"

# Find own entry by session_id
session_id=$(printf '%s' "$input" | jq -r '.session_id // empty')
[[ -z "$session_id" ]] && exit 0

child_json=$(st_find_child "$session_id") || exit 0

# Get resultPatterns array
patterns=$(printf '%s' "$child_json" | jq -r '.resultPatterns[]? // empty' 2>/dev/null)
[[ -z "$patterns" ]] && exit 0

shopt -s extglob

# Check if file_path matches any pattern
# Replace ** with * for [[ ]] pattern matching (bash [[ ]] doesn't support globstar)
matched=false
while IFS= read -r pattern; do
  [[ -z "$pattern" ]] && continue
  normalized="${pattern//\*\*/*}"
  # shellcheck disable=SC2053
  if [[ "$file_path" == $normalized ]]; then
    matched=true
    break
  fi
done <<< "$patterns"

[[ "$matched" != "true" ]] && exit 0

# Check if already registered in resultFiles
already=$(printf '%s' "$child_json" | jq -e --arg fp "$file_path" '.resultFiles[]? | select(. == $fp)' 2>/dev/null)
[[ -n "$already" ]] && exit 0

# Append to resultFiles
# Escape strings for safe jq embedding
escaped_fp=$(printf '%s' "$file_path" | jq -Rs '.')
escaped_sid=$(printf '%s' "$session_id" | jq -Rs '.')
st_write "(.children[] | select(.conversationId == ${escaped_sid}).resultFiles) += [${escaped_fp}]"
