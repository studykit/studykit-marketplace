#!/bin/bash
# SessionStart hook: report cross-file status consistency mismatches in a4/.
# Exits 0 with additionalContext injection when mismatches exist; silent
# (no output) on a clean workspace or any internal error so session start
# is never blocked.
set -u

project_dir="${CLAUDE_PROJECT_DIR:-}"
[[ -z "$project_dir" ]] && exit 0

a4_dir="$project_dir/a4"
[[ ! -d "$a4_dir" ]] && exit 0

plugin_root="${CLAUDE_PLUGIN_ROOT:-}"
[[ -z "$plugin_root" ]] && exit 0

script="$plugin_root/scripts/validate_status_consistency.py"
[[ ! -f "$script" ]] && exit 0

output=$(uv run "$script" "$a4_dir" 2>&1)
rc=$?

# rc=0: clean workspace — inject nothing.
# rc=2: mismatches reported — inject as additionalContext.
# any other rc: internal script failure — stay silent to avoid noise.
if [[ "$rc" -ne 2 ]]; then
  exit 0
fi

context="## a4/ status consistency (SessionStart check)

The following cross-file status inconsistencies exist in the current \`a4/\` workspace. They are informational only — no immediate action is required, but surface them when the user works on related files.

\`\`\`
${output}
\`\`\`

Rules checked:
- \`decision.status = superseded\` iff another decision declares \`supersedes: [<this>]\`.
- \`idea.status = promoted\` iff own \`promoted:\` list is non-empty.
- \`spark/*.brainstorm.md\` \`status = promoted\` iff own \`promoted:\` is non-empty.

See \`plugins/a4/references/frontmatter-schema.md\` for the underlying schema."

jq -n --arg ctx "$context" '{
  hookSpecificOutput: {
    hookEventName: "SessionStart",
    additionalContext: $ctx
  }
}' 2>/dev/null || exit 0

exit 0
