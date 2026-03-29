#!/usr/bin/env bash
# session-start-bootstrap.sh — SessionStart hook that injects context into child sessions.
# Reads session-tree.json to find the child entry matching this session,
# then outputs context instructions to stdout for injection into the conversation.

set -euo pipefail

# Guard: if SESSION_TREE is not set, this is a normal (non-child) session — exit silently.
if [[ -z "${SESSION_TREE:-}" ]]; then
  exit 0
fi

# Read stdin JSON from Claude Code to get session_id and transcript_path.
stdin_json=$(cat)
session_id=$(printf '%s' "$stdin_json" | jq -r '.session_id // empty')
transcript_path=$(printf '%s' "$stdin_json" | jq -r '.transcript_path // empty')

if [[ -z "$session_id" ]]; then
  exit 0
fi

# Source the session-tree library.
source "$(dirname "$0")/lib/session-tree.sh"

# Find our entry in session-tree.json.
child_json=$(st_find_child "$session_id") || exit 0

# Extract fields from the child entry.
topic=$(printf '%s' "$child_json" | jq -r '.topic // empty')
context_summary=$(printf '%s' "$child_json" | jq -r '.contextSummary // empty')
skill=$(printf '%s' "$child_json" | jq -r '.skill // empty')

# Build reference files list.
ref_files=$(printf '%s' "$child_json" | jq -r '.referenceFiles // [] | .[]')

# Build result patterns list.
result_patterns=$(printf '%s' "$child_json" | jq -r '.resultPatterns // [] | join("`, `")')

# --- Inject context via stdout ---

echo "## Session Context (injected by orchestrator)"
echo ""

if [[ -n "$topic" ]]; then
  echo "**Topic:** $topic"
  echo ""
fi

if [[ -n "$ref_files" ]]; then
  echo "**Reference files:**"
  while IFS= read -r f; do
    echo "- $f"
  done <<< "$ref_files"
  echo ""
fi

if [[ -n "$context_summary" ]]; then
  echo "**Context from main session:**"
  echo "$context_summary"
  echo ""
fi

if [[ -n "$result_patterns" ]]; then
  echo "**Result file patterns:**"
  echo "Save your deliverables to paths matching: \`$result_patterns\`"
  echo ""
fi

if [[ -n "$skill" ]]; then
  echo "**Skill:** Please invoke /$skill to begin."
  echo ""
fi

# --- Write back metadata to session-tree.json ---
# Update the child entry with conversation ID, transcript path, and PID.
# Note: $PPID is the parent process (Claude Code), since the hook runs as a subprocess.
st_write "$(cat <<JQEXPR
(.children[] | select(.conversationId == "$session_id")) |=
  (.status = "active" |
   .transcriptPath = "$transcript_path" |
   .pid = $PPID)
JQEXPR
)"
