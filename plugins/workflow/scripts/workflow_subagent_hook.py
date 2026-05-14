#!/usr/bin/env python3
"""Workflow operator subagent start hook.

Dedicated entry point invoked from ``plugins/workflow/agents/workflow-operator.md``
frontmatter when Claude spawns the workflow-operator subagent. The hook emits
the parent session id as ``additionalContext`` so the operator binds its
ledger and guard lookups to the main session's read history.

Codex has no ``SubagentStart`` event, so the codex equivalent rides on
``SessionStart`` inside ``workflow_hook.py`` and reuses the helpers exported
here (``build_operator_subagent_context``, ``extract_codex_subagent_metadata``,
``payload_targets_operator``).
"""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TextIO

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from workflow_config import WorkflowConfigError, load_workflow_config  # noqa: E402
from workflow_hook import (  # noqa: E402
    emit,
    project_dir_from_payload,
    read_payload,
    session_id_from_payload,
)

WORKFLOW_OPERATOR_AGENT_NAME = "workflow-operator"


def subagent_start(
    payload: dict[str, Any] | None = None,
    *,
    stdout: TextIO | None = None,
) -> int:
    """SubagentStart entry point for the Claude workflow-operator subagent.

    Emits the parent session id as ``additionalContext`` so the operator
    binds its ledger and guard lookups to the main session's read history.
    The manifest matcher restricts firing to ``workflow-operator``; a
    defensive re-check keeps unrelated payloads silent.
    """

    if payload is None:
        payload = read_payload()
    output = stdout or sys.stdout

    if not payload_targets_operator(payload):
        return 0

    project_dir = project_dir_from_payload(payload)
    if project_dir is None:
        return 0

    try:
        config = load_workflow_config(project_dir)
    except WorkflowConfigError:
        return 0
    if config is None:
        return 0

    parent_session_id = session_id_from_payload(payload)
    if not parent_session_id:
        return 0

    context = build_operator_subagent_context(parent_session_id, config.root)
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "SubagentStart",
                "additionalContext": context,
            }
        },
        stdout=output,
    )
    return 0


def build_operator_subagent_context(parent_session_id: str, project_root: Path) -> str:
    """Build the additionalContext block injected when the operator subagent starts."""

    return (
        "## workflow operator session\n\n"
        f"Parent session id: `{parent_session_id}`\n"
        f"Workflow project root: `{project_root}`\n\n"
        "Use this parent session id with `--session` for every authoring "
        "ledger, guard, and provider script invocation in this subagent. Reads "
        "recorded by the main session live under this id; defaulting to the "
        "subagent's own session id or environment variables will check the "
        "wrong ledger and your guarded writes will fail."
    )


def payload_targets_operator(payload: dict[str, Any]) -> bool:
    """Return true when the SubagentStart payload targets workflow-operator."""

    for key in ("agent_type", "agent_name", "subagent_type"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip() == WORKFLOW_OPERATOR_AGENT_NAME:
            return True

    tool_input = payload.get("tool_input")
    if isinstance(tool_input, Mapping):
        for key in ("subagent_type", "agent_type", "agent_name"):
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip() == WORKFLOW_OPERATOR_AGENT_NAME:
                return True
    return False


def agent_name_matches_operator(name: str | None) -> bool:
    return bool(name) and name.strip() == WORKFLOW_OPERATOR_AGENT_NAME


def extract_codex_subagent_metadata(payload: dict[str, Any]) -> tuple[str, str | None]:
    """Return (parent_thread_id, agent_name) from a codex subagent transcript.

    Returns ("", None) when the transcript is unavailable or does not match
    the expected subagent metadata shape.
    """

    transcript_path = payload.get("transcript_path")
    if not isinstance(transcript_path, str) or not transcript_path:
        return "", None
    path = Path(transcript_path).expanduser()
    if not path.is_file():
        return "", None

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
                if not isinstance(metadata, Mapping):
                    continue
                return (
                    _parent_thread_id_from_metadata(metadata),
                    _agent_name_from_metadata(metadata),
                )
    except OSError:
        return "", None

    return "", None


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


def main() -> int:
    return subagent_start()


if __name__ == "__main__":
    raise SystemExit(main())
