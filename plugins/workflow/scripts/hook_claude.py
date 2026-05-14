#!/usr/bin/env python3
"""Claude hook adapter and CLI entry point.

This module owns Claude Code payload and environment handling. Shared workflow
policy, ledger, guard, and issue-cache behavior lives in ``workflow_hook.py``
as plain functions.

The script is the executable entry point for Claude's hook manifest
(``plugins/workflow/hooks/hooks.json``). Each hook command invokes ``python3
hook_claude.py``; ``main`` dispatches by the ``hook_event_name`` value in the
hook payload. When this adapter writes hook output to stdout, it writes JSON
only; no plain-text hook output is used.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import os
import sys
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
from workflow_env import (  # noqa: E402
    CLAUDE_ENV_FILE_ENV,
    append_claude_env_file,
)
from workflow_session_state import (  # noqa: E402
    record_session_policy_announced,
    session_policy_was_announced,
)

CLAUDE_FILE_EDIT_TOOLS = {"Write", "Edit", "MultiEdit"}


@dataclass(frozen=True)
class ClaudeCommonPayload:
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: str


@dataclass(frozen=True)
class ClaudeSessionStartPayload(ClaudeCommonPayload):
    source: str
    model: str | None
    agent_type: str | None


@dataclass(frozen=True)
class ClaudePreToolUsePayload(ClaudeCommonPayload):
    permission_mode: str | None
    effort: dict[str, Any] | None
    agent_id: str | None
    agent_type: str | None
    tool_name: str
    tool_input: dict[str, Any]
    tool_use_id: str | None


@dataclass(frozen=True)
class ClaudePostToolUsePayload(ClaudeCommonPayload):
    permission_mode: str | None
    effort: dict[str, Any] | None
    agent_id: str | None
    agent_type: str | None
    tool_name: str
    tool_input: dict[str, Any]
    tool_response: Any
    tool_use_id: str | None
    duration_ms: int | None


@dataclass(frozen=True)
class ClaudeUserPromptSubmitPayload(ClaudeCommonPayload):
    permission_mode: str | None
    agent_id: str | None
    agent_type: str | None
    prompt: str


@dataclass(frozen=True)
class ClaudeStopPayload(ClaudeCommonPayload):
    permission_mode: str | None
    effort: dict[str, Any] | None
    agent_id: str | None
    agent_type: str | None
    stop_hook_active: bool
    last_assistant_message: str


ClaudeEventPayload = (
    ClaudeSessionStartPayload
    | ClaudePreToolUsePayload
    | ClaudePostToolUsePayload
    | ClaudeUserPromptSubmitPayload
    | ClaudeStopPayload
)


def _project_dir() -> Path:
    return Path(os.environ["CLAUDE_PROJECT_DIR"]).expanduser().resolve()


def _plugin_root() -> Path:
    return Path(os.environ["CLAUDE_PLUGIN_ROOT"]).expanduser().resolve()


def _persist_shell_env(project_dir: Path, session_id: str) -> None:
    append_claude_env_file(
        env_file=os.environ.get(CLAUDE_ENV_FILE_ENV, ""),
        project_dir=project_dir,
        plugin_root=_plugin_root(),
        session_id=session_id,
    )


def _resolve_path(raw_path: str) -> Path:
    return resolve_file_path(raw_path, base_dir=_project_dir())


def _edit_targets(
    tool_name: str,
    tool_input: Mapping[str, Any],
) -> tuple[EditTarget, ...]:
    if not isinstance(tool_input, dict) or tool_name not in CLAUDE_FILE_EDIT_TOOLS:
        return ()
    file_path = as_string(tool_input.get("file_path"))
    if not file_path:
        return ()
    content = tool_input.get("content") if tool_name == "Write" else None
    if not isinstance(content, str):
        content = None
    return (EditTarget(path=_resolve_path(file_path), content=content),)


def _read_target(tool_input: Mapping[str, Any]) -> Path | None:
    file_path = as_string(tool_input.get("file_path"))
    return _resolve_path(file_path) if file_path else None


def _tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("tool_input")
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_or_none(value: Any) -> dict[str, Any] | None:
    return dict(value) if isinstance(value, Mapping) else None


def _string_or_none(value: Any) -> str | None:
    text = as_string(value)
    return text if text else None


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    return value if isinstance(value, int) else None


def _common_payload_fields(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "session_id": as_string(payload.get("session_id")),
        "transcript_path": as_string(payload.get("transcript_path")),
        "cwd": as_string(payload.get("cwd")),
        "hook_event_name": as_string(payload.get("hook_event_name")),
    }


def _permission_payload_fields(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "permission_mode": _string_or_none(payload.get("permission_mode")),
    }


def _effort_payload_fields(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "effort": _mapping_or_none(payload.get("effort")),
    }


def _agent_payload_fields(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent_id": _string_or_none(payload.get("agent_id")),
        "agent_type": _string_or_none(payload.get("agent_type")),
    }


def _build_session_start_payload(payload: dict[str, Any]) -> ClaudeSessionStartPayload:
    return ClaudeSessionStartPayload(
        **_common_payload_fields(payload),
        source=as_string(payload.get("source")),
        model=_string_or_none(payload.get("model")),
        agent_type=_string_or_none(payload.get("agent_type")),
    )


def _build_pre_tool_use_payload(payload: dict[str, Any]) -> ClaudePreToolUsePayload:
    return ClaudePreToolUsePayload(
        **_common_payload_fields(payload),
        **_permission_payload_fields(payload),
        **_effort_payload_fields(payload),
        **_agent_payload_fields(payload),
        tool_name=as_string(payload.get("tool_name")),
        tool_input=_tool_input(payload),
        tool_use_id=_string_or_none(payload.get("tool_use_id")),
    )


def _build_post_tool_use_payload(payload: dict[str, Any]) -> ClaudePostToolUsePayload:
    tool_input = _tool_input(payload)
    return ClaudePostToolUsePayload(
        **_common_payload_fields(payload),
        **_permission_payload_fields(payload),
        **_effort_payload_fields(payload),
        **_agent_payload_fields(payload),
        tool_name=as_string(payload.get("tool_name")),
        tool_input=tool_input,
        tool_response=payload.get("tool_response"),
        tool_use_id=_string_or_none(payload.get("tool_use_id")),
        duration_ms=_int_or_none(payload.get("duration_ms")),
    )


def _build_user_prompt_submit_payload(
    payload: dict[str, Any],
) -> ClaudeUserPromptSubmitPayload:
    return ClaudeUserPromptSubmitPayload(
        **_common_payload_fields(payload),
        **_permission_payload_fields(payload),
        **_agent_payload_fields(payload),
        prompt=as_string(payload.get("prompt")),
    )


def _build_stop_payload(payload: dict[str, Any]) -> ClaudeStopPayload:
    return ClaudeStopPayload(
        **_common_payload_fields(payload),
        **_permission_payload_fields(payload),
        **_effort_payload_fields(payload),
        **_agent_payload_fields(payload),
        stop_hook_active=payload.get("stop_hook_active") is True,
        last_assistant_message=as_string(payload.get("last_assistant_message")),
    )


def parse_claude_event_payload(
    payload: Mapping[str, Any] | None = None,
) -> ClaudeEventPayload | None:
    data = read_payload_or_stdin(payload)
    event_name = as_string(data.get("hook_event_name"))
    if event_name == "SessionStart":
        return _build_session_start_payload(data)
    if event_name == "PreToolUse":
        return _build_pre_tool_use_payload(data)
    if event_name == "PostToolUse":
        return _build_post_tool_use_payload(data)
    if event_name == "UserPromptSubmit":
        return _build_user_prompt_submit_payload(data)
    if event_name == "Stop":
        return _build_stop_payload(data)
    return None


def session_start(
    event_payload: ClaudeSessionStartPayload,
    *,
    stdout: TextIO | None = None,
) -> int:
    """Handle a Claude ``SessionStart`` hook invocation."""

    config = workflow_config_for_project(_project_dir())
    if config is not None:
        _persist_shell_env(config.root, event_payload.session_id)

    if event_payload.agent_type:
        # Claude subagents receive the workflow shell environment persisted by
        # the main session. Do not inject the main-session policy into subagent
        # context.
        return 0

    return emit_session_start_policy(event_payload, config=config, stdout=stdout)


def emit_session_start_policy(
    event_payload: ClaudeSessionStartPayload,
    *,
    config: Any | None = None,
    stdout: TextIO | None = None,
) -> int:
    """Emit the Claude workflow authoring policy for a main session."""

    config = config or workflow_config_for_project(_project_dir())
    if config is None:
        return 0

    if event_payload.source == "compact":
        return 0
    if event_payload.source != "clear" and session_policy_was_announced(
        config.root,
        "claude",
        event_payload.session_id,
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
    record_session_policy_announced(config.root, "claude", event_payload.session_id)
    return 0


def post_read(
    event_payload: ClaudePostToolUsePayload,
    *,
    stdout: TextIO | None = None,
    state_dir: Path | None = None,
) -> int:
    """Handle a Claude ``PostToolUse`` Read hook invocation."""

    return record_authoring_read(
        project_dir=_project_dir(),
        plugin_root=_plugin_root(),
        session_id=event_payload.session_id,
        read_target=_read_target(event_payload.tool_input),
        state_dir=state_dir,
        stdout=stdout,
    )


def pre_write(
    event_payload: ClaudePreToolUsePayload,
    *,
    stdout: TextIO | None = None,
    state_dir: Path | None = None,
) -> int:
    """Handle a Claude ``PreToolUse`` write hook invocation."""

    return block_unread_authoring_write(
        project_dir=_project_dir(),
        session_id=event_payload.session_id,
        edit_targets=_edit_targets(event_payload.tool_name, event_payload.tool_input),
        state_dir=state_dir,
        stdout=stdout,
    )


def user_prompt_submit(
    event_payload: ClaudeUserPromptSubmitPayload,
    *,
    stdout: TextIO | None = None,
    runner: CommandRunner | None = None,
) -> int:
    """Handle a Claude ``UserPromptSubmit`` hook invocation."""

    return inject_prompt_issue_context(
        project_dir=_project_dir(),
        session_id=event_payload.session_id,
        prompt_text=event_payload.prompt,
        stdout=stdout,
        runner=runner,
    )


def stop(
    event_payload: ClaudeStopPayload,
    *,
    stdout: TextIO | None = None,
    runner: CommandRunner | None = None,
) -> int:
    """Handle a Claude ``Stop`` hook invocation."""

    return record_stop_issue_references(
        project_dir=_project_dir(),
        session_id=event_payload.session_id,
        scan_text=scan_text_values(event_payload.last_assistant_message),
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
    event_payload = parse_claude_event_payload(payload)
    if isinstance(event_payload, ClaudeSessionStartPayload):
        return session_start(event_payload, stdout=stdout)
    if isinstance(event_payload, ClaudePostToolUsePayload):
        return post_read(event_payload, stdout=stdout)
    if isinstance(event_payload, ClaudePreToolUsePayload):
        return pre_write(event_payload, stdout=stdout)
    if isinstance(event_payload, ClaudeUserPromptSubmitPayload):
        return user_prompt_submit(event_payload, stdout=stdout)
    if isinstance(event_payload, ClaudeStopPayload):
        return stop(event_payload, stdout=stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
