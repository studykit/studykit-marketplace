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
invoked from `hooks.json` with subcommands `post-edit`, `stop`,
`user-prompt`. SessionStart does not fire the python dispatcher — the
SessionStart entries are the two bash scripts above.

Design principles — language choice, lifecycle symmetry, ordering,
non-blocking, output channels — are documented in
**`../dev/hook-conventions.md`**.
