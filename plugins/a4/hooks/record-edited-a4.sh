#!/bin/bash
# PostToolUse hook: record edited a4/ .md files for later validation in Stop.
# Always exits 0 — must never block the editing flow.
set -u

input=$(cat 2>/dev/null)
[[ -z "${input:-}" ]] && exit 0

tool_name=$(printf '%s' "$input" | jq -r '.tool_name // empty' 2>/dev/null)
file_path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
session_id=$(printf '%s' "$input" | jq -r '.session_id // empty' 2>/dev/null)

[[ -z "${tool_name:-}" || -z "${file_path:-}" || -z "${session_id:-}" ]] && exit 0

case "$tool_name" in
  Write|Edit|MultiEdit) ;;
  *) exit 0 ;;
esac

[[ "$file_path" != *.md ]] && exit 0

project_dir="${CLAUDE_PROJECT_DIR:-}"
[[ -z "$project_dir" ]] && exit 0

# Only record files inside the project's a4/ workspace.
case "$file_path" in
  "$project_dir/a4/"*) ;;
  *) exit 0 ;;
esac

record_dir="$project_dir/.claude/tmp/a4-edited"
mkdir -p "$record_dir" 2>/dev/null || exit 0
record_file="$record_dir/a4-edited-${session_id}.txt"
printf '%s\n' "$file_path" >> "$record_file" 2>/dev/null || true

exit 0
