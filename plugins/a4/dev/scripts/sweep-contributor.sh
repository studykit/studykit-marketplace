#!/bin/bash
# SessionStart hook: sweep orphan contributor-hook sentinel files older
# than 1 day. Covers crash / SIGKILL sessions where SessionEnd never
# fires. Counterpart to plugins/a4/hooks/sweep-old-edited-a4.sh.
# Always exits 0 — must never block session start.
set -u

project_dir="${CLAUDE_PROJECT_DIR:-}"
[[ -z "$project_dir" ]] && exit 0

record_dir="$project_dir/.claude/tmp/a4-edited"
[[ ! -d "$record_dir" ]] && exit 0

find "$record_dir" -type f \
    -name 'a4-contributor-files-*.txt' \
    -mtime +1 -delete 2>/dev/null || true

exit 0
