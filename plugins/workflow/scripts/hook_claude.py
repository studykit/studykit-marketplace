#!/usr/bin/env python3
"""Claude hook CLI entry point.

Executable used by the Claude hook manifest (``plugins/workflow/hooks/hooks.json``)
and the SubagentStart hook declared in
``plugins/workflow/agents/workflow-operator.md`` frontmatter. Each event
command invokes ``python3 hook_claude.py <subcommand>``; the agent
frontmatter invokes it with no argument, which defaults to
``subagent_start``.

The Hook subtype itself (``ClaudeHook`` / ``UnknownHook``) lives in
:mod:`claude_hook`; the shared shims live in :mod:`workflow_hook`.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, TextIO

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from workflow_hook import (  # noqa: E402
    Hook,
    post_read,
    pre_write,
    session_start,
    stop,
    user_prompt_submit,
)


def subagent_start(
    payload: dict[str, Any] | None = None,
    *,
    stdout: TextIO | None = None,
) -> int:
    """Thin shim that delegates to ``ClaudeHook.handle_subagent_start``."""

    return Hook.from_payload_or_stdin(payload).handle_subagent_start(stdout=stdout)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        # Claude's SubagentStart fires this script with no argv from the
        # workflow-operator agent frontmatter.
        return subagent_start()
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
    if cmd == "subagent-start":
        return subagent_start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
