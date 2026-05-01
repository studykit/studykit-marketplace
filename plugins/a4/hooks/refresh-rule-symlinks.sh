#!/bin/bash
# SessionStart hook: refresh stale a4 rule symlinks after a plugin update.
#
# When the plugin version bumps, ${CLAUDE_PLUGIN_ROOT} resolves to a new
# cache directory and any symlinks under <project-root>/.claude/rules/
# that were created by /a4:install-rules now dangle at the previous
# cache path. This hook detects those stale links by their target shape
# (…/plugins/a4/rules/<basename>.md) and repoints them at the current
# ${CLAUDE_PLUGIN_ROOT}/rules/<basename>.md.
#
# Scope is intentionally narrow:
#   - Only refreshes pre-existing a4-owned symlinks.
#   - Never installs missing rules (that is /a4:install-rules' job —
#     keeps SessionStart from silently expanding the rule set).
#   - Never touches regular files or symlinks pointing outside
#     plugins/a4/rules/.
#
# Always exits 0 — must never block session start.
set -u

# Derive plugin root from this script's location rather than ${CLAUDE_PLUGIN_ROOT}:
# matches the script-relative resolution used by install-rules.sh / uninstall-rules.sh
# and stays correct even if the env var is missing from the hook subprocess.
# Layout: ${CLAUDE_PLUGIN_ROOT}/hooks/refresh-rule-symlinks.sh.
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
plugin_root="$(cd "$script_dir/.." && pwd)"

src_dir="$plugin_root/rules"
[[ -d "$src_dir" ]] || exit 0

project_dir="${CLAUDE_PROJECT_DIR:-}"
[[ -n "$project_dir" ]] || exit 0

# Resolve to git toplevel to match /a4:install-rules' destination.
root="$(git -C "$project_dir" rev-parse --show-toplevel 2>/dev/null || true)"
[[ -n "$root" ]] || root="$project_dir"

dst_dir="$root/.claude/rules"
[[ -d "$dst_dir" ]] || exit 0

refreshed=0
for src in "$src_dir"/*.md; do
    [[ -e "$src" ]] || continue
    base="$(basename "$src")"
    dst="$dst_dir/$base"

    [[ -L "$dst" ]] || continue
    current="$(readlink "$dst" 2>/dev/null || true)"
    [[ -n "$current" ]] || continue
    [[ "$current" = "$src" ]] && continue

    case "$current" in
        */plugins/a4/rules/"$base")
            if rm "$dst" 2>/dev/null && ln -s "$src" "$dst" 2>/dev/null; then
                refreshed=$((refreshed + 1))
            fi
            ;;
    esac
done

if (( refreshed > 0 )); then
    echo "[a4] refreshed $refreshed stale rule symlink(s) after plugin update."
fi

exit 0
