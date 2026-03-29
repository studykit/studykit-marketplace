#!/usr/bin/env bash
# spawn-session.sh — Spawn a child Claude Code session in a new iTerm2 tab.
#
# Usage:
#   bash ${CLAUDE_SKILL_DIR}/scripts/spawn-session.sh \
#     --topic "topic name" \
#     [--skill "skill-name"] \
#     [--reference-files "file1.md,file2.md"] \
#     [--context-summary "summary text"] \
#     [--result-patterns "docs/*.md,A4/**/*.requirement.md"]
#
# Environment:
#   None required — session ID is passed via --session-id argument.

set -euo pipefail

HOOKS_LIB="global/hooks/lib"

# --- Parse arguments ---

SESSION_ID=""
TOPIC=""
SKILL="null"
REFERENCE_FILES=""
CONTEXT_SUMMARY=""
RESULT_PATTERNS=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --session-id) SESSION_ID="$2"; shift 2 ;;
    --topic) TOPIC="$2"; shift 2 ;;
    --skill) SKILL="\"$2\""; shift 2 ;;
    --reference-files) REFERENCE_FILES="$2"; shift 2 ;;
    --context-summary) CONTEXT_SUMMARY="$2"; shift 2 ;;
    --result-patterns) RESULT_PATTERNS="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$SESSION_ID" ]]; then
  echo "Error: --session-id is required" >&2
  exit 1
fi

if [[ -z "$TOPIC" ]]; then
  echo "Error: --topic is required" >&2
  exit 1
fi

# --- Build JSON arrays from comma-separated strings ---

build_json_array() {
  local input="$1"
  if [[ -z "$input" ]]; then
    echo "[]"
    return
  fi
  printf '%s' "$input" | jq -R 'split(",") | map(gsub("^\\s+|\\s+$"; ""))'
}

ref_files_json=$(build_json_array "$REFERENCE_FILES")
patterns_json=$(build_json_array "$RESULT_PATTERNS")

# --- Set up paths ---

SESSION_DIR=".claude/sessions/$SESSION_ID"
export SESSION_TREE="$SESSION_DIR/session-tree.json"

source "$HOOKS_LIB/session-tree.sh"

# --- Initialize session-tree.json if needed ---

if [[ ! -f "$SESSION_TREE" ]]; then
  mkdir -p "$SESSION_DIR"
  conv_id_json=$(printf '%s' "$SESSION_ID" | jq -Rs '.')
  printf '{"mainSession":{"conversationId":%s,"name":null},"children":[]}\n' "$conv_id_json" > "$SESSION_TREE"
fi

# --- Generate child session ID ---

CHILD_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
CREATED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# --- Add child entry to session-tree.json ---

child_entry=$(jq -n \
  --arg conversationId "$CHILD_ID" \
  --arg topic "$TOPIC" \
  --arg createdAt "$CREATED_AT" \
  --argjson skill "$SKILL" \
  --argjson resultPatterns "$patterns_json" \
  --argjson referenceFiles "$ref_files_json" \
  --arg contextSummary "$CONTEXT_SUMMARY" \
  '{
    conversationId: $conversationId,
    topic: $topic,
    status: "pending",
    createdAt: $createdAt,
    pid: null,
    skill: $skill,
    transcriptPath: null,
    resultPatterns: $resultPatterns,
    resultFiles: [],
    referenceFiles: $referenceFiles,
    contextSummary: $contextSummary
  }')

st_write ".children += [$child_entry]"

# --- Launch iTerm2 pane ---

bash "$HOOKS_LIB/iterm2.sh" \
  --session-tree "$SESSION_TREE" \
  --session-id "$CHILD_ID" \
  --prompt-file "global/prompts/interactive-child.txt" \
  --title "$TOPIC"

# --- Output ---

echo "Spawned child session:"
echo "  ID:    $CHILD_ID"
echo "  Topic: $TOPIC"
echo "  Tree:  $SESSION_TREE"
