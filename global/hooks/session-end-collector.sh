#!/usr/bin/env bash
# session-end-collector.sh — SessionEnd hook
# Marks the child session as "terminated" in session-tree.json.

# Guard: not a child session if SESSION_TREE is unset
[[ -z "$SESSION_TREE" ]] && exit 0

# Read stdin to get session_id
input=$(cat)
session_id=$(printf '%s' "$input" | jq -r '.session_id // empty')
[[ -z "$session_id" ]] && exit 0

# Source library
source "$(dirname "$0")/lib/session-tree.sh"

# Find self — exit if not a managed child
st_find_child "$session_id" > /dev/null || exit 0

# Update status to terminated
st_write "(.children[] | select(.conversationId == \"$session_id\")).status = \"terminated\""
