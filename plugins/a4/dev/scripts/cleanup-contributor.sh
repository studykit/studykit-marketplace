#!/bin/bash
# SessionEnd hook: delete this session's contributor-hook sentinel files.
# Counterpart to plugins/a4/hooks/cleanup-edited-a4.sh — that one cleans
# workspace-side state for end users; this one cleans the contributor
# audience-injection sentinels written by dev/scripts/contributor_hook.py.
# Always exits 0 — must never block session termination.
set -u

input=$(cat 2>/dev/null)
[[ -z "${input:-}" ]] && exit 0

session_id=$(printf '%s' "$input" | jq -r '.session_id // empty' 2>/dev/null)
[[ -z "${session_id:-}" ]] && exit 0

project_dir="${CLAUDE_PROJECT_DIR:-}"
[[ -z "$project_dir" ]] && exit 0

record_dir="$project_dir/.claude/tmp/a4-edited"
rm -f \
    "$record_dir/a4-contributor-files-${session_id}.txt" \
    2>/dev/null || true

exit 0
