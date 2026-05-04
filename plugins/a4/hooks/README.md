# plugins/a4/hooks/

This directory holds only the bash hooks that do trivial, language-
independent filesystem operations:

- `cleanup-edited-a4.sh` — SessionEnd: delete this session's
  `a4-edited-<session_id>.txt`, `a4-resolved-ids-<session_id>.txt`,
  `a4-prestatus-<session_id>.json`, and
  `a4-injected-<session_id>.txt` record files.
- `sweep-old-edited-a4.sh` — legacy SessionStart safety-net sweep for orphan
  record files older than 1 day. Active manifests use the Python
  `session-start` dispatcher for this sweep.

All other hook logic (JSON parsing, script wrapping, structured output
shaping) lives in the Python dispatcher: **`../scripts/a4_hook.py`**,
invoked from lifecycle manifests with subcommands `pre-edit`,
`post-edit`, `stop`, `user-prompt`, `session-start`.

Lifecycle manifests:

- `hooks.json` — Claude Code / shared manifest. Keeps `SessionEnd`
  cleanup because Claude Code supports that event.
- `hooks.codex.json` — Codex manifest referenced by
  `../.codex-plugin/plugin.json`. Contains only Codex-supported events
  and dispatches through `PLUGIN_ROOT`. It passes `A4_HOOK_RUNTIME=codex`
  into hook subprocesses; the Claude manifest passes
  `A4_HOOK_RUNTIME=claude`.

SessionStart runs the Python dispatcher (`session-start` sweeps stale state and
injects the type → file-location map as additionalContext). SessionEnd fires
only the bash cleanup above in the Claude Code manifest.

## Opt-in trace

Set `A4_HOOK_TRACE=1` (also accepts `true`, `yes`, or `on`) before
launching the host to append JSON Lines diagnostics to:

```text
<project>/.claude/tmp/a4-edited/trace.log
```

The trace is file-only and records decision points / early returns such
as missing payload, missing `a4/` directory, target paths outside
`a4/`, dedupe hits, and validation outcomes. It never writes trace
records to stdout/stderr because hook stdout may be parsed as JSON.

Design principles — language choice, lifecycle symmetry, ordering,
non-blocking, output channels — are documented in
**`../dev/hook-conventions.md`**.
