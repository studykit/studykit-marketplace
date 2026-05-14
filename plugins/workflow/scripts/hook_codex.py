#!/usr/bin/env python3
"""Codex hook adapter and CLI entry point.

This module owns Codex payload and environment handling. Shared workflow policy
and issue-cache behavior lives in ``workflow_hook.py`` as plain functions.

Codex exposes ``SessionStart``, ``UserPromptSubmit``, and ``Stop`` events for
this plugin. The PreToolUse authoring-guard pair from Claude is not wired on
Codex because Codex has no ``Read`` tool: file reads happen through ``Bash``
or MCP tools whose names vary, so the read ledger cannot be populated, and
the matching write guard would block unconditionally. See the manifest
description for the resulting Codex feature surface.

Codex has no native ``SubagentStart`` event, so the operator-subagent context
emission rides on the Codex ``SessionStart`` path when the transcript metadata
identifies the spawned agent as ``workflow-operator``.

The script is the executable entry point for Codex's hook manifest
(``plugins/workflow/hooks/hooks.codex.json``). Dispatch reads
``hook_event_name`` from the payload (per the official Codex schema). When
this adapter writes hook output to stdout, it writes JSON only; no plain-text
hook output is used.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from workflow_command import CommandRunner  # noqa: E402
from workflow_hook import (  # noqa: E402
    build_session_start_context,
    inject_prompt_issue_context,
    record_stop_issue_references,
    workflow_config_for_project,
)
from util import as_string, emit_json, read_payload_or_stdin, scan_text_values  # noqa: E402
from workflow_env import write_codex_env_file  # noqa: E402
from workflow_operator_context import (  # noqa: E402
    agent_name_matches_operator,
    build_operator_subagent_context,
)
from workflow_session_state import (  # noqa: E402
    record_session_policy_announced,
    session_policy_was_announced,
)

CODEX_SESSION_START_SOURCES = {"startup", "resume", "clear"}
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
class CodexCommonPayload:
    raw: dict[str, Any]
    event_name: str
    session_id: str
    transcript_path: str
    cwd: str
    model: str


@dataclass(frozen=True)
class CodexSessionStartPayload(CodexCommonPayload):
    source: str


@dataclass(frozen=True)
class CodexUserPromptSubmitPayload(CodexCommonPayload):
    turn_id: str
    prompt_text: str


@dataclass(frozen=True)
class CodexStopPayload(CodexCommonPayload):
    turn_id: str
    stop_hook_active: bool
    last_assistant_message: str
    scan_text: str


CodexEventPayload = (
    CodexSessionStartPayload
    | CodexUserPromptSubmitPayload
    | CodexStopPayload
)


def _resolve_project_from_cwd(cwd: str) -> Path | None:
    candidate = cwd if cwd else os.getcwd()
    if not candidate:
        return None
    cwd_path = Path(candidate).expanduser().resolve()
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


def _project_dir(event_payload: CodexCommonPayload) -> Path | None:
    return _resolve_project_from_cwd(event_payload.cwd)


def _plugin_root() -> Path:
    return Path(os.environ["PLUGIN_ROOT"]).expanduser().resolve()


def _persist_codex_shell_env(
    *,
    project_dir: Path,
    codex_session_id: str,
    workflow_session_id: str,
) -> None:
    write_codex_env_file(
        project_dir=project_dir,
        plugin_root=_plugin_root(),
        codex_session_id=codex_session_id,
        workflow_session_id=workflow_session_id,
    )


def _session_start_source(payload: dict[str, Any]) -> str:
    source = as_string(payload.get("source")).lower()
    return source if source in CODEX_SESSION_START_SOURCES else ""


def _user_prompt_text(payload: dict[str, Any]) -> str:
    return as_string(payload.get("prompt"))


def _stop_scan_text(payload: dict[str, Any]) -> str:
    return scan_text_values(as_string(payload.get("last_assistant_message")))


def _payload_marks_agent(payload: Mapping[str, Any]) -> bool:
    for key in _PAYLOAD_AGENT_BOOL_KEYS:
        if payload.get(key) is True:
            return True

    for key in _PAYLOAD_AGENT_STRING_KEYS:
        if as_string(payload.get(key)):
            return True

    agent_value = payload.get("agent")
    if isinstance(agent_value, Mapping) and agent_value:
        return True

    for key in _PAYLOAD_AGENT_SOURCE_KEYS:
        value = payload.get(key)
        if not isinstance(value, str):
            continue
        if value.strip().lower().replace("-", "_") in _AGENT_MARKER_VALUES:
            return True

    return False


def _session_metadata_indicates_agent(metadata: Mapping[str, Any]) -> bool:
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


def _read_session_meta(transcript_path: str) -> Mapping[str, Any] | None:
    if not transcript_path:
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


def _parent_thread_id_from_metadata(metadata: Mapping[str, Any]) -> str:
    direct = as_string(metadata.get("parent_thread_id"))
    if direct:
        return direct
    spawn = _nested_mapping(metadata, "source", "subagent", "thread_spawn")
    if spawn is not None:
        return as_string(spawn.get("parent_thread_id"))
    return ""


def _agent_name_from_metadata(metadata: Mapping[str, Any]) -> str:
    for key in ("agent_name", "agent_role", "agent_nickname", "agent_path"):
        value = as_string(metadata.get(key))
        if value:
            return value
    subagent = _nested_mapping(metadata, "source", "subagent")
    if subagent is not None:
        for key in ("agent_name", "agent_role", "agent_nickname"):
            value = as_string(subagent.get(key))
            if value:
                return value
        spawn = subagent.get("thread_spawn")
        if isinstance(spawn, Mapping):
            for key in ("agent_name", "agent_role"):
                value = as_string(spawn.get(key))
                if value:
                    return value
    return ""


def _nested_mapping(root: Mapping[str, Any], *keys: str) -> Mapping[str, Any] | None:
    current: Any = root
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current if isinstance(current, Mapping) else None


def _common_payload_fields(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "raw": payload,
        "event_name": as_string(payload.get("hook_event_name")),
        "session_id": as_string(payload.get("session_id")),
        "transcript_path": as_string(payload.get("transcript_path")),
        "cwd": as_string(payload.get("cwd")),
        "model": as_string(payload.get("model")),
    }


def _build_session_start_payload(payload: dict[str, Any]) -> CodexSessionStartPayload:
    return CodexSessionStartPayload(
        **_common_payload_fields(payload),
        source=_session_start_source(payload),
    )


def _build_user_prompt_submit_payload(
    payload: dict[str, Any],
) -> CodexUserPromptSubmitPayload:
    return CodexUserPromptSubmitPayload(
        **_common_payload_fields(payload),
        turn_id=as_string(payload.get("turn_id")),
        prompt_text=_user_prompt_text(payload),
    )


def _build_stop_payload(payload: dict[str, Any]) -> CodexStopPayload:
    return CodexStopPayload(
        **_common_payload_fields(payload),
        turn_id=as_string(payload.get("turn_id")),
        stop_hook_active=payload.get("stop_hook_active") is True,
        last_assistant_message=as_string(payload.get("last_assistant_message")),
        scan_text=_stop_scan_text(payload),
    )


def parse_codex_event_payload(
    payload: Mapping[str, Any] | None = None,
) -> CodexEventPayload | None:
    """Parse the Codex hook payload, dispatching by ``hook_event_name``."""

    data = read_payload_or_stdin(payload)
    event_name = as_string(data.get("hook_event_name"))
    if event_name == "SessionStart":
        return _build_session_start_payload(data)
    if event_name == "UserPromptSubmit":
        return _build_user_prompt_submit_payload(data)
    if event_name == "Stop":
        return _build_stop_payload(data)
    return None


def session_start(
    event_payload: CodexSessionStartPayload,
    *,
    stdout: TextIO | None = None,
) -> int:
    """Handle a Codex ``SessionStart`` hook invocation."""

    metadata = _read_session_meta(event_payload.transcript_path)
    payload_marks_agent = _payload_marks_agent(event_payload.raw)
    metadata_marks_agent = metadata is not None and _session_metadata_indicates_agent(metadata)
    if payload_marks_agent or metadata_marks_agent:
        return _handle_agent_session_start(event_payload, metadata, stdout=stdout)
    return emit_session_start_policy(event_payload, stdout=stdout)


def _handle_agent_session_start(
    event_payload: CodexSessionStartPayload,
    metadata: Mapping[str, Any] | None,
    *,
    stdout: TextIO | None = None,
) -> int:
    """Codex subagent SessionStart: emit operator context when matched."""

    if metadata is None:
        return 0
    parent_thread_id = _parent_thread_id_from_metadata(metadata)
    if not parent_thread_id:
        return 0
    agent_name = _agent_name_from_metadata(metadata)
    if not agent_name_matches_operator(agent_name):
        return 0

    config = workflow_config_for_project(_project_dir(event_payload))
    if config is None:
        return 0

    _persist_codex_shell_env(
        project_dir=config.root,
        codex_session_id=event_payload.session_id,
        workflow_session_id=parent_thread_id,
    )

    emit_json(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": build_operator_subagent_context(
                    parent_thread_id,
                    config.root,
                ),
            }
        },
        stdout=stdout,
    )
    return 0


def emit_session_start_policy(
    event_payload: CodexSessionStartPayload,
    *,
    stdout: TextIO | None = None,
) -> int:
    """Emit the Codex workflow authoring policy for a main session."""

    config = workflow_config_for_project(_project_dir(event_payload))
    if config is None:
        return 0

    _persist_codex_shell_env(
        project_dir=config.root,
        codex_session_id=event_payload.session_id,
        workflow_session_id=event_payload.session_id,
    )

    if event_payload.source != "clear" and session_policy_was_announced(
        config.root, "codex", event_payload.session_id,
    ):
        return 0

    emit_json(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": build_session_start_context(config, _plugin_root()),
            }
        },
        stdout=stdout,
    )
    record_session_policy_announced(config.root, "codex", event_payload.session_id)
    return 0


def user_prompt_submit(
    event_payload: CodexUserPromptSubmitPayload,
    *,
    stdout: TextIO | None = None,
    runner: CommandRunner | None = None,
) -> int:
    """Handle a Codex ``UserPromptSubmit`` hook invocation."""

    return inject_prompt_issue_context(
        project_dir=_project_dir(event_payload),
        session_id=event_payload.session_id,
        prompt_text=event_payload.prompt_text,
        stdout=stdout,
        runner=runner,
    )


def stop(
    event_payload: CodexStopPayload,
    *,
    stdout: TextIO | None = None,
    runner: CommandRunner | None = None,
) -> int:
    """Handle a Codex ``Stop`` hook invocation."""

    return record_stop_issue_references(
        project_dir=_project_dir(event_payload),
        session_id=event_payload.session_id,
        scan_text=event_payload.scan_text,
        stop_hook_active=event_payload.stop_hook_active,
        stdout=stdout,
        runner=runner,
    )


def main(
    argv: list[str] | None = None,
    *,
    payload: Mapping[str, Any] | None = None,
    stdout: TextIO | None = None,
) -> int:
    _ = argv
    event_payload = parse_codex_event_payload(payload)
    if isinstance(event_payload, CodexSessionStartPayload):
        return session_start(event_payload, stdout=stdout)
    if isinstance(event_payload, CodexUserPromptSubmitPayload):
        return user_prompt_submit(event_payload, stdout=stdout)
    if isinstance(event_payload, CodexStopPayload):
        return stop(event_payload, stdout=stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
