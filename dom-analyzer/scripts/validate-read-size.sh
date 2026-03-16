#!/bin/bash
# Block Read tool on HTML files larger than 4KB.
# Used as a PreToolUse hook for the html-analyzer agent.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ "$FILE_PATH" == *.html || "$FILE_PATH" == *.htm ]]; then
  if [ -f "$FILE_PATH" ]; then
    SIZE=$(stat -f%z "$FILE_PATH" 2>/dev/null)
    if [ "$SIZE" -gt 4096 ]; then
      echo "Blocked: HTML file is ${SIZE} bytes (>4KB). Use html-tree.py or a custom Python script instead." >&2
      exit 2
    fi
  fi
fi

exit 0
