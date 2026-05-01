#!/bin/bash
# Install (and stale-refresh) the a4 plugin's path-scoped rules into
# <project-root>/.claude/rules/. See the sibling SKILL.md for the
# behavior contract. Sole entry point for the /a4:install-rules skill.
set -euo pipefail

if ! root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    echo "ERROR: not inside a git repository — cannot resolve project root." >&2
    exit 1
fi

# Derive plugin root from this script's location rather than ${CLAUDE_PLUGIN_ROOT}:
# the env var is not always exported into the bash subprocess invoked by the
# skill, but the layout ${CLAUDE_PLUGIN_ROOT}/skills/install-rules/scripts/ is fixed.
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
plugin_root="$(cd "$script_dir/../../.." && pwd)"

src_dir="$plugin_root/rules"
dst_dir="${root}/.claude/rules"

if [[ ! -d "$src_dir" ]]; then
    echo "ERROR: plugin rules directory not found: $src_dir" >&2
    exit 1
fi

mkdir -p "$dst_dir"

installed=0
refreshed=0
skipped=0
conflicted=0

for src in "$src_dir"/*.md; do
    [[ -e "$src" ]] || continue   # POSIX-safe nullglob — works under bash and zsh
    base="$(basename "$src")"
    dst="$dst_dir/$base"

    if [[ -L "$dst" ]]; then
        current="$(readlink "$dst")"
        if [[ "$current" = "$src" ]]; then
            skipped=$((skipped + 1))
            continue
        fi
        # Stale-link detection: prior a4 install whose ${CLAUDE_PLUGIN_ROOT}
        # has since moved (e.g., plugin version bump → new cache SHA dir).
        # Identify by the link target's path shape: /plugins/a4/rules/<base>.
        case "$current" in
            */plugins/a4/rules/"$base")
                rm "$dst"
                ln -s "$src" "$dst"
                echo "  [refreshed] $dst → $src (was $current)"
                refreshed=$((refreshed + 1))
                continue
                ;;
        esac
        echo "  [conflict] $dst → $current (expected $src) — left alone"
        conflicted=$((conflicted + 1))
        continue
    fi

    if [[ -e "$dst" ]]; then
        echo "  [conflict] $dst exists as a regular file — left alone"
        conflicted=$((conflicted + 1))
        continue
    fi

    ln -s "$src" "$dst"
    echo "  [installed] $dst → $src"
    installed=$((installed + 1))
done

echo
echo "installed: $installed, refreshed: $refreshed, skipped: $skipped, conflicted: $conflicted"
if [[ "$conflicted" -gt 0 ]]; then
    echo "Resolve conflicts manually (delete or back up the existing files), then re-run." >&2
fi
