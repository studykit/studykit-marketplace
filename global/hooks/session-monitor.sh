#!/usr/bin/env bash
# session-monitor.sh — FileChanged hook (matcher: session-tree.json)
# Monitors child session status changes from the main session side.
# Outputs additionalContext JSON when notable changes are detected.

set -euo pipefail

# Guard: exit if SESSION_TREE is not set
if [[ -z "${SESSION_TREE:-}" ]]; then
  exit 0
fi

# Read stdin JSON and verify file_path matches SESSION_TREE
input=$(cat)
file_path=$(printf '%s' "$input" | jq -r '.file_path // empty')

if [[ "$file_path" != "$SESSION_TREE" ]]; then
  exit 0
fi

# Source the session-tree library
source "$(dirname "$0")/lib/session-tree.sh"

# Read current state
current=$(st_read)

# Snapshot file for change detection
last_file="${SESSION_TREE%.json}.last"

# Determine previous state
if [[ -f "$last_file" ]]; then
  previous=$(cat "$last_file")
  has_previous=true
else
  previous='{"mainSession":null,"children":[]}'
  has_previous=false
fi

# Save current state as the new snapshot
printf '%s\n' "$current" > "$last_file"

notifications=()
now_epoch=$(date +%s)

# Iterate over each child in the current tree
while IFS= read -r child; do
  [[ -z "$child" || "$child" == "null" ]] && continue

  child_id=$(printf '%s' "$child" | jq -r '.conversationId')
  child_status=$(printf '%s' "$child" | jq -r '.status')
  child_topic=$(printf '%s' "$child" | jq -r '.topic // "unknown"')
  child_pid=$(printf '%s' "$child" | jq -r '.pid // empty')
  child_created=$(printf '%s' "$child" | jq -r '.createdAt // empty')

  # Get previous status for this child (empty if not found)
  prev_status=""
  if [[ "$has_previous" == true ]]; then
    prev_status=$(printf '%s' "$previous" | jq -r --arg id "$child_id" '(.children[] | select(.conversationId == $id) | .status) // empty')
  fi

  # Crash detection: active with a pid that is no longer alive
  if [[ "$child_status" == "active" && -n "$child_pid" ]]; then
    if ! kill -0 "$child_pid" 2>/dev/null; then
      st_write '(.children[] | select(.conversationId == "'"$child_id"'")).status = "crashed"'
      notifications+=("- **${child_topic}** (${child_id}): crashed — process no longer alive")
      continue
    fi
  fi

  # Handshake timeout: pending (bootstrap never completed) and createdAt older than 30 seconds
  if [[ "$child_status" == "pending" && -n "$child_created" ]]; then
    created_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$child_created" +%s 2>/dev/null || echo 0)
    if (( now_epoch - created_epoch > 30 )); then
      st_write '(.children[] | select(.conversationId == "'"$child_id"'")).status = "failed_to_start"'
      notifications+=("- **${child_topic}** (${child_id}): failed to start — handshake timeout (>30s)")
      continue
    fi
  fi

  # New result files: compare current vs previous resultFiles for active sessions
  if [[ "$child_status" == "active" && "$has_previous" == true ]]; then
    prev_files=$(printf '%s' "$previous" | jq -c --arg id "$child_id" '[(.children[] | select(.conversationId == $id) | .resultFiles // []) | .[]]' 2>/dev/null || echo '[]')
    curr_files=$(printf '%s' "$child" | jq -c '[.resultFiles // [] | .[]]' 2>/dev/null || echo '[]')
    if [[ "$prev_files" != "$curr_files" ]]; then
      new_files=$(jq -n --argjson prev "$prev_files" --argjson curr "$curr_files" '$curr - $prev | join(", ")')
      new_files="${new_files%\"}"
      new_files="${new_files#\"}"
      if [[ -n "$new_files" ]]; then
        notifications+=("- **${child_topic}** (${child_id}): new result files: ${new_files}")
      fi
    fi
  fi

  # Terminated session: report if status changed or first run with non-active status
  if [[ "$child_status" == "terminated" && "$prev_status" != "terminated" ]]; then
    result_files=$(printf '%s' "$child" | jq -r '(.resultFiles // []) | join(", ")')
    if [[ -n "$result_files" ]]; then
      notifications+=("- **${child_topic}** (${child_id}): terminated — result files: ${result_files}")
    else
      notifications+=("- **${child_topic}** (${child_id}): terminated")
    fi
    continue
  fi

  # Report other non-active statuses on first run (no previous snapshot)
  if [[ "$has_previous" == false && "$child_status" != "active" && "$child_status" != "terminated" ]]; then
    notifications+=("- **${child_topic}** (${child_id}): ${child_status}")
  fi

done < <(printf '%s' "$current" | jq -c '.children[]?' 2>/dev/null)

# Only output if there are notable changes
if [[ ${#notifications[@]} -gt 0 ]]; then
  body="## Child Session Updates\n\n"
  for note in "${notifications[@]}"; do
    body+="${note}\n"
  done

  printf '%s\n' "$body" | jq -Rs '{ additionalContext: . }'
fi
