#!/bin/bash
# PostToolUse hook: when a decision/*.md is edited and the file just
# landed at status: final with a non-empty supersedes: list, flip each
# target from final to superseded and append a back-pointer `## Log`
# entry.
#
# Scope: decision family only. The usecase cascade was absorbed into
# scripts/transition_status.py in plugin 1.10.0 — UC shipped→superseded
# now fires inside the status writer, not via this hook.
#
# Non-blocking: always exits 0. Hard errors are reported via
# additionalContext so Claude can surface them, but never block the
# editing flow.
#
# See plugins/a4/scripts/propagate_superseded.py for the full rule set.
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

# Scope: decision files only. UC edits are handled inline by
# transition_status.py invocations in skills/agents.
case "$file_path" in
  "$project_dir/a4/decision/"*) ;;
  *) exit 0 ;;
esac

a4_dir="$project_dir/a4"
[[ ! -d "$a4_dir" ]] && exit 0

plugin_root="${CLAUDE_PLUGIN_ROOT:-}"
[[ -z "$plugin_root" ]] && exit 0

script="$plugin_root/scripts/propagate_superseded.py"
[[ ! -f "$script" ]] && exit 0

# Run in JSON mode so we can report a structured summary when something
# actually changed. The script is idempotent; re-running on an already-
# propagated file is a no-op.
output=$(uv run "$script" "$a4_dir" --file "$file_path" --json 2>&1)
rc=$?

if [[ "$rc" -ne 0 && "$rc" -ne 2 ]]; then
  # Script invocation itself failed (uv missing, unexpected error). Stay
  # silent rather than blocking the session on infrastructure issues.
  exit 0
fi

propagated_count=$(printf '%s' "$output" | jq -r '.total_propagated // 0' 2>/dev/null)
error_count=$(printf '%s' "$output" | jq -r '.total_errors // 0' 2>/dev/null)

# Nothing happened and no errors — stay silent so unrelated edits don't
# accumulate noise in the conversation.
if [[ "${propagated_count:-0}" -eq 0 && "${error_count:-0}" -eq 0 ]]; then
  exit 0
fi

rel_path="${file_path#"$project_dir/"}"

if [[ "${propagated_count:-0}" -gt 0 ]]; then
  flipped_lines=$(printf '%s' "$output" | jq -r '
    [.reports[] | .propagated[] | "- \(.target): \(.previous_status) → superseded"] | .[]
  ' 2>/dev/null)
else
  flipped_lines=""
fi

if [[ "${error_count:-0}" -gt 0 ]]; then
  error_lines=$(printf '%s' "$output" | jq -r '
    [.reports[] | .errors[] | "- \(.)"] | .[]
  ' 2>/dev/null)
else
  error_lines=""
fi

context="## a4/ supersedes propagation

The edit to \`${rel_path}\` triggered \`propagate_superseded.py\`."

if [[ -n "$flipped_lines" ]]; then
  context="$context

**Targets flipped to \`superseded\`:**
$flipped_lines

Each flipped file also got its \`updated:\` bumped to today and a \`## Log\` back-pointer entry appended. These changes are unstaged in the working tree — include them in the same commit as the successor edit."
fi

if [[ -n "$error_lines" ]]; then
  context="$context

**Errors:**
$error_lines"
fi

jq -n --arg ctx "$context" '{
  hookSpecificOutput: {
    hookEventName: "PostToolUse",
    additionalContext: $ctx
  }
}' 2>/dev/null || exit 0

exit 0
