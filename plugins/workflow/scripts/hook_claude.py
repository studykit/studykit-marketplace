#!/usr/bin/env python3
"""Claude hook adapter and CLI entry point.

This module owns Claude Code payload and environment handling. Shared workflow
policy, ledger, guard, and issue-cache behavior lives in ``workflow_hook.py``
as plain functions.

The script is the executable entry point for Claude's hook manifest
(``plugins/workflow/hooks/hooks.json``) and the SubagentStart hook declared in
``plugins/workflow/agents/workflow-operator.md`` frontmatter. Each hook command
invokes ``python3 hook_claude.py``; ``main`` dispatches by the
``hook_event_name`` value in the hook payload. When this adapter writes hook
output to stdout, it writes JSON only; no plain-text hook output is used.
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
from workflow_operator_context import (  # noqa: E402
    build_operator_subagent_context,
    payload_targets_operator,
)
from workflow_session_state import (  # noqa: E402
    record_session_policy_announced,
    session_policy_was_announced,
)

CLAUDE_FILE_EDIT_TOOLS = {"Write", "Edit", "MultiEdit"}
CLAUDE_SESSION_START_SOURCES = {"startup", "resume", "clear", "compact"}


@dataclass(frozen=True)
class ClaudeCommonPayload:
    raw: dict[str, Any]
    event_name: str
    session_id: str
    transcript_path: str
    cwd: str
    permission_mode: str


@dataclass(frozen=True)
class ClaudeSessionStartPayload(ClaudeCommonPayload):
    source: str
    model: str
    agent_type: str


@dataclass(frozen=True)
class ClaudePreToolUsePayload(ClaudeCommonPayload):
    tool_name: str
    tool_input: dict[str, Any]
    edit_targets: tuple[EditTarget, ...]


@dataclass(frozen=True)
class ClaudePostToolUsePayload(ClaudeCommonPayload):
    tool_name: str
    tool_input: dict[str, Any]
    tool_response: Any
    read_target: Path | None


@dataclass(frozen=True)
class ClaudeUserPromptSubmitPayload(ClaudeCommonPayload):
    prompt_text: str


@dataclass(frozen=True)
class ClaudeStopPayload(ClaudeCommonPayload):
    stop_hook_active: bool
    last_assistant_message: str
    scan_text: str


@dataclass(frozen=True)
class ClaudeSubagentStartPayload(ClaudeCommonPayload):
    agent_id: str
    agent_type: str
    targets_operator: bool


ClaudeEventPayload = (
    ClaudeSessionStartPayload
    | ClaudePreToolUsePayload
    | ClaudePostToolUsePayload
    | ClaudeUserPromptSubmitPayload
    | ClaudeStopPayload
    | ClaudeSubagentStartPayload
)


def _project_dir() -> Path:
    return Path(os.environ["CLAUDE_PROJECT_DIR"]).expanduser().resolve()


def _plugin_root() -> Path:
    return Path(os.environ["CLAUDE_PLUGIN_ROOT"]).expanduser().resolve()


def _resolve_path(raw_path: str) -> Path:
    return resolve_file_path(raw_path, base_dir=_project_dir())


def _edit_targets(payload: dict[str, Any]) -> tuple[EditTarget, ...]:
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict) or tool_name not in CLAUDE_FILE_EDIT_TOOLS:
        return ()
    file_path = as_string(tool_input.get("file_path"))
    if not file_path:
        return ()
    content = tool_input.get("content") if tool_name == "Write" else None
    if not isinstance(content, str):
        content = None
    return (EditTarget(path=_resolve_path(file_path), content=content),)


def _tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("tool_input")
    return dict(value) if isinstance(value, Mapping) else {}


def _session_start_source(payload: dict[str, Any]) -> str:
    source = as_string(payload.get("source")).lower()
    return source if source in CLAUDE_SESSION_START_SOURCES else ""


def _common_payload_fields(payload: dict[str, Any], event_name: str) -> dict[str, Any]:
    return {
        "raw": payload,
        "event_name": as_string(payload.get("hook_event_name")) or event_name,
        "session_id": as_string(payload.get("session_id")),
        "transcript_path": as_string(payload.get("transcript_path")),
        "cwd": as_string(payload.get("cwd")),
        "permission_mode": as_string(payload.get("permission_mode")),
    }


def _build_session_start_payload(payload: dict[str, Any]) -> ClaudeSessionStartPayload:
    return ClaudeSessionStartPayload(
        **_common_payload_fields(payload, "SessionStart"),
        source=_session_start_source(payload),
        model=as_string(payload.get("model")),
        agent_type=as_string(payload.get("agent_type")),
    )


def _build_pre_tool_use_payload(payload: dict[str, Any]) -> ClaudePreToolUsePayload:
    return ClaudePreToolUsePayload(
        **_common_payload_fields(payload, "PreToolUse"),
        tool_name=as_string(payload.get("tool_name")),
        tool_input=_tool_input(payload),
        edit_targets=_edit_targets(payload),
    )


def _build_post_tool_use_payload(payload: dict[str, Any]) -> ClaudePostToolUsePayload:
    tool_input = _tool_input(payload)
    file_path = as_string(tool_input.get("file_path"))
    return ClaudePostToolUsePayload(
        **_common_payload_fields(payload, "PostToolUse"),
        tool_name=as_string(payload.get("tool_name")),
        tool_input=tool_input,
        tool_response=payload.get("tool_response"),
        read_target=_resolve_path(file_path) if file_path else None,
    )


def _build_user_prompt_submit_payload(
    payload: dict[str, Any],
) -> ClaudeUserPromptSubmitPayload:
    return ClaudeUserPromptSubmitPayload(
        **_common_payload_fields(payload, "UserPromptSubmit"),
        prompt_text=_user_prompt_text(payload),
    )


def _build_stop_payload(payload: dict[str, Any]) -> ClaudeStopPayload:
    return ClaudeStopPayload(
        **_common_payload_fields(payload, "Stop"),
        stop_hook_active=payload.get("stop_hook_active") is True,
        last_assistant_message=as_string(payload.get("last_assistant_message")),
        scan_text=_stop_scan_text(payload),
    )


def _user_prompt_text(payload: dict[str, Any]) -> str:
    return as_string(payload.get("prompt"))


def _stop_scan_text(payload: dict[str, Any]) -> str:
    return scan_text_values(as_string(payload.get("last_assistant_message")))


def _build_subagent_start_payload(payload: dict[str, Any]) -> ClaudeSubagentStartPayload:
    return ClaudeSubagentStartPayload(
        **_common_payload_fields(payload, "SubagentStart"),
        agent_id=as_string(payload.get("agent_id")),
        agent_type=as_string(payload.get("agent_type")),
        targets_operator=payload_targets_operator(payload),
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
    if event_name == "SubagentStart":
        return _build_subagent_start_payload(data)
    return None


def session_start(
    event_payload: ClaudeSessionStartPayload,
    *,
    stdout: TextIO | None = None,
) -> int:
    """Handle a Claude ``SessionStart`` hook invocation."""

    if event_payload.agent_type:
        # Claude operator subagent context is injected through SubagentStart.
        return 0

    return emit_session_start_policy(event_payload, stdout=stdout)


def emit_session_start_policy(
    event_payload: ClaudeSessionStartPayload,
    *,
    stdout: TextIO | None = None,
) -> int:
    """Emit the Claude workflow authoring policy for a main session."""

    config = workflow_config_for_project(_project_dir())
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
        read_target=event_payload.read_target,
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
        edit_targets=event_payload.edit_targets,
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
        prompt_text=event_payload.prompt_text,
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
        scan_text=event_payload.scan_text,
        stop_hook_active=event_payload.stop_hook_active,
        stdout=stdout,
        runner=runner,
    )


def subagent_start(
    event_payload: ClaudeSubagentStartPayload,
    *,
    stdout: TextIO | None = None,
) -> int:
    """Handle a Claude ``SubagentStart`` hook invocation."""

    if not event_payload.targets_operator:
        return 0

    if not event_payload.session_id:
        return 0

    config = workflow_config_for_project(_project_dir())
    if config is None:
        return 0

    emit_json(
        {
            "hookSpecificOutput": {
                "hookEventName": "SubagentStart",
                "additionalContext": build_operator_subagent_context(
                    event_payload.session_id,
                    config.root,
                ),
            }
        },
        stdout=stdout,
    )
    return 0


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
    if isinstance(event_payload, ClaudeSubagentStartPayload):
        return subagent_start(event_payload, stdout=stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
