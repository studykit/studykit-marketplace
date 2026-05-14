#!/usr/bin/env python3
"""Workflow operator subagent start hook.

Dedicated entry point invoked from ``plugins/workflow/agents/workflow-operator.md``
frontmatter when Claude spawns the workflow-operator subagent. Delegates to
``ClaudeHook.handle_subagent_start`` for the actual context emission.

Codex has no ``SubagentStart`` event; its equivalent path lives in
``CodexHook.handle_session_start`` and uses the same operator context helpers.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, TextIO

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from workflow_hook import Hook  # noqa: E402


def subagent_start(
    payload: dict[str, Any] | None = None,
    *,
    stdout: TextIO | None = None,
) -> int:
    """Thin shim that delegates to ``ClaudeHook.handle_subagent_start``."""

    return Hook.from_payload_or_stdin(payload).handle_subagent_start(stdout=stdout)


def main() -> int:
    return subagent_start()


if __name__ == "__main__":
    raise SystemExit(main())
