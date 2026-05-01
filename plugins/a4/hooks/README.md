# plugins/a4/hooks/

This directory holds only the bash hooks that do trivial, language-
independent filesystem operations:

- `cleanup-edited-a4.sh` — SessionEnd: delete this session's
  `a4-edited-<session_id>.txt` record file.
- `sweep-old-edited-a4.sh` — SessionStart: delete orphan
  `a4-edited-*.txt` files older than 1 day (safety net for crashed
  sessions).
- `refresh-rule-symlinks.sh` — SessionStart: repoint stale
  `<project>/.claude/rules/*` symlinks at the current
  `${CLAUDE_PLUGIN_ROOT}/rules/` after a plugin version bump moves
  the cache directory. No-op when `/a4:install-rules` was never run
  or when no symlinks are stale. Identifies a4-owned links by target
  path shape (`…/plugins/a4/rules/<basename>.md`) so unrelated user
  symlinks are left alone.

All other hook logic (JSON parsing, script wrapping, structured output
shaping) lives in the Python dispatcher: **`../scripts/a4_hook.py`**,
invoked from `hooks.json` with subcommands `post-edit`, `stop`,
`user-prompt`. SessionStart does not fire the python dispatcher — the
SessionStart entries are the two bash scripts above.

Design principles — language choice, lifecycle symmetry, ordering,
non-blocking, output channels — are documented in
**`../dev/hook-conventions.md`**.
