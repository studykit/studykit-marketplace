#!/bin/bash
# Remove a4-owned symlinks from <project-root>/.claude/rules/. See the
# sibling SKILL.md for the behavior contract. Sole entry point for the
# /a4:uninstall-rules skill.
set -euo pipefail

if ! root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    echo "ERROR: not inside a git repository — cannot resolve project root." >&2
    exit 1
fi

# Derive plugin root from this script's location rather than ${CLAUDE_PLUGIN_ROOT}:
# the env var is not always exported into the bash subprocess invoked by the
# skill, but the layout ${CLAUDE_PLUGIN_ROOT}/skills/uninstall-rules/scripts/ is fixed.
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
plugin_root="$(cd "$script_dir/../../.." && pwd)"

src_dir="$plugin_root/rules"
dst_dir="${root}/.claude/rules"

if [[ ! -d "$src_dir" ]]; then
    echo "ERROR: plugin rules directory not found: $src_dir" >&2
    exit 1
fi

if [[ ! -d "$dst_dir" ]]; then
    echo "Nothing to uninstall — $dst_dir does not exist."
    exit 0
fi

removed=0
skipped=0
foreign=0

for src in "$src_dir"/*.md; do
    [[ -e "$src" ]] || continue   # POSIX-safe nullglob — works under bash and zsh
    base="$(basename "$src")"
    dst="$dst_dir/$base"

    if [[ ! -e "$dst" ]] && [[ ! -L "$dst" ]]; then
        skipped=$((skipped + 1))
        continue
    fi

    if [[ -L "$dst" ]]; then
        current="$(readlink "$dst")"
        # Remove links pointing into any plugins/a4/rules/<base>.md — covers
        # both the current ${CLAUDE_PLUGIN_ROOT} and stale links left by
        # earlier plugin versions whose cache directory has since moved.
        case "$current" in
            */plugins/a4/rules/"$base")
                rm "$dst"
                echo "  [removed] $dst → $current"
                removed=$((removed + 1))
                continue
                ;;
        esac
        echo "  [foreign] $dst → $current — left alone"
        foreign=$((foreign + 1))
        continue
    fi

    echo "  [foreign] $dst is a regular file — left alone"
    foreign=$((foreign + 1))
done

echo
echo "removed: $removed, skipped: $skipped, foreign: $foreign"
