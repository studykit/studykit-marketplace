#!/bin/bash
# PostToolUse hook: report cross-file status consistency mismatches after
# an a4/ .md file is edited. Exits 0 with additionalContext injection on
# mismatch; silent (no output) on a clean workspace or internal error.
#
# Non-blocking by design — consistency is informational, not enforced.
# See plugins/a4/scripts/validate_status_consistency.py for the rules.
set -u

input=$(cat 2>/dev/null)
[[ -z "${input:-}" ]] && exit 0

tool_name=$(printf '%s' "$input" | jq -r '.tool_name // empty' 2>/dev/null)
file_path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)

[[ -z "${tool_name:-}" || -z "${file_path:-}" ]] && exit 0

case "$tool_name" in
  Write|Edit|MultiEdit) ;;
  *) exit 0 ;;
esac

[[ "$file_path" != *.md ]] && exit 0

project_dir="${CLAUDE_PROJECT_DIR:-}"
[[ -z "$project_dir" ]] && exit 0

# Scope to this project's a4/ workspace only.
case "$file_path" in
  "$project_dir/a4/"*) ;;
  *) exit 0 ;;
esac

a4_dir="$project_dir/a4"
[[ ! -d "$a4_dir" ]] && exit 0

plugin_root="${CLAUDE_PLUGIN_ROOT:-}"
[[ -z "$plugin_root" ]] && exit 0

script="$plugin_root/scripts/validate_status_consistency.py"
[[ ! -f "$script" ]] && exit 0

# --file scopes output to the edited file's connected component:
#   - idea/<id>-<slug>.md        → that file only
#   - spark/*.brainstorm.md      → that file only
#   - decision/<id>-<slug>.md    → that file + who it supersedes + who
#                                  supersedes it
#   - other paths under a4/      → no output (no consistency rule)
# Pre-existing mismatches in unrelated files are NOT re-surfaced.
output=$(uv run "$script" "$a4_dir" --file "$file_path" 2>&1)
rc=$?

if [[ "$rc" -ne 2 ]]; then
  exit 0
fi

context="## a4/ status consistency (post-edit check)

The file change to \`${file_path#"$project_dir/"}\` surfaced cross-file status inconsistencies in its connected component:

\`\`\`
${output}
\`\`\`

This is informational only — no retry is forced. Surface it to the user when relevant to the current task. Rules:
- \`decision.status = superseded\` iff another decision declares \`supersedes: [<this>]\`.
- \`idea.status = promoted\` iff own \`promoted:\` list is non-empty.
- \`spark/*.brainstorm.md\` \`status = promoted\` iff own \`promoted:\` is non-empty."

jq -n --arg ctx "$context" '{
  hookSpecificOutput: {
    hookEventName: "PostToolUse",
    additionalContext: $ctx
  }
}' 2>/dev/null || exit 0

exit 0
