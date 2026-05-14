#!/usr/bin/env python3
"""Claude hook implementations.

Hosts ``ClaudeHook`` (the runtime-bound hook for Claude Code) and
``UnknownHook`` (the fallback when the host runtime cannot be inferred).
Both inherit from the abstract ``Hook`` in :mod:`workflow_hook`; the base
also owns the module-level payload/env helpers reused here.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TextIO

from workflow_hook import (
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
)
from workflow_operator_context import (
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

        import sys

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
