# plugins/a4/hooks/

This directory holds only the bash hooks that do trivial, language-
independent filesystem operations:

- `cleanup-edited-a4.sh` — SessionEnd: delete this session's
  `a4-edited-<session_id>.txt` record file.
- `sweep-old-edited-a4.sh` — SessionStart: delete orphan
  `a4-edited-*.txt` files older than 1 day (safety net for crashed
  sessions).

All other hook logic (JSON parsing, script wrapping, structured output
shaping) lives in the Python dispatcher: **`../scripts/a4_hook.py`**,
invoked from `hooks.json` with subcommands `post-edit`, `stop`,
`session-start`.

Design principles — language choice, lifecycle symmetry, ordering,
non-blocking, output channels — are documented in
**`../docs/hook-conventions.md`**.
