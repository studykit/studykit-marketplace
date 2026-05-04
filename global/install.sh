#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$HOME/.claude"
CODEX_SKILLS_TARGET="$HOME/.codex/skills"
SKILLS_SRC="$SCRIPT_DIR/skills"

# Directories to sync
DIRS=(prompts skills)

for dir in "${DIRS[@]}"; do
  src="$SCRIPT_DIR/$dir"
  [ -d "$src" ] || continue

  # Skip empty directories
  if [ -z "$(ls -A "$src" 2>/dev/null)" ]; then
    continue
  fi

  mkdir -p "$TARGET/$dir"
  rsync -a --delete "$src"/ "$TARGET/$dir"/
  echo "Synced $dir → $TARGET/$dir"
done

# Copy global skills into Codex using the same sync style as Claude, while
# preserving unrelated user skills in ~/.codex/skills.
if [ -d "$SKILLS_SRC" ]; then
  mkdir -p "$CODEX_SKILLS_TARGET"

  find "$SKILLS_SRC" -mindepth 1 -maxdepth 1 -type d | sort | while IFS= read -r skill_dir; do
    skill_name="$(basename "$skill_dir")"
    target_dir="$CODEX_SKILLS_TARGET/$skill_name"

    mkdir -p "$target_dir"
    rsync -a --delete "$skill_dir"/ "$target_dir"/
    echo "Synced $skill_name → $target_dir"
  done
fi
