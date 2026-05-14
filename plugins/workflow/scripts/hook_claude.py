#!/usr/bin/env python3
"""Claude hook subtype and CLI entry point.

Hosts ``ClaudeHook`` (the runtime-bound hook for Claude Code) and
``UnknownHook`` (the fallback when the host runtime cannot be inferred).
Both inherit from the abstract ``Hook`` in :mod:`workflow_hook`; the base
also owns the module-level payload/env helpers reused here.

This module also doubles as the executable entry point for Claude's hook
manifest (``plugins/workflow/hooks/hooks.json``) and the SubagentStart hook
declared in ``plugins/workflow/agents/workflow-operator.md`` frontmatter.
Each event command invokes ``python3 hook_claude.py <subcommand>``; the
agent frontmatter invokes it with no argument, which defaults to
``subagent_start``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, TextIO

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from workflow_hook import (  # noqa: E402
    CLAUDE_SESSION_START_SOURCES,
    EditTarget,
    Hook,
    _claude_edit_target,
    _default_plugin_root,
    _payload_marks_agent,
    _read_target_default,
    _resolve_project_from_cwd,
    _session_start_source_value,
    _string,
    post_read,
    pre_write,
    session_start,
    stop,
    user_prompt_submit,
)
from workflow_operator_context import (  # noqa: E402
    build_operator_subagent_context,
    payload_targets_operator,
)


class ClaudeHook(Hook):
    @property
    def runtime(self) -> str:
        return "claude"

    def project_dir(self) -> Path | None:
        env_value = os.environ.get("CLAUDE_PROJECT_DIR")
        if env_value:
            return Path(env_value).expanduser().resolve()
        return _resolve_project_from_cwd(self.payload.get("cwd"))

    def plugin_root(self) -> Path:
        env_value = os.environ.get("CLAUDE_PLUGIN_ROOT")
        if env_value:
            return Path(env_value).expanduser().resolve()
        return _default_plugin_root()

    def session_id(self) -> str:
        return _string(self.payload, "session_id")

    def is_agent_session(self) -> bool:
        return _payload_marks_agent(self.payload)

    def edit_targets(self) -> tuple[EditTarget, ...]:
        return _claude_edit_target(self.payload, self.resolve_path)

    def read_target(self) -> Path | None:
        return _read_target_default(self.payload, self.resolve_path)

    def session_start_source(self) -> str:
        return _session_start_source_value(self.payload, CLAUDE_SESSION_START_SOURCES)

    def handle_subagent_start(self, *, stdout: TextIO | None = None) -> int:
        """SubagentStart for Claude: inject parent session id for workflow-operator."""

        output = stdout or sys.stdout
        if not payload_targets_operator(self.payload):
            return 0

        parent_session_id = self.session_id()
        if not parent_session_id:
            return 0

        config = self.workflow_config()
        if config is None:
            return 0

        context = build_operator_subagent_context(parent_session_id, config.root)
        self.emit(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SubagentStart",
                    "additionalContext": context,
                }
            },
            stdout=output,
        )
        return 0


class UnknownHook(ClaudeHook):
    """Fallback when the runtime cannot be inferred.

    Behaves like Claude for payload access but reports its own runtime name so
    callers can apply unknown-runtime policies (e.g.,
    ``should_skip_session_start_policy`` treats ``compact`` as a skip-worthy
    source for unknown runtimes the same way it does for Claude).
    """

    @property
    def runtime(self) -> str:
        return "unknown"


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
