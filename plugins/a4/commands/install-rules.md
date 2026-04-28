---
description: Symlink the a4 plugin's path-scoped rules into <project-root>/.claude/rules/
---

Install the a4 plugin's path-scoped rules into the current project.

Run the bash block below. It creates `<project-root>/.claude/rules/`
if missing, and for every rule file shipped under
`${CLAUDE_PLUGIN_ROOT}/rules/` it creates a symlink at
`<project-root>/.claude/rules/<basename>`.

Behavior:

- already a symlink to the same plugin source → skipped silently.
- target absent → symlink created.
- target exists as a regular file or as a symlink pointing somewhere
  else → flagged as a conflict; not overwritten. The user decides.

The command is idempotent. It only creates symlinks (so plugin updates
flow through without re-running). Counts are reported at the end.

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

mkdir -p "$dst_dir"

installed=0
skipped=0
conflicted=0

for src in "$src_dir"/*.md; do
  [ -e "$src" ] || continue   # POSIX-safe nullglob — works under bash and zsh
  base="$(basename "$src")"
  dst="$dst_dir/$base"

  if [ -L "$dst" ]; then
    current="$(readlink "$dst")"
    if [ "$current" = "$src" ]; then
      skipped=$((skipped + 1))
      continue
    fi
    echo "  [conflict] $dst → $current (expected $src) — left alone"
    conflicted=$((conflicted + 1))
    continue
  fi

  if [ -e "$dst" ]; then
    echo "  [conflict] $dst exists as a regular file — left alone"
    conflicted=$((conflicted + 1))
    continue
  fi

  ln -s "$src" "$dst"
  echo "  [installed] $dst → $src"
  installed=$((installed + 1))
done

echo
echo "installed: $installed, skipped: $skipped, conflicted: $conflicted"
if [ "$conflicted" -gt 0 ]; then
  echo "Resolve conflicts manually (delete or back up the existing files), then re-run." >&2
fi
```

If `installed` is non-zero, the new path-scoped rules will start
applying the next time Claude Code reads any matching file in the
project (e.g., `a4/**/*.md` for `a4-section-enum.md`). To remove them
later, run `/a4:uninstall-rules`.
