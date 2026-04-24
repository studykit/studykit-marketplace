#!/bin/bash
# SessionEnd hook: delete this session's a4-edited record file.
# Record is session-scoped; once the session ends its contents are moot.
# Always exits 0 — must never block session termination.
set -u

input=$(cat 2>/dev/null)
[[ -z "${input:-}" ]] && exit 0

session_id=$(printf '%s' "$input" | jq -r '.session_id // empty' 2>/dev/null)
[[ -z "${session_id:-}" ]] && exit 0

project_dir="${CLAUDE_PROJECT_DIR:-}"
[[ -z "$project_dir" ]] && exit 0

rm -f "$project_dir/.claude/tmp/a4-edited/a4-edited-${session_id}.txt" 2>/dev/null || true

exit 0
