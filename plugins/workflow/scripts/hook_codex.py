#!/usr/bin/env python3
"""Codex hook adapter and CLI entry point.

This module owns Codex payload and environment handling. Shared workflow policy,
ledger, guard, and issue-cache behavior lives in ``workflow_hook.py`` as plain
functions.

Codex has no native ``SubagentStart`` event, so the operator-subagent context
emission rides on the Codex ``SessionStart`` path when the transcript metadata
identifies the spawned agent as ``workflow-operator``.

The script is the executable entry point for Codex's hook manifest
(``plugins/workflow/hooks/hooks.codex.json``). Each event command invokes
``python3 hook_codex.py <subcommand>``. When this adapter writes hook output to
stdout, it writes JSON only; no plain-text hook output is used.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TextIO

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from workflow_command import CommandRunner  # noqa: E402
from workflow_hook import (  # noqa: E402
    EditTarget,
    block_unread_authoring_write,
    build_session_start_context,
    inject_prompt_issue_context,
    record_authoring_read,
    record_stop_issue_references,
    workflow_config_for_project,
)
from util import as_string, emit_json, read_payload_or_stdin, resolve_file_path, scan_text_values  # noqa: E402
from workflow_operator_context import (  # noqa: E402
    agent_name_matches_operator,
    build_operator_subagent_context,
)
from workflow_session_state import (  # noqa: E402
    record_session_policy_announced,
    session_policy_was_announced,
)

CODEX_FILE_EDIT_ALIASES = {"Write", "Edit", "MultiEdit"}
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


def _project_dir(payload: dict[str, Any]) -> Path | None:
    return _resolve_project_from_cwd(payload.get("cwd"))


def _plugin_root() -> Path:
    return Path(os.environ["PLUGIN_ROOT"]).expanduser().resolve()


def _session_id(payload: dict[str, Any]) -> str:
    for key in ("session_id", "turn_id"):
        value = as_string(payload.get(key))
        if value:
            return value
    return ""


def _path_base_dir(payload: dict[str, Any]) -> Path:
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        return Path(cwd).expanduser()
    return _project_dir(payload) or Path.cwd()


def _resolve_path(payload: dict[str, Any], raw_path: str) -> Path:
    return resolve_file_path(raw_path, base_dir=_path_base_dir(payload))


def _edit_targets(payload: dict[str, Any]) -> tuple[EditTarget, ...]:
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return ()
    if tool_name in CODEX_FILE_EDIT_ALIASES:
        file_path = as_string(tool_input.get("file_path"))
        if not file_path:
            return ()
        content = tool_input.get("content") if tool_name == "Write" else None
        if not isinstance(content, str):
            content = None
        return (EditTarget(path=_resolve_path(payload, file_path), content=content),)
    if tool_name == "apply_patch":
        command = as_string(tool_input.get("command"))
        if not command:
            return ()
        return _apply_patch_targets(payload, command)
    return ()


def _read_target(payload: dict[str, Any]) -> Path | None:
    if payload.get("tool_name") != "Read":
        return None
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return None
    file_path = as_string(tool_input.get("file_path")) or as_string(tool_input.get("path"))
    if not file_path:
        return None
    return _resolve_path(payload, file_path)


def _user_prompt_text(payload: dict[str, Any]) -> str:
    return as_string(payload.get("prompt"))


def _stop_scan_text(payload: dict[str, Any]) -> str:
    return scan_text_values(as_string(payload.get("last_assistant_message")))


def _session_start_source(payload: dict[str, Any]) -> str:
    source = as_string(payload.get("source")).lower()
    return source if source in CODEX_SESSION_START_SOURCES else ""


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


def _is_agent_session(payload: dict[str, Any]) -> bool:
    if _payload_marks_agent(payload):
        return True
    return _transcript_marks_agent(payload)


def _subagent_metadata(payload: dict[str, Any]) -> tuple[str, str | None]:
    metadata = _read_session_meta(payload)
    if metadata is None:
        return "", None
    return (
        _parent_thread_id_from_metadata(metadata),
        _agent_name_from_metadata(metadata),
    )


def _handle_agent_session_start(
    payload: dict[str, Any],
    *,
    stdout: TextIO | None = None,
) -> int:
    """Codex subagent SessionStart: emit operator context when matched."""

    parent_thread_id, agent_name = _subagent_metadata(payload)
    if not parent_thread_id or not agent_name_matches_operator(agent_name):
        return 0

    config = workflow_config_for_project(_project_dir(payload))
    if config is None:
        return 0

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


def _apply_patch_targets(payload: dict[str, Any], command: str) -> tuple[EditTarget, ...]:
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
            out.append(EditTarget(path=current_path, content="\n".join(current_added) + "\n"))
        current_path = None
        current_added = None

    for line in command.splitlines():
        if line.startswith("*** Add File: "):
            flush_add()
            raw_path = line.removeprefix("*** Add File: ").strip()
            current_path = _resolve_path(payload, raw_path)
            current_added = []
            continue

        if line.startswith("*** Update File: ") or line.startswith("*** Delete File: "):
            flush_add()
            raw_path = line.split(": ", 1)[1].strip()
            path = _resolve_path(payload, raw_path)
            if path not in seen:
                seen.add(path)
                out.append(EditTarget(path=path))
            continue

        if line.startswith("*** Move to: "):
            raw_path = line.removeprefix("*** Move to: ").strip()
            path = _resolve_path(payload, raw_path)
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


def _transcript_marks_agent(payload: dict[str, Any]) -> bool:
    metadata = _read_session_meta(payload)
    if metadata is None:
        return False
    return _session_metadata_indicates_agent(metadata)


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


def _read_session_meta(payload: dict[str, Any]) -> Mapping[str, Any] | None:
    transcript_path = payload.get("transcript_path")
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


def _parent_thread_id_from_metadata(metadata: Mapping[str, Any]) -> str:
    direct = as_string(metadata.get("parent_thread_id"))
    if direct:
        return direct
    spawn = _nested_mapping(metadata, "source", "subagent", "thread_spawn")
    if spawn is not None:
        return as_string(spawn.get("parent_thread_id"))
    return ""


def _agent_name_from_metadata(metadata: Mapping[str, Any]) -> str | None:
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
    return None


def _nested_mapping(root: Mapping[str, Any], *keys: str) -> Mapping[str, Any] | None:
    current: Any = root
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current if isinstance(current, Mapping) else None


def session_start(
    payload: dict[str, Any] | None = None,
    *,
    stdout: TextIO | None = None,
) -> int:
    """Handle a Codex ``SessionStart`` hook invocation."""

    data = read_payload_or_stdin(payload)
    if _is_agent_session(data):
        return _handle_agent_session_start(data, stdout=stdout)

    return emit_session_start_policy(data, stdout=stdout)


def emit_session_start_policy(
    payload: dict[str, Any],
    *,
    stdout: TextIO | None = None,
) -> int:
    """Emit the Codex workflow authoring policy for a main session."""

    config = workflow_config_for_project(_project_dir(payload))
    if config is None:
        return 0

    source = _session_start_source(payload)
    session_id = _session_id(payload)
    if source != "clear" and session_policy_was_announced(config.root, "codex", session_id):
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
    record_session_policy_announced(config.root, "codex", session_id)
    return 0


def post_read(
    payload: dict[str, Any] | None = None,
    *,
    stdout: TextIO | None = None,
    state_dir: Path | None = None,
) -> int:
    """Handle a Codex ``PostToolUse`` Read hook invocation."""

    data = read_payload_or_stdin(payload)
    return record_authoring_read(
        project_dir=_project_dir(data),
        plugin_root=_plugin_root(),
        session_id=_session_id(data),
        read_target=_read_target(data),
        state_dir=state_dir,
        stdout=stdout,
    )


def pre_write(
    payload: dict[str, Any] | None = None,
    *,
    stdout: TextIO | None = None,
    state_dir: Path | None = None,
) -> int:
    """Handle a Codex ``PreToolUse`` write hook invocation."""

    data = read_payload_or_stdin(payload)
    return block_unread_authoring_write(
        project_dir=_project_dir(data),
        session_id=_session_id(data),
        edit_targets=_edit_targets(data),
        state_dir=state_dir,
        stdout=stdout,
    )


def user_prompt_submit(
    payload: dict[str, Any] | None = None,
    *,
    stdout: TextIO | None = None,
    runner: CommandRunner | None = None,
) -> int:
    """Handle a Codex ``UserPromptSubmit`` hook invocation."""

    data = read_payload_or_stdin(payload)
    return inject_prompt_issue_context(
        project_dir=_project_dir(data),
        session_id=_session_id(data),
        prompt_text=_user_prompt_text(data),
        stdout=stdout,
        runner=runner,
    )


def stop(
    payload: dict[str, Any] | None = None,
    *,
    stdout: TextIO | None = None,
    runner: CommandRunner | None = None,
) -> int:
    """Handle a Codex ``Stop`` hook invocation."""

    data = read_payload_or_stdin(payload)
    return record_stop_issue_references(
        project_dir=_project_dir(data),
        session_id=_session_id(data),
        scan_text=_stop_scan_text(data),
        stop_hook_active=data.get("stop_hook_active") is True,
        stdout=stdout,
        runner=runner,
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
