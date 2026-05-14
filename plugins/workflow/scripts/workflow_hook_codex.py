#!/usr/bin/env python3
"""Codex hook implementation.

Hosts ``CodexHook``, the runtime-bound hook for Codex CLI. Inherits the
abstract ``Hook`` from :mod:`workflow_hook`; payload/env helpers and
operator-context helpers come from the same module.

Codex has no native ``SubagentStart`` event, so the operator-subagent
context emission rides on ``handle_session_start`` via the
``_handle_agent_session_start`` override.
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TextIO

from workflow_hook import (
    CLAUDE_EDIT_TOOLS,
    CODEX_SESSION_START_SOURCES,
    EditTarget,
    Hook,
    _agent_name_from_metadata,
    _claude_edit_target,
    _default_plugin_root,
    _parent_thread_id_from_metadata,
    _payload_marks_agent,
    _read_target_default,
    _resolve_project_from_cwd,
    _session_metadata_indicates_agent,
    _session_start_source_value,
    _string,
)
from workflow_operator_context import (
    agent_name_matches_operator,
    build_operator_subagent_context,
)


class CodexHook(Hook):
    @property
    def runtime(self) -> str:
        return "codex"

    def project_dir(self) -> Path | None:
        return _resolve_project_from_cwd(self.payload.get("cwd"))

    def plugin_root(self) -> Path:
        env_value = os.environ.get("PLUGIN_ROOT")
        if env_value:
            return Path(env_value).expanduser().resolve()
        return _default_plugin_root()

    def session_id(self) -> str:
        for key in ("session_id", "turn_id"):
            value = _string(self.payload, key)
            if value:
                return value
        return ""

    def is_agent_session(self) -> bool:
        if _payload_marks_agent(self.payload):
            return True
        return self._transcript_marks_agent()

    def edit_targets(self) -> tuple[EditTarget, ...]:
        tool_name = self.payload.get("tool_name")
        tool_input = self.payload.get("tool_input") or {}
        if not isinstance(tool_input, dict):
            return ()
        if tool_name in CLAUDE_EDIT_TOOLS:
            return _claude_edit_target(self.payload, self.resolve_path)
        if tool_name == "apply_patch":
            command = _string(tool_input, "command")
            if not command:
                return ()
            return self._apply_patch_targets(command)
        return ()

    def read_target(self) -> Path | None:
        return _read_target_default(self.payload, self.resolve_path)

    def session_start_source(self) -> str:
        return _session_start_source_value(self.payload, CODEX_SESSION_START_SOURCES)

    def subagent_metadata(self) -> tuple[str, str | None]:
        metadata = self._read_session_meta()
        if metadata is None:
            return "", None
        return (
            _parent_thread_id_from_metadata(metadata),
            _agent_name_from_metadata(metadata),
        )

    def _handle_agent_session_start(self, *, stdout: TextIO | None = None) -> int:
        """Codex subagent SessionStart: emit operator context when matched."""

        output = stdout or sys.stdout
        parent_thread_id, agent_name = self.subagent_metadata()
        if not parent_thread_id or not agent_name_matches_operator(agent_name):
            return 0

        config = self.workflow_config()
        if config is None:
            return 0

        context = build_operator_subagent_context(parent_thread_id, config.root)
        self.emit(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": context,
                }
            },
            stdout=output,
        )
        return 0

    def _apply_patch_targets(self, command: str) -> tuple[EditTarget, ...]:
        out: list[EditTarget] = []
        seen: set[Path] = set()
        current_path: Path | None = None
        current_added: list[str] | None = None

        def flush_add() -> None:
            nonlocal current_path, current_added
            if current_path is None or current_added is None:
                return
            if current_path not in seen:
                seen.add(current_path)
                out.append(
                    EditTarget(path=current_path, content="\n".join(current_added) + "\n")
                )
            current_path = None
            current_added = None

        for line in command.splitlines():
            if line.startswith("*** Add File: "):
                flush_add()
                raw_path = line.removeprefix("*** Add File: ").strip()
                current_path = self.resolve_path(raw_path)
                current_added = []
                continue

            if line.startswith("*** Update File: ") or line.startswith("*** Delete File: "):
                flush_add()
                raw_path = line.split(": ", 1)[1].strip()
                path = self.resolve_path(raw_path)
                if path not in seen:
                    seen.add(path)
                    out.append(EditTarget(path=path))
                continue

            if line.startswith("*** Move to: "):
                raw_path = line.removeprefix("*** Move to: ").strip()
                path = self.resolve_path(raw_path)
                if path not in seen:
                    seen.add(path)
                    out.append(EditTarget(path=path))
                continue

            if line.startswith("*** ") and current_added is not None:
                flush_add()
                continue

            if current_added is not None and line.startswith("+"):
                current_added.append(line[1:])

        flush_add()
        return tuple(out)

    def _transcript_marks_agent(self) -> bool:
        metadata = self._read_session_meta()
        if metadata is None:
            return False
        return _session_metadata_indicates_agent(metadata)

    def _read_session_meta(self) -> Mapping[str, Any] | None:
        transcript_path = self.payload.get("transcript_path")
        if not isinstance(transcript_path, str) or not transcript_path:
            return None
        path = Path(transcript_path).expanduser()
        if not path.is_file():
            return None
        try:
            with path.open("r", encoding="utf-8") as handle:
                for index, line in enumerate(handle):
                    if index >= 8:
                        break
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(event, Mapping) or event.get("type") != "session_meta":
                        continue
                    metadata = event.get("payload")
                    if isinstance(metadata, Mapping):
                        return metadata
        except OSError:
            return None
        return None
