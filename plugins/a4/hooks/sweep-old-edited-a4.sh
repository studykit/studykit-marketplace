#!/bin/bash
# SessionStart hook: sweep orphan a4 record files older than 1 day.
# Covers crash / SIGKILL sessions where SessionEnd never fires.
# Always exits 0 — must never block session start.
set -u

project_dir="${CLAUDE_PROJECT_DIR:-}"
[[ -z "$project_dir" ]] && exit 0

record_dir="$project_dir/.claude/tmp/a4-edited"
[[ ! -d "$record_dir" ]] && exit 0

find "$record_dir" -type f \
    \( -name 'a4-edited-*.txt' \
       -o -name 'a4-resolved-ids-*.txt' \
       -o -name 'a4-prestatus-*.json' \
       -o -name 'a4-injected-*.txt' \) \
    -mtime +1 -delete 2>/dev/null || true

exit 0
