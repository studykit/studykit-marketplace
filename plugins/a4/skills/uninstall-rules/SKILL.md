---
name: uninstall-rules
description: "Remove the a4 plugin's symlinks from <project-root>/.claude/rules/. Removes only symlinks pointing into any plugins/a4/rules/<basename>.md (covers both the current ${CLAUDE_PLUGIN_ROOT} and stale links from a prior plugin version's cache directory). Regular files and symlinks pointing elsewhere are left alone."
disable-model-invocation: true
context: fork
model: sonnet
allowed-tools: Bash
---

# Uninstall a4 path-scoped rules

Run the script. For every rule file shipped under `${CLAUDE_PLUGIN_ROOT}/rules/`, it removes `<project-root>/.claude/rules/<basename>` **only if** that path is a symlink whose target points into any `…/plugins/a4/rules/<basename>.md` (matches both the current `${CLAUDE_PLUGIN_ROOT}` and stale links from a prior plugin version's cache directory). Regular files and symlinks pointing outside `plugins/a4/rules/` are left alone.

## Run

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/uninstall-rules/scripts/uninstall-rules.sh"
```

Surface the script's stdout verbatim. Counts (`removed`, `skipped`, `foreign`) are reported on the final line.

This command never deletes user-owned files. If `foreign` is non-zero, those files were not installed by this skill and must be removed manually if desired.
