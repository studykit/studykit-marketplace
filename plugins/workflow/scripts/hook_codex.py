#!/usr/bin/env python3
"""Codex hook CLI entry point.

Executable used by the Codex hook manifest
(``plugins/workflow/hooks/hooks.codex.json``). Each event command invokes
``python3 hook_codex.py <subcommand>``; ``main`` dispatches to the matching
shim in :mod:`workflow_hook`.

The Hook subtype itself (``CodexHook``) lives in :mod:`codex_hook`.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from workflow_hook import (  # noqa: E402
    post_read,
    pre_write,
    session_start,
    stop,
    user_prompt_submit,
)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        return 0
    cmd = args[0]
    if cmd == "session-start":
        return session_start()
    if cmd == "post-read":
        return post_read()
    if cmd == "pre-write":
        return pre_write()
    if cmd in {"user-prompt", "user-prompt-submit"}:
        return user_prompt_submit()
    if cmd == "stop":
        return stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
