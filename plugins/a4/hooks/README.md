# plugins/a4/hooks/

This directory holds only the bash hooks that do trivial, language-
independent filesystem operations:

- `cleanup-edited-a4.sh` — SessionEnd: delete this session's
  `a4-edited-<session_id>.txt`, `a4-resolved-ids-<session_id>.txt`,
  `a4-prestatus-<session_id>.json`, and `a4-injected-<session_id>.txt`
  record files.
- `sweep-old-edited-a4.sh` — SessionStart: delete orphan record files
  in the same family older than 1 day (safety net for crashed
  sessions).

All other hook logic (JSON parsing, script wrapping, structured output
shaping) lives in the Python dispatcher: **`../scripts/a4_hook.py`**,
invoked from lifecycle manifests with subcommands `pre-edit`,
`post-edit`, `stop`, `user-prompt`, `session-start`.

Lifecycle manifests:

- `hooks.json` — Claude Code / shared manifest. Keeps `SessionEnd`
  cleanup because Claude Code supports that event.
- `hooks.codex.json` — Codex manifest referenced by
  `../.codex-plugin/plugin.json`. Contains only Codex-supported events
  and resolves the plugin root from `PLUGIN_ROOT` with
  `CLAUDE_PLUGIN_ROOT` as a compatibility fallback.

SessionStart fires both the bash sweep above and the python dispatcher
(`session-start` injects the type → file-location map as
additionalContext); SessionEnd fires only the bash cleanup above in the
Claude Code manifest.

Design principles — language choice, lifecycle symmetry, ordering,
non-blocking, output channels — are documented in
**`../dev/hook-conventions.md`**.
