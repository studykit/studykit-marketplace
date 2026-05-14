#!/usr/bin/env python3
"""Hook input adapter strategy.

This module hosts the ``HookContext`` strategy that absorbs every runtime- or
event-shape-aware bit of payload/environment extraction the workflow hooks
need. ``ClaudeHookContext`` and ``CodexHookContext`` implement the runtime
specifics; ``hook_context(payload)`` is the factory.

Centralizing this surface keeps runtime conditionals out of hook entry points
and gives the codex transcript / Claude env-var variations a single home each.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

RUNTIME_ENV_VAR = "WORKFLOW_HOOK_RUNTIME"
STATE_DIR_ENV_VAR = "WORKFLOW_LEDGER_STATE_DIR"
CLAUDE_EDIT_TOOLS = {"Write", "Edit", "MultiEdit"}
CODEX_SESSION_START_SOURCES = {"startup", "resume", "clear"}
CLAUDE_SESSION_START_SOURCES = {"startup", "resume", "clear", "compact"}
_PAYLOAD_AGENT_BOOL_KEYS = ("is_agent", "is_subagent", "agent_session")
_PAYLOAD_AGENT_STRING_KEYS = (
    "agent_id",
    "agent_name",
    "agent_path",
    "subagent_id",
    "subagent_type",
    "parent_agent_id",
    "parent_session_id",
    "parent_thread_id",
    "parent_conversation_id",
)
_PAYLOAD_AGENT_SOURCE_KEYS = (
    "source",
    "session_type",
    "session_kind",
    "conversation_type",
    "invocation",
    "origin",
)
_AGENT_MARKER_VALUES = {"agent", "subagent", "sub_agent", "child_agent", "spawned_agent"}
_TRANSCRIPT_AGENT_KEYS = {
    "agent",
    "agent_id",
    "agent_name",
    "agent_nickname",
    "agent_path",
    "agent_role",
    "parent_thread_id",
    "subagent",
    "thread_spawn",
}


@dataclass(frozen=True)
class EditTarget:
    """Potential local workflow write target."""

    path: Path
    content: str | None = None


class HookContext(ABC):
    """Strategy interface for runtime-specific hook payload adapters."""

    def __init__(self, payload: Mapping[str, Any]) -> None:
        self.payload: dict[str, Any] = dict(payload)

    # ----- runtime identity -----

    @property
    @abstractmethod
    def runtime(self) -> str:
        ...

    # ----- runtime-aware extraction -----

    @abstractmethod
    def project_dir(self) -> Path | None:
        ...

    @abstractmethod
    def plugin_root(self) -> Path:
        ...

    @abstractmethod
    def session_id(self) -> str:
        ...

    @abstractmethod
    def is_agent_session(self) -> bool:
        ...

    @abstractmethod
    def edit_targets(self) -> tuple[EditTarget, ...]:
        ...

    @abstractmethod
    def read_target(self) -> Path | None:
        ...

    @abstractmethod
    def session_start_source(self) -> str:
        ...

    # ----- shared utilities -----

    def should_reinject_session_policy(self) -> bool:
        return self.session_start_source() == "clear"

    def should_skip_session_start_policy(self) -> bool:
        if self.session_start_source() != "compact":
            return False
        return self.runtime in {"claude", "unknown"}

    def resolve_path(self, raw_path: str) -> Path:
        path = Path(raw_path).expanduser()
        if path.is_absolute():
            return path.resolve(strict=False)

        cwd = self.payload.get("cwd")
        if isinstance(cwd, str) and cwd:
            base = Path(cwd).expanduser()
        else:
            project = self.project_dir()
            base = project if project is not None else Path.cwd()
        return (base / path).resolve(strict=False)

    def state_dir(self, override: Path | None = None) -> Path | None:
        if override is not None:
            return override.resolve()
        explicit = os.environ.get(STATE_DIR_ENV_VAR)
        if explicit:
            return Path(explicit).expanduser().resolve()
        return None

    def emit(self, payload: dict[str, Any], *, stdout: TextIO | None = None) -> None:
        output = stdout or sys.stdout
        json.dump(payload, output, ensure_ascii=False)
        output.write("\n")

    def subagent_metadata(self) -> tuple[str, str | None]:
        """Return (parent_thread_id, agent_name) from a subagent transcript.

        Default implementation is empty; only ``CodexHookContext`` populates
        this because Codex is the only runtime that surfaces subagent
        metadata through ``transcript_path``.
        """

        return "", None

    # ----- factories -----

    @classmethod
    def from_stdin(cls) -> "HookContext":
        return hook_context(_read_stdin_json())

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "HookContext":
        return hook_context(payload)

    # ----- shared payload helpers -----

    def _payload_marks_agent(self) -> bool:
        for key in _PAYLOAD_AGENT_BOOL_KEYS:
            if self.payload.get(key) is True:
                return True

        for key in _PAYLOAD_AGENT_STRING_KEYS:
            value = self.payload.get(key)
            if isinstance(value, str) and value.strip():
                return True

        agent_value = self.payload.get("agent")
        if isinstance(agent_value, Mapping) and agent_value:
            return True

        for key in _PAYLOAD_AGENT_SOURCE_KEYS:
            value = self.payload.get(key)
            if not isinstance(value, str):
                continue
            normalized = value.strip().lower().replace("-", "_")
            if normalized in _AGENT_MARKER_VALUES:
                return True

        return False

    def _session_start_source_value(self, allowed: set[str]) -> str:
        value = self.payload.get("source")
        if not isinstance(value, str):
            return ""
        source = value.strip().lower()
        return source if source in allowed else ""

    def _claude_edit_target(self) -> tuple[EditTarget, ...]:
        tool_name = self.payload.get("tool_name")
        tool_input = self.payload.get("tool_input") or {}
        if not isinstance(tool_input, dict) or tool_name not in CLAUDE_EDIT_TOOLS:
            return ()
        file_path = tool_input.get("file_path") or ""
        if not isinstance(file_path, str) or not file_path:
            return ()
        path = self.resolve_path(file_path)
        content = tool_input.get("content") if tool_name == "Write" else None
        if not isinstance(content, str):
            content = None
        return (EditTarget(path=path, content=content),)

    def _read_target_default(self) -> Path | None:
        if self.payload.get("tool_name") != "Read":
            return None
        tool_input = self.payload.get("tool_input") or {}
        if not isinstance(tool_input, dict):
            return None
        file_path = tool_input.get("file_path") or tool_input.get("path") or ""
        if not isinstance(file_path, str) or not file_path:
            return None
        return self.resolve_path(file_path)


class ClaudeHookContext(HookContext):
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
        value = self.payload.get("session_id")
        return value if isinstance(value, str) and value else ""

    def is_agent_session(self) -> bool:
        return self._payload_marks_agent()

    def edit_targets(self) -> tuple[EditTarget, ...]:
        return self._claude_edit_target()

    def read_target(self) -> Path | None:
        return self._read_target_default()

    def session_start_source(self) -> str:
        return self._session_start_source_value(CLAUDE_SESSION_START_SOURCES)


class CodexHookContext(HookContext):
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
            value = self.payload.get(key)
            if isinstance(value, str) and value:
                return value
        return ""

    def is_agent_session(self) -> bool:
        if self._payload_marks_agent():
            return True
        return self._transcript_marks_agent()

    def edit_targets(self) -> tuple[EditTarget, ...]:
        tool_name = self.payload.get("tool_name")
        tool_input = self.payload.get("tool_input") or {}
        if not isinstance(tool_input, dict):
            return ()
        if tool_name in CLAUDE_EDIT_TOOLS:
            return self._claude_edit_target()
        if tool_name == "apply_patch":
            command = tool_input.get("command") or ""
            if not isinstance(command, str) or not command:
                return ()
            return self._apply_patch_targets(command)
        return ()

    def read_target(self) -> Path | None:
        return self._read_target_default()

    def session_start_source(self) -> str:
        return self._session_start_source_value(CODEX_SESSION_START_SOURCES)

    def subagent_metadata(self) -> tuple[str, str | None]:
        metadata = self._read_session_meta()
        if metadata is None:
            return "", None
        return (
            _parent_thread_id_from_metadata(metadata),
            _agent_name_from_metadata(metadata),
        )

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


class UnknownHookContext(ClaudeHookContext):
    """Fallback when the runtime cannot be inferred.

    Behaves like Claude for payload access but reports its own runtime name so
    callers can apply unknown-runtime policies (e.g.,
    ``should_skip_session_start_policy`` treats ``compact`` as a skip-worthy
    source for unknown runtimes the same way it does for Claude).
    """

    @property
    def runtime(self) -> str:
        return "unknown"


def hook_context(payload: Mapping[str, Any]) -> HookContext:
    runtime = _detect_runtime(payload)
    if runtime == "codex":
        return CodexHookContext(payload)
    if runtime == "claude":
        return ClaudeHookContext(payload)
    return UnknownHookContext(payload)


def _detect_runtime(payload: Mapping[str, Any]) -> str:
    runtime = os.environ.get(RUNTIME_ENV_VAR, "").strip().lower()
    if runtime in {"claude", "codex"}:
        return runtime
    if payload.get("turn_id"):
        return "codex"
    return "unknown"


def _resolve_project_from_cwd(cwd: Any) -> Path | None:
    if not isinstance(cwd, str) or not cwd:
        cwd = os.getcwd()
    if not isinstance(cwd, str) or not cwd:
        return None
    cwd_path = Path(cwd).expanduser().resolve()
    try:
        proc = subprocess.run(
            ["git", "-C", str(cwd_path), "rev-parse", "--show-toplevel"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return cwd_path
    root = proc.stdout.strip()
    if not root:
        return cwd_path
    return Path(root).expanduser().resolve()


def _default_plugin_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _read_stdin_json() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
    except OSError:
        return {}
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _session_metadata_indicates_agent(metadata: Any) -> bool:
    if not isinstance(metadata, Mapping):
        return False

    thread_source = metadata.get("thread_source")
    if isinstance(thread_source, str):
        normalized = thread_source.strip().lower().replace("-", "_")
        if normalized in _AGENT_MARKER_VALUES:
            return True

    source = metadata.get("source")
    if isinstance(source, Mapping) and _mapping_has_agent_marker(source):
        return True

    for key in ("agent_role", "agent_nickname", "agent_path"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return True

    return False


def _mapping_has_agent_marker(value: Mapping[str, Any]) -> bool:
    for key, item in value.items():
        if isinstance(key, str) and key in _TRANSCRIPT_AGENT_KEYS:
            return True
        if isinstance(item, Mapping) and _mapping_has_agent_marker(item):
            return True
    return False


def _parent_thread_id_from_metadata(metadata: Mapping[str, Any]) -> str:
    direct = metadata.get("parent_thread_id")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    source = metadata.get("source")
    if isinstance(source, Mapping):
        subagent = source.get("subagent")
        if isinstance(subagent, Mapping):
            spawn = subagent.get("thread_spawn")
            if isinstance(spawn, Mapping):
                value = spawn.get("parent_thread_id")
                if isinstance(value, str) and value.strip():
                    return value.strip()
    return ""


def _agent_name_from_metadata(metadata: Mapping[str, Any]) -> str | None:
    for key in ("agent_name", "agent_role", "agent_nickname", "agent_path"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    source = metadata.get("source")
    if isinstance(source, Mapping):
        subagent = source.get("subagent")
        if isinstance(subagent, Mapping):
            for key in ("agent_name", "agent_role", "agent_nickname"):
                value = subagent.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            spawn = subagent.get("thread_spawn")
            if isinstance(spawn, Mapping):
                for key in ("agent_name", "agent_role"):
                    value = spawn.get(key)
                    if isinstance(value, str) and value.strip():
                        return value.strip()
    return None
