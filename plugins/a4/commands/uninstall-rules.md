---
description: Remove the a4 plugin's symlinks from <project-root>/.claude/rules/
context: fork
model: sonnet
---

Remove the a4 plugin's path-scoped rules from the current project.

Run the bash block below. For every rule file shipped under
`${CLAUDE_PLUGIN_ROOT}/rules/`, it removes
`<project-root>/.claude/rules/<basename>` **only if** that path is a
symlink pointing back at the plugin's source. Regular files and
symlinks pointing elsewhere are left alone.

```bash
set -euo pipefail

if ! root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  echo "ERROR: not inside a git repository — cannot resolve project root." >&2
  exit 1
fi

src_dir="${CLAUDE_PLUGIN_ROOT}/rules"
dst_dir="${root}/.claude/rules"

if [ ! -d "$src_dir" ]; then
  echo "ERROR: plugin rules directory not found: $src_dir" >&2
  exit 1
fi

if [ ! -d "$dst_dir" ]; then
  echo "Nothing to uninstall — $dst_dir does not exist."
  exit 0
fi

removed=0
skipped=0
foreign=0

for src in "$src_dir"/*.md; do
  [ -e "$src" ] || continue   # POSIX-safe nullglob — works under bash and zsh
  base="$(basename "$src")"
  dst="$dst_dir/$base"

  if [ ! -e "$dst" ] && [ ! -L "$dst" ]; then
    skipped=$((skipped + 1))
    continue
  fi

  if [ -L "$dst" ]; then
    current="$(readlink "$dst")"
    if [ "$current" = "$src" ]; then
      rm "$dst"
      echo "  [removed] $dst"
      removed=$((removed + 1))
      continue
    fi
    echo "  [foreign] $dst → $current — left alone"
    foreign=$((foreign + 1))
    continue
  fi

  echo "  [foreign] $dst is a regular file — left alone"
  foreign=$((foreign + 1))
done

echo
echo "removed: $removed, skipped: $skipped, foreign: $foreign"
```

This command never deletes user-owned files. If `foreign` is non-zero,
those files were not installed by this command and must be removed
manually if desired.
