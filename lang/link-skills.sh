#!/usr/bin/env bash
# Creates symbolic links in ~/.claude/skills/ for each skill under lang/skills/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_SRC="$SCRIPT_DIR/skills"
SKILLS_DST="$HOME/.claude/skills"

mkdir -p "$SKILLS_DST"

for skill_dir in "$SKILLS_SRC"/*/; do
  skill_name="$(basename "$skill_dir")"
  target="$SKILLS_DST/$skill_name"

  if [ -L "$target" ]; then
    current="$(readlink "$target")"
    if [ "$current" = "$skill_dir" ] || [ "$current" = "${skill_dir%/}" ]; then
      echo "skip: $skill_name (already linked)"
      continue
    fi
    echo "update: $skill_name (relink)"
    rm "$target"
  elif [ -e "$target" ]; then
    echo "skip: $skill_name (non-symlink exists, remove manually to link)"
    continue
  fi

  ln -s "$SKILLS_SRC/$skill_name" "$target"
  echo "link: $skill_name -> $SKILLS_SRC/$skill_name"
done
