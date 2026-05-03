# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""a4 hook dispatcher — thin entry point.

Subcommands route to modules under `a4_hook/` (sibling package to this
script). Imports are lazy: a `pre-edit` invocation only loads the
`_pre_edit` module, not `_post_edit` etc., keeping the per-invocation
import cost minimal (the `post-edit` fast path fires on every
Write/Edit/MultiEdit, so this matters).
Claude/Codex payload differences live behind runtime Strategy objects in
`a4_hook._runtime`; the edit subcommands pick one strategy up front and then
operate on normalized edit targets.

Subcommand surface:
  pre-edit       PreToolUse on Write|Edit|MultiEdit or Codex apply_patch.
                 Stash on-disk
                 ``status:`` for cascade detection AND inject the
                 type-specific authoring-contract pointers as
                 ``additionalContext`` once per type per session when the
                 runtime supports PreToolUse context injection.
  post-edit      PostToolUse on Write|Edit|MultiEdit or Codex apply_patch.
                 Record edit, stamp
                 ``created:`` on new-file Writes, run ``status:``
                 transition cascade if applicable, refresh ``updated:``
                 on the primary, and report cross-file status-consistency
                 mismatches. Cascade results surface as additionalContext
                 + systemMessage.
  stop           Stop. Validate all a4/*.md edited in this session
                 (frontmatter schema + transition-legality safety net).
                 On violations, emit JSON
                 ``{"decision": "block", "reason": ...}`` on stdout.
  user-prompt    UserPromptSubmit. Resolve `#<id>` references to
                 `a4/<type>/<id>-<slug>.md` paths.
  session-start  SessionStart. Inject the type → file-location map +
                 the runnable `allocate_id.py` command + the reserved-
                 frontmatter-fields directive (`created:`/`updated:`
                 are hook-owned).

SessionStart does not run workspace-wide status-consistency reporting —
that sweep is manual via `/a4:validate` (or `validate.py`).

Conventions (state classification, lifecycle symmetry, language/invocation,
in-event ordering, non-blocking policy, output channel usage) live in
`plugins/a4/dev/hook-conventions.md`.

Invoked from `plugins/a4/hooks/hooks.json` as
`uv run "${CLAUDE_PLUGIN_ROOT}/scripts/a4_hook.py" <subcommand>`.
Codex plugin hooks provide `CLAUDE_PLUGIN_ROOT` as a compatibility alias
for the plugin root.

The `markdown_validator` package next to this file is imported in-process
rather than shelled out via `uv run`, so per-invocation interpreter
startup is paid once — not once per validator call.

Every subcommand exits 0. `stop` signals validation violations via a
JSON `{"decision": "block", "reason": ...}` payload on stdout (rather
than rc=2 + stderr) so Claude Code surfaces the message without the
`[command]: ` harness prefix. Internal failures (missing env, missing
modules, library errors) never propagate — hooks must not block
session/stop flows.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Sibling scripts and the `a4_hook` package live next to this file.
# Make them importable regardless of how uv invokes python (explicit —
# do not rely on sys.path[0] auto-insertion).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


def main() -> int:
    if len(sys.argv) < 2:
        return 0
    sub = sys.argv[1]
    if sub == "pre-edit":
        from a4_hook._pre_edit import pre_edit
        return pre_edit()
    if sub == "post-edit":
        from a4_hook._post_edit import post_edit
        return post_edit()
    if sub == "stop":
        from a4_hook._stop import stop
        return stop()
    if sub == "user-prompt":
        from a4_hook._user_prompt import user_prompt
        return user_prompt()
    if sub == "session-start":
        from a4_hook._session_start import session_start
        return session_start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
