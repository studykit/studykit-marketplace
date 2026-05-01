---
name: install-rules
description: "Symlink the a4 plugin's path-scoped rules into <project-root>/.claude/rules/. Idempotent and upgrade-safe — re-run after a plugin version bump and any symlinks left dangling at the previous ${CLAUDE_PLUGIN_ROOT} cache directory are repointed at the current install. The SessionStart hook performs the same refresh automatically; manual re-runs are usually only needed when a plugin update adds a new rule file."
disable-model-invocation: true
context: fork
model: sonnet
allowed-tools: Bash
---

# Install a4 path-scoped rules

Run the script, which creates `<project-root>/.claude/rules/` if missing and, for every rule file shipped under `${CLAUDE_PLUGIN_ROOT}/rules/`, manages a symlink at `<project-root>/.claude/rules/<basename>`.

Behavior:

- already a symlink to the same plugin source → skipped silently.
- target absent → symlink created.
- target is a symlink whose `readlink` points at a *different* `…/plugins/a4/rules/<basename>.md` path (typical after a plugin version bump moved `${CLAUDE_PLUGIN_ROOT}` to a new cache directory and left the old symlink dangling) → automatically refreshed to the current source.
- target exists as a regular file, or as a symlink pointing outside any `plugins/a4/rules/` directory → flagged as a conflict; not overwritten. The user decides.

The command is idempotent and upgrade-safe — re-run after a plugin update to repoint stale symlinks at the new `${CLAUDE_PLUGIN_ROOT}`. The SessionStart hook (`hooks/refresh-rule-symlinks.sh`) performs the same refresh automatically, so manual re-runs are usually unnecessary.

## Run

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/install-rules/scripts/install-rules.sh"
```

Surface the script's stdout and any stderr verbatim. Counts (`installed`, `refreshed`, `skipped`, `conflicted`) are reported on the final line.

If `installed` is non-zero, the new path-scoped rules will start applying the next time Claude Code reads any matching file in the project (e.g., `a4/**/*.md` for `a4-section-enum.md`). If `refreshed` is non-zero, stale links from an older `${CLAUDE_PLUGIN_ROOT}` cache directory have been repointed at the current install. If `conflicted` is non-zero, surface the script's per-line conflict notes — the user must resolve them manually before re-running. To remove the rules later, run `/a4:uninstall-rules`.
