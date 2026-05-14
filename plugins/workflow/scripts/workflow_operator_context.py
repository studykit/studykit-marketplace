#!/usr/bin/env python3
"""Workflow operator subagent context helpers.

Operator-specific detection and the ``additionalContext`` template are shared
between Claude's ``SubagentStart`` entry (``hook_claude.py``) and the Codex
``SessionStart`` operator branch (``hook_codex.py``). Hosting
them here keeps a single home for operator-specific text and detection so
neither hook script has to import the other.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

WORKFLOW_OPERATOR_AGENT_NAME = "workflow-operator"


def build_operator_subagent_context(parent_session_id: str, project_root: Path) -> str:
    """Build the ``additionalContext`` block emitted when the operator subagent starts."""

    return (
        "## workflow operator session\n\n"
        f"Parent session id: `{parent_session_id}`\n"
        f"Workflow project root: `{project_root}`\n\n"
        "Use workflow wrapper commands so the operator shell receives "
        "`WORKFLOW_SESSION_ID` for this parent session before invoking workflow "
        "scripts. Reads recorded by the main session live under this id; "
        "defaulting to the subagent's own runtime session id will check the "
        "wrong ledger and guarded writes will fail. If the workflow environment "
        "contract is unavailable, pass this parent session id explicitly as "
        "`--session`."
    )


def payload_targets_operator(payload: Mapping[str, Any]) -> bool:
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
