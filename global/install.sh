#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$HOME/.claude"

# Directories to sync
DIRS=(agents hooks prompts skills)

for dir in "${DIRS[@]}"; do
  src="$SCRIPT_DIR/$dir"
  [ -d "$src" ] || continue

  # Skip empty directories
  if [ -z "$(ls -A "$src" 2>/dev/null)" ]; then
    continue
  fi

  mkdir -p "$TARGET/$dir"
  cp -R "$src"/. "$TARGET/$dir"/
  echo "Copied $dir → $TARGET/$dir"
done
